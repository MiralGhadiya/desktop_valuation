# app/middleware/ip_country.py
import os
import requests
from fastapi import Request
from functools import lru_cache

IPINFO_TOKEN = os.getenv("IPINFO_TOKEN")

@lru_cache(maxsize=10_000)
def get_ip_country(ip: str) -> str | None:
    """
    Returns ISO country code (e.g. 'IN') or None
    """
    if not ip or ip in ("127.0.0.1", "localhost"):
        return None

    try:
        url = f"https://api.ipinfo.io/lite/{ip}"
        res = requests.get(
            url,
            params={"token": IPINFO_TOKEN},
            timeout=2
        )

        if res.status_code == 200:
            data = res.json()
            return data.get("country_code")
    except Exception as e:
        print("IPINFO error:", e)

    return None


def get_client_ip(request: Request) -> str:
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()

    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip()

    return request.client.host