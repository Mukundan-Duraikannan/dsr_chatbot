from sqlalchemy import Column,Integer,String,Date,ForeignKey
from db.base import Base
import datetime

class DailyLog(Base):
    __tablename__='daily_logs'
    id=Column(Integer,primary_key=True,index=True)
    employee_id=Column(Integer,ForeignKey('employees.id'))
    task=Column(String)
    time_spent=Column(Integer)
    status=Column(String)
    log_date=Column(Date,default=datetime.date.today)