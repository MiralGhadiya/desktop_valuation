# app/models/staff.py

from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.db import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Staff(Base):
    __tablename__ = "staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    
    can_access_user = Column(Boolean, default=False)  # User Access
    can_access_staff = Column(Boolean, default=False)  # Staff Access
    can_access_property = Column(Boolean, default=False)  # Property Access

    # Access Permissions
    can_add_property = Column(Boolean, default=False)
    can_edit_property = Column(Boolean, default=False)
    can_delete_property = Column(Boolean, default=False)
    can_unlist_property = Column(Boolean, default=False)

    # Relationship with user table if needed
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    user = relationship("User", back_populates="staff_member")  # Add back_populates here
