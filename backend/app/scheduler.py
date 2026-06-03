import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models.email_sequence import Email
from app.services import resend_service

logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 60


async def run_scheduler() -> None:
    """Poll for scheduled emails and send any that are due."""
    logger.info("[Scheduler] Started — polling every %ds.", POLL_INTERVAL_SECONDS)
    while True:
        try:
            await _send_due_emails()
        except asyncio.CancelledError:
            logger.info("[Scheduler] Stopped.")
            raise
        except Exception:
            logger.exception("[Scheduler] Error during poll cycle.")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def _send_due_emails() -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Email).where(
                Email.status == "scheduled",
                Email.scheduled_at <= now,
            )
        )
        due = result.scalars().all()

        if not due:
            return

        logger.info("[Scheduler] %d email(s) due for send.", len(due))
        for email in due:
            resend_id = await resend_service.send_email(
                to_email=email.prospect_email,
                subject=email.subject,
                body=email.body,
                email_id=email.id,
            )
            email.status = "sent"
            email.sent_at = now
            email.resend_email_id = resend_id
            db.add(email)
            logger.info("[Scheduler] Sent %s → %s", email.id, email.prospect_email)

        await db.commit()
