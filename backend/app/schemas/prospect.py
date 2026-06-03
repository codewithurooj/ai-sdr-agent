from datetime import datetime

from pydantic import BaseModel, EmailStr


class ProspectResponse(BaseModel):
    id: str
    campaign_id: str
    first_name: str
    last_name: str
    email: EmailStr
    title: str
    company: str
    company_size: str | None
    country: str
    linkedin_url: str | None
    recent_news: str | None
    job_postings: list[str]
    pain_points: list[str]
    personalisation_hook: str | None
    enriched_at: datetime

    model_config = {"from_attributes": True}


class ProspectListResponse(BaseModel):
    items: list[ProspectResponse]
    total: int
    page: int
    limit: int
