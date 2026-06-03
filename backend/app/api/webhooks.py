from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.email_sequence import Email

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# Maps Resend event type → (Email.status, timestamp field)
EVENT_MAP = {
    "email.sent":      ("sent",    "sent_at"),
    "email.opened":    ("opened",  "opened_at"),
    "email.clicked":   ("clicked", "opened_at"),
    "email.bounced":   ("bounced", None),
    "email.complained":("bounced", None),
}


@router.post("/resend", status_code=200)
async def resend_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        return {"ok": False, "detail": "Invalid JSON"}

    event_type = payload.get("type", "")
    mapping = EVENT_MAP.get(event_type)
    if not mapping:
        return {"ok": True, "detail": "Event type not tracked"}

    new_status, ts_field = mapping
    resend_email_id = payload.get("data", {}).get("email_id")
    if not resend_email_id:
        return {"ok": False, "detail": "Missing email_id in payload"}

    result = await db.execute(
        select(Email).where(Email.resend_email_id == resend_email_id)
    )
    email = result.scalar_one_or_none()
    if not email:
        return {"ok": True, "detail": "Email not found in DB (may be from another system)"}

    # Only advance status — never go backwards
    STATUS_ORDER = ["draft", "scheduled", "sent", "opened", "clicked", "replied", "bounced"]
    current_idx = STATUS_ORDER.index(email.status) if email.status in STATUS_ORDER else 0
    new_idx = STATUS_ORDER.index(new_status) if new_status in STATUS_ORDER else 0

    if new_idx > current_idx:
        email.status = new_status
        if ts_field:
            setattr(email, ts_field, datetime.now(timezone.utc))
        db.add(email)
        await db.commit()

    return {"ok": True}


@router.post("/inbound-reply", status_code=200)
async def inbound_reply_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Receives inbound email notifications (from Resend Inbound or a forwarding service).
    Expects a reply-to address of the form reply+{email_id}@{domain} in the 'to' field.
    Sets the email status to 'replied' when found.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"ok": False, "detail": "Invalid JSON"}

    to_addresses = payload.get("to", [])
    if isinstance(to_addresses, str):
        to_addresses = [to_addresses]

    email_id = None
    for addr in to_addresses:
        local = addr.split("@")[0] if "@" in addr else ""
        if local.startswith("reply+"):
            email_id = local[len("reply+"):]
            break

    if not email_id:
        return {"ok": False, "detail": "No reply+{id} address found in 'to' field"}

    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()
    if not email:
        return {"ok": True, "detail": "Email not found — may belong to another system"}

    STATUS_ORDER = ["draft", "scheduled", "sent", "opened", "clicked", "replied", "bounced"]
    current_idx = STATUS_ORDER.index(email.status) if email.status in STATUS_ORDER else 0
    replied_idx = STATUS_ORDER.index("replied")

    if replied_idx > current_idx:
        email.status = "replied"
        email.replied_at = datetime.now(timezone.utc)
        db.add(email)
        await db.commit()

    return {"ok": True}
