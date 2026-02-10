from app.database.db import SessionLocal
from app.services.subscription_service import (
    expire_subscriptions,
    send_expiry_reminders,
)

def run():
    db = SessionLocal()
    try:
        expire_subscriptions(db)
        send_expiry_reminders(db)
    finally:
        db.close()

if __name__ == "__main__":
    run()
