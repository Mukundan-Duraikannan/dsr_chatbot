import os
import json
from datetime import date, timedelta
from langchain_groq import ChatGroq
from models.dailylogs_model import DailyLog
from models.employee_model import Employee
from db.database import SessionLocal
from dotenv import load_dotenv
import os
load_dotenv()

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),model="openai/gpt-oss-120b",temperature=0)

def detect_intent(state):
    msg = state['message']
    role = state['role']

    if role == 'employee':
        state['intent'] = 'daily_update'
    else:
        state['intent'] = 'manager_query'
    return state

def save_daily_update(state):
    msg = state['message']
    db=SessionLocal()
    prompt=f"""
Extract JSON only:
{{
  "task":"",
  "status":"",
  "time_spent":0
}}

Text: {msg}
"""
    
    result = llm.invoke(prompt).content
    try:
        data = json.loads(result)
    except:
        data = {
            "task": msg,
            "status": "submitted",
            "time_spent": 0
        }

    log = DailyLog(employee_id=state['user_id'],task=data['task'],status=data['status'],time_spent=data['time_spent'])
    db.add(log)
    db.commit()
    db.close()
    state['response'] = 'Daily progress saved successfully.'
    return state

def manager_summary(state):
    msg = state['message']
    db = SessionLocal()
    employees = db.query(Employee).all()
    target = None

    for e in employees:
        if e.name.lower() in msg.lower():
            target = e
            break

    if not target:
        state['response'] = 'Employee not found.'
        db.close()
        return state

    days = 7
    if '30' in msg:
        days = 30
    elif '15' in msg:
        days = 15

    from_date = date.today() - timedelta(days=days)

    rows = db.query(DailyLog).filter(
        DailyLog.employee_id == target.id,
        DailyLog.log_date >= from_date
    ).all()

    if not rows:
        state['response']="No logs found"
        db.close()
        return state

    logs_text = "\n".join([f"Date:{r.log_date},Task:{r.task},Status:{r.status},Hours:{r.time_spent}"
        for r in rows 
    ])
     
    prompt = f"""
Summarize the following employee progress for manager.
Give concise bullet points.
Mention completed work, pending work, productivity trend.

Employee: {target.name}
Logs:
{logs_text}
"""
    summary=llm.invoke(prompt).content
    state['response']=summary
    db.close()
    return state