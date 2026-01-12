#app/routes/admin/subscription_plans.py

from datetime import datetime
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import get_db, require_superuser
from app.models.subscription import SubscriptionPlan
from app.schemas import SubscriptionPlanResponse, SubscriptionPlanCreate, SubscriptionPlanUpdate

from app.common import PaginatedResponse
from app.deps import pagination_params
from app.utils.date_filters import filter_by_date_range

from app.utils.logger_config import app_logger as logger

router = APIRouter(
    prefix="/admin/subscription-plans",
    tags=["admin-subscription-plans"]
)

SUBSCRIPTION_PLAN_NOT_FOUND = "Subscription plan not found"


class SubscriptionPlanFilters:
    def __init__(
        self,
        country_code: Optional[str] = Query(None),
        is_active: Optional[bool] = Query(None),

        min_price: Optional[int] = Query(None, ge=0),
        max_price: Optional[int] = Query(None, ge=0),
        
        max_reports: Optional[int] = Query(None, ge=0),
        min_reports: Optional[int] = Query(None, ge=0),

        currency: Optional[str] = Query(None),

        has_per_report_price: Optional[bool] = Query(None),

        created_from: Optional[datetime] = Query(None),
        created_to: Optional[datetime] = Query(None),

        category: Optional[str] = Query(None),
    ):
        self.country_code = country_code
        self.is_active = is_active
        self.min_price = min_price
        self.max_price = max_price
        self.min_reports = min_reports
        self.max_reports = max_reports
        self.currency = currency
        self.has_per_report_price = has_per_report_price
        self.created_from = created_from
        self.created_to = created_to
        self.category = category
        

@router.get("", response_model=PaginatedResponse[SubscriptionPlanResponse])
def list_subscription_plans(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
    
    params: dict = Depends(pagination_params),
    
    filters: SubscriptionPlanFilters = Depends(),

):
    logger.info(
        "Admin subscription plans list requested "
        f"country_code={filters.country_code} is_active={filters.is_active} "
        f"search={params['search']}"
    )

    query = db.query(SubscriptionPlan)

    if params["search"]:
        query = query.filter(
            SubscriptionPlan.name.ilike(f"%{params['search']}%")
        )

    if filters.country_code:
        query = query.filter(
            SubscriptionPlan.country_code == filters.country_code.upper()
        )

    if filters.is_active is not None:
        query = query.filter(
            SubscriptionPlan.is_active == filters.is_active
        )

    if filters.min_price is not None:
        query = query.filter(SubscriptionPlan.price >= filters.min_price)

    if filters.max_price is not None:
        query = query.filter(SubscriptionPlan.price <= filters.max_price)

    if filters.currency:
        query = query.filter(
            SubscriptionPlan.currency == filters.currency.upper()
        )

    if filters.min_reports is not None:
        query = query.filter(
            SubscriptionPlan.max_reports >= filters.min_reports
        )

    if filters.max_reports is not None:
        query = query.filter(
            SubscriptionPlan.max_reports <= filters.max_reports
        )

    if filters.has_per_report_price is not None:
        if filters.has_per_report_price:
            query = query.filter(
                SubscriptionPlan.per_report_price.isnot(None)
            )
        else:
            query = query.filter(
                SubscriptionPlan.per_report_price.is_(None)
            )

    if filters.category:
        query = query.filter(
            SubscriptionPlan.allowed_categories.contains(
                [filters.category]
            )
        )
        
    query = filter_by_date_range(
        query,
        SubscriptionPlan.created_at,
        filters.created_from,
        filters.created_to,
    )

    total = query.count()

    plans = (
        query
        .order_by(SubscriptionPlan.id.desc())
        .offset((params["page"] - 1) * params["limit"])
        .limit(params["limit"])
        .all()
    )

    logger.debug(f"Admin subscription plans fetched count={len(plans)}")

    return {
        "data": plans,
        "pagination": {
            "page": params["page"],
            "limit": params["limit"],
            "total": total,
        }
    }
    
    
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

    try:
        db.add(plan)
        db.commit()
        db.refresh(plan)
    except Exception:
        db.rollback()
        logger.exception("Failed to create subscription plan")
        raise HTTPException(500, "Creation failed")
    
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

    try:
        db.commit()
        db.refresh(plan)
    except Exception:
        db.rollback()
        logger.exception("Failed to update subscription plan")
        raise HTTPException(500, "Update failed")
    
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
    
    try:
        plan.is_active = not plan.is_active
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to toggle subscription plan")
        raise HTTPException(500, "Update failed")

    logger.info(
        f"Subscription plan status changed plan_id={plan.id} "
        f"is_active={plan.is_active}"
    )

    return {
        "message": "Plan status updated",
        "is_active": plan.is_active
    }
