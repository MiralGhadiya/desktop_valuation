# app/routes/auth.py

import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import pwd_context
from datetime import datetime, timedelta, timezone
from app.models import EmailVerificationToken, User, SubscriptionPlan,UserSubscription, PasswordResetToken
from app import schemas
from app.utils.email import send_reset_email, send_verification_email
from app.deps import get_db
from app.deps import get_current_user
from app.utils.phone import get_country_from_mobile
from app.auth import verify_password, create_access_token, create_refresh_token
from app.services import user_service, country_service, auth_service
from app.utils.logger_config import app_logger as logger

datetime.now(timezone.utc)

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    
    if user.email and user_service.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_service.get_user_by_mobile(db, user.mobile_number):
        raise HTTPException(status_code=400, detail="Mobile number already registered")

    dial_code, country_code = get_country_from_mobile(user.mobile_number)
    
    logger.info(f"Registration attempt email={user.email} mobile={user.mobile_number}")

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
    
    logger.info(f"User registered successfully id={new_user.id}")
    
    free_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == "FREE",
        SubscriptionPlan.country_code == country.country_code,
        SubscriptionPlan.is_active == True
    ).first()

    if free_plan:
        free_sub = UserSubscription(
            user_id=new_user.id,
            plan_id=free_plan.id,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=True
        )
        db.add(free_sub)
        db.commit()


    raw_token = secrets.token_urlsafe(48)
    hashed_token = pwd_context.hash(raw_token)

    verification = EmailVerificationToken(
        user_id=new_user.id,
        token_hash=hashed_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
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
    
    logger.info("Email verification attempt")
    
    tokens = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.used == False,
        EmailVerificationToken.expires_at > datetime.now(timezone.utc)
    ).all()
    
    verification = next(
        (t for t in tokens if pwd_context.verify(token, t.token_hash)),
        None
    )

    if not verification:
        raise HTTPException(status_code=400, detail="Invalid or expired verification link")

    user = db.query(User).filter(User.id == verification.user_id).first()
    logger.info(f"Email verified for user_id={user.id}")
    
    user.is_email_verified = True
    user.email_verified_at = datetime.now(timezone.utc)

    verification.used = True
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
def resend_verification_email(
    data: schemas.ResendVerificationRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == data.email).first()

    # Do NOT reveal whether user exists (security)
    if not user:
        return {
            "message": "If this email is registered, a verification link has been sent"
        }

    if user.is_email_verified:
        raise HTTPException(
            status_code=400,
            detail="Email is already verified"
        )

    # Revoke all previous unused verification tokens
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == user.id,
        EmailVerificationToken.used == False,
    ).update({"used": True})

    # Generate new token
    raw_token = secrets.token_urlsafe(48)
    hashed_token = pwd_context.hash(raw_token)

    verification = EmailVerificationToken(
        user_id=user.id,
        token_hash=hashed_token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )

    db.add(verification)
    db.commit()

    verify_link = f"http://localhost:8000/verify-email?token={raw_token}"
    send_verification_email(user.email, verify_link)

    logger.info(f"Verification email resent user_id={user.id}")

    return {
        "message": "Verification email sent successfully"
    }


@router.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    
    logger.info(f"Login attempt for mail={user.email}")

    db_user = user_service.get_user_by_email(db, user.email)
    
    if not db_user:
        raise HTTPException(401, "Invalid credentials")
    
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
        datetime.now(timezone.utc) + timedelta(days=7),
    )
    
    logger.info(f"User logged in successfully user_id={db_user.id}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }
 
   
@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh_token(
    data: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Rotate refresh token and issue new access token
    """

    token_record = auth_service.verify_refresh_token(
        db=db,
        refresh_token=data.refresh_token,
        pwd_context=pwd_context,
    )

    if not token_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )

    token_record.is_revoked = True

    # Create new tokens
    access_token = create_access_token(
        {"sub": str(token_record.user_id)}
    )
    new_refresh_token = create_refresh_token(
        {"sub": str(token_record.user_id)}
    )

    # Store new refresh token
    auth_service.store_refresh_token(
        db=db,
        user_id=token_record.user_id,
        token_hash=pwd_context.hash(new_refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )

    db.commit()

    logger.info(
        f"Refresh token rotated user_id={token_record.user_id}"
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
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
 
 
@router.put("/edit-profile")
def update_profile(
    data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check email uniqueness
    if data.email and data.email != current_user.email:
        existing_email = user_service.get_user_by_email(db, data.email)
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already in use"
            )
        current_user.email = data.email
        current_user.is_email_verified = False  # re-verify if email changes

    # Check mobile uniqueness
    if data.mobile_number and data.mobile_number != current_user.mobile_number:
        existing_mobile = user_service.get_user_by_mobile(db, data.mobile_number)
        if existing_mobile:
            raise HTTPException(
                status_code=400,
                detail="Mobile number already in use"
            )
        current_user.mobile_number = data.mobile_number

    # Update username
    if data.username:
        current_user.username = data.username

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "mobile_number": current_user.mobile_number
        }
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
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)
    )

    db.add(reset)
    db.commit()
    
    reset_link = f"http://localhost:8000/reset-password?token={raw_token}"
    
    send_reset_email(user.email, reset_link)

    logger.info(f"Password reset requested for email={user.email}")

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
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
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



# @router.post("/logout")
# def logout(
#     data: schemas.LogoutRequest,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Logout only the current device by revoking the provided refresh token
#     """

#     revoked = auth_service.revoke_refresh_token(
#         db=db,
#         user_id=current_user.id,
#         refresh_token=data.refresh_token,
#         pwd_context=pwd_context,
#     )

#     if not revoked:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid or already revoked refresh token"
#         )

#     logger.info(
#         f"User single-device logout user_id={current_user.id}"
#     )

#     return {"message": "Logged out from this device successfully"}



@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logout user from ALL devices (revoke all refresh tokens)
    """

    auth_service.logout_user(db, current_user.id)

    logger.info(f"User logout user_id={current_user.id}")

    return {"message": "Logged out successfully"}