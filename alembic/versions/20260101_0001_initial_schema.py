"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "advertisers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("external_ref", sa.String(255), nullable=False),
        sa.Column("meta_business_id", sa.String(64), nullable=True),
        sa.Column("meta_ad_account_id", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("external_ref", name="uq_advertisers_external_ref"),
    )

    op.create_table(
        "pixels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "advertiser_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("advertisers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("meta_pixel_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("meta_pixel_id", name="uq_pixels_meta_pixel_id"),
    )
    op.create_index("ix_pixels_advertiser_id", "pixels", ["advertiser_id"])

    op.create_table(
        "conversion_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "advertiser_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("advertisers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "pixel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pixels.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("value", sa.Numeric(18, 4), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("rule", postgresql.JSONB, nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("meta_custom_conversion_id", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "advertiser_id", "name", name="uq_conversion_tags_advertiser_id_name"
        ),
    )
    op.create_index("ix_conversion_tags_advertiser_id", "conversion_tags", ["advertiser_id"])
    op.create_index("ix_conversion_tags_pixel_id", "conversion_tags", ["pixel_id"])

    op.create_table(
        "oauth_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "advertiser_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("advertisers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("access_token_encrypted", sa.String, nullable=False),
        sa.Column("refresh_token_encrypted", sa.String, nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scopes", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "advertiser_id", "provider", name="uq_oauth_tokens_advertiser_id_provider"
        ),
    )
    op.create_index("ix_oauth_tokens_advertiser_id", "oauth_tokens", ["advertiser_id"])

    op.create_table(
        "idempotency_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("endpoint", sa.String(128), nullable=False),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("response_status", sa.Integer, nullable=False),
        sa.Column("response_body", postgresql.JSONB, nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("endpoint", "key", name="uq_idempotency_records_endpoint_key"),
    )


def downgrade() -> None:
    op.drop_table("idempotency_records")
    op.drop_index("ix_oauth_tokens_advertiser_id", table_name="oauth_tokens")
    op.drop_table("oauth_tokens")
    op.drop_index("ix_conversion_tags_pixel_id", table_name="conversion_tags")
    op.drop_index("ix_conversion_tags_advertiser_id", table_name="conversion_tags")
    op.drop_table("conversion_tags")
    op.drop_index("ix_pixels_advertiser_id", table_name="pixels")
    op.drop_table("pixels")
    op.drop_table("advertisers")
