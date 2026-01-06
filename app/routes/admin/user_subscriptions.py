#app/routes/admin/user_subscriptions.py

from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_db, require_superuser

from app.models import User
from app.models.subscription import SubscriptionPlan, UserSubscription

from app.schemas import UpdateSubscription, UserSubscriptionResponse, AssignSubscription

from app.utils.logger_config import app_logger as logger


router = APIRouter(
    prefix="/admin",
    tags=["admin-user-subscriptions"]
)


@router.get("/user-subscriptions", response_model=List[UserSubscriptionResponse])
def list_all_user_subscriptions(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),

    user_id: Optional[int] = Query(None),
    plan_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    logger.info(
        "Admin listing user subscriptions "
        f"user_id={user_id} plan_id={plan_id} is_active={is_active}"
    )
    
    query = db.query(UserSubscription).join(SubscriptionPlan)

    if user_id:
        query = query.filter(UserSubscription.user_id == user_id)

    if plan_id:
        query = query.filter(UserSubscription.plan_id == plan_id)

    if is_active is not None:
        query = query.filter(UserSubscription.is_active == is_active)

    subs = query.order_by(UserSubscription.start_date.desc()).all()
    
    logger.debug(f"Admin fetched user subscriptions count={len(subs)}")

    return [
        UserSubscriptionResponse(
            id=s.id,
            user_id=s.user_id,
            plan_id=s.plan_id,
            plan_name=s.plan.name,
            pricing_country_code=s.pricing_country_code,
            start_date=s.start_date,
            end_date=s.end_date,
            reports_used=s.reports_used,
            is_active=s.is_active,
        )
        for s in subs
    ]


@router.get("/users/{user_id}/subscriptions", response_model=List[UserSubscriptionResponse])
def get_user_subscriptions(
    user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin fetching subscriptions for user_id={user_id}")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found while fetching subscriptions user_id={user_id}")
        raise HTTPException(404, "User not found")

    subs = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(UserSubscription.user_id == user_id)
        .order_by(UserSubscription.start_date.desc())
        .all()
    )
    
    logger.debug(
        f"Admin fetched subscriptions for user_id={user_id} count={len(subs)}"
    )

    return [
        UserSubscriptionResponse(
            id=s.id,
            user_id=s.user_id,
            plan_id=s.plan_id,
            plan_name=s.plan.name,
            pricing_country_code=s.pricing_country_code,
            start_date=s.start_date,
            end_date=s.end_date,
            reports_used=s.reports_used,
            is_active=s.is_active,
        )
        for s in subs
    ]


@router.post("/users/{user_id}/assign-subscription", response_model=UserSubscriptionResponse)
def assign_subscription_to_user(
    user_id: int,
    data: AssignSubscription,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(
        f"Admin assigning subscription user_id={user_id} "
        f"plan_id={data.plan_id} duration_days={data.duration_days}"
    )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found while assigning subscription user_id={user_id}")
        raise HTTPException(404, "User not found")

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == data.plan_id,
        SubscriptionPlan.is_active == True
    ).first()

    if not plan:
        logger.warning(
            f"Subscription plan not found while assigning plan_id={data.plan_id}"
        )
        raise HTTPException(404, "Subscription plan not found")

    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=data.duration_days)

    sub = UserSubscription(
        user_id=user.id,
        plan_id=plan.id,
        pricing_country_code=data.pricing_country_code or plan.country_code,
        ip_country_code=None,
        start_date=start_date,
        end_date=end_date,
        is_active=True,
    )
    try:
        db.add(sub)
        db.commit()
        db.refresh(sub)
    except Exception:
        db.rollback()
        logger.exception("Failed to assign subscription to user")
        raise
    
    logger.info(
        f"Subscription assigned sub_id={sub.id} "
        f"user_id={user.id} plan_id={plan.id}"
    )

    return UserSubscriptionResponse(
        id=sub.id,
        user_id=sub.user_id,
        plan_id=sub.plan_id,
        plan_name=plan.name,
        pricing_country_code=sub.pricing_country_code,
        start_date=sub.start_date,
        end_date=sub.end_date,
        reports_used=sub.reports_used,
        is_active=sub.is_active,
    )


@router.patch("/user-subscriptions/{subscription_id}")
def update_user_subscription(
    subscription_id: int,
    data: UpdateSubscription,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin updating subscription sub_id={subscription_id}")

    sub = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id
    ).first()
    
    if not sub:
        raise HTTPException(404, "Subscription not found")
    
    try:
        changes = []

        if data.extend_days:
            sub.end_date += timedelta(days=data.extend_days)
            changes.append(f"extend_days={data.extend_days}")

        if data.reset_reports_used:
            sub.reports_used = 0
            changes.append("reset_reports_used")

        if data.deactivate:
            sub.is_active = False
            changes.append("deactivated")

        db.commit()
        
    except Exception:
        db.rollback()
        logger.exception("Failed to update user subscription")
        raise HTTPException(500, "Update failed")

    logger.info(
        f"Subscription updated sub_id={subscription_id} "
        f"changes={changes}"
    )

    return {"message": "Subscription updated successfully"}


@router.post("/user-subscriptions/{subscription_id}/cancel")
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin cancelling subscription sub_id={subscription_id}")

    sub = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id
    ).first()

    if not sub:
        logger.warning(f"Subscription not found during cancel sub_id={subscription_id}")
        raise HTTPException(404, "Subscription not found")
    
    try:
        sub.is_active = False
        sub.end_date = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to cancel subscription")
        raise HTTPException(500, "Cancel failed")
    
    logger.info(f"Subscription cancelled sub_id={subscription_id}")

    return {"message": "Subscription cancelled"}