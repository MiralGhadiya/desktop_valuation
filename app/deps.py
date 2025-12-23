# app/deps.py

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.database import get_db
from app import models
from fastapi.security import OAuth2PasswordBearer
from app.auth import decode_token
from app.utils.logger_config import app_logger as logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        logger.warning("Invalid or expired access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = int(payload.get("sub"))
    user = db.query(models.User).filter(models.User.id == user_id).first()

    if not user:
        logger.warning(f"Authenticated user not found user_id={user_id}")
        raise HTTPException(404, "User not found")

    if not user.is_email_verified:
        logger.warning(f"Unverified email access blocked user_id={user.id}")
        raise HTTPException(403, "Email not verified")

    if not user.is_active:
        logger.warning(f"Inactive user access blocked user_id={user.id}")
        raise HTTPException(401, "User inactive")

    return user


def require_superuser(
    current_user: models.User = Depends(get_current_user),
):
    if not current_user.is_superuser:
        logger.warning(f"Superuser access denied user_id={current_user.id}")
        raise HTTPException(403, "Superuser access required")
    return current_user
