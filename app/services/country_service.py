from sqlalchemy.orm import Session
from app.models import Country


def get_country_by_dial_code(db: Session, dial_code: str):
    return db.query(Country).filter(
        Country.dial_code == dial_code
    ).first()


def create_country(db: Session, name: str, dial_code: str, country_code: str):
    country = Country(
        name=name,
        dial_code=dial_code,
        country_code=country_code,
    )
    db.add(country)
    db.commit()
    db.refresh(country)
    return country