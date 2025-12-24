#app/models/valuation.py

from fastapi import Form   
from typing import Optional 
from datetime import datetime
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey

from app.database import Base


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
    
    
# class ValuationJob(Base):
#     __tablename__ = "valuation_jobs"

#     id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
#     subscription_id = Column(Integer, ForeignKey("user_subscriptions.id"), nullable=False)

#     status = Column(String, nullable=False, default="queued")  # queued|processing|completed|failed
#     category = Column(String, nullable=True)

#     request_payload = Column(JSON, nullable=False)
#     valuation_id = Column(String, nullable=True)
#     pdf_path = Column(String, nullable=True)
#     error_message = Column(Text, nullable=True)

#     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)



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
    
    
def desktop_valuation_form_dep(
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
