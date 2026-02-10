# app/routes/valuation.py

import os
from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Depends,
    Form,
    Query,
    Request,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database.db import get_db
from app.deps import get_current_user, pagination_params
from app.common import PaginatedResponse
from app.utils.maps import geocode_address, build_static_maps
from app.models import User, ValuationReport
from app.models.valuation import DesktopValuationForm, desktop_valuation_form_dep

from app.services.subscription_service import (
    enforce_subscription,
    increment_usage,
)
from app.services.valuation_service import save_valuation_report
from app.services.valuation_report_builder import build_report_context

from app.llm.openai import (
    generate_valuation_report,
    generate_forecast,
    generate_swot,
)

from app.utils.pdf_generator import render_html, generate_pdf_from_html
from app.utils.email import send_pdf_email
from app.utils.date_filters import filter_by_date_range
from app.utils.logger_config import app_logger as logger


router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# --------------------------------------------------
# 🔥 FULLY SYNCHRONOUS REPORT GENERATION
# --------------------------------------------------
@router.post("/create")
def generate_valuation(
    request: Request,
    subscription_id: UUID = Form(...),
    form: DesktopValuationForm = Depends(desktop_valuation_form_dep),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(
        f"Valuation generation started user_id={current_user.id} "
        f"subscription_id={subscription_id}"
    )

    # 1️⃣ Validate input
    try:
        user_input = form.model_dump()
    except Exception:
        logger.exception("Invalid valuation form")
        raise HTTPException(400, "Invalid valuation input")

    category = user_input.get("property_type")
    if not category:
        raise HTTPException(400, "Invalid property type")

    # 2️⃣ Enforce subscription
    subscription = enforce_subscription(
        db=db,
        user_id=current_user.id,
        subscription_id=subscription_id,
    )

    # 3️⃣ Resolve country
    country_code = (
        current_user.country.country_code
        if getattr(current_user, "country", None)
        else getattr(request.state, "ip_country", None)
        or "UNKNOWN"
    )

    logger.info("Generating valuation via AI")

    # 4️⃣ Generate AI output
    try:
        core = generate_valuation_report(user_input)
        forecast = generate_forecast(core)
        swot = generate_swot(core)

        core["forecast"] = forecast
        core["swot_analysis"] = swot
    except Exception:
        logger.exception("AI generation failed")
        raise HTTPException(500, "Failed to generate valuation")

    # 5️⃣ Build report context
    # Extract address safely
    property_address = (
        core.get("property_details", {}).get("address")
        or user_input.get("property_address")
    )

    maps_data = None

    if property_address:
        try:
            coords = geocode_address(property_address)
            if coords:
                maps_data = build_static_maps(
                    coords["lat"],
                    coords["lng"]
                )
        except Exception:
            logger.exception("Failed to generate maps")

    context = build_report_context(core, user_input)

    # Inject maps into context
    context["property_maps"] = maps_data

    # 6️⃣ Generate PDF
    try:
        html = render_html("valuation_template.html", context)
        pdf_path = generate_pdf_from_html(html)
    except Exception:
        logger.exception("PDF generation failed")
        raise HTTPException(500, "Failed to generate PDF")

    # 7️⃣ Send email
    # try:
    #     send_pdf_email(
    #         to_email=user_input["email"],
    #         subject="Your Desktop Valuation Report",
    #         message=(
    #             f"Dear {user_input.get('full_name')},\n\n"
    #             "Please find attached your valuation report."
    #         ),
    #         pdf_path=pdf_path,
    #     )
    # except Exception:
    #     logger.exception("Email sending failed")
    #     raise HTTPException(500, "Failed to send valuation email")

    # 8️⃣ Save valuation to DB
    valuation_id = str(uuid4())

    save_valuation_report(
        db,
        {
            "valuation_id": valuation_id,
            "user_id": current_user.id,
            "subscription_id": subscription.id,
            "category": category,
            "country_code": country_code,
            "user_fields": user_input,
            "ai_response": core,
            "report_context": context,
            "pdf_path": pdf_path,
        },
    )

    increment_usage(db, subscription)

    logger.info(
        f"Valuation generated successfully valuation_id={valuation_id} "
        f"user_id={current_user.id}"
    )

    return {
        "status": "success",
        "valuation_id": valuation_id,
        "pdf_available": True,
        "report_context": context
    }

# --------------------------------------------------
# 📄 LIST USER VALUATIONS
# --------------------------------------------------
@router.get(
    "/my-valuations",
    response_model=PaginatedResponse[dict]
)
def my_valuations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    params: dict = Depends(pagination_params),
    category: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
):
    query = db.query(ValuationReport).filter(
        ValuationReport.user_id == current_user.id
    )

    if category:
        query = query.filter(ValuationReport.category == category)

    if params["search"]:
        query = query.filter(
            or_(
                ValuationReport.valuation_id.ilike(f"%{params['search']}%"),
                ValuationReport.category.ilike(f"%{params['search']}%"),
                ValuationReport.country_code.ilike(f"%{params['search']}%"),
            )
        )

    query = filter_by_date_range(
        query,
        ValuationReport.created_at,
        from_date,
        to_date,
    )

    total = query.count()

    records = (
        query.order_by(ValuationReport.created_at.desc())
        .offset((params["page"] - 1) * params["limit"])
        .limit(params["limit"])
        .all()
    )

    return {
        "data": [
            {
                "valuation_id": v.valuation_id,
                "category": v.category,
                "country_code": v.country_code,
                "created_at": v.created_at,
            }
            for v in records
        ],
        "pagination": {
            "page": params["page"],
            "limit": params["limit"],
            "total": total,
        },
    }


# --------------------------------------------------
# 📥 DOWNLOAD PDF
# --------------------------------------------------
@router.get("/{valuation_id}/download")
def download_valuation_pdf(
    valuation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valuation = (
        db.query(ValuationReport)
        .filter(
            ValuationReport.valuation_id == valuation_id,
            ValuationReport.user_id == current_user.id,
        )
        .first()
    )

    if not valuation:
        raise HTTPException(404, "Valuation not found")

    if not valuation.pdf_path or not os.path.exists(valuation.pdf_path):
        raise HTTPException(404, "PDF not available")

    return FileResponse(
        valuation.pdf_path,
        media_type="application/pdf",
        filename=f"{valuation.valuation_id}.pdf",
    )
