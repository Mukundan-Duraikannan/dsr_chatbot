from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from db.base import Base
import datetime

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("employees.id"))
    message = Column(String)
    response = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)