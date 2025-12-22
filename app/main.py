# app/main.py

from fastapi import FastAPI, Request
from app.database import engine, Base
from app.models import *   
from app.routes import auth, valuation, subscription
from app.routes.admin import auth, users, subscription_plans, user_subscriptions, valuations, dashboard
from app.middleware.ip_country import get_ip_country, get_client_ip

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Desktop Valuation API")

app.include_router(auth.router)
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
    ip = get_client_ip(request)  # ✅ FIX
    print("Client IP:", ip)

    country = get_ip_country(ip)
    print("IP Country:", country)

    request.state.ip_country = country
    return await call_next(request)