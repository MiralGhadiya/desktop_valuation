#app/router/admin/users.py

from sqlalchemy import or_
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import hash_password
from app.deps import pagination_params
from app.deps import get_db, require_superuser

from app.models import User
from app.services import auth_service
from app.schemas import AdminUserResponse, AdminResetPassword
from app.common import PaginatedResponse

from app.utils.logger_config import app_logger as logger


router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"]
)


USER_NOT_FOUND = "User not found"

@router.get("", response_model=PaginatedResponse[AdminUserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_superuser),
    
    params: dict = Depends(pagination_params),

    is_email_verified: Optional[bool] = Query(None),
    is_superuser: Optional[bool] = Query(None),
    country_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    
    verified_from: Optional[datetime] = Query(
        None, description="Email verified from this date (UTC)"
    ),
    verified_to: Optional[datetime] = Query(
        None, description="Email verified until this date (UTC)"
    ),
    verified_within_days: Optional[int] = Query(
        None, ge=1, le=365, description="Email verified within last N days"
    ),

    sort_by: str = Query("id"),
    order: str = Query("desc"),

):
    logger.info(
        "Admin listing users "
        f"page={params['page']} limit={params['limit']} "
        f"search={params['search']}"
    )

    query = db.query(User)
    
    if params["search"]:
        query = query.filter(
            or_(
                User.username.ilike(f"%{params['search']}%"),
                User.email.ilike(f"%{params['search']}%"),
                User.mobile_number.ilike(f"%{params['search']}%"),
            )
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    if is_email_verified is not None:
        query = query.filter(User.is_email_verified == is_email_verified)

    if is_superuser is not None:
        query = query.filter(User.is_superuser == is_superuser)

    if country_id:
        query = query.filter(User.country_id == country_id)
        
    now = datetime.now(timezone.utc)

    if verified_within_days:
        start_date = now - timedelta(days=verified_within_days)
        query = query.filter(
            User.email_verified_at.isnot(None),
            User.email_verified_at >= start_date
        )

    if verified_from:
        query = query.filter(User.email_verified_at >= verified_from)

    if verified_to:
        query = query.filter(User.email_verified_at <= verified_to)
        
    # 📊 TOTAL COUNT
    total = query.count()

    # 🔃 SORTING
    ALLOWED_SORT_FIELDS = {
        "id": User.id,
        "email": User.email,
        "username": User.username,
        "email_verified_at": User.email_verified_at,
    }

    sort_column = ALLOWED_SORT_FIELDS.get(sort_by)
    if not sort_column:
        raise HTTPException(400, "Invalid sort field")

    if order.lower() == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # 📄 PAGINATION
    users = (
        query
        .offset((params["page"] - 1) * params["limit"])
        .limit(params["limit"])
        .all()
    )

    logger.debug(
        f"Admin fetched users count={len(users)} total={total}"
    )

    return {
        "data": users,
        "pagination": {
            "page": params["page"],
            "limit": params["limit"],
            "total": total,
        }
    }


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
    
    try:
        user.is_email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to verify user email")
        raise HTTPException(500, "Email verification failed")
    
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
