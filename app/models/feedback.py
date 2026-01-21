#app/models/feedback.py

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database.mixins import UUIDPrimaryKeyMixin

from app.database.db import Base

class Feedback(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "feedback"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    type = Column(
        Enum(
            "GENERAL",
            "VALUATION",
            "PAYMENT",
            "SUBSCRIPTION",
            name="feedback_type"
        ),
        nullable=False
    )

    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    rating = Column(Integer, nullable=True)  # 1–5

    valuation_id = Column(String, nullable=True)
    subscription_id = Column(UUID(as_uuid=True), nullable=True)

    status = Column(
        Enum(
            "OPEN",
            "IN_PROGRESS",
            "RESOLVED",
            "CLOSED",
            name="feedback_status"
        ),
        default="OPEN"
    )

    admin_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), onupdate=datetime.utcnow)
    
    user = relationship("User", backref="feedbacks")