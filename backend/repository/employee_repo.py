from models.dailylogs_model import DailyLog

def add_log(db,user_id,data):
    log=DailyLog(employee_id=user_id,task=data.task,time_spent=data.time_spent,status=data.status)
    db.add(log)
    db.commit()
    return log

def get_logs(db, user_id):
    return db.query(DailyLog).filter(DailyLog.employee_id == user_id).all()

def get_log_by_id(db, user_id, log_id):
    return db.query(DailyLog).filter(DailyLog.id == log_id,DailyLog.employee_id == user_id).first()

def update_log(db, user_id, log_id, data):
    log = db.query(DailyLog).filter(DailyLog.id == log_id,DailyLog.employee_id==user_id).first()
    if not log:
        return None
    log.task = data.task
    log.time_spent = data.time_spent
    log.status = data.status
    db.commit()
    db.refresh(log)
    return log

def delete_log(db, user_id, log_id):
    log = db.query(DailyLog).filter(DailyLog.id==log_id,DailyLog.employee_id==user_id).first()
    if not log:
        return None
    db.delete(log)
    db.commit()
    return log