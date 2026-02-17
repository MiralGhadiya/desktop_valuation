"""make country_code unique

Revision ID: e10e64164a35
Revises: b23ecf8035b0
Create Date: 2026-02-17 12:15:49.191095

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e10e64164a35'
down_revision: Union[str, Sequence[str], None] = 'b23ecf8035b0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_countries_country_code",
        "countries",
        ["country_code"]
    )

def downgrade() -> None:
    op.drop_constraint(
        "uq_countries_country_code",
        "countries",
        type_="unique"
    )
