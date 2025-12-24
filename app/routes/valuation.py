# app/routes/valuation.py

import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from fastapi.responses import FileResponse
from app.utils.pdf_generator import render_html, generate_pdf_from_html
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.valuation_service import save_valuation_report
from app.models.valuation import DesktopValuationForm, desktop_valuation_form_dep
from app.llm.openai import generate_valuation_report
from app.llm.gemini import generate_valuation_summary
from app.services.subscription_service import enforce_subscription, increment_usage
from app.utils.email import send_pdf_email
from app.deps import get_current_user
from app.models import User, ValuationReport
from datetime import datetime
import uuid

from app.utils.logger_config import app_logger as logger

def build_report_context(ai_json, user_input):

    # -------- PROPERTY IDENTIFICATION --------
    property_identification = {
        "property_address": ai_json["property_details"]["address"],
        "valuation_id": f"DVP-{uuid.uuid4().hex[:8].upper()}",
        "date_of_report": datetime.now().strftime("%d-%b-%Y"),
        "purpose_of_valuation": user_input["purpose_of_valuation"],
        "report_type": "Desktop Valuation (Automated)",
        "client_name": user_input["full_name"],
        "contact_information": {
            "email": user_input["email"],
            "phone": user_input["contact_number"]
        }
    }

    # -------- PROPERTY SUMMARY --------
    property_summary = {
        "property_type": ai_json["property_details"]["property_type"],
        "land_area": f"{ai_json['property_details']['land_area_sqft']} sqft",
        "built_up_area": f"{ai_json['property_details']['built_up_area_sqft']} sqft",
        "zoning": "Residential",
        "title_details": "Not Available",
        "construction_year": f"{ai_json['property_details']['age_years']} years old",
        "structure": "RCC Construction",
        "car_parking": "Available",
        "ownership_type": "Freehold",
        "occupancy": "Owner Occupied",
        "local_authority": ai_json["property_details"]["city"].title(),
        "last_sale_date": "N/A",
        "last_sale_price": "N/A",
        "customer_estimate": user_input.get("estimated_market_value", "N/A")
    }

    # -------- COMPARABLE SALES --------
    comparable_sales = []
    for c in ai_json["comparables_used"]:
        comparable_sales.append({
            "address": c["address"],
            "beds": "-",      # AI JSON does not provide beds
            "baths": "-",     # AI JSON does not provide baths
            "land_area": c["land_area"],
            "sale_date": "N/A",
            "sale_price": c["sale_price"],
            "comparison": c["adjustment_reason"],
            "distance": f"{c['distance_km']} km"
        })

    # -------- COMPARABLE SUMMARY --------
    comparable_analysis_summary = {
        "average_comparable_value": ai_json["predicted_value"]["mid_value"],
        "adjusted_subject_estimate": ai_json["predicted_value"]["fair_market_value"]
    }

    # -------- THREE-TIER --------
    three_tier_valuation = {
        "conservative_value": ai_json["predicted_value"]["low_value"],
        "mid_range_value": ai_json["predicted_value"]["mid_value"],
        "high_value": ai_json["predicted_value"]["high_value"]
    }

    # -------- RISK ANALYSIS --------
    valuation_risk_analysis = {
        "value_range": f"{ai_json['predicted_value']['low_value']} - {ai_json['predicted_value']['high_value']}",
        "confidence_index": ai_json["predicted_value"]["confidence_score"],
        "market_risk_score": ai_json["bank_lending_model"]["risk_level"],
        "property_risk_score": "Moderate",
        "recommended_ltv": ai_json["bank_lending_model"]["recommended_ltv"],
        "validity": "45 Days"
    }

    # -------- MARKET COMMENTARY --------
    market_commentary = ai_json["buy_sell_recommendation"]["reasoning"]

    # -------- SWOT --------
    swot_analysis = {
        "strengths": ["Good locality demand", "Stable RCC structure", "Moderate appreciation potential"],
        "weaknesses": ["Property age moderate", "Average liquidity"],
        "opportunities": ["Growing micro-market demand", "Future redevelopment potential"],
        "threats": ["Interest rate fluctuations", "Market corrections"]
    }

    # -------- FORECAST (5 years) --------
    growth = ai_json["forecast"]["growth_rate_percent"] / 100
    base = ai_json["predicted_value"]["fair_market_value"]
    value_forecast = []

    for i in range(1, 6):
        projected = int(base * ((1 + growth) ** i))
        value_forecast.append({
            "year": datetime.now().year + i,
            "growth_rate": f"{ai_json['forecast']['growth_rate_percent']}%",
            "forecast_value": projected
        })

    return {
        "property_identification": property_identification,
        "property_summary": property_summary,
        "comparable_sales": comparable_sales,
        "comparable_analysis_summary": comparable_analysis_summary,
        "three_tier_valuation": three_tier_valuation,
        "valuation_risk_analysis": valuation_risk_analysis,
        "market_commentary": market_commentary,
        "swot_analysis": swot_analysis,
        "value_forecast": value_forecast
    }


router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/create")
async def create_valuation_form(
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
            "commercial": "commercial",
            "industrial unit": "industrial unit",
            "commercial office": "commercial",
            "commercial shop": "commercial",
            "residential": "residential",
            "residential flat": "residential",
            "residential house": "residential",
            "land": "land",
            "plot": "land",
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
        ai_json = generate_valuation_report(user_input)
        
        context = build_report_context(ai_json, user_input)

        html = render_html("valuation_template.html", context)
        pdf_path = await generate_pdf_from_html(html)
        
        logger.info(f"PDF generated at path={pdf_path}")

        send_pdf_email(
            to_email=user_input["email"],
            subject="Your Desktop Valuation Report",
            message=(
                f"Dear {user_input['full_name']},\n\n"
                "Please find attached your valuation report.\n\nRegards,\nEvenMore"
            ),
            pdf_path=pdf_path
        )
        logger.info(f"Valuation PDF emailed to {user_input['email']}")

        valuation_id = context["property_identification"]["valuation_id"]

        record_id = save_valuation_report(
            db,
            {
                "valuation_id": valuation_id,
                "user_id": current_user.id,
                "subscription_id": subscription.id,  
                "category": category,
                "country_code": current_user.country.country_code,
                "user_fields": user_input,
                "ai_response": ai_json,
                "report_context": context,
                "pdf_path": pdf_path,
            }
        )
        
        logger.info(
            f"Valuation saved valuation_id={valuation_id} "
            f"user_id={current_user.id}"
        )

        increment_usage(db, subscription)

        return {
            "status": "success",
            "valuation_id": valuation_id,
            "db_record_id": record_id,
            "subscription_used": subscription.id,
            "pdf_path": pdf_path
        }
        
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
