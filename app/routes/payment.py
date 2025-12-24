import os
import razorpay
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from razorpay.errors import SignatureVerificationError
from fastapi import APIRouter, Depends, HTTPException, Request

from app.deps import get_db, get_current_user
from app.models import SubscriptionPlan, UserSubscription, User

from app.utils.logger_config import app_logger as logger

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    logger.error("RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET is not set")
    raise RuntimeError("Missing RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET")

router = APIRouter(prefix="/payment", tags=["payment"])

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def _pricing_country(request: Request, current_user: User) -> str:
    ip_country = getattr(request.state, "ip_country", None)
    user_country = current_user.country.country_code
    return ip_country or user_country


def _expire_existing_active_subs(db: Session, user_id: int, now: datetime):
    db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.is_active == True,
        UserSubscription.is_expired == False
    ).update({
        "is_active": False,
        "is_expired": True,
        "end_date": now
    })


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

    pricing_country = _pricing_country(request, current_user)
    if pricing_country != plan.country_code:
        raise HTTPException(403, "Plan pricing country mismatch")

    existing_pending = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.plan_id == plan.id,
        UserSubscription.payment_status.in_(["CREATED", "PENDING"]),
        UserSubscription.is_active == False
    ).order_by(UserSubscription.id.desc()).first()

    if existing_pending and existing_pending.razorpay_order_id:
        return {
            "order_id": existing_pending.razorpay_order_id,
            "razorpay_key": RAZORPAY_KEY_ID,
            "amount": plan.price * 100,
            "currency": plan.currency,
            "subscription_id": existing_pending.id
        }

    amount = plan.price * 100  # paise

    order = client.order.create({
        "amount": amount,
        "currency": plan.currency,
        "payment_capture": 1,
        "notes": {
            "user_id": str(current_user.id),
            "plan_id": str(plan.id),
            "pricing_country": pricing_country
        }
    })

    sub = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        pricing_country_code=pricing_country,
        ip_country_code=getattr(request.state, "ip_country", None),
        payment_country_code=pricing_country,
        razorpay_order_id=order["id"],
        payment_status="PENDING",
        is_active=False,
        is_expired=False,
        start_date=None,
        end_date=None,
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
    """
    Frontend calls this after Razorpay checkout success.
    Still keep webhook for ultimate truth.
    """
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

    if sub.payment_status == "PAID" and sub.is_active:
        return {"message": "Already activated"}

    now = datetime.now(timezone.utc)

    _expire_existing_active_subs(db, current_user.id, now)

    sub.razorpay_payment_id = data["razorpay_payment_id"]
    sub.razorpay_signature = data["razorpay_signature"]
    sub.payment_status = "PAID"
    sub.is_active = True
    sub.is_expired = False
    sub.start_date = now
    sub.end_date = now + timedelta(days=30)

    db.commit() 
    return {"message": "Payment successful & subscription activated"}


# @router.post("/refund/{user_subscription_id}")
# def refund_payment(
#     subscription_id: int,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user),
# ):
#     # 1️⃣ Fetch subscription
#     sub = db.query(UserSubscription).filter(
#         UserSubscription.id == subscription_id,
#         UserSubscription.user_id == current_user.id
#     ).first()
    
#     print("sub", sub)

#     if not sub:
#         raise HTTPException(404, "Subscription not found")

#     # 2️⃣ Validate refund eligibility
#     if sub.payment_status != "PAID":
#         raise HTTPException(400, "Only paid subscriptions can be refunded")

#     if not sub.razorpay_payment_id:
#         raise HTTPException(400, "Payment ID missing")

#     # 3️⃣ Call Razorpay refund API
#     try:
#         refund = client.payment.refund(
#             sub.razorpay_payment_id,
#             {
#                 "notes": {
#                     "reason": "User requested refund"
#                 }
#             }
#         )
#         print("refund", refund)
#     except Exception as e:
#         logger.error(f"Refund failed: {e}")
#         raise HTTPException(500, "Refund initiation failed")

#     # 4️⃣ Update DB
#     sub.payment_status = "REFUNDED"
#     sub.is_active = False
#     sub.is_expired = True
#     sub.end_date = datetime.now(timezone.utc)

#     db.commit()

#     return {
#         "message": "Refund initiated successfully",
#         "refund_id": refund.get("id"),
#     }
