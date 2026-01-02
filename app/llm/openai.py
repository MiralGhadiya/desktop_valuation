#app/llm/openai.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from langsmith import traceable
from app.utils.logger_config import app_logger as logger

# --------------------------------------------------
# Init
# --------------------------------------------------

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is not set")
    raise RuntimeError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
logger.info("OpenAI client initialized successfully")

# --------------------------------------------------
# Base Prompt (Always Included)
# --------------------------------------------------

BASE_PROMPT = """
          You are an automated real estate valuation engine.

          Global Rules:
          - Return ONLY valid JSON
          - No text outside JSON
          - No markdown
          - Numbers only (no commas or symbols)
          - Infer missing data logically
          - Maintain internal calculation consistency
          -If built-up area is missing, estimate using standard norms
          
          Three-Tier Valuation Rule:

          - low_value, mid_value, and high_value MUST be derived from DIFFERENT assumptions.
          - Do NOT calculate tiers using simple percentage adjustments from one base value.
          - Each tier must represent a distinct market scenario:
              - low_value = conservative / forced-sale / weak demand scenario
              - mid_value = fair market equilibrium scenario
              - high_value = optimistic / premium buyer / strong demand scenario
          
          Three-Tier & Adjustment Enforcement:

          - low_value, mid_value, and high_value MUST be reasoned independently.
          - Do NOT derive tiers by applying percentages to a single base value.

          Comparable vs Subject Rule:
          - Average Comparable Value = market baseline only.
          - Adjusted Subject Estimate MUST reflect subject-specific differences and
            MUST NOT equal the comparable average unless the subject is identical.

          Directional Adjustments:
          - Superior subject attributes → adjusted value MUST increase.
          - Inferior subject attributes → adjusted value MUST decrease.
          - Zero-net adjustments are NOT allowed.

          Separation Rule:
          - low, mid, and high values must show meaningful spread.
          - If values converge, assumptions must be re-evaluated and separated.
          
          IMPORTANT:
            Three-tier values must NOT be scaled versions of each other.
            Each tier must be reasoned independently with different assumptions,
            different comparable weighting, and different premium/depreciation logic.
            Flat or near-identical tier outputs indicate incorrect reasoning and must be corrected.

          Core Objectives:
          - Estimate fair market value using appropriate valuation methods
          - Reconcile market and cost approaches logically
          - Recommend bank lending LTV with risk classification
          - Provide 5-year growth forecast using non-uniform rates

          Output must EXACTLY match the provided JSON schema.
        """

PROPERTY_PROMPTS = {

    "residential plot": """
            Property Rules: Residential Plot

            Valuation Method:
            - Market comparable value is PRIMARY
            - Cost-based construction valuation is NOT applicable
            - Value land using nearby recent plot sale rates per sqft

            Adjustments:
            - Apply corner, road-facing, and size premiums
            - Apply demand premium in high-growth residential zones
            - Do NOT apply depreciation on land

            Reconciliation:
            - Final value must not be lower than strong comparable-derived value
        """,

    "residential house": """
            Property Rules: Residential House

            Valuation Method:
            - Hybrid valuation: market comparables as anchor, cost-based as support
            - Value land separately from construction
            - Apply depreciation ONLY on construction

            Depreciation Caps:
            - Age < 10 years: max 10%
            - Age 10-20 years: max 20%

            Constraints:
            - Do NOT allow depreciated construction value to reduce market-driven valuation
            - Bias final value toward market comparables in high-demand zones

            Premiums:
            - Independent houses
            - Redevelopment potential
            - Corner or road-facing properties
        """,

    "residential flat": """
            Property Rules: Residential Flat

            Valuation Method:
            - Market comparable value is PRIMARY
            - Cost-based construction valuation is SECONDARY and supportive
            - Land value must be apportioned based on undivided share (UDS)

            Depreciation:
            - Apply depreciation on construction component only
            - Cap depreciation at:
                - 10% if age < 10 years
                - 20% if age between 10 and 20 years

            Constraints:
            - Do NOT allow depreciation to pull value below comparable apartment prices
            - Prefer same-building or same-society comparables

            Premiums:
            - Higher floor with lift access
            - Newer societies with amenities
            - Strong rental demand zones
            - Proximity to transit, IT parks, or CBD
        """,

    "commercial shop": """
            Property Rules: Commercial Shop

            Valuation Method:
            - Market comparables are DOMINANT
            - Ignore residential construction norms
            - Ground-floor retail premium applies

            Depreciation:
            - Cap depreciation at 10% if age < 15 years

            Constraints:
            - Cost-based valuation must NOT undercut comparable-derived value
            - Apply footfall and frontage demand premiums
        """,

    "industrial unit": """
        Property Rules: Industrial Unit

        Valuation Method:
        - Market comparables dominate where available
        - Value land plus industrial construction
        - Ignore residential norms entirely
        - Apply functional obsolescence risk adjustments

        Depreciation:
        - Cap depreciation at 15% if age < 20 years

        Constraints:
        - Cost-based value cannot undercut market-derived value
        - Consider logistics access, zoning, and warehouse demand
    """
}


JSON_SCHEMA = """
        {
          "property_details": {
            "address": "",
            "city": "",
            "country": "",
            "property_type": "",
            "land_area_sqft": 0,
            "built_up_area_sqft": 0,
            "age_years": 0
          },
          "predicted_value": {
            "low_value": 0,
            "mid_value": 0,
            "high_value": 0,
            "fair_market_value": 0,
            "confidence_score": 0
          },
          "bank_lending_model": {
            "recommended_ltv": 0,
            "safe_lending_value": 0,
            "risk_level": "",
            "reason": ""
          },
          "buy_sell_recommendation": {
            "buyer_recommendation": "",
            "seller_recommendation": "",
            "reasoning": ""
          },
          "comparables_used": [
            {
              "address": "",
              "land_area": "",
              "sale_price": 0,
              "distance_km": 0,
              "adjustment_reason": ""
            }
          ],
          "forecast": {
            "year_1_growth_percent": 0,
            "year_2_growth_percent": 0,
            "year_3_growth_percent": 0,
            "year_4_growth_percent": 0,
            "year_5_growth_percent": 0,
            "value_in_12_months": 0
          }
        }
      """


@traceable(name="openai_chat_completion", run_type="llm")
def _call_openai(final_prompt: str):
    return client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": final_prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

# --------------------------------------------------
# Main Valuation Function (Traced)
# --------------------------------------------------

@traceable(name="generate_valuation_report", run_type="chain")
def generate_valuation_report(form_data: dict):
    logger.info("Starting valuation report generation")

    property_type = form_data.get("property_type")

    if not property_type or property_type not in PROPERTY_PROMPTS:
        logger.error(f"Unsupported or missing property_type: {property_type}")
        raise ValueError("Invalid or unsupported property_type")

    final_prompt = f"""
{BASE_PROMPT}

{PROPERTY_PROMPTS[property_type]}

Input:
{json.dumps(form_data)}

Return exactly this JSON structure:
{JSON_SCHEMA}
"""

    logger.debug("Final prompt constructed")

    try:
        response = _call_openai(final_prompt)

        content = response.choices[0].message.content
        parsed = json.loads(content)

        logger.info("Valuation report generated successfully")
        return parsed

    except json.JSONDecodeError:
        logger.error("Invalid JSON returned by OpenAI")
        logger.debug(content)
        raise ValueError("AI returned invalid JSON")

    except Exception:
        logger.exception("Valuation generation failed")
        raise