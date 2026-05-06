from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import date, timedelta

from auth.dependencies import get_current_user
from langgraph_agent.graph import chat_graph

from db.database import SessionLocal
from models.reminder_model import Reminder
from models.chat_history_model import ChatHistory
from models.employee_model import Employee
from models.dailylogs_model import DailyLog

router = APIRouter(prefix='/chatbot', tags=['Chatbot'])


class ChatRequest(BaseModel):
    message: str


def load_history(db, user_id, limit=10):
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.asc())
        .limit(limit)
        .all()
    )

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

def load_ui_history(db, user_id, limit=100):
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.asc())
        .limit(limit)
        .all()
    )

    return [(row.message, row.response) for row in rows]

@router.get('/history')
def get_history(user=Depends(get_current_user)):
    db = SessionLocal()
    try:
        history = load_ui_history(db, user['id'])
        print("HISTORY FROM DB:", history)
        return {"history": history}
    finally:
        db.close()

@router.post('/chat')
def chat(data: ChatRequest, user=Depends(get_current_user)):
    db = SessionLocal()

    try:
        user_id = user['id']
        role = user['role']
        msg_lower = data.message.lower()

        history = load_history(db, user_id)

        if role == "manager" and "missed" in msg_lower:

            yesterday = date.today() - timedelta(days=1)

            all_employees = db.query(Employee).all()

            logged_ids = db.query(DailyLog.employee_id).filter(
                DailyLog.log_date == yesterday
            ).all()

            logged_ids = {x[0] for x in logged_ids}

            missed_employees = [
                emp.name for emp in all_employees
                if emp.id not in logged_ids
            ]

            return {
                "response": f"Employees who missed yesterday's DSR:\n{missed_employees}"
            }

        manager_keywords = [
            "summary", "report", "progress of",
            "logs of", "status of", "show employees",
            "team report"
        ]

        if role != 'manager':
            if any(keyword in msg_lower for keyword in manager_keywords):
                return {
                    "response": "You are not authorized to view other employees' data."
                }

        last_employee = None
        for h in reversed(history):
            if h.startswith("User:"):
                last_employee = h.replace("User:", "").strip()
                break

        result = chat_graph.invoke({
            'message': data.message,
            'role': role,
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
            response = (
                "You missed logging your DSR yesterday.\n"
                "Please update it when possible.\n\n"
                + response
            )
            reminder.status = "sent"
            db.commit()
        save_chat(db, user_id, data.message, response)

        return {'response': response}

    finally:
        db.close()