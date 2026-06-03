from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import researcher, sequencer, writer
from app.models.campaign import Campaign


async def run_pipeline(campaign_id: str, db: AsyncSession) -> None:
    """
    Full agent pipeline: Researcher → Writer → Sequencer.
    Updates campaign.status at each stage.
    Any unhandled exception marks the campaign as failed.
    """
    from sqlalchemy import select

    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        return

    async def on_progress(message: str) -> None:
        campaign.progress_message = message
        db.add(campaign)
        await db.commit()

    try:
        # ── Stage 1: Researcher ─────────────────────────────────────────
        campaign.status = "researching"
        await on_progress("Starting prospect research...")

        enriched_prospects = await researcher.run(
            campaign_id=campaign_id,
            search_query=campaign.search_query,
            max_prospects=campaign.max_prospects,
            value_proposition=campaign.value_proposition,
            on_progress=on_progress,
        )

        if not enriched_prospects:
            await _fail(campaign, db, "Researcher agent found 0 prospects. Try a broader search query.")
            return

        # ── Stage 2: Writer ─────────────────────────────────────────────
        campaign.status = "writing"
        await on_progress(f"Writing emails for {len(enriched_prospects)} prospects...")

        email_sequences = await writer.run(
            prospects=enriched_prospects,
            sender_name=campaign.sender_name,
            sender_title=campaign.sender_title,
            sender_company=campaign.sender_company,
            value_proposition=campaign.value_proposition,
            email_tone=campaign.email_tone,
            on_progress=on_progress,
        )

        # ── Stage 3: Sequencer ──────────────────────────────────────────
        campaign.status = "sequencing"
        await on_progress("Saving emails to database...")

        await sequencer.run(
            campaign=campaign,
            email_sequences=email_sequences,
            db=db,
            on_progress=on_progress,
        )

    except Exception as exc:
        await _fail(campaign, db, str(exc))
        raise


async def _fail(campaign: Campaign, db: AsyncSession, reason: str) -> None:
    campaign.status = "failed"
    campaign.error = reason
    campaign.progress_message = None
    campaign.completed_at = datetime.now(timezone.utc)
    db.add(campaign)
    await db.commit()
