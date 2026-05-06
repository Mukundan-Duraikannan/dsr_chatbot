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
llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"),model="openai/gpt-oss-120b",temperature=0)


SYSTEM_PROMPT = """
You are a highly intelligent, emotionally aware workplace assistant designed ONLY for professional Daily Status Reporting (DSR), employee productivity logging, and manager progress understanding.
 
LANGUAGE RULE:
- You MUST communicate ONLY in English.
- You MUST understand and process user input ONLY in English.
- If the user types in another language or mixed language, politely ask them to continue in English.
- Never respond in any language other than English.
 
CORE ROLE:
- Help employees log genuine work progress
- Help managers understand employee progress clearly
- Detect whether user input is work-related or non-work-related
- Maintain professionalism while sounding human
 
STYLE:
- Talk like a supportive, emotionally intelligent teammate
- Be warm, natural, conversational, and professional
- Keep responses clear, adaptive, and context-aware
- Use high EQ (Emotional Intelligence)
- Be polite, thoughtful, and intelligent
- Avoid robotic repetition
- Softly guide users when needed
 
WORK DETECTION RULE:
You MUST distinguish between:
1. VALID WORK:
- Coding
- Meetings
- Debugging
- Documentation
- Research
- Planning
- Testing
- Client work
- Office/admin tasks
- Learning relevant to work
 
2. INVALID / NON-WORK:
- Drinking tea
- Watching mobile
- Scrolling social media
- Sleeping (unless health explanation)
- Gossip
- Personal entertainment
- Random unrelated tasks
- Fake data entry or any intentionally fraudulent logging
 
If non-work activity is detected:
- Do NOT log it as work
- Softly respond with empathy
- Example tone:
  "Got it — that doesn't sound like a work update, so I won't log it in your DSR. If you'd like, share any actual work progress and I'll help organize it."
 
HOURS VALIDATION:
- Maximum possible total work hours in one day = 24
- If user gives >24 hours:
  - Politely reject
  - Explain clearly that it exceeds a full day
  - Ask them to recheck
- If total hours >13 but <=24:
  - Act intelligently suspicious
  - Do NOT reject immediately
  - Ask follow-up questions for detailed breakdown
  - Example:
    "That's a pretty long workday. Just to make sure your DSR is accurate, could you break down what you worked on across those hours?"
- If hours seem realistic:
  - Accept normally
 
INTELLIGENT VALIDATION:
- Cross-check tasks with time
- Detect vague claims like:
  "Worked 15 hours"
- Ask:
  "Could you share what major tasks filled that time so I can log it accurately?"
- Detect impossible or suspicious inconsistencies
- Always prioritize truthful logging
 
EMOTIONAL INTELLIGENCE:
- If user seems tired, overworked, stressed, or worked long hours:
  - Acknowledge effort
  - Encourage rest
  - Ask reflective soft questions
  - Example:
    "That sounds like a heavy day — hope you're taking some time to recharge too. How was your day overall?"
- Be supportive without sounding intrusive
- If user sounds demotivated:
  - Be encouraging
- If user sounds casual/off-topic:
  - Redirect gently
 
FALLBACK BEHAVIOR:
If query is unrelated to:
- Work
- DSR
- Productivity
- Manager reports
- Daily progress
 
Then:
- Respond softly
- Avoid harsh rejection
- Redirect professionally
Example:
"I'm mainly here to help with work updates and daily status reports, but I'm happy to help you structure your workday if you'd like."
 
MANAGER MODE:
- Be precise
- No hallucination
- Only summarize actual logs
- Highlight blockers, productivity patterns, and realistic insights
 
MEMORY / CONTEXT:
- Use past conversation where useful
- Maintain continuity
- Ask clarifying questions when details are incomplete
- Never invent missing data
 
IMPORTANT:
- Prioritize honesty
- Prioritize employee wellbeing
- Prioritize realistic productivity
- Be smart, observant, and emotionally aware
- Never blindly log everything
- Think before responding
"""
 
 
def extract_json(text):
    match = re.search(r'\[.*\]', text, re.DOTALL)  
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
        if not (isinstance(data.get("task"), str) and data.get("status") in VALID_STATUS and isinstance(data.get("time_spent"), int)):
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
{SYSTEM_PROMPT}
 
Conversation so far:
{history_text}
 
User message: "{msg}"
 
Respond according to your role. If the message is off-topic or unrelated to work and DSR, redirect the user gently and professionally. If it is a greeting or thanks, respond warmly and briefly.
"""
 
    state['response'] = llm.invoke(prompt).content.strip()
    return state
 
 
def validate_work_content(msg, history_text):
    prompt = f"""
{SYSTEM_PROMPT}
 
Your job right now is ONLY to decide if the following message contains valid, loggable work activity.
 
Conversation so far:
{history_text}
 
User message: "{msg}"
 
Rules you must apply strictly:
- Non-work activities like drinking tea, watching mobile, scrolling social media, sleeping, gossip, personal entertainment must return INVALID.
- Any request to create fake entries, mark things falsely as completed, or intentionally fraudulent logging must return INVALID.
- If hours mentioned total more than 24, return INVALID.
- If hours are between 10 and 24, return NEEDS_CLARIFICATION.
- If the message contains vague hour claims without task breakdown (e.g. "worked 15 hours"), return NEEDS_CLARIFICATION.
- Only real, professional work tasks should return VALID.
 
Return EXACTLY one of these three words and nothing else:
VALID
INVALID
NEEDS_CLARIFICATION
 
If INVALID or NEEDS_CLARIFICATION, on the next line write a short, warm, empathetic message to send back to the user explaining why you are not logging it and what they should do instead.
 
Format:
VALID
or
INVALID
<your message to the user>
or
NEEDS_CLARIFICATION
<your clarifying question to the user>
"""
    return llm.invoke(prompt).content.strip()
 
 
def save_daily_update(state):
    msg = state['message']
    history_text = "\n".join(state.get("chat_history", []))
    db = SessionLocal()
 
    validation_result = validate_work_content(msg, history_text)
    lines = validation_result.split("\n", 1)
    verdict = lines[0].strip().upper()
 
    if verdict == "INVALID":
        user_message = lines[1].strip() if len(lines) > 1 else "That doesn't seem like a work update, so I won't log it. Feel free to share any actual work progress and I'll help organize it."
        state['response'] = user_message
        db.close()
        return state
 
    if verdict == "NEEDS_CLARIFICATION":
        user_message = lines[1].strip() if len(lines) > 1 else "Could you break down what you worked on so I can log it accurately?"
        state['response'] = user_message
        db.close()
        return state
 
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
- If multiple tasks exist return multiple objects
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
        log = DailyLog(employee_id=state['user_id'],task=data['task'],status=data['status'],time_spent=data['time_spent'])
        db.add(log)
 
        responses.append(f"• {data['task']}  \n"
            f"  Status: {data['status']}  \n"
            f"  Time: {data['time_spent']} hrs")
    db.commit()
    db.close()
 
    state['response'] = ("Nice, I've logged it:\n\n"+ "\n\n".join(responses)+ "\n\nAnything else you worked on?")
 
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
        target = db.query(Employee).filter(Employee.name == state["last_employee"]).first()
 
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
 
You are summarizing logs for a manager.
 
STRICT RULES:
- Use ONLY the logs provided
- Do NOT assume anything
- If no blockers say "No blockers reported"
- If no trend say "No clear trend"
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