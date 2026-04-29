from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from db.database import get_db
from repository.manager_repo import get_summary
from auth.dependencies import manager_only

router=APIRouter(prefix='/manager',tags=['Manager'])

@router.get('/summary/{employee_id}/{days}')
def summary(employee_id:int,days:int,db:Session=Depends(get_db),user=Depends(manager_only)):
    data=get_summary(db,employee_id,days)
    return data