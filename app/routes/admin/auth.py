#app/routes/admin/auth.py

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.models import User
from app.services import auth_service
from app.schemas import AdminLogin, AdminProfile, ChangePassword

from app.deps import get_db, require_superuser
from app.auth import verify_password, create_access_token, hash_password

from app.utils.logger_config import app_logger as logger


router = APIRouter(
    prefix="/admin",
    tags=["admin-auth"]
)


@router.post("/login")
def admin_login(
    data: AdminLogin,
    db: Session = Depends(get_db),
):
    logger.info(f"Admin login attempt email={data.email}")

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not user.is_superuser:
        logger.warning(f"Admin access denied email={data.email}")
        raise HTTPException(
            status_code=403,
            detail="Admin access denied"
        )

    if not verify_password(data.password, user.hashed_password):
        logger.warning(f"Invalid admin password email={data.email}")
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not user.is_active:
        logger.warning(f"Inactive admin login attempt user_id={user.id}")
        raise HTTPException(
            status_code=403,
            detail="Admin account disabled"
        )

    access_token = create_access_token(
        {"sub": str(user.id), "role": "superuser"}
    )
    
    logger.info(f"Admin login successful user_id={user.id}")

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=AdminProfile)
def admin_me(
    current_admin: User = Depends(require_superuser),
):
    logger.debug(f"Admin profile fetched user_id={current_admin.id}")
    return current_admin


@router.post("/logout")
def admin_logout(
    current_admin: User = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    auth_service.revoke_all_refresh_tokens(
        db,
        current_admin.id
    )
    logger.info(f"Admin logged out user_id={current_admin.id}")

    return {"message": "Admin logged out successfully"}


@router.post("/change-password")
def admin_change_password(
    data: ChangePassword,
    current_admin: User = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    logger.info(f"Admin password change attempt user_id={current_admin.id}")
    
    if data.new_password != data.confirm_password:
        logger.warning(f"Admin password mismatch user_id={current_admin.id}")
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    if not verify_password(
        data.old_password,
        current_admin.hashed_password
    ):
        logger.warning(f"Admin old password incorrect user_id={current_admin.id}")
        raise HTTPException(
            status_code=401,
            detail="Old password is incorrect"
        )

    try:
        current_admin.hashed_password = hash_password(data.new_password)
        db.commit()
    except Exception as e:
        logger.error(f"Error changing admin password user_id={current_admin.id} error={str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error changing password"
        )
        
    logger.info(f"Admin password changed user_id={current_admin.id}")

    return {"message": "Admin password changed successfully"}
