import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(120))
    search_query: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    progress_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    max_prospects: Mapped[int] = mapped_column(Integer, default=10)
    prospect_count: Mapped[int] = mapped_column(Integer, default=0)
    email_count: Mapped[int] = mapped_column(Integer, default=0)
    sender_name: Mapped[str] = mapped_column(String(100))
    sender_title: Mapped[str] = mapped_column(String(100))
    sender_company: Mapped[str] = mapped_column(String(100))
    value_proposition: Mapped[str] = mapped_column(String(500))
    email_tone: Mapped[str] = mapped_column(String(20), default="professional")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    prospects: Mapped[list["Prospect"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")  # noqa: F821
    emails: Mapped[list["Email"]] = relationship(back_populates="campaign", cascade="all, delete-orphan")  # noqa: F821
