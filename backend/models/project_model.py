from sqlalchemy import Column,Integer,String
from db.base import Base

class Project(Base):
    __tablename__="projects"

    id=Column(Integer,primary_key=True,index=True)
    name=Column(String,unique=True,nullable=False)