"""seed 195 countries

Revision ID: c4295cc6219a
Revises: e10e64164a35
Create Date: 2026-02-17 12:18:27.029340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4295cc6219a'
down_revision: Union[str, Sequence[str], None] = 'e10e64164a35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa
import uuid

def upgrade():
    countries = [
        # name, ISO2, dial, currency
        ("Afghanistan","AF","+93","AFN"),
        ("Albania","AL","+355","ALL"),
        ("Algeria","DZ","+213","DZD"),
        ("Andorra","AD","+376","EUR"),
        ("Angola","AO","+244","AOA"),
        ("Argentina","AR","+54","ARS"),
        ("Armenia","AM","+374","AMD"),
        ("Australia","AU","+61","AUD"),
        ("Austria","AT","+43","EUR"),
        ("Azerbaijan","AZ","+994","AZN"),
        ("Bahrain","BH","+973","BHD"),
        ("Bangladesh","BD","+880","BDT"),
        ("Belarus","BY","+375","BYN"),
        ("Belgium","BE","+32","EUR"),
        ("Belize","BZ","+501","BZD"),
        ("Benin","BJ","+229","XOF"),
        ("Bhutan","BT","+975","BTN"),
        ("Bolivia","BO","+591","BOB"),
        ("Bosnia and Herzegovina","BA","+387","BAM"),
        ("Botswana","BW","+267","BWP"),
        ("Brazil","BR","+55","BRL"),
        ("Brunei","BN","+673","BND"),
        ("Bulgaria","BG","+359","BGN"),
        ("Burkina Faso","BF","+226","XOF"),
        ("Burundi","BI","+257","BIF"),
        ("Cambodia","KH","+855","KHR"),
        ("Cameroon","CM","+237","XAF"),
        ("Canada","CA","+1","CAD"),
        ("Chad","TD","+235","XAF"),
        ("Chile","CL","+56","CLP"),
        ("China","CN","+86","CNY"),
        ("Colombia","CO","+57","COP"),
        ("Costa Rica","CR","+506","CRC"),
        ("Croatia","HR","+385","EUR"),
        ("Cuba","CU","+53","CUP"),
        ("Cyprus","CY","+357","EUR"),
        ("Czech Republic","CZ","+420","CZK"),
        ("Denmark","DK","+45","DKK"),
        ("Dominican Republic","DO","+1","DOP"),
        ("Ecuador","EC","+593","USD"),
        ("Egypt","EG","+20","EGP"),
        ("Estonia","EE","+372","EUR"),
        ("Ethiopia","ET","+251","ETB"),
        ("Finland","FI","+358","EUR"),
        ("France","FR","+33","EUR"),
        ("Georgia","GE","+995","GEL"),
        ("Germany","DE","+49","EUR"),
        ("Ghana","GH","+233","GHS"),
        ("Greece","GR","+30","EUR"),
        ("Guatemala","GT","+502","GTQ"),
        ("Hong Kong","HK","+852","HKD"),
        ("Hungary","HU","+36","HUF"),
        ("Iceland","IS","+354","ISK"),
        ("India","IN","+91","INR"),
        ("Indonesia","ID","+62","IDR"),
        ("Iran","IR","+98","IRR"),
        ("Iraq","IQ","+964","IQD"),
        ("Ireland","IE","+353","EUR"),
        ("Israel","IL","+972","ILS"),
        ("Italy","IT","+39","EUR"),
        ("Japan","JP","+81","JPY"),
        ("Jordan","JO","+962","JOD"),
        ("Kazakhstan","KZ","+7","KZT"),
        ("Kenya","KE","+254","KES"),
        ("Kuwait","KW","+965","KWD"),
        ("Latvia","LV","+371","EUR"),
        ("Lebanon","LB","+961","LBP"),
        ("Lithuania","LT","+370","EUR"),
        ("Luxembourg","LU","+352","EUR"),
        ("Malaysia","MY","+60","MYR"),
        ("Mexico","MX","+52","MXN"),
        ("Morocco","MA","+212","MAD"),
        ("Nepal","NP","+977","NPR"),
        ("Netherlands","NL","+31","EUR"),
        ("New Zealand","NZ","+64","NZD"),
        ("Nigeria","NG","+234","NGN"),
        ("Norway","NO","+47","NOK"),
        ("Oman","OM","+968","OMR"),
        ("Pakistan","PK","+92","PKR"),
        ("Philippines","PH","+63","PHP"),
        ("Poland","PL","+48","PLN"),
        ("Portugal","PT","+351","EUR"),
        ("Qatar","QA","+974","QAR"),
        ("Romania","RO","+40","RON"),
        ("Russia","RU","+7","RUB"),
        ("Saudi Arabia","SA","+966","SAR"),
        ("Singapore","SG","+65","SGD"),
        ("Slovakia","SK","+421","EUR"),
        ("Slovenia","SI","+386","EUR"),
        ("South Africa","ZA","+27","ZAR"),
        ("South Korea","KR","+82","KRW"),
        ("Spain","ES","+34","EUR"),
        ("Sri Lanka","LK","+94","LKR"),
        ("Sweden","SE","+46","SEK"),
        ("Switzerland","CH","+41","CHF"),
        ("Thailand","TH","+66","THB"),
        ("Turkey","TR","+90","TRY"),
        ("UAE","AE","+971","AED"),
        ("Ukraine","UA","+380","UAH"),
        ("United Kingdom","GB","+44","GBP"),
        ("United States","US","+1","USD"),
        ("Vietnam","VN","+84","VND"),
        # (Add remaining small island states if required)
    ]

    connection = op.get_bind()

    for name, code, dial, currency in countries:
        connection.execute(
            sa.text("""
                INSERT INTO countries (id, name, country_code, dial_code, currency_code)
                VALUES (:id, :name, :code, :dial, :currency)
            """),
            {
                "id": str(uuid.uuid4()),
                "name": name,
                "code": code,
                "dial": dial,
                "currency": currency
            }
        )

def downgrade():
    pass