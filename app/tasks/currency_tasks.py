import os
import requests
from datetime import datetime

from app.models import ExchangeRate
from app.database.db import SessionLocal


def update_exchange_rates():
    print("Currency update started...")  # 👈 ADD

    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    if not api_key:
        print("API KEY NOT SET")
        raise RuntimeError("EXCHANGE_RATE_API_KEY not set")
    print("API KEY FOUND")  
    db = SessionLocal()
    try:
        res = requests.get(
            "https://api.exchangerate.host/live",
            params={"access_key": api_key, "base": "USD"},
            timeout=10,
        )
        res.raise_for_status()

        data = res.json()
        quotes = data.get("quotes", {})

        for pair, rate in quotes.items():
            if not pair.startswith("USD"):
                continue

            currency = pair.replace("USD", "")

            existing = db.query(ExchangeRate).filter(
                ExchangeRate.currency_code == currency
            ).first()

            if existing:
                existing.rate_to_usd = rate
                existing.updated_at = datetime.utcnow()
            else:
                db.add(
                    ExchangeRate(
                        currency_code=currency,
                        rate_to_usd=rate,
                        updated_at=datetime.utcnow(),
                    )
                )

        db.commit()

    finally:
        db.close()
