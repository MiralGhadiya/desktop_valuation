# app/tasks/valuation_tasks.py

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.valuation import ValuationJob
from app.services.valuation_service import save_valuation_report
from app.services.subscription_service import increment_usage
from app.services.valuation_report_builder import build_report_context
from app.llm.openai import generate_valuation_report
from app.utils.pdf_generator import render_html, generate_pdf_from_html
from app.utils.email import send_pdf_email
from app.models.subscription import UserSubscription

from app.utils.logger_config import app_logger as logger

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=15,
    retry_kwargs={"max_retries": 3},
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

        ai_json = generate_valuation_report(user_input)
        
        print("AI JSON RESPONSE:", ai_json) 
        
        print("FORECAST FROM AI:", ai_json.get("forecast"))

        context = build_report_context(ai_json, user_input)
        html = render_html("valuation_template.html", context)
        pdf_path = generate_pdf_from_html(html)

        send_pdf_email(
            to_email=user_input["email"],
            subject="Your Desktop Valuation Report",
            message=f"Dear {user_input['full_name']},\n\nPlease find attached your valuation report.",
            pdf_path=pdf_path,
        )

        valuation_id = context["property_identification"]["valuation_id"]
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

        # increment_usage(db, job.subscription_id)
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
