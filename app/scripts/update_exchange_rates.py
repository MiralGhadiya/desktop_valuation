from app.database.db import SessionLocal
from app.models import ExchangeRate
from datetime import datetime
import requests
import os

def run():
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    db = SessionLocal()

    try:
        res = requests.get(
            "https://api.exchangerate.host/live",
            params={"access_key": api_key, "base": "USD"},
            timeout=10,
        )
        data = res.json()

        for pair, rate in data["quotes"].items():
            currency = pair.replace("USD", "")
            obj = db.query(ExchangeRate).filter_by(currency_code=currency).first()

            if obj:
                obj.rate_to_usd = rate
                obj.updated_at = datetime.utcnow()
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

if __name__ == "__main__":
    run()
