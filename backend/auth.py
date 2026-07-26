import os, jwt, bcrypt
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
security = HTTPBearer(auto_error=False)
SECRET = os.getenv("SECRET_KEY", "change-me-in-production")
def hash_password(password: str) -> str:
    """bcrypt accepts a maximum of 72 UTF-8 bytes."""
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("Password must be at most 72 bytes")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
def create_token(user_id, role):
    return jwt.encode({"sub": str(user_id), "role": role, "exp": datetime.now(timezone.utc)+timedelta(hours=12)}, SECRET, algorithm="HS256")
def current_claims(creds: HTTPAuthorizationCredentials = Depends(security)):
    if not creds: raise HTTPException(401, "Sign in required")
    try: return jwt.decode(creds.credentials, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError: raise HTTPException(401, "Invalid or expired session")
