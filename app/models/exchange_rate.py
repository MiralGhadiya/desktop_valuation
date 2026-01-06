# app/models/exchange_rate.py

from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime
from app.database import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    currency_code = Column(String(3), primary_key=True)
    rate_to_usd = Column(Numeric(12, 6), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
