#app/routes/admin/dashboard.py

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta, timezone

from app.deps import get_db, require_superuser

from app.models import User
from app.models.feedback import Feedback
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.models.valuation import ValuationReport

from app.utils.response import APIResponse, success_response
from app.utils.logger_config import app_logger as logger

datetime.now(timezone.utc)


router = APIRouter(
    prefix="/admin/dashboard",
    tags=["admin-dashboard"]
)


@router.get("/overview", response_model=APIResponse[dict])
def dashboard_overview(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    try:
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

        return success_response(
            data={
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
            },
            message="Dashboard overview fetched successfully"
        )

    except Exception:
        logger.exception("Dashboard overview failed")
        raise HTTPException(500, "Failed to load dashboard overview")


@router.get("/users", response_model=APIResponse[dict])
def dashboard_users(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    try:
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
            User.email_verified_at >= last_30_days
        ).scalar()

        logger.debug("Admin dashboard: users stats aggregation completed")

        return success_response(
            data={
                "email_verified": verified,
                "email_unverified": unverified,
                "inactive_users": inactive,
                "new_users_last_30_days": new_users_30d,
            },
            message="Users stats fetched successfully"
        )
    except Exception:
        logger.exception("Dashboard users stats failed")
        raise HTTPException(500, "Failed to load users stats")


@router.get("/user-registrations-by-year", response_model=APIResponse[dict])
def user_registrations_by_last_five_years(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    try:
        # Get the current year (e.g., 2026)
        current_year = datetime.now().year

        # Query user registrations by year
        results = (
            db.query(func.extract('year', User.email_verified_at).label('year'), func.count(User.id).label('total'))
            .filter(func.extract('year', User.email_verified_at).in_([current_year-4, current_year-3, current_year-2, current_year-1, current_year]))
            .group_by(func.extract('year', User.email_verified_at))
            .order_by('year')
            .all()
        )

        # Create a dictionary for years 2022–2026 (or current year - 4 to current year)
        year_data = {year: 0 for year in range(current_year - 4, current_year + 1)}

        # Populate the dictionary with actual data from the query
        for year, total in results:
            if year is not None:
                year_data[int(year)] = total

        # Format the data to return to frontend
        user_data_by_year = [
            {"year": year, "registrations": year_data[year]}
            for year in range(current_year - 4, current_year + 1)
        ]

        logger.debug("Admin dashboard: user registrations by year aggregation completed")

        return success_response(
            data={"user_registrations_by_year": user_data_by_year},
            message="User registrations by year fetched successfully"
        )

    except Exception:
        logger.exception("Failed to load user registrations by year")
        raise HTTPException(500, "Failed to load user registrations by year")
    

@router.get("/subscriptions", response_model=APIResponse[list])
def dashboard_subscriptions_country_wise(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    try:
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

        return success_response(
            data=[
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
        ],
            message="Subscriptions breakdown fetched successfully"
        )
    except Exception:
        logger.exception("Dashboard subscriptions breakdown failed")
        raise HTTPException(500, "Failed to load subscriptions breakdown")


@router.get("/valuations", response_model=APIResponse[dict])
def dashboard_valuations(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    try:
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

        return success_response(
            data={
                "by_category": [
                    {"category": cat, "count": count}
                    for cat, count in by_category
                ],
                "last_30_days": last_30d_count,
            },
            message="Valuations stats fetched successfully"
        )
    except Exception:
        logger.exception("Dashboard valuations stats failed")
        raise HTTPException(500, "Failed to load valuations stats")
    

@router.get("/countries", response_model=APIResponse[dict])
def dashboard_countries(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    try:
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

        return success_response(
            data={
                "subscriptions": [
                    {"country": c, "count": count}
                    for c, count in subs_by_country
                ],
                "valuations": [
                {"country": c, "count": count}
                for c, count in valuations_by_country
            ],
        },
            message="Country-wise stats fetched successfully"
        )
    except Exception:
        logger.exception("Dashboard country-wise stats failed")
        raise HTTPException(500, "Failed to load country-wise stats")
    


@router.get("/feedback", response_model=APIResponse[dict])
def feedback_stats(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    total = db.query(func.count(Feedback.id)).scalar()

    open_count = (
        db.query(func.count(Feedback.id))
        .filter(Feedback.status == "OPEN")
        .scalar()
    )

    avg_rating = (
        db.query(func.avg(Feedback.rating))
        .filter(Feedback.rating.isnot(None))
        .scalar()
    )

    return success_response(
        data={
            "total_feedback": total,
            "open_feedback": open_count,
            "avg_rating": round(float(avg_rating), 2) if avg_rating is not None else None,
        },
        message="Feedback stats fetched successfully"
    )