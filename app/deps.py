# app/deps.py

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.database import get_db
from app import models
from fastapi.security import OAuth2PasswordBearer
from app.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = decode_token(token)
    print("Payload:", payload)
    
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = int(payload.get("sub"))
    user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not user.is_email_verified:
        raise HTTPException(403, "Email not verified")

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User inactive")

    return user