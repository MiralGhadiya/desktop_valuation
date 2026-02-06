# app/tasks/valuation_tasks.py

from uuid import uuid4
from app.celery_app import celery_app
from app.database.db import SessionLocal
from app.models.valuation import ValuationJob
from app.services.valuation_service import save_valuation_report
from app.services.subscription_service import increment_usage
from app.services.valuation_report_builder import build_report_context
from app.llm.openai import generate_valuation_report, generate_forecast, generate_swot
from app.utils.pdf_generator import render_html, generate_pdf_from_html
from app.utils.maps import geocode_address, build_static_maps
from app.utils.email import send_pdf_email
from app.models.subscription import UserSubscription

from app.utils.logger_config import app_logger as logger

@celery_app.task(
    bind=True,
    autoretry_for=(RuntimeError,),
    retry_backoff=5,
    retry_kwargs={"max_retries": 2},
)
def process_valuation_job(self, job_id: str):
    db = SessionLocal()
    try:
        job = db.query(ValuationJob).filter(ValuationJob.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        user_input = job.request_payload

        # ai_json = generate_valuation_report(user_input)
        
        core = generate_valuation_report(user_input)
        forecast = generate_forecast(core)
        swot = generate_swot(core)   

        core["forecast"] = forecast
        core["swot_analysis"] = swot
        ai_json = core

        
        print("AI JSON RESPONSE:", ai_json) 
        
        print("FORECAST FROM AI:", ai_json.get("forecast"))

        context = build_report_context(ai_json, user_input)
        
        address = ai_json["property_details"]["address"]

        # 3️⃣ Geocode
        geo = geocode_address(address)
        if geo:
            context["property_location"] = {
                "latitude": geo["lat"],
                "longitude": geo["lng"],
                "location_type": geo["location_type"],
                "formatted_address": geo["formatted_address"],
                "maps": build_static_maps(geo["lat"], geo["lng"]),
            }
        else:
            context["property_location"] = None

        # if geo:
        #     maps = build_static_maps(geo["lat"], geo["lng"])

        #     # context["property_identification"]["location"] = {
        #     #     "latitude": geo["lat"],
        #     #     "longitude": geo["lng"],
        #     #     "location_type": geo["location_type"],
        #     #     "formatted_address": geo["formatted_address"],
        #     #     "maps": maps
        #     # }
        # else:
        #     context["property_identification"]["location"] = None
            
        html = render_html("valuation_template.html", context)
        pdf_path = generate_pdf_from_html(html)

        send_pdf_email(
            to_email=user_input["email"],
            subject="Your Desktop Valuation Report",
            message=f"Dear {user_input['full_name']},\n\nPlease find attached your valuation report.",
            pdf_path=pdf_path,
        )
        
        valuation_id = str(uuid4())

        # valuation_id = context["property_identification"]["valuation_id"]
        save_valuation_report(
            db,
            {
                "valuation_id": valuation_id,
                "user_id": job.user_id,
                "subscription_id": job.subscription_id,
                "category": job.category,
                "country_code": job.country_code,
                "user_fields": user_input,
                "ai_response": ai_json,
                "report_context": context,
                "pdf_path": pdf_path,
            },
        )
        
        subscription = (
            db.query(UserSubscription)
            .filter(UserSubscription.id == job.subscription_id)
            .first()
        )

        if not subscription:
            raise RuntimeError("Subscription not found for job")

        increment_usage(db, subscription)

        job.status = "completed"
        job.valuation_id = valuation_id
        job.pdf_path = pdf_path
        db.commit()

        logger.info(f"Valuation completed job_id={job_id}")

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        logger.exception(f"Valuation failed job_id={job_id}")
        raise
    finally:
        db.close()