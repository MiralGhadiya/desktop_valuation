from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from app.database import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

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
    subscription_id = Column(Integer, nullable=True)

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