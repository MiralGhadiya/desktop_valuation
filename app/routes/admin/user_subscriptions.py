from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta

from app.deps import get_db, require_superuser
from app.models import User
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.schemas import UpdateSubscription, UserSubscriptionResponse, AssignSubscription

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
    query = db.query(UserSubscription).join(SubscriptionPlan)

    if user_id:
        query = query.filter(UserSubscription.user_id == user_id)

    if plan_id:
        query = query.filter(UserSubscription.plan_id == plan_id)

    if is_active is not None:
        query = query.filter(UserSubscription.is_active == is_active)

    subs = query.order_by(UserSubscription.start_date.desc()).all()

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    subs = (
        db.query(UserSubscription)
        .join(SubscriptionPlan)
        .filter(UserSubscription.user_id == user_id)
        .order_by(UserSubscription.start_date.desc())
        .all()
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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == data.plan_id,
        SubscriptionPlan.is_active == True
    ).first()

    if not plan:
        raise HTTPException(404, "Subscription plan not found")

    start_date = datetime.utcnow()
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

    db.add(sub)
    db.commit()
    db.refresh(sub)

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
    sub = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id
    ).first()

    if not sub:
        raise HTTPException(404, "Subscription not found")

    if data.extend_days:
        sub.end_date += timedelta(days=data.extend_days)

    if data.reset_reports_used:
        sub.reports_used = 0

    if data.deactivate:
        sub.is_active = False

    db.commit()

    return {"message": "Subscription updated successfully"}


@router.post("/user-subscriptions/{subscription_id}/cancel")
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    sub = db.query(UserSubscription).filter(
        UserSubscription.id == subscription_id
    ).first()

    if not sub:
        raise HTTPException(404, "Subscription not found")

    sub.is_active = False
    sub.end_date = datetime.utcnow()
    db.commit()

    return {"message": "Subscription cancelled"}