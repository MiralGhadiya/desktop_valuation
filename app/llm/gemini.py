import google.generativeai as genai
import os
import json

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")
print("Gemini API configured.")
print(model)

def generate_valuation_summary(form_data: dict):

    prompt = f"""
    You are an Automated Valuation Model (AVM).
    Return ONLY valid JSON. DO NOT include explanations.

    {{
      "property_details": {{
          "address": "{form_data.get('full_address')}",
          "city": "{form_data.get('city_location')}",
          "country": "{form_data.get('country')}",
          "property_type": "{form_data.get('property_type')}",
          "land_area_sqft": {int(form_data.get("land_area").split()[0])},
          "built_up_area_sqft": {int(form_data.get("built_up_area").split()[0])},
          "age_years": {int(form_data.get("year_built"))}
      }},
      "predicted_value": {{
          "low_value": 0,
          "mid_value": 0,
          "high_value": 0,
          "fair_market_value": 0,
          "confidence_score": 80
      }},
      "bank_lending_model": {{
          "recommended_ltv": 75,
          "safe_lending_value": 0,
          "risk_level": "Moderate",
          "reason": ""
      }},
      "buy_sell_recommendation": {{
          "buyer_recommendation": "",
          "seller_recommendation": "",
          "reasoning": ""
      }},
      "comparables_used": [
          {{
              "address": "",
              "land_area": "",
              "sale_price": 0,
              "distance_km": 0,
              "adjustment_reason": ""
          }}
      ],
      "forecast": {{
          "growth_rate_percent": 6.0,
          "value_in_12_months": 0
      }}
    }}

    Return ONLY JSON.
    """

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Parse JSON safely
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        cleaned = raw[raw.find("{"): raw.rfind("}") + 1]
        return json.loads(cleaned)
