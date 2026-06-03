import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Prospect(Base):
    __tablename__ = "prospects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"))

    # Identity — from Apollo
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(150))
    company: Mapped[str] = mapped_column(String(150))
    company_size: Mapped[str | None] = mapped_column(String(30), nullable=True)
    country: Mapped[str] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Enrichment — from Tavily + LLM
    recent_news: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_postings: Mapped[list] = mapped_column(JSON, default=list)
    pain_points: Mapped[list] = mapped_column(JSON, default=list)
    personalisation_hook: Mapped[str | None] = mapped_column(Text, nullable=True)
    enriched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    campaign: Mapped["Campaign"] = relationship(back_populates="prospects")  # noqa: F821
    emails: Mapped[list["Email"]] = relationship(back_populates="prospect", cascade="all, delete-orphan")  # noqa: F821
