#app/routes/admin/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from app.deps import get_db, require_superuser
from app.models import User
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.models.valuation import ValuationReport
from app.utils.logger_config import app_logger as logger

datetime.now(timezone.utc)

router = APIRouter(
    prefix="/admin/dashboard",
    tags=["admin-dashboard"]
)


@router.get("/overview")
def dashboard_overview(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info("Admin dashboard: overview requested")

    total_users = db.query(func.count(User.id)).scalar()
    active_users = db.query(func.count(User.id)).filter(
        User.is_active == True
    ).scalar()

    total_subscriptions = db.query(func.count(UserSubscription.id)).scalar()
    active_subscriptions = db.query(func.count(UserSubscription.id)).filter(
        UserSubscription.is_active == True
    ).scalar()

    total_valuations = db.query(func.count(ValuationReport.id)).scalar()

    logger.debug("Admin dashboard: overview aggregation completed")

    return {
        "users": {
            "total": total_users,
            "active": active_users,
        },
        "subscriptions": {
            "total": total_subscriptions,
            "active": active_subscriptions,
        },
        "valuations": {
            "total": total_valuations
        }
    }


@router.get("/users")
def dashboard_users(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info("Admin dashboard: users stats requested")

    verified = db.query(func.count(User.id)).filter(
        User.is_email_verified == True
    ).scalar()

    unverified = db.query(func.count(User.id)).filter(
        User.is_email_verified == False
    ).scalar()

    inactive = db.query(func.count(User.id)).filter(
        User.is_active == False
    ).scalar()

    last_30_days = datetime.now(timezone.utc) - timedelta(days=30)
    new_users_30d = db.query(func.count(User.id)).filter(
        User.created_at >= last_30_days
    ).scalar()

    logger.debug("Admin dashboard: users stats aggregation completed")

    return {
        "email_verified": verified,
        "email_unverified": unverified,
        "inactive_users": inactive,
        "new_users_last_30_days": new_users_30d,
    }


@router.get("/subscriptions")
def dashboard_subscriptions_country_wise(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info("Admin dashboard: subscriptions breakdown requested")

    rows = (
        db.query(
            SubscriptionPlan.country_code,
            SubscriptionPlan.name,
            SubscriptionPlan.currency,
            SubscriptionPlan.price,
            func.count(UserSubscription.id).label("total"),
            func.count(
                func.nullif(UserSubscription.is_active == False, True)
            ).label("active"),
        )
        .outerjoin(UserSubscription, SubscriptionPlan.id == UserSubscription.plan_id)
        .group_by(
            SubscriptionPlan.country_code,
            SubscriptionPlan.name,
            SubscriptionPlan.currency,
            SubscriptionPlan.price,
        )
        .order_by(
            SubscriptionPlan.country_code,
            SubscriptionPlan.name,
        )
        .all()
    )

    logger.debug("Admin dashboard: subscription aggregation completed")

    return [
        {
            "country": r.country_code,
            "plan": r.name,
            "currency": r.currency,
            "price": r.price,
            "subscriptions": {
                "total": r.total,
                "active": r.active,
            },
            "revenue": {
                "total": r.total * r.price,
                "active": r.active * r.price,
            },
        }
        for r in rows
    ]


@router.get("/valuations")
def dashboard_valuations(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info("Admin dashboard: valuation stats requested")

    by_category = (
        db.query(
            ValuationReport.category,
            func.count(ValuationReport.id)
        )
        .group_by(ValuationReport.category)
        .all()
    )

    last_30_days = datetime.now(timezone.utc) - timedelta(days=30)
    last_30d_count = db.query(func.count(ValuationReport.id)).filter(
        ValuationReport.created_at >= last_30_days
    ).scalar()

    logger.debug("Admin dashboard: valuation aggregation completed")

    return {
        "by_category": [
            {"category": cat, "count": count}
            for cat, count in by_category
        ],
        "last_30_days": last_30d_count,
    }


@router.get("/countries")
def dashboard_countries(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info("Admin dashboard: country-wise stats requested")

    subs_by_country = (
        db.query(
            UserSubscription.pricing_country_code,
            func.count(UserSubscription.id)
        )
        .group_by(UserSubscription.pricing_country_code)
        .all()
    )

    valuations_by_country = (
        db.query(
            ValuationReport.country_code,
            func.count(ValuationReport.id)
        )
        .group_by(ValuationReport.country_code)
        .all()
    )

    logger.debug("Admin dashboard: country-wise aggregation completed")

    return {
        "subscriptions": [
            {"country": c, "count": count}
            for c, count in subs_by_country
        ],
        "valuations": [
            {"country": c, "count": count}
            for c, count in valuations_by_country
        ],
    }
