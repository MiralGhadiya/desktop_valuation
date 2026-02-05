#app/routes/admin/auth.py

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.models import User
from app.services import auth_service
from app.schemas.admin import AdminTokenResponse
from app.schemas import AdminLogin, AdminProfile, ChangePassword

from app.deps import get_db, require_superuser
from app.utils.response import APIResponse, success_response
from app.auth import verify_password, create_access_token, hash_password

from app.utils.logger_config import app_logger as logger


router = APIRouter(
    prefix="/admin",
    tags=["admin-auth"]
)


@router.post(
    "/login",
    response_model=APIResponse[AdminTokenResponse]
)
def admin_login(
    data: AdminLogin,
    db: Session = Depends(get_db),
):
    logger.info(f"Admin login attempt email={data.email}")

    user = db.query(User).filter(User.email == data.email).first()

    if not user or not user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access denied")

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Admin account disabled")

    access_token = create_access_token(
        {"sub": str(user.id), "role": "superuser"}
    )

    logger.info(f"Admin login successful user_id={user.id}")

    return success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
        },
        message="Admin login successful"
    )
    

@router.get("/me", response_model=APIResponse[AdminProfile])
def admin_me(
    current_admin: User = Depends(require_superuser),
):
    logger.debug(f"Admin profile fetched user_id={current_admin.id}")
    return success_response(data=current_admin, message="Admin profile fetched successfully")


@router.post("/logout")
def admin_logout(
    current_admin: User = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    try:
        auth_service.revoke_all_refresh_tokens(db, current_admin.id)
    except Exception as e:
        logger.exception("Admin logout failed")
        raise HTTPException(500, "Logout failed")

    return success_response(
        data=None,
        message="Admin logged out successfully"
    )


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

    return success_response(
        data=None,
        message="Password changed successfully"
    )
