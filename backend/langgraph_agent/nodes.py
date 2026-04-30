import os
import json
from datetime import date, timedelta
from langchain_groq import ChatGroq
from models.dailylogs_model import DailyLog
from models.employee_model import Employee
from db.database import SessionLocal
from dotenv import load_dotenv
import os
import re
load_dotenv()

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),model="openai/gpt-oss-120b",temperature=0)


SYSTEM_PROMPT = """
You are an AI assistant for employee productivity tracking.

- Speak naturally like a human
- Be clear and concise
- Avoid robotic tone
- Use conversation context if available
- Do not hallucinate
"""

def detect_intent(state):
    msg = state['message']

    prompt = f"""
Classify the intent of this message:

"{msg}"

Return ONLY one:
- greeting
- daily_update
- manager_query
- thanks
- follow_up
- other
"""

    intent = llm.invoke(prompt).content.strip().lower()

    if intent not in ["greeting","daily_update","manager_query","thanks","follow_up"]:
        intent = "other"

    state['intent'] = intent
    return state

def handle_smalltalk(state):
    msg=state['message']

    prompt=f"""
    Respond naturally like a human to this message.

Message: {msg}
Keep it short and friendly.
"""
    state['response']=llm.invoke(prompt).content 
    return state

def save_daily_update(state):
    msg = state['message']
    db = SessionLocal()
    history_text = "\n".join(state.get("chat_history", []))
    prompt = f"""
{SYSTEM_PROMPT}
You are helping an employee log daily work.
Conversation so far:
{history_text}
From the latest message, extract structured data.
Return ONLY valid JSON:
{{
  "task": "short description of work",
  "status": "completed / in progress / blocked",
  "time_spent": number_of_hours
}}
Rules:
- If time not mentioned → assume 0
- If status unclear → use "in progress"
- Keep task short and meaningful
Message:
{msg}
"""
    result = llm.invoke(prompt).content
    try:
        data = json.loads(result)
    except:
        data = {
            "task": msg,
            "status": "in progress",
            "time_spent": 0
        }
    log = DailyLog(employee_id=state['user_id'],task=data['task'],status=data['status'],time_spent=data['time_spent'])
    db.add(log)
    db.commit()
    db.close()
    state['response'] = f"""
Got it 
I've logged your work:

• Task: {data['task']}  
• Status: {data['status']}  
• Time Spent: {data['time_spent']} hrs  

Anything else you'd like to add?
"""

    return state

def manager_summary(state):
    msg = state['message']
    db = SessionLocal()

    history_text = "\n".join(state.get("chat_history", []))
    employees = db.query(Employee).all()
    target = None
    for e in employees:
        if e.name.lower() in msg.lower():
            target = e
            break

    if not target and state.get("last_employee"):
        target=db.query(Employee).filter(Employee.name==state["last_employee"]).first()
        state['last_employee'] = target.name
        db.close()
        return state
        
    match=re.search(r'\d+',msg)
    if match:
        days=int(match.group())
    else:
        days=7
    from_date = date.today() - timedelta(days=days)
    rows = db.query(DailyLog).filter(DailyLog.employee_id == target.id,DailyLog.log_date >= from_date).all()

    if not rows:
        state['response'] = "No logs found for this period."
        db.close()
        return state

    logs_text = "\n".join([f"Date: {r.log_date}, Task: {r.task}, Status: {r.status}, Hours: {r.time_spent}"
        for r in rows
    ])
    prompt = f"""
{SYSTEM_PROMPT}

You are a manager assistant preparing a quick team update.

Conversation so far:
{history_text}

Analyze the employee logs and respond like a human manager.

Guidelines:
- Use natural language (not robotic)
- Use bullet points
- Be concise but insightful
- Highlight:
  • Completed work
  • Work in progress
  • Any blockers (if visible)
  • Productivity trend
Employee: {target.name}
Time Period: Last {days} days
Logs:
{logs_text}
"""
    summary = llm.invoke(prompt).content
    state['response'] = summary
    db.close()
    return state