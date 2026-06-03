"""Initial schema: campaigns, prospects, emails

Revision ID: 001
Revises:
Create Date: 2026-05-31
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("search_query", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("progress_message", sa.Text, nullable=True),
        sa.Column("max_prospects", sa.Integer, nullable=False, server_default="10"),
        sa.Column("prospect_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("email_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("sender_name", sa.String(100), nullable=False),
        sa.Column("sender_title", sa.String(100), nullable=False),
        sa.Column("sender_company", sa.String(100), nullable=False),
        sa.Column("value_proposition", sa.String(500), nullable=False),
        sa.Column("email_tone", sa.String(20), nullable=False, server_default="professional"),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "prospects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("company", sa.String(150), nullable=False),
        sa.Column("company_size", sa.String(30), nullable=True),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("recent_news", sa.Text, nullable=True),
        sa.Column("job_postings", sa.JSON, nullable=False),
        sa.Column("pain_points", sa.JSON, nullable=False),
        sa.Column("personalisation_hook", sa.Text, nullable=True),
        sa.Column("enriched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prospects_campaign_id", "prospects", ["campaign_id"])

    op.create_table(
        "emails",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("campaigns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "prospect_id",
            sa.String(36),
            sa.ForeignKey("prospects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("prospect_email", sa.String(255), nullable=False),
        sa.Column("prospect_name", sa.String(200), nullable=False),
        sa.Column("sequence_day", sa.Integer, nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("resend_email_id", sa.String(100), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_emails_campaign_id", "emails", ["campaign_id"])
    op.create_index("ix_emails_prospect_id", "emails", ["prospect_id"])
    op.create_index("ix_emails_status", "emails", ["status"])
    op.create_index("ix_emails_resend_email_id", "emails", ["resend_email_id"])


def downgrade() -> None:
    op.drop_table("emails")
    op.drop_table("prospects")
    op.drop_table("campaigns")
