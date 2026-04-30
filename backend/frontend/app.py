import gradio as gr
import requests

URL = "http://localhost:8000"

def login(email, password):
    r = requests.post(URL + "/auth/login",data={"username": email, "password": password})
    if r.status_code == 200:
        token = r.json()["access_token"]
        return token, "Login Success"
    return "", "Login Failed"

def chat_ui(message, token, history):
    if token == "":
        return history, history
    r = requests.post(URL + "/chatbot/chat",json={"message": message},headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 200:
        bot_reply = r.json()["response"]
    else:
        bot_reply = "Unauthorized / Error"
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": bot_reply})
    return history, history

with gr.Blocks() as app:
    token = gr.State("")
    chat_history = gr.State([])
    gr.Markdown("Employee Chatbot")
    with gr.Row():
        email = gr.Textbox(label="Email")
        password = gr.Textbox(label="Password", type="password")
    status = gr.Textbox(label="Status")
    gr.Button("Login").click(login, [email, password], [token, status])
    chatbot = gr.Chatbot()
    with gr.Row():
        msg = gr.Textbox(placeholder="Type your message...", scale=4)
        send_btn = gr.Button("Send", scale=1)
    send_btn.click(chat_ui, [msg, token, chat_history], [chatbot, chat_history]).then(lambda: "", None, msg)
    msg.submit(chat_ui, [msg, token, chat_history], [chatbot, chat_history]).then(lambda: "", None, msg)

app.launch(share=True)