#app/routes/subscription.py

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.deps import get_db, get_current_user
from app.models import User
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.services.subscription_service import get_active_subscription

router = APIRouter(prefix="/subscription", tags=["subscription"])


# @router.get("/plans/{country_code}")
# def list_plans(country_code: str, db: Session = Depends(get_db)):
#     return db.query(SubscriptionPlan).filter(
#         SubscriptionPlan.country_code == country_code.upper(),
#         SubscriptionPlan.is_active == True,
#     ).all()
    
    
@router.get("/plans")
def list_plans(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    country = request.state.ip_country or current_user.country.country_code

    print("🟢 IP Country:", request.state.ip_country)
    print("🟢 User Country:", current_user.country.country_code)
    print("🟢 Final Pricing Country:", country)

    return db.query(SubscriptionPlan).filter(
        SubscriptionPlan.country_code == country,
        SubscriptionPlan.is_active == True,
    ).all()
    

@router.post("/buy/{plan_id}")
def buy_plan(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id,
        SubscriptionPlan.is_active == True
    ).first()

    if not plan:
        raise HTTPException(404, "Plan not found")

    ip_country = request.state.ip_country
    user_country = current_user.country.country_code

    # FINAL pricing country (until payment integration)
    pricing_country = ip_country or user_country

    if pricing_country != plan.country_code:
        raise HTTPException(
            403,
            "Plan pricing country mismatch. Please purchase correct regional plan."
        )

    sub = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        pricing_country_code=pricing_country,
        ip_country_code=ip_country,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        is_active=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    return sub


@router.get("/my-plans")
def get_my_active_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()

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

    return [
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
            "expired": s.end_date < datetime.utcnow(),
            "purchased_on": s.start_date,
        }
        for s in plans
    ]


@router.get("/default")
def get_default_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.utcnow()

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