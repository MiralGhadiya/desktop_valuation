#app/schemas/valuation.py

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel


class ValuationResponse(BaseModel):
    id: UUID
    valuation_id: str
    user_id: UUID
    category: str
    country_code: str
    subscription_id: UUID
    created_at: datetime
    pdf_path: str

    class Config:
        from_attributes = True


class ValuationDetailResponse(ValuationResponse):
    user_fields: dict
    ai_response: dict
    report_context: dict
