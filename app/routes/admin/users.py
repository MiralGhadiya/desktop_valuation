from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.deps import get_db
from app.deps import require_superuser

from app.models import User
from app.services import auth_service
from app.auth import hash_password
from app.schemas import AdminUserResponse, AdminResetPassword

router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"]
)


@router.get("", response_model=List[AdminUserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),

    is_active: Optional[bool] = Query(None),
    is_email_verified: Optional[bool] = Query(None),
    country_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
):
    query = db.query(User)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_email_verified is not None:
        query = query.filter(
            User.is_email_verified == is_email_verified
        )

    if country_id:
        query = query.filter(User.country_id == country_id)

    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.mobile_number.ilike(f"%{search}%"))
        )

    return query.order_by(User.id.desc()).all()


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(404, "User not found")

    return user


@router.patch("/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    user.is_active = not user.is_active
    db.commit()

    if not user.is_active:
        auth_service.revoke_all_refresh_tokens(db, user.id)

    return {
        "message": "User status updated",
        "is_active": user.is_active
    }


@router.post("/{user_id}/logout")
def force_logout_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    auth_service.revoke_all_refresh_tokens(db, user.id)

    return {"message": "User logged out from all sessions"}


# ----- MANUAL EMAIL VERIFY -----
@router.post("/{user_id}/verify-email")
def verify_user_email(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    if user.is_email_verified:
        return {"message": "Email already verified"}

    user.is_email_verified = True
    user.email_verified_at = datetime.utcnow()
    db.commit()

    return {"message": "User email verified"}


@router.post("/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    data: AdminResetPassword,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(404, "User not found")

    user.hashed_password = hash_password(data.new_password)
    db.commit()

    auth_service.revoke_all_refresh_tokens(db, user.id)

    return {"message": "User password reset successfully"}
