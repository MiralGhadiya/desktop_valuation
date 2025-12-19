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

    # deactivate previous subs
    db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.is_active == True
    ).update({"is_active": False})

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


@router.get("/me")
def get_my_subscription(
    country_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = get_active_subscription(
        db=db,
        user_id=current_user.id,
        country_code=country_code.upper(),
    )

    if not sub:
        raise HTTPException(
            status_code=404,
            detail="No active subscription"
        )

    return {
        "subscription_id": sub.id,
        "plan": {
            "id": sub.plan.id,
            "name": sub.plan.name,
            "price": sub.plan.price,
            "currency": sub.plan.currency,
            "max_reports": sub.plan.max_reports,
            "allowed_categories": sub.plan.allowed_categories,
        },
        "usage": {
            "reports_used": sub.reports_used,
            "remaining": (
                None if sub.plan.max_reports is None
                else sub.plan.max_reports - sub.reports_used
            )
        },
        "start_date": sub.start_date,
        "end_date": sub.end_date,
        "is_active": sub.is_active,
    }