#app/services/subscription_service.py

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.subscription import SubscriptionPlan, UserSubscription
from app.utils.logger_config import app_logger as logger


def get_active_subscription(
    db: Session,
    user_id: int,
    country_code: str,
):
    logger.debug(
        f"Fetching active subscription user_id={user_id} country={country_code}"
    )
    
    now = datetime.now(timezone.utc)
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
    *,
    db: Session,
    user_id: int,
    subscription_id: int,
    category: str,
):
    logger.info(
        f"Enforcing subscription user_id={user_id} "
        f"subscription_id={subscription_id} category={category}"
    )

    sub = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(
            UserSubscription.id == subscription_id,
            UserSubscription.user_id == user_id,
        )
        .first()
    )

    if not sub:
        raise HTTPException(403, "Subscription not found")

    if sub.is_expired:
        logger.warning("Subscription has expired.")
        raise HTTPException(403,"Subscription has expired. Please buy one to proceed further!")

    if not sub.is_active:
        raise HTTPException(403, "Subscription is inactive")

    now = datetime.utcnow()
    if sub.start_date > now or sub.end_date < now:
        raise HTTPException(403, "Subscription is not valid at this time")

    plan = sub.plan

    if category not in plan.allowed_categories:
        raise HTTPException(403, "Category not allowed for this plan")

    if plan.max_reports is not None and sub.reports_used >= plan.max_reports:
        raise HTTPException(403, "Report limit exceeded")

    return sub


def increment_usage(db: Session, subscription: UserSubscription):
    subscription.reports_used += 1
    db.commit()
    logger.info(
        f"Subscription usage incremented "
        f"subscription_id={subscription.id} "
        f"reports_used={subscription.reports_used}"
    )
    
    
def expire_subscriptions(db: Session) -> int:
    """
    Deactivate expired subscriptions.
    Returns number of expired subscriptions.
    """
    
    print("working........")

    now = datetime.utcnow()

    # Fetch active subscriptions only
    subs = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.is_expired == False,
            UserSubscription.end_date < now,
        )
        .all()
    )

    count = 0
    for sub in subs:
        sub.is_expired = True
        count += 1

    if count:
        db.commit()
        logger.info(f"Expired {count} subscriptions")
    else:
        logger.info("No subscriptions to expire")

    return count