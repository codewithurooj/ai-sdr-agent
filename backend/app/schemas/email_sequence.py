from datetime import datetime
from typing import Literal

from pydantic import BaseModel

EmailStatus = Literal[
    "draft", "scheduled", "sent", "opened",
    "clicked", "replied", "bounced", "discarded"
]
SequenceDay = Literal[1, 4, 7]


class EmailResponse(BaseModel):
    id: str
    campaign_id: str
    prospect_id: str
    prospect_email: str
    prospect_name: str
    sequence_day: SequenceDay
    subject: str
    body: str
    status: EmailStatus
    resend_email_id: str | None
    scheduled_at: datetime | None
    sent_at: datetime | None
    opened_at: datetime | None
    replied_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateEmailRequest(BaseModel):
    subject: str | None = None
    body: str | None = None


class ProspectEmailGroup(BaseModel):
    prospect: "ProspectResponse"  # noqa: F821
    emails: list[EmailResponse]


class CampaignEmailsResponse(BaseModel):
    campaign_id: str
    grouped_by_prospect: list[ProspectEmailGroup]


# Resolve forward ref
from app.schemas.prospect import ProspectResponse  # noqa: E402
ProspectEmailGroup.model_rebuild()
