from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Dict, Optional

class StaffBase(BaseModel):
    name: str  
    email: str  
    phone: str 
    password: str 
    role: str 
    
    
class StaffLogin(BaseModel):
    email: EmailStr
    password: str


class StaffCreate(StaffBase):
    can_access_user: bool = False
    can_access_staff: bool = False
    can_access_property: bool = False

    can_add_property: bool = False
    can_edit_property: bool = False
    can_delete_property: bool = False
    can_unlist_property: bool = False


class StaffUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    can_access_user: Optional[bool] = None
    can_access_staff: Optional[bool] = None
    can_access_property: Optional[bool] = None
    can_add_property: Optional[bool] = None
    can_edit_property: Optional[bool] = None
    can_delete_property: Optional[bool] = None
    can_unlist_property: Optional[bool] = None


class StaffResponse(BaseModel):
    id: UUID
    name: str
    email: str
    phone: str
    role: str
    accesses: Dict[str, bool]

    class Config:
        from_attributes = True