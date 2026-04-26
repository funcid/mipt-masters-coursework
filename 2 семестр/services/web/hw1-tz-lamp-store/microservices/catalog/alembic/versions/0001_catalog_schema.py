"""catalog schema

Revision ID: 0001_catalog_schema
Revises:
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_catalog_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")
    op.create_table(
        "category",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
        schema="catalog",
    )
    op.create_table(
        "product",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("watt", sa.Integer(), nullable=True),
        sa.Column("base_type", sa.String(length=16), nullable=True),
        sa.Column("color_temp_k", sa.Integer(), nullable=True),
        sa.Column("lifetime_hours", sa.Integer(), nullable=True),
        sa.Column("stock_qty", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("price_cents >= 0", name="ck_product_price_cents_non_negative"),
        sa.CheckConstraint("stock_qty >= 0", name="ck_product_stock_qty_non_negative"),
        sa.ForeignKeyConstraint(["category_id"], ["catalog.category.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sku"),
        schema="catalog",
    )
    op.create_index("ix_catalog_product_base_type", "product", ["base_type"], schema="catalog")
    op.create_index("ix_catalog_product_category_id", "product", ["category_id"], schema="catalog")
    op.create_index("ix_catalog_product_is_active", "product", ["is_active"], schema="catalog")
    op.create_index("ix_catalog_product_sku", "product", ["sku"], schema="catalog")
    op.create_table(
        "product_image",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["catalog.product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="catalog",
    )
    op.create_index("ix_catalog_product_image_product_id", "product_image", ["product_id"], schema="catalog")


def downgrade() -> None:
    op.drop_index("ix_catalog_product_image_product_id", table_name="product_image", schema="catalog")
    op.drop_table("product_image", schema="catalog")
    op.drop_index("ix_catalog_product_sku", table_name="product", schema="catalog")
    op.drop_index("ix_catalog_product_is_active", table_name="product", schema="catalog")
    op.drop_index("ix_catalog_product_category_id", table_name="product", schema="catalog")
    op.drop_index("ix_catalog_product_base_type", table_name="product", schema="catalog")
    op.drop_table("product", schema="catalog")
    op.drop_table("category", schema="catalog")
    op.execute("DROP SCHEMA IF EXISTS catalog")
