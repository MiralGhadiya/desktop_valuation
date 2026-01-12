#app/utils/email.py

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from app.utils.logger_config import app_logger as logger

from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
ADMIN_FEEDBACK_EMAILS = (os.getenv("ADMIN_FEEDBACK_EMAILS", "").split(","))

SMTP_URL = "smtp.gmail.com"

if not EMAIL_USER or not EMAIL_PASSWORD:
    logger.error("EMAIL_USER or EMAIL_PASSWORD not configured")

def send_reset_email(to_email: str, link: str):
    logger.info(f"Sending password reset email to={to_email}")
    
    try:
        msg = MIMEText(f"Reset your password:\n\n{link}")
        msg["Subject"] = "Password Reset"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL(SMTP_URL, 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Password reset email sent to={to_email}")

    except Exception:
        logger.exception(f"Failed to send password reset email to={to_email}")
        raise
        

def send_verification_email(to_email: str, link: str):
    logger.info(f"Sending verification email to={to_email}")

    try:
        msg = MIMEText(f"Verify your email address:\n\n{link}")
        msg["Subject"] = "Verify Your Email"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL(SMTP_URL, 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Verification email sent to={to_email}")
        
    except Exception:
        logger.exception(f"Failed to send verification email to={to_email}")
        raise

        
        
def send_pdf_email(to_email: str, subject: str, message: str, pdf_path: str):
    logger.info(f"Sending PDF email to={to_email} pdf={os.path.basename(pdf_path)}")

    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(pdf_path),
            )
            msg.attach(part)

        server = smtplib.SMTP(SMTP_URL, 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"PDF email sent to={to_email}")

    except Exception:
        logger.exception(f"Failed to send PDF email to={to_email}")
        raise


def send_subscription_expiry_email(to_email: str, plan_name: str, expiry_date):
    logger.info(f"Sending subscription expiry reminder to={to_email}")

    try:
        body = f"""
            Hello,

            Your subscription plan "{plan_name}" will expire on {expiry_date.strftime('%Y-%m-%d')}.

            Please renew your subscription to continue uninterrupted access.

            Thank you.
        """

        msg = MIMEText(body)
        msg["Subject"] = "Your Subscription Expires in 3 Days"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL(SMTP_URL, 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Subscription expiry email sent to={to_email}")

    except Exception:
        logger.exception(f"Failed to send expiry email to={to_email}")
        raise


def send_admin_feedback_email(feedback, user):
    logger.info(
        f"Sending admin feedback email feedback_id={feedback.id}"
    )

    try:
        body = f"""
        New feedback received

        User ID: {user.id}
        Feedback ID: {feedback.id}
        Type: {feedback.type}
        Rating: {feedback.rating or "N/A"}

        Subject:
        {feedback.subject}

        Message:
        {feedback.message}

        Status: {feedback.status}
        """

        msg = MIMEText(body)
        msg["Subject"] = f"[Feedback] {feedback.type} - {feedback.subject}"
        msg["From"] = EMAIL_USER
        msg["To"] = ", ".join(ADMIN_FEEDBACK_EMAILS)

        with smtplib.SMTP_SSL(SMTP_URL, 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(
            f"Admin feedback email sent feedback_id={feedback.id}"
        )

    except Exception:
        logger.exception(
            f"Failed sending admin feedback email feedback_id={feedback.id}"
        )
        

def send_feedback_reply_email(to_email: str, feedback_id: int, reply: str):
    logger.info(
        f"Sending feedback reply email feedback_id={feedback_id}"
    )

    try:
        body = f"""
        Hello,

        Our support team has replied to your feedback.

        Feedback ID: {feedback_id}

        Reply:
        {reply}

        Thank you for helping us improve.
        """

        msg = MIMEText(body)
        msg["Subject"] = "Update on your feedback"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL(SMTP_URL, 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(
            f"Feedback reply email sent feedback_id={feedback_id}"
        )

    except Exception:
        logger.exception(
            f"Failed sending feedback reply email feedback_id={feedback_id}"
        )