import secrets
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, AdminSession
from backend.schemas import RegisterIn, LoginIn, Token, UserOut, ForgotPasswordIn, ResetPasswordIn
from backend.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=Token)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    """Register a new pilgrim/user account."""
    existing = db.query(User).filter_by(email=data.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email is already registered. Please sign in.")

    allowed_roles = {"pilgrim", "volunteer"}
    role = data.role if data.role in allowed_roles else "pilgrim"

    user = User(
        name=data.name.strip(),
        email=data.email.lower().strip(),
        password_hash=hash_password(data.password),
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token_str = create_token(user.id, user.role)
    return Token(
        access_token=token_str,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.post("/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    """Authenticate pilgrim or admin user."""
    email_clean = data.email.lower().strip()
    user = db.query(User).filter_by(email=email_clean).first()

    if not user:
        raise HTTPException(status_code=404, detail="Account not found. Please check your email or register.")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    if hasattr(user, 'is_active') and user.is_active is False:
        raise HTTPException(status_code=403, detail="Account is disabled. Please contact TTD support.")

    user.last_login = datetime.utcnow()
    db.commit()
    token_str = create_token(user.id, user.role)

    # Record admin session with server timestamp
    if user.role in ("admin", "super_admin"):
        try:
            # Deactivate any previous active sessions
            db.query(AdminSession).filter(
                AdminSession.admin_id == user.id,
                AdminSession.is_active == True
            ).update({"is_active": False})
            session = AdminSession(
                admin_id=user.id,
                admin_email=user.email,
                session_id=str(uuid.uuid4()),
                login_time=datetime.utcnow(),
                is_active=True,
            )
            db.add(session)
            db.commit()
        except Exception:
            db.rollback()  # Don't fail login if session tracking fails

    return Token(
        access_token=token_str,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )



@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordIn, db: Session = Depends(get_db)):
    """Generate a secure password reset token."""
    email_clean = data.email.lower().strip()
    user = db.query(User).filter_by(email=email_clean).first()

    if not user:
        # Don't leak user existence for security
        return {
            "status": "success",
            "message": f"If an account exists for {email_clean}, password reset instructions have been dispatched."
        }

    # Generate secure random token valid for 1 hour
    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()

    return {
        "status": "success",
        "message": f"Password reset token generated for {email_clean}. Use link or token to reset password.",
        "dev_reset_token": token  # Included for local testing/demo without SMTP server
    }


@router.post("/reset-password")
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    """Reset password using a valid reset token."""
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=422, detail="New password and confirmation password do not match.")

    user = db.query(User).filter(User.reset_token == data.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    if not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        user.reset_token = None
        user.reset_token_expires = None
        db.commit()
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")

    # Update password and invalidate single-use token
    user.password_hash = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {
        "status": "success",
        "message": "Password reset successfully. You can now log in with your new password."
    }
