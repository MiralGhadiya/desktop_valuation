#app/llm/openai.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from langsmith import traceable
from openai import OpenAIError
from app.utils.logger_config import app_logger as logger

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY is not set")
    raise RuntimeError("Missing OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)
logger.info("OpenAI client initialized successfully")

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class LLMServiceUnavailable(LLMError):
    pass

BASE_PROMPT = """
          Role: Certified real estate valuation engine.

          Global Constraints:
          - Output ONLY valid JSON
          - No markdown, no explanations
          - Numbers only (no commas)
          - Infer missing data logically
          - Maintain internal consistency

          Valuation Contract:
          - Produce three independent values: low, mid, high
          - Each tier MUST use different assumptions
          - Apply directional adjustments (superior ↑, inferior ↓)
          - Enforce meaningful spread between tiers

          Compliance:
          - Market approach dominates
          - Lending model must be conservative and defensible
        """

PROPERTY_PROMPTS = {

    "residential plot": """
            Property Rules: Residential Plot

            Valuation Method:
            - Market comparable value is PRIMARY
            - Value land and buildup both is buildup area is given but focus on land value
            - Value land using nearby recent plot sale rates per sqft

            Adjustments:
            - Apply corner, road-facing, and size premiums
            - Apply demand premium in high-growth residential zones
            - Apply negative adjustments for irregular shape or poor access or outdated zoning or outside approved residential areas
            - Do NOT apply depreciation on land
            - Apply depreciation on buildup area

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
            - Land value must be apportioned based on undivided share

            Depreciation:
            - Apply depreciation on construction component only
            - Cap depreciation at:
                - 10% if age < 10 years
                - 20% if age between 10 and 20 years
                - 30% if age > 20 years
                - 40% if age > 30 years
                
            Constraints:
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
            - If propery is too small or old then apply decriciation accordingly on construction

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
        - Apply higher depreciation for specialized facilities

        Constraints:
        - Cost-based value cannot undercut market-derived value
        - Consider logistics access, zoning, and warehouse demand
      """
}


CORE_JSON_SCHEMA = """
        {
          "property_details":{
            "address":"","city":"","country":"","property_type":"",
            "land_area_sqft":0,"built_up_area_sqft":0,"age_years":0,"zoning":""
          },
          "predicted_value":{
            "low_value":0,"mid_value":0,"high_value":0,
            "fair_market_value":0,"confidence_score":0
          },
          "bank_lending_model":{
            "recommended_ltv":0,"safe_lending_value":0,
            "risk_level":"","reason":""
          },
          "buy_sell_recommendation":{
            "buyer_recommendation":"",
            "seller_recommendation":"",
            "reasoning":""
          },
          "comparables_used":[{
            "address":"","land_area":"",
            "sale_price":0,"distance_km":0,
            "adjustment_reason":""
          }]
        }
      """


FORECAST_SCHEMA = """
        {
          "year_1_growth_percent": 0,
          "year_2_growth_percent": 0,
          "year_3_growth_percent": 0,
          "year_4_growth_percent": 0,
          "year_5_growth_percent": 0,
          "value_in_12_months": 0
        }
      """


@traceable(name="generate_forecast", run_type="llm")
def generate_forecast(core_output: dict):
    prompt = f"""
        You are a real estate market forecasting engine.

        Rules:
        - Return ONLY valid JSON
        - No markdown
        - Numbers only
        - Growth rates must vary year-to-year
        - Base forecast on market maturity and property type

        Input:
        {{
          "fair_market_value": {core_output["predicted_value"]["fair_market_value"]},
          "property_type": "{core_output["property_details"]["property_type"]}",
          "city": "{core_output["property_details"]["city"]}",
          "confidence_score": {core_output["predicted_value"]["confidence_score"]}
        }}

        Return exactly this JSON:
        {{
          "year_1_growth_percent": 0,
          "year_2_growth_percent": 0,
          "year_3_growth_percent": 0,
          "year_4_growth_percent": 0,
          "year_5_growth_percent": 0,
          "value_in_12_months": 0
        }}
      """
    try:
      response = client.chat.completions.create(
          model="gpt-5.2",
          messages=[{"role": "user", "content": prompt}],
          temperature=0.2,
          response_format={"type": "json_object"},
      )

      return json.loads(response.choices[0].message.content)
    
    except json.JSONDecodeError:
          logger.exception("Invalid JSON in forecast response")
          raise LLMServiceUnavailable("Forecast generation failed")

    except OpenAIError as e:
        logger.exception("OpenAI error during forecast")
        raise LLMServiceUnavailable("Forecast service unavailable") from e

    except Exception:
        logger.exception("Unexpected forecast failure")
        raise LLMServiceUnavailable("Forecast generation failed")



@traceable(name="openai_chat_completion", run_type="llm")
def _call_openai(final_prompt: str):
    return client.chat.completions.create(
        model="gpt-5.2",
        messages=[{"role": "user", "content": final_prompt}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )


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
              # {json.dumps(form_data)}
              {json.dumps(form_data, separators=(",", ":"))}

              Return exactly this JSON structure:
              {CORE_JSON_SCHEMA}
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

    except OpenAIError as e:
        logger.exception("OpenAI API error")
        raise RuntimeError("AI service unavailable") from e

    except Exception:
        logger.exception("Valuation generation failed")
        raise
