"""order schema

Revision ID: 0001_order_schema
Revises:
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_order_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS orders")
    op.create_table(
        "cart",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cart_token", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cart_token"),
        schema="orders",
    )
    op.create_table(
        "customer_order",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("cart_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=False),
        sa.Column("customer_phone", sa.String(length=32), nullable=False),
        sa.Column("delivery_address", sa.Text(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("total_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cart_id"], ["orders.cart.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_number"),
        schema="orders",
    )
    op.create_index("ix_orders_customer_order_created_at", "customer_order", ["created_at"], schema="orders")
    op.create_index("ix_orders_customer_order_customer_email", "customer_order", ["customer_email"], schema="orders")
    op.create_index("ix_orders_customer_order_order_number", "customer_order", ["order_number"], schema="orders")
    op.create_index("ix_orders_customer_order_status", "customer_order", ["status"], schema="orders")
    op.create_table(
        "cart_line",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cart_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_cart_line_quantity_positive"),
        sa.ForeignKeyConstraint(["cart_id"], ["orders.cart.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cart_id", "product_id", name="uq_cart_line_cart_product"),
        schema="orders",
    )
    op.create_index("ix_orders_cart_line_cart_id", "cart_line", ["cart_id"], schema="orders")
    op.create_table(
        "order_line",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_name", sa.String(length=255), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("unit_price_cents", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("line_total_cents", sa.Integer(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_line_quantity_positive"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.customer_order.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="orders",
    )
    op.create_index("ix_orders_order_line_order_id", "order_line", ["order_id"], schema="orders")


def downgrade() -> None:
    op.drop_index("ix_orders_order_line_order_id", table_name="order_line", schema="orders")
    op.drop_table("order_line", schema="orders")
    op.drop_index("ix_orders_cart_line_cart_id", table_name="cart_line", schema="orders")
    op.drop_table("cart_line", schema="orders")
    op.drop_index("ix_orders_customer_order_status", table_name="customer_order", schema="orders")
    op.drop_index("ix_orders_customer_order_order_number", table_name="customer_order", schema="orders")
    op.drop_index("ix_orders_customer_order_customer_email", table_name="customer_order", schema="orders")
    op.drop_index("ix_orders_customer_order_created_at", table_name="customer_order", schema="orders")
    op.drop_table("customer_order", schema="orders")
    op.drop_table("cart", schema="orders")
    op.execute("DROP SCHEMA IF EXISTS orders")
