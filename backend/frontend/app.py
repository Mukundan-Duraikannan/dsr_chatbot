import gradio as gr
import requests
 
URL = "http://localhost:8000"
 
def login(email, password):
    r = requests.post(
        URL + "/auth/login",
        data={"username": email, "password": password}
    )
    if r.status_code == 200:
        token = r.json()["access_token"]
        return token, "Login Success"
    return "", "Login Failed"
 
def chat(message, token):
    if token == "":
        return "Login first"
    r = requests.post(
        URL + "/chatbot/chat",
        json={"message": message},
        headers={"Authorization": "Bearer " + token}
    )
    if r.status_code == 200:
        return r.json()["response"]
    return "Unauthorized"
 
with gr.Blocks() as app:
    token = gr.State("")
    email = gr.Textbox(label="Email")
    password = gr.Textbox(label="Password", type="password")
    status = gr.Textbox(label="Status")
    gr.Button("Login").click(login, [email, password], [token, status])
    msg = gr.Textbox(label="Message")
    reply = gr.Textbox(label="Reply")
    gr.Button("Send").click(chat, [msg, token], reply)
 
app.launch(share=True)