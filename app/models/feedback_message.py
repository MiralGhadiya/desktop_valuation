from app.database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime, Enum

class FeedbackMessage(Base):
    __tablename__ = "feedback_messages"

    id = Column(Integer, primary_key=True)
    feedback_id = Column(
        Integer,
        ForeignKey("feedback.id", ondelete="CASCADE"),
        nullable=False
    )

    sender = Column(
        Enum("USER", "ADMIN", name="feedback_sender"),
        nullable=False
    )

    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
