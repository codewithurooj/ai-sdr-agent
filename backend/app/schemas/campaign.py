from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CampaignStatus = Literal["pending", "researching", "writing", "sequencing", "completed", "failed"]
EmailTone = Literal["professional", "casual", "direct"]


class CreateCampaignRequest(BaseModel):
    name: str = Field(..., max_length=120)
    search_query: str = Field(..., min_length=10, max_length=300)
    max_prospects: int = Field(default=10, ge=1, le=50)
    sender_name: str
    sender_title: str
    sender_company: str
    value_proposition: str = Field(..., min_length=20, max_length=500)
    email_tone: EmailTone = "professional"


class CampaignResponse(BaseModel):
    id: str
    name: str
    search_query: str
    status: CampaignStatus
    progress_message: str | None
    max_prospects: int
    prospect_count: int
    email_count: int
    sender_name: str
    sender_title: str
    sender_company: str
    value_proposition: str
    email_tone: EmailTone
    error: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    items: list[CampaignResponse]
    total: int
    page: int
    limit: int


class CampaignStats(BaseModel):
    campaign_id: str
    total_prospects: int
    total_emails: int
    emails_sent: int
    emails_opened: int
    emails_replied: int
    emails_bounced: int
    open_rate: float
    reply_rate: float
