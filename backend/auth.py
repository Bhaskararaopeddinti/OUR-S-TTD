import os
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.database import get_db

security = HTTPBearer(auto_error=False)
SECRET = os.getenv("SECRET_KEY", "change-me-in-production")


def hash_password(password: str) -> str:
    """bcrypt accepts a maximum of 72 UTF-8 bytes."""
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Password must be at most 72 bytes")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=12)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def current_claims(creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sign in required")
    try:
        return jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Retrieve and validate current authenticated User model."""
    claims = current_claims(creds)
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid authentication token")

    from backend.models import User
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account not found")

    if hasattr(user, 'is_active') and user.is_active is False:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is disabled. Contact support.")

    return user


def get_current_admin(current_user = Depends(get_current_user)):
    """Verify that current user possesses an admin or super_admin role."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="403 Forbidden: Administrator credentials required."
        )
    return current_user
