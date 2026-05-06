"""add product description

Revision ID: 002_add_product_description
Revises: 001_create_products
Create Date: 2026-05-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_add_product_description"
down_revision: Union[str, None] = "001_create_products"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=False,
            server_default="No description",
        ),
    )


def downgrade() -> None:
    op.drop_column("products", "description")
