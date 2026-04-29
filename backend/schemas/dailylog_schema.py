from pydantic import BaseModel

class DailyLogCreate(BaseModel):
    task:str
    time_spent:int
    status:str