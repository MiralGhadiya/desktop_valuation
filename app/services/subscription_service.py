#app/services/subscription_service.py

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
    subscription_id: int,
    category: str,
):
    sub = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(
            UserSubscription.id == subscription_id,
            UserSubscription.user_id == user_id,
            UserSubscription.is_active == True,
            UserSubscription.start_date <= datetime.utcnow(),
            UserSubscription.end_date >= datetime.utcnow(),
        )
        .first()
    )

    if not sub:
        raise HTTPException(403, "Invalid or inactive subscription")

    plan = sub.plan

    if category not in plan.allowed_categories:
        raise HTTPException(403, "Category not allowed for this plan")

    if plan.max_reports is not None and sub.reports_used >= plan.max_reports:
        raise HTTPException(403, "Report limit exceeded")

    return sub


def increment_usage(db: Session, subscription: UserSubscription):
    subscription.reports_used += 1
    db.commit()