from models.dailylogs_model import DailyLog

def add_log(db,user_id,data):
    log=DailyLog(employee_id=user_id,task=data.task,time_spent=data.time_spent,status=data.status)
    db.add(log)
    db.commit()
    return log