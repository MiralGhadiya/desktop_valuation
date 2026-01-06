#app/router/admin/users.py

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import hash_password
from app.deps import get_db, require_superuser

from app.models import User
from app.services import auth_service
from app.schemas import AdminUserResponse, AdminResetPassword

from app.utils.logger_config import app_logger as logger


router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"]
)


USER_NOT_FOUND = "User not found"

@router.get("", response_model=List[AdminUserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),

    is_active: Optional[bool] = Query(None),
    is_email_verified: Optional[bool] = Query(None),
    country_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
):
    logger.info(
        "Admin listing users "
        f"is_active={is_active} verified={is_email_verified} "
        f"country_id={country_id} search={search}"
    )

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
        
    users = query.order_by(User.id.desc()).all()
    logger.debug(f"Admin fetched users count={len(users)}")

    return query.order_by(User.id.desc()).all()


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    logger.info(f"Admin fetching user user_id={user_id}")
    
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        logger.warning(f"{USER_NOT_FOUND} user_id={user_id}")
        raise HTTPException(404, USER_NOT_FOUND)

    return user


@router.patch("/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    logger.info(f"Admin toggling user active state user_id={user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"{USER_NOT_FOUND} during toggle user_id={user_id}")
        raise HTTPException(404, USER_NOT_FOUND)

    try:
        user.is_active = not user.is_active
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to toggle user active state")
        raise HTTPException(500, "Update failed")

    if not user.is_active:
        logger.info(f"User deactivated and sessions revoked user_id={user.id}")
        auth_service.revoke_all_refresh_tokens(db, user.id)
    else:
        logger.info(f"User activated user_id={user.id}")

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
    logger.info(f"Admin forcing logout user_id={user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"{USER_NOT_FOUND} during force logout user_id={user_id}")
        raise HTTPException(404, USER_NOT_FOUND)

    auth_service.revoke_all_refresh_tokens(db, user.id)
    
    logger.info(f"User logged out from all sessions user_id={user.id}")

    return {"message": "User logged out from all sessions"}


# ----- MANUAL EMAIL VERIFY -----
@router.post("/{user_id}/verify-email")
def verify_user_email(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    logger.info(f"Admin verifying email user_id={user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"{USER_NOT_FOUND} during email verify user_id={user_id}")
        raise HTTPException(404, USER_NOT_FOUND)

    if user.is_email_verified:
        logger.info(f"Email already verified user_id={user_id}")
        return {"message": "Email already verified"}

    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()
    
    logger.info(f"User email verified user_id={user_id}")

    return {"message": "User email verified"}


@router.post("/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    data: AdminResetPassword,
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
):
    logger.info(f"Admin resetting password user_id={user_id}")
    
    if data.new_password != data.confirm_password:
        logger.warning(f"Password mismatch during reset user_id={user_id}")
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        logger.warning(f"{USER_NOT_FOUND} during password reset user_id={user_id}")
        raise HTTPException(404, USER_NOT_FOUND)
    
    try:
        user.hashed_password = hash_password(data.new_password)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to reset user password")
        raise HTTPException(500, "Password reset failed")

    auth_service.revoke_all_refresh_tokens(db, user.id)
    
    logger.info(f"User password reset and sessions revoked user_id={user.id}")

    return {"message": "User password reset successfully"}
