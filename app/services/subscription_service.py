#app/services/subscription_service.py

from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.utils.email import send_subscription_expiry_email
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


def send_expiry_reminders(db: Session):
    today = datetime.utcnow().date()
    sent = 0

    logger.info(f"[EXPIRY REMINDER] Job started | today={today}")

    subscriptions = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.end_date.isnot(None),
            UserSubscription.is_active == True,
            UserSubscription.is_expired == False,
        )
        .all()
    )

    logger.info(f"[EXPIRY REMINDER] Active subscriptions found={len(subscriptions)}")

    for sub in subscriptions:
        if not sub.end_date:
            logger.warning(
                f"[EXPIRY REMINDER] Subscription id={sub.id} has no end_date"
            )
            continue

        days_left = (sub.end_date.date() - today).days

        logger.info(
            f"[EXPIRY REMINDER] sub_id={sub.id} "
            f"user_id={sub.user_id} "
            f"end_date={sub.end_date.date()} "
            f"days_left={days_left}"
        )

        if days_left in (1, 2, 3):
            user = sub.user

            if not user:
                logger.warning(
                    f"[EXPIRY REMINDER] sub_id={sub.id} has no user relation"
                )
                continue

            if not user.email:
                logger.warning(
                    f"[EXPIRY REMINDER] user_id={user.id} has no email"
                )
                continue

            logger.info(
                f"[EXPIRY REMINDER] Sending email | "
                f"user_id={user.id} email={user.email} "
                f"plan={sub.plan.name} expires_in={days_left} days"
            )

            try:
                send_subscription_expiry_email(
                    to_email=user.email,
                    plan_name=sub.plan.name,
                    expiry_date=sub.end_date,
                )
                sent += 1

            except Exception:
                logger.exception(
                    f"[EXPIRY REMINDER] FAILED sending email | "
                    f"user_id={user.id} sub_id={sub.id}"
                )

        else:
            logger.debug(
                f"[EXPIRY REMINDER] Skipped | sub_id={sub.id} days_left={days_left}"
            )

    logger.info(
        f"[EXPIRY REMINDER] Job finished | emails_sent={sent}"
    )

    return {"emails_sent": sent}