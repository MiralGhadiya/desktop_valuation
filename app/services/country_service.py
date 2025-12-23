#app/services/country_service.py

from sqlalchemy.orm import Session
from app.models import Country
from app.utils.logger_config import app_logger as logger


def get_country_by_dial_code(db: Session, dial_code: str):
    logger.debug(f"Looking up country by dial_code={dial_code}")

    return db.query(Country).filter(
        Country.dial_code == dial_code
    ).first()


def create_country(db: Session, name: str, dial_code: str, country_code: str):
    logger.info(
        f"Creating country name={name} dial_code={dial_code} country_code={country_code}"
    )

    country = Country(
        name=name,
        dial_code=dial_code,
        country_code=country_code,
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    return country