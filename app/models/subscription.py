# app/models/subscription.py

from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.dialects.postgresql import UUID
from app.database.mixins import UUIDPrimaryKeyMixin

from app.database.db import Base


class SubscriptionPlan(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "subscription_plans"

    name = Column(String, nullable=False)              
    country_code = Column(String, nullable=False, index=True)  

    price = Column(Integer, nullable=False)             
    currency = Column(String, nullable=False)           

    max_reports = Column(Integer, nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class UserSubscription(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "user_subscriptions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False, index=True)
    
    pricing_country_code = Column(String, nullable=False)  
    ip_country_code = Column(String, nullable=True)
    payment_country_code = Column(String, nullable=True)
    
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    razorpay_signature = Column(String, nullable=True)
    payment_status = Column(String, default="CREATED")  
    
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    reports_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_expired = Column(Boolean, default=False)
    
    auto_renew = Column(Boolean, default=False)
    cancelled_at = Column(DateTime, nullable=True)

    user = relationship("User")
    plan = relationship("SubscriptionPlan")
    