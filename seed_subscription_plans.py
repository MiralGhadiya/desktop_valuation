from app.database import SessionLocal
from app.models.subscription import SubscriptionPlan

def run():
    db = SessionLocal()

    plans = [
        SubscriptionPlan(
            name="BASIC",
            country_code="IN",
            price=999,
            currency="INR",
            max_reports=10,
            allowed_categories=["residential"],
            per_report_price=199,
        ),
        SubscriptionPlan(
            name="PRO",
            country_code="IN",
            price=2499,
            currency="INR",
            max_reports=50,
            allowed_categories=["residential", "commercial"],
            per_report_price=149,
        ),
        SubscriptionPlan(
            name="ENTERPRISE",
            country_code="IN",
            price=5999,
            currency="INR",
            max_reports=None,
            allowed_categories=["residential", "commercial", "land"],
        ),
    ]

    db.add_all(plans)
    db.commit()
    db.close()

    print("✅ Subscription plans seeded successfully")

if __name__ == "__main__":
    run()