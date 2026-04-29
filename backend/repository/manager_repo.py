from models.dailylogs_model import DailyLog
from models.employee_model import Employee
from datetime import date,timedelta


def get_summary(db,employee_id,days):
    from_date = date.today()-timedelta(days=days)
    return db.query(DailyLog).filter(DailyLog.employee_id==employee_id,DailyLog.log_date>=from_date).all()

def all_employees(db):
    return db.query(Employee).all()