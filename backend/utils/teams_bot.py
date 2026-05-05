import requests
from aiohttp import web
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
from botbuilder.schema import Activity
import os
from dotenv import load_dotenv


APP_ID = os.getenv("APP_ID")
APP_PASSWORD = os.getenv("APP_PASSWORD")

adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
# adapter_settings = BotFrameworkAdapterSettings("", "")
adapter = BotFrameworkAdapter(adapter_settings)
async def handle_message(turn_context: TurnContext):
    user_msg = turn_context.activity.text

    print("User said:", user_msg)
    try:
        res = requests.post(
            "http://localhost:8000/chatbot/chat",
            json={"message": user_msg}
        )

        if res.status_code == 200:
            reply = res.json().get("response", "No response")
        else:
            reply = "Backend error"

    except Exception as e:
        reply = f"Error: {str(e)}"

    await turn_context.send_activity(reply)


async def messages(req):
    body = await req.json()
    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    async def aux(turn_context):
        await handle_message(turn_context)

    await adapter.process_activity(activity, auth_header, aux)
    return web.Response(status=200)


app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    web.run_app(app, port=3978)