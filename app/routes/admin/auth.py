from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.deps import get_db
from app.deps import require_superuser

from app.models import User
from app.schemas import AdminLogin, AdminProfile
from app.schemas import ChangePassword

from app.auth import verify_password, create_access_token, hash_password
from app.services import auth_service

router = APIRouter(
    prefix="/admin",
    tags=["admin-auth"]
)


@router.post("/login")
def admin_login(
    data: AdminLogin,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user or not user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Admin access denied"
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Admin account disabled"
        )

    access_token = create_access_token(
        {"sub": str(user.id), "role": "superuser"}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=AdminProfile)
def admin_me(
    current_admin: User = Depends(require_superuser),
):
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

    return {"message": "Admin logged out successfully"}


@router.post("/change-password")
def admin_change_password(
    data: ChangePassword,
    current_admin: User = Depends(require_superuser),
    db: Session = Depends(get_db),
):
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match"
        )

    if not verify_password(
        data.old_password,
        current_admin.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Old password is incorrect"
        )

    current_admin.hashed_password = hash_password(data.new_password)
    db.commit()

    return {"message": "Admin password changed successfully"}
