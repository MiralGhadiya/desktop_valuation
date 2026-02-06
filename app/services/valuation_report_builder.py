# app/services/valuation_report_builder.py

from datetime import datetime


def build_report_context(ai_json, user_input):
    
    built_up_area = (
        user_input.get("built_up_area_sqft")
        or ai_json["property_details"].get("built_up_area_sqft")
    )

    property_details = {
        "name_of_owner": user_input.get("full_name", "N/A"),
        "project_name": user_input.get("project_name", "N/A"),
        "property_address": ai_json["property_details"].get("address", "N/A"),
        "property_type": ai_json["property_details"].get("property_type", "N/A"),
        "configuration": (
            user_input.get("configuration")
            or ai_json["property_details"].get("configuration")
            or "N/A"
        ),
        "carpet_area_sqft": built_up_area if built_up_area else "N/A",
        "construction_status": (
            user_input.get("construction_status")
            or ai_json["property_details"].get("construction_status")
            or "N/A"
        ),
        "purpose_of_report": user_input.get("purpose_of_valuation", "N/A"),
        "type_of_valuation": "Desktop Valuation Opinion",
        "inspection": "No Physical Inspection Conducted",
        "confidentiality": "Strictly for internal reference",
    }

    location_identification = {
        "micro_location": (
            user_input.get("micro_location")
            or ai_json["property_details"].get("micro_location")
            or "N/A"
        ),
        "municipal_authority": (
            user_input.get("municipal_authority")
            or ai_json["property_details"].get("municipal_authority")
            or "N/A"
        ),
        "connectivity": (
            user_input.get("connectivity")
            or ai_json["property_details"].get("connectivity")
            or "N/A"
        ),
        "social_infrastructure": (
            user_input.get("social_infrastructure")
            or ai_json["property_details"].get("social_infrastructure")
            or "N/A"
        ),
        "surroundings": (
            user_input.get("surroundings")
            or ai_json["property_details"].get("surroundings")
            or "N/A"
        ),
        "zoning": ai_json["property_details"].get("zoning", "N/A"),
        "demand_profile": (
            user_input.get("demand_profile")
            or ai_json["property_details"].get("demand_profile")
            or "N/A"
        ),
    }

    project_profile = {
        "developer": (
            user_input.get("developer")
            or ai_json["property_details"].get("developer")
            or "N/A"
        ),
        "project_positioning": (
            user_input.get("project_positioning")
            or ai_json["property_details"].get("project_positioning")
            or "N/A"
        ),
        "towers": (
            user_input.get("towers")
            or ai_json["property_details"].get("towers")
            or "N/A"
        ),
        "amenities": (
            user_input.get("amenities")
            or ai_json["property_details"].get("amenities")
            or "N/A"
        ),
        "market_perception": (
            user_input.get("market_perception")
            or ai_json["property_details"].get("market_perception")
            or "N/A"
        ),
    }

    area_details = {
        "carpet_area_sqft": built_up_area if built_up_area else "N/A",
        "layout": (
            user_input.get("layout")
            or ai_json["property_details"].get("layout")
            or "N/A"
        ),
        "floor_plan": (
            user_input.get("floor_plan")
            or ai_json["property_details"].get("floor_plan")
            or "N/A"
        ),
        "current_usage": (
            user_input.get("current_usage")
            or ai_json["property_details"].get("current_usage")
            or "N/A"
        ),
    }


    market_benchmark = ai_json.get("comparables_used", [])

    mid_value = ai_json["predicted_value"]["mid_value"]
    area_for_valuation = built_up_area or 0

    adopted_rate = (
        int(mid_value / area_for_valuation)
        if area_for_valuation and area_for_valuation > 0
        else "N/A"
    )

    indicative_market_value = {
        "area_considered_sqft": area_for_valuation,
        "adopted_market_rate": adopted_rate,
        "indicative_value": mid_value,
    }
    value_range = {
        "conservative": ai_json["predicted_value"]["low_value"],
        "mid_range": ai_json["predicted_value"]["mid_value"],
        "optimistic": ai_json["predicted_value"]["high_value"],
    }

    nearby_market_evidence = [
        "Recent transactions in nearby premium projects support the adopted rate",
        "Strong demand for ready-to-move residential units",
        "Limited supply of new premium projects in the locality",
        "Healthy resale and rental absorption observed",
    ]

    forecast = ai_json.get("forecast", {})
    current_value = ai_json["predicted_value"]["mid_value"]
    current_year = datetime.now().year

    future_outlook = []
    growth_rates = [
        forecast.get("year_1_growth_percent", 0),
        forecast.get("year_2_growth_percent", 0),
        forecast.get("year_3_growth_percent", 0),
        forecast.get("year_4_growth_percent", 0),
        forecast.get("year_5_growth_percent", 0),
    ]

    for i, rate in enumerate(growth_rates, start=1):
        current_value = int(current_value * (1 + rate / 100))
        future_outlook.append({
            "year": current_year + i,
            "expected_value": current_value,
        })

    swot_analysis = ai_json.get(
        "swot_analysis",
        {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": [],
        }
    )

    disclaimer = [
        "This report is a Desktop Valuation Opinion prepared using secondary market data.",
        "No physical or on-site inspection of the subject property has been carried out.",
        "The value stated represents an indicative market value for cross-check/reference purposes only.",
        "Actual realizable value may vary based on physical condition, legal status, negotiations, and market sentiment.",
        "This report is not intended for statutory, legal, lending, or enforcement purposes.",
        "No responsibility is assumed for title verification, encumbrances, or statutory approvals.",
        "This report is confidential and intended solely for the client.",
    ]

    return {
        "property_details": property_details,
        "location_identification": location_identification,
        "project_profile": project_profile,
        "area_details": area_details,
        "market_benchmark": market_benchmark,
        "indicative_market_value": indicative_market_value,
        "value_range": value_range,
        "nearby_market_evidence": nearby_market_evidence,
        "future_outlook": future_outlook,
        "swot_analysis": swot_analysis,
        "disclaimer": disclaimer,
    }
