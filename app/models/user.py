# app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, index=True, nullable=False)
    mobile_number = Column(String, unique=True, index=True, nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"))
    hashed_password = Column(String, nullable=False)

    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)

    country = relationship("Country", back_populates="users")
    
    is_superuser = Column(Boolean, default=False)
