#app/services/aut_service.py

from datetime import datetime
from sqlalchemy.orm import Session
from app.models import User, RefreshToken


def store_refresh_token(
    db: Session,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
):
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(token)
    db.commit()


def revoke_all_refresh_tokens(db: Session, user_id: int):
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id
    ).update({"revoked": True})
    db.commit()


def logout_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.is_active = False

    revoke_all_refresh_tokens(db, user_id)
    db.commit()
