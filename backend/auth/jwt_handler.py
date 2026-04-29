from jose import jwt
from datetime import datetime,timedelta

SECRET='09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7'
ALGO='HS256'


def create_token(data:dict):
    payload=data.copy()
    payload['exp']=datetime.utcnow()+timedelta(days=1)
    return jwt.encode(payload,SECRET,algorithm=ALGO)

def verify_token(token:str):
    return jwt.decode(token,SECRET,algorithms=[ALGO])