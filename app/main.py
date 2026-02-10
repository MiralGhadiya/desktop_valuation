import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from app.database.db import engine, Base
from app.routes import auth as user_auth, valuation, subscription, payment, user_feedback, maintenance
from app.routes.admin import (
    auth,
    users,
    subscription_plans,
    user_subscriptions,
    valuations,
    dashboard,
    feedback,
    staff,
)

from app.middleware.ip_country import get_ip_country, get_client_ip
from app.utils.logger_config import app_logger as logger


logger.info("Starting Desktop Valuation API")

if os.getenv("ENV") != "production":
    Base.metadata.create_all(bind=engine)

logger.info("Database tables ensured")

app = FastAPI(title="Desktop Valuation API")


if os.getenv("ENV") != "production":
    @app.middleware("http")
    async def add_ngrok_header(request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["ngrok-skip-browser-warning"] = "true"
        return response

# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Routers (User)
# --------------------------------------------------

app.include_router(user_auth.router)
app.include_router(valuation.router)
app.include_router(subscription.router)
app.include_router(payment.router)
app.include_router(user_feedback.router)
app.include_router(maintenance.router)

# --------------------------------------------------
# Routers (Admin)
# --------------------------------------------------

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscription_plans.router)
app.include_router(user_subscriptions.router)
app.include_router(valuations.router)
app.include_router(dashboard.router)
app.include_router(feedback.router)
app.include_router(staff.router)

# --------------------------------------------------
# IP → Country middleware
# --------------------------------------------------

@app.middleware("http")
async def add_ip_country(request: Request, call_next):
    ip = get_client_ip(request)
    country = get_ip_country(ip)

    logger.debug(f"Request IP resolved ip={ip} country={country}")

    request.state.ip_country = country
    return await call_next(request)


@app.get("/")
def health():
    return {"status": "ok"}