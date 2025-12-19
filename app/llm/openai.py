import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("OpenAI API configured.")
print(client)


def generate_valuation_report(form_data: dict):
    prompt = f"""
            You are an automated real estate valuation engine.

            Goal:
            Estimate the current fair accurate market value of the property using local comparables, and if buildup area not given then
            calculate it according to standard construction norms and add valuation of both construction and land. 
            Provide a bank lending model with recommended LTV based on
            property attributes, age, micro-location demand, and lending risk assumptions.
            caclculate growth forecast correctly based on local market trends.

            Rules:
            - Return ONLY valid JSON
            - No text outside JSON
            - No markdown
            - Numbers only (no symbols or commas)
            - Infer missing data logically
            - Assume standard RCC residential construction

            Input:
            {form_data}

            Return exactly this JSON structure:

            {{
            "property_details": {{
                "address": "",
                "city": "",
                "country": "",
                "property_type": "",
                "land_area_sqft": 0,
                "built_up_area_sqft": 0,
                "age_years": 0
            }},
            "predicted_value": {{
                "low_value": 0,
                "mid_value": 0,
                "high_value": 0,
                "fair_market_value": 0,
                "confidence_score": 0
            }},
            "bank_lending_model": {{
                "recommended_ltv": 0,
                "safe_lending_value": 0,
                "risk_level": "",
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
                "growth_rate_percent": 0,
                "value_in_12_months": 0
            }}
            }}
        """


    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    content = response.choices[0].message.content

    try:
        parsed = json.loads(content)
        return parsed
    except Exception as e:
        print("JSON PARSE ERROR:", e)
        print("RAW AI OUTPUT:", content)
        raise ValueError("AI did not return valid JSON")