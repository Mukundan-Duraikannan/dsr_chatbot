from fastapi import Depends,HTTPException
from fastapi.security import OAuth2PasswordBearer
from auth.jwt_handler import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/login')

def get_current_user(token:str=Depends(oauth2_scheme)):
    try:
        return verify_token(token)
    except:
        raise HTTPException(401,'Invalid token')

def manager_only(user=Depends(get_current_user)):
    if user['role']!='manager':
        raise HTTPException(403,'Manager only')
    return user

def employee_only(user=Depends(get_current_user)):
    if user['role']!='employee':
        raise HTTPException(403,'Employee only')
    return user