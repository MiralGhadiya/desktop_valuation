#app/schemas/admin.py

from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr
from typing_extensions import Literal


class AdminProfile(BaseModel):
    id: UUID
    email: EmailStr
    username: str


class AdminUserResponse(BaseModel):
    id: UUID
    email: Optional[EmailStr]
    username: str
    mobile_number: str
    is_active: bool
    is_email_verified: bool
    is_superuser: bool
    role: str

    class Config:
        from_attributes = True


class AdminResetPassword(BaseModel):
    new_password: str
    confirm_password: str


class AdminFeedbackAction(BaseModel):
    status: Optional[
        Literal["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"]
    ] = None
    reply: Optional[str] = None
    notify_user: bool = False
    admin_note: Optional[str] = None
