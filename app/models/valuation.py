#app/models/valuation.py

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from datetime import datetime
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, EmailStr
from typing import Optional
from fastapi import Form    


class ValuationReport(Base):
    __tablename__ = "valuation_reports"

    id = Column(Integer, primary_key=True, index=True)
    valuation_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User")
    category = Column(String, nullable=False)    
    country_code = Column(String, nullable=False)  
    created_at = Column(DateTime, default=datetime.utcnow)
    user_fields = Column(JSON, nullable=False)
    ai_response = Column(JSON, nullable=False)
    subscription_id = Column(Integer, ForeignKey("user_subscriptions.id"), nullable=False)
    report_context = Column(JSON, nullable=False)
    pdf_path = Column(String, nullable=False)


class DesktopValuationForm(BaseModel):
    country: str
    city_location: str
    full_address: str
    property_type: str
    land_area: str
    built_up_area: Optional[str] = None
    year_built: Optional[str] = None
    estimated_market_value: Optional[str] = None
    purpose_of_valuation: str
    full_name: str
    email: EmailStr
    contact_number: str
    
    
def DesktopValuationFormDep(
    country: str = Form(...),
    city_location: str = Form(...),
    full_address: str = Form(...),
    property_type: str = Form(...),
    land_area: str = Form(...),
    built_up_area: Optional[str] = Form(None),
    year_built: Optional[str] = Form(None),
    estimated_market_value: Optional[str] = Form(None),
    purpose_of_valuation: str = Form(...),
    full_name: str = Form(...),
    email: EmailStr = Form(...),
    contact_number: str = Form(...),
) -> DesktopValuationForm:
    return DesktopValuationForm(
        country=country,
        city_location=city_location,
        full_address=full_address,
        property_type=property_type,
        land_area=land_area,
        built_up_area=built_up_area,
        year_built=year_built,
        estimated_market_value=estimated_market_value,
        purpose_of_valuation=purpose_of_valuation,
        full_name=full_name,
        email=email,
        contact_number=contact_number,
    )
