from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import date

from auth.dependencies import get_current_user
from langgraph_agent.graph import chat_graph

from db.database import SessionLocal
from models.reminder_model import Reminder
from models.chat_history_model import ChatHistory

router = APIRouter(prefix='/chatbot', tags=['Chatbot'])


class ChatRequest(BaseModel):
    message: str

def load_history(db, user_id, limit=10):
    rows = db.query(ChatHistory)\
        .filter(ChatHistory.user_id == user_id)\
        .order_by(ChatHistory.created_at.desc())\
        .limit(limit).all()

    history = []
    for row in reversed(rows):
        history.append(f"User: {row.message}")
        history.append(f"Assistant: {row.response}")  

    return history


def save_chat(db, user_id, message, response):
    chat = ChatHistory(
        user_id=user_id,
        message=message,
        response=response
    )
    db.add(chat)
    db.commit()

@router.post('/chat')
def chat(data: ChatRequest, user=Depends(get_current_user)):
    user_id = user['id']
    db = SessionLocal()

    try:
        history = load_history(db, user_id)
        last_employee = None
        for h in reversed(history):
            if "Employee:" in h:
                last_employee = h.split("Employee:")[-1].strip()
                break
        result = chat_graph.invoke({
            'message': data.message,
            'role': user['role'],
            'user_id': user_id,
            'chat_history': history,
            'last_employee': last_employee
        })

        response = result.get('response', "Something went wrong.")
        today = date.today()

        reminder = db.query(Reminder).filter(
            Reminder.employee_id == user_id,
            Reminder.reminder_date == today,
            Reminder.status == "pending"
        ).first()

        if reminder:
            response = f"""
Hey 

Looks like you missed logging your progress yesterday.

No worries — want to quickly add it now?

{response}
"""
            reminder.status = "sent"
            db.commit()
        save_chat(db, user_id, data.message, response)

        return {'response': response}

    finally:
        db.close()