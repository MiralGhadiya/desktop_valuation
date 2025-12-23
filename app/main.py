from fastapi import FastAPI, Request

from app.database import engine, Base
from app.routes import auth as user_auth, valuation, subscription
from app.routes.admin import (
    auth,
    users,
    subscription_plans,
    user_subscriptions,
    valuations,
    dashboard,
)
from app.middleware.ip_country import get_ip_country, get_client_ip
from app.utils.logger_config import app_logger as logger

logger.info("Starting Desktop Valuation API")

Base.metadata.create_all(bind=engine)
logger.info("Database tables ensured")

app = FastAPI(title="Desktop Valuation API")

app.include_router(user_auth.router)
app.include_router(valuation.router)
app.include_router(subscription.router)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(subscription_plans.router)
app.include_router(user_subscriptions.router)
app.include_router(valuations.router)
app.include_router(dashboard.router)


@app.middleware("http")
async def add_ip_country(request: Request, call_next):
    ip = get_client_ip(request)
    country = get_ip_country(ip)

    logger.debug(f"Request IP resolved ip={ip} country={country}")

    request.state.ip_country = country
    return await call_next(request)
