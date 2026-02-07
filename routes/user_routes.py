from fastapi import APIRouter
from sqlalchemy.orm import Session
from fastapi import Depends
from db import get_db
from models import User
from repositories.User_repo import UserRepo
from schemas.User_schemas import User_schemas
router = APIRouter()


@router.post("/signup")
def signup(user: User_schemas, db: Session = Depends(get_db)):
    user_repo = UserRepo(db)
    # Convert Pydantic schema to SQLAlchemy model
    db_user = User(email=user.email, password=user.password)
    user_repo.add_user(db_user)
    return {"message": "User signed up successfully"}

@router.post("/login")
def login():
    return {"message": "User logged in successfully"}