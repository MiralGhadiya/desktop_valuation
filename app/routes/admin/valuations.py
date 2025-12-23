# app/router/admin/valuations.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.deps import get_db, require_superuser
from app.models import User
from app.models.valuation import ValuationReport
from app.schemas import ValuationResponse, ValuationDetailResponse
from app.utils.logger_config import app_logger as logger

router = APIRouter(
    prefix="/admin",
    tags=["admin-valuations"]
)


@router.get("/valuations", response_model=List[ValuationResponse])
def list_valuations(
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),

    user_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
):
    logger.info(
        "Admin listing valuations "
        f"user_id={user_id} country={country_code} "
        f"category={category} from={from_date} to={to_date}"
    )
    
    query = db.query(ValuationReport)

    if user_id:
        query = query.filter(ValuationReport.user_id == user_id)

    if country_code:
        query = query.filter(
            ValuationReport.country_code == country_code.upper()
        )

    if category:
        query = query.filter(
            ValuationReport.category == category
        )

    if from_date:
        query = query.filter(
            ValuationReport.created_at >= from_date
        )

    if to_date:
        query = query.filter(
            ValuationReport.created_at <= to_date
        )

    valuations = query.order_by(
            ValuationReport.created_at.desc()
        ).all()

    logger.debug(f"Admin fetched valuations count={len(valuations)}")

    return valuations


@router.get("/valuations/{valuation_id}", response_model=ValuationDetailResponse)
def get_valuation_details(
    valuation_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin fetching valuation valuation_id={valuation_id}")
    valuation = db.query(ValuationReport).filter(
        ValuationReport.valuation_id == valuation_id
    ).first()

    if not valuation:
        logger.warning(f"Valuation not found valuation_id={valuation_id}")
        raise HTTPException(404, "Valuation not found")

    return valuation


@router.get("/users/{user_id}/valuations", response_model=List[ValuationResponse])
def get_user_valuations(
    user_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin fetching valuations for user_id={user_id}")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found while fetching valuations user_id={user_id}")
        raise HTTPException(404, "User not found")

    valuations = (
        db.query(ValuationReport)
        .filter(ValuationReport.user_id == user_id)
        .order_by(ValuationReport.created_at.desc())
        .all()
    )

    logger.debug(
        f"Admin fetched valuations for user_id={user_id} count={len(valuations)}"
    )

    return valuations


@router.delete("/valuations/{valuation_id}")
def delete_valuation(
    valuation_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_superuser),
):
    logger.info(f"Admin deleting valuation valuation_id={valuation_id}")
    
    valuation = db.query(ValuationReport).filter(
        ValuationReport.valuation_id == valuation_id
    ).first()

    if not valuation:
        logger.warning(f"Valuation not found during delete valuation_id={valuation_id}")
        raise HTTPException(404, "Valuation not found")

    db.delete(valuation)
    db.commit()
    
    logger.info(f"Valuation deleted valuation_id={valuation_id}")

    return {"message": "Valuation deleted successfully"}