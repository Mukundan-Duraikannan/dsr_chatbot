from pydantic import BaseModel

class EmployeeCreate(BaseModel):
    name:str
    email:str
    password:str
    role:str