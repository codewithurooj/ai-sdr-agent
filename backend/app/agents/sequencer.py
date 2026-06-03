from datetime import datetime, timedelta, timezone

import pytz

from app.models.campaign import Campaign
from app.models.email_sequence import Email
from app.models.prospect import Prospect

TIMEZONE_MAP = {
    "UAE": "Asia/Dubai",
    "United Arab Emirates": "Asia/Dubai",
    "Saudi Arabia": "Asia/Riyadh",
    "Pakistan": "Asia/Karachi",
    "Jordan": "Asia/Amman",
    "UK": "Europe/London",
    "United Kingdom": "Europe/London",
    "USA": "America/New_York",
    "United States": "America/New_York",
}

SEQUENCE_DAY_OFFSETS = {1: 0, 4: 3, 7: 6}  # days after campaign start


async def run(
    campaign: Campaign,
    email_sequences: list[dict],
    db,
    on_progress: callable,
) -> None:
    """
    Sequencer agent — persists prospects and emails, calculates send dates.
    All emails saved with status='draft'. Human approves before any send.
    """
    await on_progress("Saving prospects and emails to database...")

    start_date = datetime.now(timezone.utc)
    prospect_count = 0
    email_count = 0

    for seq in email_sequences:
        prospect_data = seq["prospect"]
        prospect_emails = seq["emails"]

        # Persist prospect
        prospect = Prospect(
            campaign_id=campaign.id,
            first_name=prospect_data["first_name"],
            last_name=prospect_data["last_name"],
            email=prospect_data["email"],
            title=prospect_data["title"],
            company=prospect_data["company"],
            company_size=prospect_data.get("company_size"),
            country=prospect_data.get("country", ""),
            linkedin_url=prospect_data.get("linkedin_url"),
            recent_news=prospect_data.get("recent_news"),
            job_postings=prospect_data.get("job_postings", []),
            pain_points=prospect_data.get("pain_points", []),
            personalisation_hook=prospect_data.get("personalisation_hook"),
        )
        db.add(prospect)
        await db.flush()  # get prospect.id before creating emails

        prospect_name = f"{prospect.first_name} {prospect.last_name}"
        tz = _get_timezone(prospect.country)

        for email_data in prospect_emails:
            day = email_data["sequence_day"]
            scheduled_at = _calculate_send_time(start_date, day, tz)

            email = Email(
                campaign_id=campaign.id,
                prospect_id=prospect.id,
                prospect_email=prospect.email,
                prospect_name=prospect_name,
                sequence_day=day,
                subject=email_data["subject"],
                body=email_data["body"],
                status="draft",
                scheduled_at=scheduled_at,
            )
            db.add(email)
            email_count += 1

        prospect_count += 1

    # Update campaign counters
    campaign.prospect_count = prospect_count
    campaign.email_count = email_count
    campaign.status = "completed"
    campaign.completed_at = datetime.now(timezone.utc)
    campaign.progress_message = (
        f"Done! {prospect_count} prospects, {email_count} emails ready for review."
    )
    db.add(campaign)
    await db.commit()


def _get_timezone(country: str) -> pytz.BaseTzInfo:
    tz_name = TIMEZONE_MAP.get(country, "UTC")
    try:
        return pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        return pytz.UTC


def _calculate_send_time(
    start: datetime, sequence_day: int, tz: pytz.BaseTzInfo
) -> datetime:
    """Return 9:00 AM prospect-local-time on the correct offset day, as UTC."""
    offset_days = SEQUENCE_DAY_OFFSETS.get(sequence_day, 0)
    local_9am = tz.localize(
        datetime(
            start.year, start.month, start.day, 9, 0, 0
        ) + timedelta(days=offset_days)
    )
    return local_9am.astimezone(timezone.utc)
