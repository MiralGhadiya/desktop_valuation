import uuid
from datetime import datetime


def build_report_context(ai_json, user_input):

    # -------- PROPERTY IDENTIFICATION --------
    property_identification = {
        "property_address": ai_json["property_details"]["address"],
        "valuation_id": f"DVP-{uuid.uuid4().hex[:8].upper()}",
        "date_of_report": datetime.now().strftime("%d-%b-%Y"),
        "purpose_of_valuation": user_input["purpose_of_valuation"],
        "report_type": "Desktop Valuation (Automated)",
        "client_name": user_input["full_name"],
        "contact_information": {
            "email": user_input["email"],
            "phone": user_input["contact_number"]
        }
    }

    # -------- PROPERTY SUMMARY --------
    property_summary = {
        "property_type": ai_json["property_details"]["property_type"],
        "land_area": f"{ai_json['property_details']['land_area_sqft']} sqft",
        "built_up_area": f"{ai_json['property_details']['built_up_area_sqft']} sqft",
        "zoning": "Residential",
        "title_details": "Not Available",
        "construction_year": f"{ai_json['property_details']['age_years']} years old",
        "structure": "RCC Construction",
        "car_parking": "Available",
        "ownership_type": "Freehold",
        "occupancy": "Owner Occupied",
        "local_authority": ai_json["property_details"]["city"].title(),
        "last_sale_date": "N/A",
        "last_sale_price": "N/A",
        "customer_estimate": user_input.get("estimated_market_value", "N/A")
    }

    # -------- COMPARABLE SALES --------
    comparable_sales = []
    for c in ai_json["comparables_used"]:
        comparable_sales.append({
            "address": c["address"],
            "beds": "-",      # AI JSON does not provide beds
            "baths": "-",     # AI JSON does not provide baths
            "land_area": c["land_area"],
            "sale_date": "N/A",
            "sale_price": c["sale_price"],
            "comparison": c["adjustment_reason"],
            "distance": f"{c['distance_km']} km"
        })

    # -------- COMPARABLE SUMMARY --------
    comparable_analysis_summary = {
        "average_comparable_value": ai_json["predicted_value"]["mid_value"],
        "adjusted_subject_estimate": ai_json["predicted_value"]["fair_market_value"]
    }

    # -------- THREE-TIER --------
    three_tier_valuation = {
        "conservative_value": ai_json["predicted_value"]["low_value"],
        "mid_range_value": ai_json["predicted_value"]["mid_value"],
        "high_value": ai_json["predicted_value"]["high_value"]
    }

    # -------- RISK ANALYSIS --------
    valuation_risk_analysis = {
        "value_range": f"{ai_json['predicted_value']['low_value']} - {ai_json['predicted_value']['high_value']}",
        "confidence_index": ai_json["predicted_value"]["confidence_score"],
        "market_risk_score": ai_json["bank_lending_model"]["risk_level"],
        "property_risk_score": "Moderate",
        "recommended_ltv": ai_json["bank_lending_model"]["recommended_ltv"],
        "validity": "45 Days"
    }

    # -------- MARKET COMMENTARY --------
    market_commentary = ai_json["buy_sell_recommendation"]["reasoning"]

    # -------- SWOT --------
    swot_analysis = {
        "strengths": ["Good locality demand", "Stable RCC structure", "Moderate appreciation potential"],
        "weaknesses": ["Property age moderate", "Average liquidity"],
        "opportunities": ["Growing micro-market demand", "Future redevelopment potential"],
        "threats": ["Interest rate fluctuations", "Market corrections"]
    }

    # -------- FORECAST (5 years) --------
    growth = ai_json["forecast"]["growth_rate_percent"] / 100
    base = ai_json["predicted_value"]["fair_market_value"]
    value_forecast = []

    for i in range(1, 6):
        projected = int(base * ((1 + growth) ** i))
        value_forecast.append({
            "year": datetime.now().year + i,
            "growth_rate": f"{ai_json['forecast']['growth_rate_percent']}%",
            "forecast_value": projected
        })

    return {
        "property_identification": property_identification,
        "property_summary": property_summary,
        "comparable_sales": comparable_sales,
        "comparable_analysis_summary": comparable_analysis_summary,
        "three_tier_valuation": three_tier_valuation,
        "valuation_risk_analysis": valuation_risk_analysis,
        "market_commentary": market_commentary,
        "swot_analysis": swot_analysis,
        "value_forecast": value_forecast
    }