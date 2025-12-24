#app/routes/admin/subscription_plans.py

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_db, require_superuser
from app.models.subscription import SubscriptionPlan
from app.schemas import SubscriptionPlanResponse, SubscriptionPlanCreate, SubscriptionPlanUpdate

from app.utils.logger_config import app_logger as logger

router = APIRouter(
    prefix="/admin/subscription-plans",
    tags=["admin-subscription-plans"]
)

SUBSCRIPTION_PLAN_NOT_FOUND = "Subscription plan not found"


@router.get("", response_model=List[SubscriptionPlanResponse])
def list_subscription_plans(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),

    country_code: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    logger.info(
        "Admin subscription plans list requested "
        f"country_code={country_code} is_active={is_active}"
    )

    query = db.query(SubscriptionPlan)

    if country_code:
        query = query.filter(
            SubscriptionPlan.country_code == country_code.upper()
        )

    if is_active is not None:
        query = query.filter(
            SubscriptionPlan.is_active == is_active
        )
        
    plans = query.order_by(SubscriptionPlan.id.desc()).all()
    logger.debug(f"Admin subscription plans fetched count={len(plans)}")

    return query.order_by(SubscriptionPlan.id.desc()).all()


@router.get("/{plan_id}", response_model=SubscriptionPlanResponse)
def get_subscription_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin requested subscription plan plan_id={plan_id}")

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()

    if not plan:
        logger.warning(f"{SUBSCRIPTION_PLAN_NOT_FOUND} plan_id={plan_id}")
        raise HTTPException(404, SUBSCRIPTION_PLAN_NOT_FOUND)

    return plan


@router.post("", response_model=SubscriptionPlanResponse)
def create_subscription_plan(
    data: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(
        "Admin creating subscription plan "
        f"name={data.name} country={data.country_code}"
    )

    plan = SubscriptionPlan(
        name=data.name.upper(),
        country_code=data.country_code.upper(),
        price=data.price,
        currency=data.currency.upper(),
        max_reports=data.max_reports,
        allowed_categories=data.allowed_categories,
        per_report_price=data.per_report_price,
        is_active=True,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    logger.info(f"Subscription plan created plan_id={plan.id}")

    return plan


@router.put("/{plan_id}", response_model=SubscriptionPlanResponse)
def update_subscription_plan(
    plan_id: int,
    data: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin updating subscription plan plan_id={plan_id}")

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()

    if not plan:
        logger.warning(f"{SUBSCRIPTION_PLAN_NOT_FOUND} plan_id={plan_id}")
        raise HTTPException(404, SUBSCRIPTION_PLAN_NOT_FOUND)
    
    updates = data.model_dump(exclude_unset=True)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    
    logger.info(
        f"Subscription plan updated plan_id={plan.id} "
        f"fields={list(updates.keys())}"
    )


    return plan


@router.patch("/{plan_id}/toggle")
def toggle_subscription_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin toggling subscription plan plan_id={plan_id}")

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()

    if not plan:
        logger.warning(f"{SUBSCRIPTION_PLAN_NOT_FOUND} plan_id={plan_id}")
        raise HTTPException(404, SUBSCRIPTION_PLAN_NOT_FOUND)

    plan.is_active = not plan.is_active
    db.commit()
    
    logger.info(
        f"Subscription plan status changed plan_id={plan.id} "
        f"is_active={plan.is_active}"
    )

    return {
        "message": "Plan status updated",
        "is_active": plan.is_active
    }
