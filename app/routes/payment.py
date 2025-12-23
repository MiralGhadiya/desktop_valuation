# app/routes/payment.py
import os
import razorpay
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.deps import get_db, get_current_user
from razorpay.errors import SignatureVerificationError

from app.models import SubscriptionPlan, UserSubscription, User
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
 
router = APIRouter(prefix="/payment", tags=["payment"])

client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

@router.post("/create-order/{plan_id}")
def create_order(
    plan_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.id == plan_id,
        SubscriptionPlan.is_active == True
    ).first()

    if not plan:
        raise HTTPException(404, "Plan not found")

    amount = plan.price * 100  # Razorpay expects paise

    order = client.order.create({
        "amount": amount,
        "currency": plan.currency,
        "payment_capture": 1
    })

    sub = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        pricing_country_code=plan.country_code,
        ip_country_code=request.state.ip_country,
        payment_country_code=plan.country_code,
        razorpay_order_id=order["id"],
        payment_status="PENDING",
    )

    db.add(sub)
    db.commit()
    db.refresh(sub)

    return {
        "order_id": order["id"],
        "razorpay_key": RAZORPAY_KEY_ID,
        "amount": amount,
        "currency": plan.currency,
        "subscription_id": sub.id
    }


@router.post("/verify")
def verify_payment(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"],
        })
    except SignatureVerificationError:
        raise HTTPException(400, "Payment verification failed")

    sub = db.query(UserSubscription).filter(
        UserSubscription.razorpay_order_id == data["razorpay_order_id"],
        UserSubscription.user_id == current_user.id
    ).first()

    if not sub:
        raise HTTPException(404, "Subscription not found")

    # ✅ Activate subscription
    sub.razorpay_payment_id = data["razorpay_payment_id"]
    sub.razorpay_signature = data["razorpay_signature"]
    sub.payment_status = "PAID"
    sub.is_active = True
    sub.start_date = datetime.now(timezone.utc)
    sub.end_date = sub.start_date + timedelta(days=30)

    db.commit()

    return {"message": "Payment successful & subscription activated"}