from jose import jwt
from datetime import datetime,timedelta
import os
from dotenv import load_dotenv

load_dotenv()

SECRET=os.getenv("SECRET_KEY")
ALGO=os.getenv("ALGORITHM")


def create_token(data:dict):
    payload=data.copy()
    payload['exp']=datetime.utcnow()+timedelta(days=1)
    return jwt.encode(payload,SECRET,algorithm=ALGO)

def verify_token(token:str):
    return jwt.decode(token,SECRET,algorithms=[ALGO])