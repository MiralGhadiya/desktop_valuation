#app/models/country.py

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from app.database.mixins import UUIDPrimaryKeyMixin

from app.database.db import Base


class Country(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "countries"

    name = Column(String, nullable=False)
    country_code = Column(String, unique=True, index=True)
    dial_code = Column(String)
    currency_code = Column(String, nullable=True)  
    
    users = relationship("User", back_populates="country")
