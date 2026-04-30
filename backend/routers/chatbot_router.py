from fastapi import APIRouter, Depends
from pydantic import BaseModel
from auth.dependencies import get_current_user
from langgraph_agent.graph import chat_graph

from db.database import SessionLocal
from models.reminder_model import Reminder
from datetime import date

router = APIRouter(prefix='/chatbot', tags=['Chatbot'])


class ChatRequest(BaseModel):
    message: str


memory_store = {}

@router.post('/chat')
def chat(data: ChatRequest, user=Depends(get_current_user)):
    user_id = user['id']
    db = SessionLocal()

    if user_id not in memory_store:
        memory_store[user_id] = {
            "history": [],
            "last_employee": None
        }

    history = memory_store[user_id]["history"]
    last_employee = memory_store[user_id]["last_employee"]
    result=chat_graph.invoke({'message':data.message,'role':user['role'],'chat_history':history,'last_employee':last_employee})
    

    response = result['response']

    today = date.today()

    reminder = db.query(Reminder).filter(
        Reminder.employee_id == user_id,
        Reminder.reminder_date == today,
        Reminder.status == "pending"
    ).first()

    if reminder:
        response = f"""
Hey 👋

Looks like you missed logging your progress yesterday.

Would you like to add it now?

{response}
"""
        reminder.status = "sent"
        db.commit()
    history.append(f"User: {data.message}")
    history.append(f"Bot: {response}")

    memory_store[user_id]["history"] = history[-10:]
    memory_store[user_id]["last_employee"] = result.get("last_employee")

    db.close()

    return {'response': response}