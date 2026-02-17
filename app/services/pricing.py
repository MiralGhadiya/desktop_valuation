# app/services/pricing.py

def resolve_pricing_country(request, current_user) -> str:
    if getattr(request.state, "ip_country", None):
        return request.state.ip_country
    
    if current_user and current_user.country:
        return current_user.country.country_code

    return "DEFAULT"


def resolve_currency_code(request, current_user) -> str:
    # preferred: currency from user profile country
    if current_user.country and getattr(current_user.country, "currency_code", None):
        return current_user.country.currency_code
    return "USD"
