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

if not EMAIL_USER or not EMAIL_PASSWORD:
    logger.error("EMAIL_USER or EMAIL_PASSWORD not configured")

def send_reset_email(to_email: str, link: str):
    logger.info(f"Sending password reset email to={to_email}")
    
    try:
        msg = MIMEText(f"Reset your password:\n\n{link}")
        msg["Subject"] = "Password Reset"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info(f"Password reset email sent to={to_email}")

    except Exception as e:
        logger.exception(f"Failed to send password reset email to={to_email}")
        raise
        

def send_verification_email(to_email: str, link: str):
    logger.info(f"Sending verification email to={to_email}")

    try:
        msg = MIMEText(f"Verify your email address:\n\n{link}")
        msg["Subject"] = "Verify Your Email"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
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

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        logger.info(f"PDF email sent to={to_email}")

    except Exception:
        logger.exception(f"Failed to send PDF email to={to_email}")
        raise
