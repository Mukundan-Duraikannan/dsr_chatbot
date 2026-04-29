from sqlalchemy import Column,Integer,Date,ForeignKey,String
from db.base import Base
import datetime

class Reminder(Base):
    __tablename__='reminders'
    id=Column(Integer,primary_key=True,index=True)
    employee_id=Column(Integer,ForeignKey('employees.id'))
    reminder_date=Column(Date,default=datetime.date.today)
    status=Column(String,default='pending')