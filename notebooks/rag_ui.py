import os
import gradio as gr
from IPython.display import display, HTML

def launch_rag_ui(
    chat_fn,
    title="Simple RAG Demo",
    port=7860,
    public_base_url="https://dmproject.myddns.me",
    show_sources=True,
):
    jupyterhub_user = os.environ.get("JUPYTERHUB_USER", "denis")

    with gr.Blocks() as demo:
        gr.Markdown(f"# {title}")
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(placeholder="Ask a question...")
        clear = gr.Button("Clear")

        if show_sources:
            with gr.Accordion("Retrieved sources", open=False):
                sources = gr.Markdown("No sources yet.")

        def _submit_wrapper(message, history):
            result = chat_fn(message, history)

            # Backward compatibility:
            # old chat_fn -> (history, msg_value)
            # new chat_fn -> (history, sources_md, msg_value)
            if show_sources:
                if isinstance(result, tuple):
                    if len(result) == 3:
                        return result
                    elif len(result) == 2:
                        history_out, msg_out = result
                        return history_out, "No sources available.", msg_out

                # very defensive fallback
                return history, "No sources available.", ""

            else:
                # original behavior
                if isinstance(result, tuple) and len(result) >= 2:
                    return result[0], result[-1]

                return history, ""

        if show_sources:
            msg.submit(_submit_wrapper, [msg, chatbot], [chatbot, sources, msg])
            clear.click(
                lambda: ([], "No sources yet.", ""),
                None,
                [chatbot, sources, msg]
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

    service_prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", f"/user/{jupyterhub_user}/")
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