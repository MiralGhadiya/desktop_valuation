#app/routes/subscription.py

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request

from app.deps import get_db, get_current_user

from app.models import User
from app.models.subscription import SubscriptionPlan, UserSubscription

from app.utils.logger_config import app_logger as logger


router = APIRouter(prefix="/subscription", tags=["subscription"])

    
@router.get("/plans")
def list_plans(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    country = request.state.ip_country or current_user.country.country_code

    logger.debug(
            f"IP country={request.state.ip_country}, "
            f"user country={current_user.country.country_code}, "
            f"final pricing country={country}"
        )

    return db.query(SubscriptionPlan).filter(
        SubscriptionPlan.country_code == country,
        SubscriptionPlan.is_active == True,
    ).all()


@router.get("/my-plans")
def get_my_active_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)

    plans = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(
            UserSubscription.user_id == current_user.id,
            UserSubscription.is_active == True,
            UserSubscription.start_date <= now,
            UserSubscription.end_date >= now,
            SubscriptionPlan.is_active == True,
        )
        .order_by(UserSubscription.end_date.asc())
        .all()
    )

    return [
        {
            "subscription_id": s.id,
            "plan_name": s.plan.name,
            "country": s.plan.country_code,
            "price": s.plan.price,
            "currency": s.plan.currency,
            "max_reports": s.plan.max_reports,
            "reports_used": s.reports_used,
            "remaining": (
                None if s.plan.max_reports is None
                else s.plan.max_reports - s.reports_used
            ),
            "start_date": s.start_date,
            "end_date": s.end_date,
        }
        for s in plans
    ]
    
    
@router.get("/plan-history")
def subscription_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plans = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(UserSubscription.user_id == current_user.id)
        .order_by(UserSubscription.start_date.desc())
        .all()
    )

    now = datetime.now(timezone.utc)

    result = []
    for s in plans:
        end_date = s.end_date

        # ✅ normalize DB datetime
        if end_date and end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        result.append(
            {
                "subscription_id": s.id,
                "plan_name": s.plan.name,
                "country": s.plan.country_code,
                "price": s.plan.price,
                "currency": s.plan.currency,
                "max_reports": s.plan.max_reports,
                "reports_used": s.reports_used,
                "start_date": s.start_date,
                "end_date": s.end_date,
                "is_active": s.is_active,
                "expired": end_date < now if end_date else False,
                "purchased_on": s.start_date,
            }
        )

    return result



@router.get("/default")
def get_default_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)

    sub = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(
            UserSubscription.user_id == current_user.id,
            UserSubscription.is_active == True,
            UserSubscription.start_date <= now,
            UserSubscription.end_date >= now,
        )
        .order_by(
            SubscriptionPlan.price.desc(),
            UserSubscription.end_date.desc()
        )
        .first()
    )

    if not sub:
        raise HTTPException(404, "No active subscription")

    return {
        "subscription_id": sub.id,
        "plan": sub.plan.name,
        "remaining": (
            None if sub.plan.max_reports is None
            else sub.plan.max_reports - sub.reports_used
        ),
    }
    

@router.get("/{subscription_id}/usage")
def get_subscription_usage(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subscription = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(
            UserSubscription.id == subscription_id,
            UserSubscription.user_id == current_user.id,
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )

    now = datetime.now(timezone.utc)

    # 🔑 FIX: normalize DB datetime
    end_date = subscription.end_date
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)

    max_reports = subscription.plan.max_reports
    reports_used = subscription.reports_used

    remaining = (
        None
        if max_reports is None
        else max(0, max_reports - reports_used)
    )

    return {
        "subscription_id": subscription.id,
        "plan_name": subscription.plan.name,
        "max_reports": max_reports,
        "reports_used": reports_used,
        "remaining": remaining,
        "expires_at": end_date,
        "is_active": subscription.is_active and end_date >= now,
    }