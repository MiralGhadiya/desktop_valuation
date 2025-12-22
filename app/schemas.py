from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr | None = None
    username: str
    mobile_number: str


class UserCreate(UserBase):
    password: str
    
    
class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    mobile_number: str
    country: str

    class Config:
        from_attributes = True
        
        
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
    
    
    
class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminProfile(BaseModel):
    id: int
    email: EmailStr
    username: str
    
    
class AdminUserResponse(BaseModel):
    id: int
    email: Optional[EmailStr]
    username: str
    mobile_number: str
    is_active: bool
    is_email_verified: bool
    is_superuser: bool

    class Config:
        from_attributes = True


class AdminResetPassword(BaseModel):
    new_password: str
    confirm_password: str
    
    
class SubscriptionPlanCreate(BaseModel):
    name: str
    country_code: str
    price: int
    currency: str
    max_reports: Optional[int] = None
    allowed_categories: List[str]
    per_report_price: Optional[int] = None


class SubscriptionPlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[int] = None
    currency: Optional[str] = None
    max_reports: Optional[int] = None
    allowed_categories: Optional[List[str]] = None
    per_report_price: Optional[int] = None


class SubscriptionPlanResponse(BaseModel):
    id: int
    name: str
    country_code: str
    price: int
    currency: str
    max_reports: Optional[int]
    allowed_categories: List[str]
    per_report_price: Optional[int]
    is_active: bool

    class Config:
        from_attributes = True
        
        
class AssignSubscription(BaseModel):
    plan_id: int
    duration_days: int = 30
    pricing_country_code: Optional[str] = None


class UpdateSubscription(BaseModel):
    extend_days: Optional[int] = None
    reset_reports_used: Optional[bool] = False
    deactivate: Optional[bool] = False


class UserSubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    plan_name: str
    pricing_country_code: str
    start_date: datetime
    end_date: datetime
    reports_used: int
    is_active: bool

    class Config:
        from_attributes = True
        
        
class ValuationResponse(BaseModel):
    id: int
    valuation_id: str
    user_id: int
    category: str
    country_code: str
    subscription_id: int
    created_at: datetime
    pdf_path: str

    class Config:
        from_attributes = True


class ValuationDetailResponse(ValuationResponse):
    user_fields: dict
    ai_response: dict
    report_context: dict