from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.dailylog_schema import DailyLogCreate
from repository.employee_repo import add_log,get_logs,get_log_by_id,update_log,delete_log
from auth.dependencies import employee_only

router=APIRouter(prefix='/employee',tags=['Employee'])

@router.post('/daily-log')
def create_log(data:DailyLogCreate,db:Session=Depends(get_db),user=Depends(employee_only)):
    add_log(db,user['id'],data)
    return {'msg':'Daily log added'}

@router.get('/daily-log')
def get_all_logs(db: Session = Depends(get_db),user=Depends(employee_only)):
    logs = get_logs(db, user['id'])
    return logs

@router.get('/daily-log/{log_id}')
def get_single_log(log_id: int,db: Session = Depends(get_db),user=Depends(employee_only)):
    log = get_log_by_id(db, user['id'], log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return log

@router.put('/daily-log/{log_id}')
def update_single_log(log_id: int,data: DailyLogCreate,db: Session = Depends(get_db),user=Depends(employee_only)):
    log = update_log(db, user['id'], log_id, data)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return {'msg': 'Log updated', 'data': log}

@router.delete('/daily-log/{log_id}')
def delete_single_log(log_id: int,db: Session = Depends(get_db),user=Depends(employee_only)):
    log = delete_log(db, user['id'], log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return {'msg': 'Log deleted'}
