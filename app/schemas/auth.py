from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ChangePassword(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class ResetPassword(BaseModel):
    token: str
    new_password: str
    confirm_password: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr
