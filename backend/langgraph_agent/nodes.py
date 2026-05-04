import os
import json
import re
from datetime import date, timedelta
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from models.dailylogs_model import DailyLog
from models.employee_model import Employee
from db.database import SessionLocal

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="openai/gpt-oss-120b",
    temperature=0
)

SYSTEM_PROMPT = """
You are a friendly workplace assistant.

Style:
- Talk like a human, not a robot
- Be warm, natural, and conversational
- Keep responses short and clear
- Sound like a teammate (Slack/Teams style)

Behavior:
- Use past conversation if helpful
- Avoid repeating phrases
- Do not hallucinate

Goal:
Help employees log work and help managers understand progress easily.
"""


def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except:
        return None


VALID_STATUS = {"completed", "in progress", "blocked"}

def validate_log(data):
    return (
        isinstance(data.get("task"), str) and
        data.get("status") in VALID_STATUS and
        isinstance(data.get("time_spent"), int)
    )


def detect_intent(state):
    msg = state['message']

    prompt = f"""
Classify the intent of this message.

Message: "{msg}"

Return EXACTLY one word from:
greeting | daily_update | manager_query | thanks | follow_up | other

No explanation. No extra text.
"""

    intent = llm.invoke(prompt).content.strip().lower()

    allowed = {"greeting", "daily_update", "manager_query", "thanks", "follow_up"}
    if intent not in allowed:
        intent = "other"

    state['intent'] = intent
    return state



def handle_smalltalk(state):
    msg = state['message']
    history_text = "\n".join(state.get("chat_history", []))

    prompt = f"""
You are a friendly coworker chatting casually.

Conversation:
{history_text}

Message:
{msg}

Reply:
- Short
- Natural
- Friendly
"""

    state['response'] = llm.invoke(prompt).content.strip()
    return state


def save_daily_update(state):
    msg = state['message']
    db = SessionLocal()

    history_text = "\n".join(state.get("chat_history", []))

    prompt = f"""
You are a data extraction engine.

{SYSTEM_PROMPT}

Extract structured data.

Return ONLY valid JSON.

Schema:
{{
  "task": string,
  "status": "completed" | "in progress" | "blocked",
  "time_spent": integer
}}

Rules:
- No explanation
- No extra text
- Do NOT invent info
- If unsure:
  status = "in progress"
  time_spent = 0
- Keep task short

Conversation:
{history_text}

Message:
{msg}
"""

    result = llm.invoke(prompt).content.strip()

    data = extract_json(result)

    if not data or not validate_log(data):
        data = {
            "task": msg,
            "status": "in progress",
            "time_spent": 0
        }

    log = DailyLog(
        employee_id=state['user_id'],
        task=data['task'],
        status=data['status'],
        time_spent=data['time_spent']
    )

    db.add(log)
    db.commit()
    db.close()

    state['response'] = f"""
Nice, I've logged it:

• {data['task']}  
• Status: {data['status']}  
• Time: {data['time_spent']} hrs  

Anything else you worked on?
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
        target = db.query(Employee).filter(
            Employee.name == state["last_employee"]
        ).first()

    if not target:
        state['response'] = "Which employee are you asking about?"
        db.close()
        return state

    state["last_employee"] = target.name

    match = re.search(r'\d+', msg)
    days = int(match.group()) if match else 7

    from_date = date.today() - timedelta(days=days)

    rows = db.query(DailyLog).filter(
        DailyLog.employee_id == target.id,
        DailyLog.log_date >= from_date
    ).all()

    if not rows:
        state['response'] = f"No logs found for {target.name} in the last {days} days."
        db.close()
        return state

    logs_text = "\n".join([
        f"Date: {r.log_date}, Task: {r.task}, Status: {r.status}, Hours: {r.time_spent}"
        for r in rows
    ])

    prompt = f"""
{SYSTEM_PROMPT}

You are a manager giving an update.

STRICT RULES:
- Use ONLY the logs provided
- Do NOT assume anything
- If no blockers → say "No blockers reported"
- If no trend → say "No clear trend"
- Do NOT add fake insights

Conversation:
{history_text}

Employee: {target.name}
Time Period: Last {days} days

Logs:
{logs_text}

Output:
- Bullet points
- Short
- Clear
"""

    summary = llm.invoke(prompt).content.strip()

    state['response'] = summary
    db.close()

    return state