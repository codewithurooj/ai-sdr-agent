import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id: Mapped[str] = mapped_column(String(36), ForeignKey("campaigns.id", ondelete="CASCADE"))
    prospect_id: Mapped[str] = mapped_column(String(36), ForeignKey("prospects.id", ondelete="CASCADE"))

    # Denormalised for quick access without joins
    prospect_email: Mapped[str] = mapped_column(String(255))
    prospect_name: Mapped[str] = mapped_column(String(200))

    sequence_day: Mapped[int] = mapped_column(Integer)   # 1, 4, or 7
    subject: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    resend_email_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    campaign: Mapped["Campaign"] = relationship(back_populates="emails")  # noqa: F821
    prospect: Mapped["Prospect"] = relationship(back_populates="emails")  # noqa: F821
