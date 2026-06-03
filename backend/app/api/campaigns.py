from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.crew import run_pipeline
from app.db.database import get_db
from app.models.campaign import Campaign
from app.models.email_sequence import Email
from app.models.prospect import Prospect
from app.schemas.campaign import (
    CampaignListResponse,
    CampaignResponse,
    CampaignStats,
    CreateCampaignRequest,
)
from app.schemas.email_sequence import CampaignEmailsResponse, ProspectEmailGroup
from app.schemas.prospect import ProspectListResponse, ProspectResponse

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


@router.post("", response_model=CampaignResponse, status_code=202)
async def create_campaign(
    body: CreateCampaignRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    campaign = Campaign(
        name=body.name,
        search_query=body.search_query,
        max_prospects=body.max_prospects,
        sender_name=body.sender_name,
        sender_title=body.sender_title,
        sender_company=body.sender_company,
        value_proposition=body.value_proposition,
        email_tone=body.email_tone,
        status="pending",
        progress_message="Pipeline is starting...",
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    background_tasks.add_task(run_pipeline, campaign.id, db)
    return campaign


@router.get("", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Campaign)
    if status:
        q = q.where(Campaign.status == status)
    q = q.order_by(Campaign.created_at.desc())

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    q = q.offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    campaigns = result.scalars().all()

    return CampaignListResponse(items=campaigns, total=total, page=page, limit=limit)


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    campaign = await _get_or_404(campaign_id, db)
    return campaign


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: str, db: AsyncSession = Depends(get_db)):
    campaign = await _get_or_404(campaign_id, db)
    await db.delete(campaign)
    await db.commit()


@router.get("/{campaign_id}/prospects", response_model=ProspectListResponse)
async def get_campaign_prospects(
    campaign_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    await _get_or_404(campaign_id, db)

    q = select(Prospect).where(Prospect.campaign_id == campaign_id)
    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    q = q.offset((page - 1) * limit).limit(limit)
    result = await db.execute(q)
    prospects = result.scalars().all()

    return ProspectListResponse(items=prospects, total=total, page=page, limit=limit)


@router.get("/{campaign_id}/emails", response_model=CampaignEmailsResponse)
async def get_campaign_emails(
    campaign_id: str,
    prospect_id: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    await _get_or_404(campaign_id, db)

    prospect_q = select(Prospect).where(Prospect.campaign_id == campaign_id)
    if prospect_id:
        prospect_q = prospect_q.where(Prospect.id == prospect_id)
    prospects_result = await db.execute(prospect_q)
    prospects = prospects_result.scalars().all()

    email_q = select(Email).where(Email.campaign_id == campaign_id)
    if prospect_id:
        email_q = email_q.where(Email.prospect_id == prospect_id)
    email_q = email_q.order_by(Email.prospect_id, Email.sequence_day)
    emails_result = await db.execute(email_q)
    all_emails = emails_result.scalars().all()

    emails_by_prospect: dict[str, list] = {}
    for e in all_emails:
        emails_by_prospect.setdefault(e.prospect_id, []).append(e)

    groups = [
        ProspectEmailGroup(
            prospect=ProspectResponse.model_validate(p),
            emails=emails_by_prospect.get(p.id, []),
        )
        for p in prospects
    ]

    return CampaignEmailsResponse(campaign_id=campaign_id, grouped_by_prospect=groups)


@router.get("/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(campaign_id: str, db: AsyncSession = Depends(get_db)):
    await _get_or_404(campaign_id, db)

    result = await db.execute(select(Email).where(Email.campaign_id == campaign_id))
    emails = result.scalars().all()

    total = len(emails)
    sent = sum(1 for e in emails if e.status in ("sent", "opened", "clicked", "replied", "bounced"))
    opened = sum(1 for e in emails if e.status in ("opened", "clicked", "replied"))
    replied = sum(1 for e in emails if e.status == "replied")
    bounced = sum(1 for e in emails if e.status == "bounced")

    return CampaignStats(
        campaign_id=campaign_id,
        total_prospects=(await db.execute(
            select(func.count(Prospect.id)).where(Prospect.campaign_id == campaign_id)
        )).scalar_one(),
        total_emails=total,
        emails_sent=sent,
        emails_opened=opened,
        emails_replied=replied,
        emails_bounced=bounced,
        open_rate=round(opened / sent * 100, 1) if sent else 0.0,
        reply_rate=round(replied / sent * 100, 1) if sent else 0.0,
    )


async def _get_or_404(campaign_id: str, db: AsyncSession) -> Campaign:
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
