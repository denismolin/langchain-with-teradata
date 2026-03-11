import os
import gradio as gr
from IPython.display import display, HTML

def launch_rag_ui(chat_fn, title="Simple RAG Demo", port=7860, public_base_url="https://dmproject.myddns.me"):
    jupyterhub_user = os.environ.get("JUPYTERHUB_USER", "denis")

    with gr.Blocks() as demo:
        gr.Markdown(f"# {title}")
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(placeholder="Ask a question...")
        clear = gr.Button("Clear")

        msg.submit(chat_fn, [msg, chatbot], [chatbot, msg])
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