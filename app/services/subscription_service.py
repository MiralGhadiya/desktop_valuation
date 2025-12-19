from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException

from app.models.subscription import SubscriptionPlan, UserSubscription


def get_active_subscription(
    db: Session,
    user_id: int,
    country_code: str,
):
    now = datetime.utcnow()
    return (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(
            UserSubscription.user_id == user_id,
            UserSubscription.is_active == True,
            UserSubscription.start_date <= now,
            UserSubscription.end_date >= now,
            SubscriptionPlan.country_code == country_code,
            SubscriptionPlan.is_active == True,
        )
        .first()
    )


def enforce_subscription(
    db: Session,
    user_id: int,
    country_code: str,
    category: str,
):
    sub = get_active_subscription(db, user_id, country_code)

    if not sub:
        raise HTTPException(403, "No active subscription for this country")

    plan = sub.plan

    if plan.max_reports is not None and sub.reports_used >= plan.max_reports:
        if plan.per_report_price:
            raise HTTPException(
                status_code=402,
                detail=f"Pay per report required: {plan.per_report_price} {plan.currency}"
            )
        raise HTTPException(403, "Report limit exceeded")

    return sub


def increment_usage(db: Session, subscription: UserSubscription):
    subscription.reports_used += 1
    db.commit()