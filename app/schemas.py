from pydantic import BaseModel, EmailStr

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