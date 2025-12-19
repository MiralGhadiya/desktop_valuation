# app/services/user_service.py

from sqlalchemy.orm import Session
from app.models import User
from app.auth import hash_password, verify_password


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_mobile(db: Session, mobile_number: str):
    return db.query(User).filter(
        User.mobile_number == mobile_number
    ).first()


def create_user(
    db: Session,
    email: str,
    username: str,
    mobile_number: str,
    password: str,
    country_id: int,
):
    user = User(
        email=email,
        username=username,
        mobile_number=mobile_number,
        country_id=country_id,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, old_password: str, new_password: str):
    if not verify_password(old_password, user.hashed_password):
        raise ValueError("Invalid password")

    user.hashed_password = hash_password(new_password)
    db.commit()
