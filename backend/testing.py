from pyngrok import ngrok

url = ngrok.connect(3978)
print(url)