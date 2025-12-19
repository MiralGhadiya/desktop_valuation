# import requests

# def get_ip_country(ip: str) -> str | None:
#     try:
#         res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
#         print("resres", res)
#         if res.status_code == 200:
#             return res.json().get("country_code")
#     except Exception:
#         pass
#     return None


from fastapi import Request
import requests

def get_ip_country(ip: str) -> str | None:
    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
        print("resres", res)
        if res.status_code == 200:
            return res.json().get("country_code")
    except Exception:
        pass
    return None


def get_client_ip(request: Request) -> str:
    # Cloudflare
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()

    # ngrok / nginx / load balancers
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()

    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip()

    return request.client.host



# ------------------------------------------------------------------------------------ Testing ---------------------------------------------------------------------------------------


# from fastapi import Request
# import requests

# # Static map for DEV testing
# DEV_IP_COUNTRY_MAP = {
#     "8.8.8.8": "US",
#     "1.1.1.1": "AU",
#     "94.200.0.0": "AE",
#     "49.37.12.1": "IN",
# }

# def get_ip_country(ip: str) -> str | None:
#     try:
#         res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=2)
#         print("resres", res)
#         if res.status_code == 200:
#             return res.json().get("country_code")
#     except Exception:
#         pass
#     return None


# def get_client_ip_and_country(request: Request):
#     # 🔥 DEV override (NO external API)
#     dev_ip = request.headers.get("x-dev-ip")
#     if dev_ip:
#         return dev_ip, DEV_IP_COUNTRY_MAP.get(dev_ip)

#     # Production headers
#     for header in ("cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
#         value = request.headers.get(header)
#         if value:
#             ip = value.split(",")[0].strip()
#             return ip, get_ip_country(ip)

#     ip = request.client.host
#     return ip, get_ip_country(ip)