# app/models/subscription.py

from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON

from app.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)              
    country_code = Column(String, nullable=False, index=True)  

    price = Column(Integer, nullable=False)             
    currency = Column(String, nullable=False)           

    max_reports = Column(Integer, nullable=True)         
    allowed_categories = Column(JSON, nullable=False)  

    per_report_price = Column(Integer, nullable=True)   
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False, index=True)
    
    pricing_country_code = Column(String, nullable=False)  
    ip_country_code = Column(String, nullable=True)
    payment_country_code = Column(String, nullable=True)
    
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)
    payment_status = Column(String, default="CREATED")  # CREATED | PENDING | PAID | FAILED | REFUNDED
    
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    reports_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_expired = Column(Boolean, default=False)

    user = relationship("User")
    plan = relationship("SubscriptionPlan")
    