import uuid
import os

SYSTEM_PROMPT = """
You are a SQL assistant with access to tools.

IMPORTANT:
- You MUST use tools to answer questions about the database.
- NEVER answer from general knowledge.
- ALWAYS inspect the database first using tools.
- If the user asks about tables, you MUST call a tool to list tables.
- If you do not call tools, your answer is wrong.

Rules:
- Do not invent schema.
- Be concise.
"""


def _get_text_content(content):
    """Extract readable text from LangChain message content."""
    if content is None:
        return ""

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text" and "text" in item:
                    parts.append(str(item["text"]))
        return "\n".join(p for p in parts if p).strip()

    return str(content).strip()


def _extract_answer_and_trace(result: dict) -> tuple[str, str]:
    """
    Extract:
    - final assistant answer
    - markdown trace of tool calls + skills used
    """
    messages = result.get("messages", [])

    final_answer = ""
    tool_calls_md = []
    used_skills = []
    seen_skills = set()

    for msg in messages:
        msg_type = getattr(msg, "type", msg.__class__.__name__.lower())

        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_name = tc.get("name", "unknown_tool")
                tool_args = tc.get("args", {})

                tool_calls_md.append(
                    f"### Tool: `{tool_name}`\n"
                    f"**Args:**\n```python\n{tool_args}\n```"
                )

                if tool_name == "load_skill" and isinstance(tool_args, dict):
                    skill_name = tool_args.get("skill_name")
                    if skill_name and skill_name not in seen_skills:
                        used_skills.append(skill_name)
                        seen_skills.add(skill_name)

        if msg_type == "tool":
            tool_name = getattr(msg, "name", None) or getattr(msg, "tool_name", "tool")
            content = _get_text_content(getattr(msg, "content", ""))

            if tool_name == "load_skill" and content.startswith("Loaded skill:"):
                first_line = content.splitlines()[0]
                skill_name = first_line.replace("Loaded skill:", "").strip()
                if skill_name and skill_name not in seen_skills:
                    used_skills.append(skill_name)
                    seen_skills.add(skill_name)

        if msg_type == "ai":
            text = _get_text_content(getattr(msg, "content", ""))
            if text:
                final_answer = text

    if not final_answer.strip():
        final_answer = _get_text_content(result.get("output", "")) or "No answer was produced."

    if not tool_calls_md:
        tool_calls_md = ["No tool calls were made."]

    if used_skills:
        skills_md = "\n".join(f"- `{name}`" for name in used_skills)
    else:
        skills_md = "No skills were explicitly loaded."

    trace_md = (
        "## Tool Calls\n\n"
        + "\n\n".join(tool_calls_md)
        + "\n\n## Skills Used\n\n"
        + skills_md
    )

    return final_answer, trace_md


def build_skill_answer(agent, return_trace=False):
    async def skill_answer(question: str):
        result = await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": question}
                ]
            },
            config={"configurable": {"thread_id": f"sql-test-{uuid.uuid4()}"}},
        )

        answer, trace_md = _extract_answer_and_trace(result)
        return (answer, trace_md) if return_trace else answer

    return skill_answer

    import os
import gradio as gr
from IPython.display import display, HTML
import inspect

def launch_agent_ui(
    chat_fn,
    title="SQL Assistant Demo",
    port=7860,
    public_base_url="https://dmproject.myddns.me",
    show_trace=True,
    trace_title="Tool calls and skills used",
):
    jupyterhub_user = os.environ.get("JUPYTERHUB_USER", "denis")

    with gr.Blocks() as demo:
        gr.Markdown(f"# {title}")
        chatbot = gr.Chatbot(height=400)
        msg     = gr.Textbox(placeholder="Ask a question...")
        clear   = gr.Button("Clear")

        if show_trace:
            with gr.Accordion(trace_title, open=False):
                trace = gr.Markdown("No tool calls yet.")


        
        async def _submit_wrapper(message, history):
            if inspect.iscoroutinefunction(chat_fn):
                result = await chat_fn(message, history)
            else:
                result = chat_fn(message, history)
        
            # Backward compatibility:
            if show_trace:
                if isinstance(result, tuple):
                    if len(result) == 3:
                        return result
                    elif len(result) == 2:
                        history_out, msg_out = result
                        return history_out, "No trace available.", msg_out
        
                return history, "No trace available.", ""
        
            else:
                if isinstance(result, tuple) and len(result) >= 2:
                    return result[0], result[-1]
        
                return history, ""

        if show_trace:
            msg.submit(_submit_wrapper, [msg, chatbot], [chatbot, trace, msg])
            clear.click(
                lambda: ([], "No tool calls yet.", ""),
                None,
                [chatbot, trace, msg],
            )
        else:
            msg.submit(_submit_wrapper, [msg, chatbot], [chatbot, msg])
            clear.click(lambda: ([], ""), None, [chatbot, msg])

    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        inline=False,
        share=False,
        root_path=f"/user/{jupyterhub_user}/proxy/{port}/",
        prevent_thread_lock=True,
    )

    service_prefix = os.environ.get(
        "JUPYTERHUB_SERVICE_PREFIX",
        f"/user/{jupyterhub_user}/",
    )
    public_url = f"{public_base_url}{service_prefix}proxy/{port}/"

    display(HTML(f"""
    <div style="margin-bottom:10px;">
      <b>Open in new tab:</b>
      <a href="{public_url}" target="_blank">{public_url}</a>
    </div>

    <iframe
        src="{public_url}"
        width="100%"
        height="700"
        style="border:1px solid #ddd; border-radius:8px;"
    ></iframe>
    """))

    return demo