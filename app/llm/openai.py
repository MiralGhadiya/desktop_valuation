#app/llm/openai.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

from app.utils.logger_config import app_logger as logger

logger.info("Initializing OpenAI client")

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is not set")
    raise RuntimeError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

logger.info("OpenAI API configured successfully")
logger.debug("OpenAI client initialized")


def generate_valuation_report(form_data: dict):
    logger.info("Starting OpenAI valuation report generation")
    

    prompt = f"""
            You are an automated real estate valuation engine.

            Goal:
            - Estimate current fair market value using recent local comparable sales.
            - If built-up area is not provided, calculate it using standard construction norms and value land and construction separately.
            - Apply depreciation based on property age, condition, and construction quality.
            - Reconcile cost-based valuation with market comparables and clearly state assumptions.
            - Recommend bank lending LTV based on property attributes, age, micro-location demand, and lending risk.
            - Classify lending risk as Low, Moderate, or High with justification.
            - Provide year-wise growth forecast based on local market trends without uniform annual growth rates.
            - Present outputs clearly with consistent calculations and professional valuation standards.
            
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
    try:
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        content = response.choices[0].message.content
        logger.debug("Raw OpenAI response received")

        parsed = json.loads(content)
        logger.info("OpenAI valuation report parsed successfully")
        return parsed

    except json.JSONDecodeError:
        logger.error("OpenAI returned invalid JSON")
        logger.debug(f"Raw OpenAI output: {content}")
        raise ValueError("AI did not return valid JSON")

    except Exception:
        logger.exception("OpenAI valuation generation failed")
        raise
