# app/models/subscription.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy import Index


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)                 # BASIC / PRO / ENTERPRISE
    country_code = Column(String, nullable=False, index=True)  # IN / US / AE etc

    price = Column(Integer, nullable=False)               # monthly price (minor units optional)
    currency = Column(String, nullable=False)             # INR / USD etc

    max_reports = Column(Integer, nullable=True)          # None = unlimited
    allowed_categories = Column(JSON, nullable=False)     # ["residential","commercial","land"]

    per_report_price = Column(Integer, nullable=True)     # optional fallback per report price
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

    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    reports_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    user = relationship("User")
    plan = relationship("SubscriptionPlan")
    

Index(
    "uq_active_user_subscription",
    UserSubscription.user_id,
    unique=True,
    postgresql_where=UserSubscription.is_active == True
)
