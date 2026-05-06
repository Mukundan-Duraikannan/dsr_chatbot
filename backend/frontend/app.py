import gradio as gr
import requests

URL = "http://localhost:3978"

def login(email, password):
    try:
        r = requests.post(
            URL + "/auth/login",
            data={"username": email, "password": password}
        )

        if r.status_code == 200:
            token = r.json()["access_token"]

            h = requests.get(
                URL + "/chatbot/history",
                headers={"Authorization": f"Bearer {token}"}
            )
            history = h.json()["history"] if h.status_code == 200 else []
            formatted_history = []
            for msg, res in history:
                if msg == "SYSTEM":
                    formatted_history.append({"role": "assistant","content": res})
                else:
                    formatted_history.append({"role": "user","content": msg})
                    formatted_history.append({"role": "assistant","content": res})
            return token, "Login successful", formatted_history, formatted_history

        else:
            return "", "Invalid credentials", [], []

    except Exception as e:
        return "", f"Error: {str(e)}", [], []


def chat_ui(message, token, history):
    if not token:
        return history, history

    try:
        r = requests.post(
            URL + "/chatbot/chat",
            json={"message": message},
            headers={"Authorization": f"Bearer {token}"}
        )

        if r.status_code == 200:
            bot_reply = r.json()["response"]
        else:
            bot_reply = "Unauthorized or server error"

    except Exception as e:
        bot_reply = f"Error: {str(e)}"

    history = history or []
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": bot_reply})

    return history, history


with gr.Blocks() as app:
    token = gr.State("")
    chat_history = gr.State([])

    gr.Markdown("## Employee Productivity Chatbot")

    with gr.Row():
        email = gr.Textbox(label="Email")
        password = gr.Textbox(label="Password", type="password")

    status = gr.Textbox(label="Status", interactive=False)

    chatbot = gr.Chatbot(label="Chat")

    gr.Button("Login").click(
        login,
        [email, password],
        [token, status, chatbot, chat_history]
    )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Type your message...",
            scale=4
        )
        send_btn = gr.Button("Send", scale=1)

    send_btn.click(
        chat_ui,
        [msg, token, chat_history],
        [chatbot, chat_history]
    ).then(lambda: "", None, msg)

    msg.submit(
        chat_ui,
        [msg, token, chat_history],
        [chatbot, chat_history]
    ).then(lambda: "", None, msg)


app.launch(share=True)