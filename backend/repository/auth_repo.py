from models.employee_model import Employee
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"])

def register(db, data):
    user=Employee(name=data.name,email=data.email,password=pwd.hash(data.password),role=data.role)
    db.add(user)
    db.commit()
    return user

def login_user(db, email, password):
    user = db.query(Employee).filter(Employee.email == email).first()

    if user and pwd.verify(password, user.password):
        return user

    return None