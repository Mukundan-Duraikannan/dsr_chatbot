from fastapi import FastAPI
from db.base import Base
from db.database import engine
from routers.auth_router import router as auth_router
from routers.employee_router import router as employee_router
from routers.manager_router import router as manager_router
from routers.chatbot_router import router as chatbot_router
from scheduler.reminder_scheduler import start_scheduler
from scheduler.reminder_scheduler import check_missing_logs

import models.employee_model
import models.dailylogs_model
import models.reminder_model
import models.chat_history_model
app=FastAPI()


Base.metadata.create_all(bind=engine)
app.include_router(auth_router)
app.include_router(employee_router)
app.include_router(manager_router)
app.include_router(chatbot_router)

@app.on_event("startup")
def startup_event():
    start_scheduler()