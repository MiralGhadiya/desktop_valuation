from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.database.mixins import UUIDPrimaryKeyMixin
from app.database.db import Base


class Inquiry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "inquiries"

    type = Column(
        Enum("CONTACT", "SERVICE", name="inquiry_type"),
        nullable=False
    )

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)

    email = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)

    message = Column(Text, nullable=False)

    services = Column(JSON, nullable=True)
    subscribe_newsletter = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)