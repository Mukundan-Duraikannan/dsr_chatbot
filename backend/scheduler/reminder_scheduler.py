from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta, date
from db.database import SessionLocal
from models.employee_model import Employee
from models.dailylogs_model import DailyLog
from models.reminder_model import Reminder
from utils.email_service import send_email

scheduler = BackgroundScheduler()

def get_previous_working_day(today):
    if today.weekday() == 0:  
        return today - timedelta(days=3)  
    elif today.weekday() == 6:  
        return today - timedelta(days=2)
    elif today.weekday() == 5:  
        return today - timedelta(days=1)
    else:
        return today - timedelta(days=1)


def check_missing_logs():
    db = SessionLocal()
    try:
        today = date.today()
        check_date = get_previous_working_day(today)
        if check_date.weekday() >= 5:
            return

        employees = db.query(Employee).filter(Employee.role == "employee").all()
        manager = db.query(Employee).filter(Employee.role == "manager").all()

        for emp in employees:

            log = db.query(DailyLog).filter(
                DailyLog.employee_id == emp.id,
                DailyLog.log_date == check_date
            ).first()

            if not log:

                existing = db.query(Reminder).filter(
                    Reminder.employee_id == emp.id,
                    Reminder.reminder_date == today
                ).first()

                if not existing:
                    db.add(Reminder(
                        employee_id=emp.id,
                        reminder_date=today,
                        status="sent"
                    ))
                    send_email(
                        emp.email,
                        "Missing Daily Log Reminder",
                        f"""
Hi {emp.name},

You missed submitting your daily progress for {check_date}.

Please update it as soon as possible.

Thanks,
DSR Bot
"""
                    )
                   
                    for mgr in manager:
                        send_email(
                            mgr.email,
                            f"{emp.name} missed daily log",
                            f"""
Hi {mgr.name},

{emp.name} did not submit their daily progress for {check_date}.

Please follow up if needed.

- DSR Bot
"""
    )
                        
        db.commit()
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(check_missing_logs,trigger='cron',hour=18,minute=11)
    scheduler.start()