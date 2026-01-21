# app/models/exchange_rate.py

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime
from app.database.db import Base

from sqlalchemy.dialects.postgresql import UUID
from app.database.mixins import UUIDPrimaryKeyMixin

class ExchangeRate(UUIDPrimaryKeyMixin,Base):
    __tablename__ = "exchange_rates"

    currency_code = Column(String(3), unique=True, nullable=False)
    rate_to_usd = Column(Numeric(12, 6), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
