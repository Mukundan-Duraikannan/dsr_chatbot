from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from db.database import get_db
from schemas.employee_schema import EmployeeCreate
from repository.auth_repo import register, login_user
from auth.jwt_handler import create_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def signup(data: EmployeeCreate, db: Session = Depends(get_db)):
    register(db, data)
    return {"msg": "Registered"}


@router.post("/login")
def signin(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = login_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({
        "id": user.id,
        "role": user.role,
        "email": user.email
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }