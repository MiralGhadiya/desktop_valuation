#app/models/country.py

from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String

from app.database import Base


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country_code = Column(String, index=True)  # IN, US
    dial_code = Column(String)

    users = relationship("User", back_populates="country")
