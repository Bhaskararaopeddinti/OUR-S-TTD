from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import RegisterIn, LoginIn, Token
from backend.auth import hash_password, verify_password, create_token
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
@router.post("/register", response_model=Token)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    if db.query(User).filter_by(email=data.email).first(): raise HTTPException(409, "Email is already registered")
    role = data.role if data.role in {"pilgrim", "volunteer"} else "pilgrim"
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), role=role)
    db.add(user); db.commit(); db.refresh(user)
    return Token(access_token=create_token(user.id, user.role))
@router.post("/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, "Incorrect email or password")
    return Token(access_token=create_token(user.id, user.role))
