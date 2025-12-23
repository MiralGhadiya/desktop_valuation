import phonenumbers
from phonenumbers.phonenumberutil import region_code_for_country_code
from app.utils.logger_config import app_logger as logger


def get_country_from_mobile(mobile: str):
    try:
        phone = phonenumbers.parse(mobile)
        dial_code = f"+{phone.country_code}"
        country_code = region_code_for_country_code(phone.country_code)
        return dial_code, country_code

    except Exception:
        logger.warning(f"Invalid phone number provided mobile={mobile}")
        raise