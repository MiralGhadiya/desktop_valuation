from pydantic import BaseModel, EmailStr
from typing import List, Optional


class InquiryCreate(BaseModel):
    type: str  # CONTACT or SERVICE

    first_name: str
    last_name: Optional[str] = None

    email: EmailStr
    phone_number: Optional[str] = None

    message: str

    services: Optional[List[str]] = None
    subscribe_newsletter: Optional[bool] = False
