# app/routes/valuation.py

import os
import uuid
from fastapi import Request
from datetime import datetime
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form

# from app.llm.openai import generate_valuation_report
# from app.llm.gemini import generate_valuation_summary

from app.deps import get_current_user
from app.tasks.valuation_tasks import process_valuation_job

# from app.utils.email import send_pdf_email
# from app.utils.pdf_generator import render_html, generate_pdf_from_html

# from app.services.valuation_service import save_valuation_report
from app.services.subscription_service import enforce_subscription, increment_usage

from app.models import User, ValuationReport
from app.models.valuation import DesktopValuationForm, ValuationJob, desktop_valuation_form_dep

from app.utils.logger_config import app_logger as logger


router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/create")
async def create_valuation_form(
    request: Request,
    subscription_id: int = Form(...),
    form: DesktopValuationForm = Depends(desktop_valuation_form_dep),
    attachment: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    logger.info(
        f"Valuation request started user_id={current_user.id} "
        f"subscription_id={subscription_id}"
    )
    
    try:
    
        user_input = form.model_dump()

        raw_type = user_input["property_type"].strip().lower()
        
        logger.debug(f"Raw category type={raw_type}")

        CATEGORY_ALIASES = {
            # Residential
            "residential": "residential",
            "residential flat": "residential",
            "residential apartment": "residential",
            "flat": "residential",
            "apartment": "residential",
            "residential house": "residential",
            "independent house": "residential",
            "villa": "residential",

            # Commercial
            "commercial": "commercial",
            "commercial shop": "commercial",
            "shop": "commercial",
            "retail shop": "commercial",
            "commercial office": "commercial",
            "office": "commercial",
            "showroom": "commercial",

            # Industrial
            "industrial unit": "industrial unit",
            "factory": "industrial unit",
            "warehouse": "industrial unit",
            "industrial shed": "industrial unit",
            "logistics park": "industrial unit",

            # Land (non-residential)
            "land": "land",
            "plot": "land",
            "commercial plot": "land",
            "industrial plot": "land",
            "vacant land": "land",

            # Residential Plot (explicit, preserved case)
            "residential plot": "RESIDENTIAL PLOT",
            "res plot": "RESIDENTIAL PLOT",
            "housing plot": "RESIDENTIAL PLOT"
        }

        category = CATEGORY_ALIASES.get(raw_type)

        if not category:
            raise HTTPException(400, "Invalid property type")
        
        logger.debug(f"Resolved property category={category}")
        
        logger.debug("Enforcing subscription limits")

        subscription = enforce_subscription(
            db=db,
            user_id=current_user.id,
            subscription_id=subscription_id,
            category=category,
        )
        
        logger.info("Generating valuation via OpenAI")
        
        country_code = None

        if hasattr(current_user, "country") and current_user.country:
            country_code = current_user.country.country_code

        if not country_code:
            country_code = request.state.ip_country
                
        job = ValuationJob(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            subscription_id=subscription.id,
            category=category,
            request_payload=user_input,
            country_code=country_code,
        )

        db.add(job)
        db.commit()
        
        existing = (
            db.query(ValuationJob)
            .filter(
                ValuationJob.user_id == current_user.id,
                ValuationJob.status.in_(["queued", "processing"]),
            )
            .first()
        )

        if existing:
            return {
                "job_id": existing.id,
                "status": "already queued",
                "message": "A valuation is already in progress",
            }


        process_valuation_job.delay(job.id)

        return {
            "job_id": job.id,
            "status": "queued",
            "message": "Valuation job queued successfully"
        }


    #     ai_json = generate_valuation_report(user_input)
        
    #     context = build_report_context(ai_json, user_input)

    #     html = render_html("valuation_template.html", context)
    #     pdf_path = await generate_pdf_from_html(html)
        
    #     logger.info(f"PDF generated at path={pdf_path}")

    #     send_pdf_email(
    #         to_email=user_input["email"],
    #         subject="Your Desktop Valuation Report",
    #         message=(
    #             f"Dear {user_input['full_name']},\n\n"
    #             "Please find attached your valuation report.\n\nRegards,\nEvenMore"
    #         ),
    #         pdf_path=pdf_path
    #     )
    #     logger.info(f"Valuation PDF emailed to {user_input['email']}")

    #     valuation_id = context["property_identification"]["valuation_id"]

    #     record_id = save_valuation_report(
    #         db,
    #         {
    #             "valuation_id": valuation_id,
    #             "user_id": current_user.id,
    #             "subscription_id": subscription.id,  
    #             "category": category,
    #             "country_code": current_user.country.country_code,
    #             "user_fields": user_input,
    #             "ai_response": ai_json,
    #             "report_context": context,
    #             "pdf_path": pdf_path,
    #         }
    #     )
        
    #     logger.info(
    #         f"Valuation saved valuation_id={valuation_id} "
    #         f"user_id={current_user.id}"
    #     )

    #     increment_usage(db, subscription)

    #     return {
    #         "status": "success",
    #         "valuation_id": valuation_id,
    #         "db_record_id": record_id,
    #         "subscription_used": subscription.id,
    #         "pdf_path": pdf_path
    #     }
        
    except Exception:
        logger.exception("Valuation creation failed")
        raise
    
    
@router.get("/my-valuations")
def my_valuations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    valuations = (
        db.query(ValuationReport)
        .filter(ValuationReport.user_id == current_user.id)
        .order_by(ValuationReport.created_at.desc())
        .all()
    )

    return [
        {
            "valuation_id": v.valuation_id,
            "category": v.category,
            "country_code": v.country_code,
            "created_at": v.created_at,
        }
        for v in valuations
    ]


@router.get("/valuation/{valuation_id}")
def get_valuation(
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

    return {
        "valuation_id": valuation.valuation_id,
        "category": valuation.category,
        "country_code": valuation.country_code,
        "user_fields": valuation.user_fields,
        "ai_response": valuation.ai_response,
        "created_at": valuation.created_at,
    }
    

@router.get("/valuation/{valuation_id}/download")
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


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(ValuationJob).filter(
        ValuationJob.id == job_id,
        ValuationJob.user_id == current_user.id,
    ).first()

    if not job:
        raise HTTPException(404, "Job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "valuation_id": job.valuation_id,
        "error": job.error_message,
    }