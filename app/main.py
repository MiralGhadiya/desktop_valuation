# app/main.py

from fastapi import FastAPI, Request
from app.database import engine, Base
from app.models import *   
from app.routes import auth, valuation, subscription
from app.middleware.ip_country import get_ip_country
# from app.middleware.ip_country import get_client_ip_and_country

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Desktop Valuation API")

app.include_router(auth.router)
app.include_router(valuation.router)
app.include_router(subscription.router)


@app.middleware("http")
async def add_ip_country(request: Request, call_next):
    ip = request.client.host
    print("ip_address", ip)
    request.state.ip_country = get_ip_country(ip)
    response = await call_next(request)
    print("ip response", response)
    return response


# @app.middleware("http")
# async def add_ip_country(request: Request, call_next):
#     ip, country = get_client_ip_and_country(request)

#     print("Detected client IP:", ip)
#     print("Detected IP country:", country)

#     request.state.ip_country = country  # ✅ FIX

#     response = await call_next(request)
#     return response