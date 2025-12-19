# app/routes/auth.py

import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import pwd_context
from datetime import datetime, timedelta
from app.models.subscription import SubscriptionPlan, UserSubscription

from app import schemas
from app.models import *
from app.utils.email import send_reset_email, send_verification_email
from app.deps import get_db
from app.deps import get_current_user
from app.utils.phone import get_country_from_mobile
from app.auth import verify_password, create_access_token, create_refresh_token
from app.services import user_service, country_service, auth_service


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    
    if user.email and user_service.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_service.get_user_by_mobile(db, user.mobile_number):
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    dial_code, country_code = get_country_from_mobile(user.mobile_number)

    country = country_service.get_country_by_dial_code(db, dial_code)
    if not country:
        country = country_service.create_country(
            db, country_code, dial_code, country_code
        )

    new_user = user_service.create_user(
        db,
        email=user.email,
        username=user.username,
        mobile_number=user.mobile_number,
        password=user.password,
        country_id=country.id,
    )
    
    free_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == "FREE",
        SubscriptionPlan.country_code == country.country_code,
        SubscriptionPlan.is_active == True
    ).first()

    if free_plan:
        free_sub = UserSubscription(
            user_id=new_user.id,
            plan_id=free_plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=365),
            is_active=True
        )
        db.add(free_sub)
        db.commit()


    raw_token = secrets.token_urlsafe(48)
    hashed_token = pwd_context.hash(raw_token)

    verification = EmailVerificationToken(
        user_id=new_user.id,
        token_hash=hashed_token,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )

    db.add(verification)
    db.commit()

    verify_link = f"http://localhost:8000/verify-email?token={raw_token}"
    send_verification_email(new_user.email, verify_link)

    return {
        "message": "Registration successful. Please verify your email."
    }


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    tokens = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.used == False,
        EmailVerificationToken.expires_at > datetime.utcnow()
    ).all()

    verification = next(
        (t for t in tokens if pwd_context.verify(token, t.token_hash)),
        None
    )

    if not verification:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user = db.query(User).filter(User.id == verification.user_id).first()
    user.is_email_verified = True
    user.email_verified_at = datetime.utcnow()

    verification.used = True
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = user_service.get_user_by_username(db, user.username)
    
    if not db_user.is_email_verified:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in"
        )

    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")


    db_user.is_active = True
    db.commit()

    access_token = create_access_token({"sub": str(db_user.id)})
    refresh_token = create_refresh_token({"sub": str(db_user.id)})

    auth_service.store_refresh_token(
        db,
        db_user.id,
        pwd_context.hash(refresh_token),
        datetime.utcnow() + timedelta(days=7),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
    
    
@router.get("/profile", response_model=schemas.UserProfile)
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "mobile_number": current_user.mobile_number,
        "country": current_user.country.name
    }
    
    
@router.post("/change-password")
def change_password(
    data: schemas.ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        user_service.change_password(
            db, current_user, data.old_password, data.new_password
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
def forgot_password(
    data: schemas.ForgotPassword,
    db: Session = Depends(get_db)
):
    
    user = user_service.get_user_by_email(db, data.email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="This email is not registered. Please enter your registered email id"
        )

    raw_token = secrets.token_urlsafe(48)
    hashed_token = pwd_context.hash(raw_token)

    reset = PasswordResetToken(
        user_id=user.id,
        token_hash=hashed_token,
        expires_at=datetime.utcnow() + timedelta(minutes=30)
    )

    db.add(reset)
    db.commit()
    
    reset_link = f"http://localhost:8000/reset-password?token={raw_token}"
    
    send_reset_email(user.email, reset_link)

    print("Password reset link:", reset_link)

    return {
        "message": "reset link sent to email"
    }


@router.post("/reset-password")
def reset_password(
    data: schemas.ResetPassword,
    db: Session = Depends(get_db)
):

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow()
    ).all()

    reset_token = next(
        (t for t in tokens if pwd_context.verify(data.token, t.token_hash)),
        None
    )

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    user.hashed_password = pwd_context.hash(data.new_password)

    reset_token.used = True
    db.commit()

    return {"message": "Password reset successful"}


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(request: Request):
    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request}
    )


@router.post("/logout")
def logout(user_id: int, db: Session = Depends(get_db)):
    auth_service.logout_user(db, user_id)
    return {"message": "Logged out successfully"}