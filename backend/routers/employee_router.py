from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.dailylog_schema import DailyLogCreate
from repository.employee_repo import add_log
from auth.dependencies import employee_only

router=APIRouter(prefix='/employee',tags=['Employee'])

@router.post('/daily-log')
def create_log(data:DailyLogCreate,db:Session=Depends(get_db),user=Depends(employee_only)):
    add_log(db,user['id'],data)
    return {'msg':'Daily log added'}