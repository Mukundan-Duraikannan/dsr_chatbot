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
    match = re.search(r'\[.*\]', text, re.DOTALL)  # now expects LIST
    if not match:
        return None
    try:
        return json.loads(match.group())
    except:
        return None


VALID_STATUS = {"completed", "in progress", "blocked"}

def validate_log(data_list):
    if not isinstance(data_list, list):
        return False

    for data in data_list:
        if not (
            isinstance(data.get("task"), str) and
            data.get("status") in VALID_STATUS and
            isinstance(data.get("time_spent"), int)
        ):
            return False

    return True

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

    prompt = f"""
You are a STRICT data extraction engine.

Extract ALL tasks from the message.

Return ONLY a valid JSON array.

Schema:
[
  {{
    "task": string,
    "status": "completed" | "in progress" | "blocked",
    "time_spent": integer
  }}
]

Rules:
- Output MUST be a JSON array ([])
- Do NOT return a single object
- Do NOT add any text before or after JSON
- If multiple tasks exist → return multiple objects
- Do NOT merge tasks
- Do NOT miss any task
- Keep task short and clear
- Do NOT invent information
- If unsure:
  - status = "in progress"
  - time_spent = 0

Message:
{msg}
"""

    result = llm.invoke(prompt).content.strip()

    data_list = extract_json(result)
    if not data_list or not validate_log(data_list):
        data_list = [{
            "task": msg,
            "status": "in progress",
            "time_spent": 0
        }]

    responses = []
    for data in data_list:
        log = DailyLog(
            employee_id=state['user_id'],
            task=data['task'],
            status=data['status'],
            time_spent=data['time_spent']
        )
        db.add(log)

        responses.append(
            f"• {data['task']}  \n"
            f"  Status: {data['status']}  \n"
            f"  Time: {data['time_spent']} hrs"
        )

    db.commit()
    db.close()

    state['response'] = (
        "Nice, I've logged it:\n\n"
        + "\n\n".join(responses)
        + "\n\nAnything else you worked on?"
    )

    return state

def manager_summary(state):
    if state.get("role")!="manager":
        state['response']="You are not authorized to access this information"
        return state 
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