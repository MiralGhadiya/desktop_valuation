# app/utils/maps.py

import os
import requests

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

def geocode_address(address: str):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_MAPS_KEY
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if data.get("status") != "OK":
        return None

    result = data["results"][0]
    loc = result["geometry"]["location"]

    return {
        "lat": loc["lat"],
        "lng": loc["lng"],
        "location_type": result["geometry"]["location_type"],
        "formatted_address": result["formatted_address"]
    }


def build_static_maps(lat, lng):
    base = "https://maps.googleapis.com/maps/api/staticmap"

    def common_params(zoom):
        return (
            f"center={lat},{lng}"
            f"&zoom={zoom}"
            f"&size=600x400"
            f"&scale=2"
            f"&markers=color:red%7C{lat},{lng}"
            f"&key={GOOGLE_MAPS_KEY}"
        )

    return {
        "roadmap": f"{base}?{common_params(16)}&maptype=roadmap",
        "satellite": f"{base}?{common_params(16)}&maptype=satellite",
        "hybrid": f"{base}?{common_params(16)}&maptype=hybrid",
        "terrain": f"{base}?{common_params(19)}&maptype=terrain",
    }