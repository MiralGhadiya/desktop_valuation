from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.deps import get_db, require_superuser
from app.models.subscription import SubscriptionPlan
from app.schemas import SubscriptionPlanResponse, SubscriptionPlanCreate, SubscriptionPlanUpdate

router = APIRouter(
    prefix="/admin/subscription-plans",
    tags=["admin-subscription-plans"]
)


@router.get("", response_model=List[SubscriptionPlanResponse])
def list_subscription_plans(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),

    country_code: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    query = db.query(SubscriptionPlan)

    if country_code:
        query = query.filter(
            SubscriptionPlan.country_code == country_code.upper()
        )

    if is_active is not None:
        query = query.filter(
            SubscriptionPlan.is_active == is_active
        )

    return query.order_by(SubscriptionPlan.id.desc()).all()


@router.get("/{plan_id}", response_model=SubscriptionPlanResponse)
def get_subscription_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(404, "Subscription plan not found")

    return plan


@router.post("", response_model=SubscriptionPlanResponse)
def create_subscription_plan(
    data: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
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

    return plan


@router.put("/{plan_id}", response_model=SubscriptionPlanResponse)
def update_subscription_plan(
    plan_id: int,
    data: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(404, "Subscription plan not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)

    return plan


@router.patch("/{plan_id}/toggle")
def toggle_subscription_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id
    ).first()

    if not plan:
        raise HTTPException(404, "Subscription plan not found")

    plan.is_active = not plan.is_active
    db.commit()

    return {
        "message": "Plan status updated",
        "is_active": plan.is_active
    }


# # -----------------------------
# # 6️⃣ SOFT DELETE PLAN
# # -----------------------------
# @router.delete("/{plan_id}")
# def delete_subscription_plan(
#     plan_id: int,
#     db: Session = Depends(get_db),
#     _: None = Depends(require_superuser),
# ):
#     plan = db.query(SubscriptionPlan).filter(
#         SubscriptionPlan.id == plan_id
#     ).first()

#     if not plan:
#         raise HTTPException(404, "Subscription plan not found")

#     plan.is_active = False
#     db.commit()

#     return {"message": "Subscription plan deleted"}
