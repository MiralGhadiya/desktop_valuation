import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

print(EMAIL_USER, EMAIL_PASSWORD)

def send_reset_email(to_email: str, link: str):
    try:
        msg = MIMEText(f"Reset your password:\n\n{link}")
        msg["Subject"] = "Password Reset"
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        print("Email sent successfully")

    except Exception as e:
        print("EMAIL ERROR:", e)
        

def send_verification_email(to_email: str, link: str):
    msg = MIMEText(f"Verify your email address:\n\n{link}")
    msg["Subject"] = "Verify Your Email"
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        
        
def send_pdf_email(to_email: str, subject: str, message: str, pdf_path: str):
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = to_email
        msg["Subject"] = subject

        # Email body
        msg.attach(MIMEText(message, "plain"))

        # Attach PDF
        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=os.path.basename(pdf_path))
            msg.attach(part)

        # Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        print("Email sent successfully.")

    except Exception as e:
        print("Email sending failed:", e)
        raise e
