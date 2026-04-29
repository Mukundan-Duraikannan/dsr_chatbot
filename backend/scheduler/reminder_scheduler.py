from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import calendar
from db.database import SessionLocal
from models.employee_model import Employee
from models.dailylogs_model import DailyLog
from models.reminder_model import Reminder 

scheduler = BackgroundScheduler()

def check_missing_logs():
    db = SessionLocal()
    today = datetime.now().date()
    check_date = today - timedelta(days=1)
    if calendar.day_name[check_date.weekday()] in ["Saturday", "Sunday"]:
        db.close()
        return
    employees = db.query(Employee).all()
    for emp in employees:
        log = db.query(DailyLog).filter(DailyLog.employee_id==emp.id,DailyLog.log_date==check_date).first()
        if not log:
            existing = db.query(Reminder).filter(Reminder.employee_id == emp.id,Reminder.reminder_date == today).first()
            if not existing:
                reminder = Reminder(employee_id=emp.id,reminder_date=today,status="pending")
                db.add(reminder)
            print(f"Reminder: {emp.name} missed log for {check_date}")
    db.commit()
    db.close()

def start_scheduler():
    scheduler.add_job(check_missing_logs,trigger='cron',hour=9,minute=0)
    scheduler.start()
