from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.email_sequence import Email
from app.schemas.email_sequence import EmailResponse, UpdateEmailRequest
from app.services import resend_service

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.get("/{email_id}", response_model=EmailResponse)
async def get_email(email_id: str, db: AsyncSession = Depends(get_db)):
    return await _get_or_404(email_id, db)


@router.patch("/{email_id}", response_model=EmailResponse)
async def update_email(
    email_id: str,
    body: UpdateEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    email = await _get_or_404(email_id, db)
    if email.status not in ("draft", "scheduled"):
        raise HTTPException(status_code=400, detail="Cannot edit an already-sent email")
    if body.subject is not None:
        email.subject = body.subject
    if body.body is not None:
        email.body = body.body
    db.add(email)
    await db.commit()
    await db.refresh(email)
    return email


@router.post("/{email_id}/approve", response_model=EmailResponse)
async def approve_email(email_id: str, db: AsyncSession = Depends(get_db)):
    email = await _get_or_404(email_id, db)
    if email.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft emails can be approved")
    email.status = "scheduled"
    db.add(email)
    await db.commit()
    await db.refresh(email)
    return email


@router.post("/{email_id}/send", response_model=EmailResponse)
async def send_email_now(email_id: str, db: AsyncSession = Depends(get_db)):
    email = await _get_or_404(email_id, db)
    if email.status in ("sent", "opened", "clicked", "replied", "bounced"):
        raise HTTPException(status_code=400, detail="Email already sent")
    if email.status == "discarded":
        raise HTTPException(status_code=400, detail="Email has been discarded")

    resend_id = await resend_service.send_email(
        to_email=email.prospect_email,
        subject=email.subject,
        body=email.body,
        email_id=email.id,
    )

    email.status = "sent"
    email.sent_at = datetime.now(timezone.utc)
    email.resend_email_id = resend_id
    db.add(email)
    await db.commit()
    await db.refresh(email)
    return email


@router.post("/{email_id}/discard", response_model=EmailResponse)
async def discard_email(email_id: str, db: AsyncSession = Depends(get_db)):
    email = await _get_or_404(email_id, db)
    if email.status in ("sent", "opened", "clicked", "replied", "bounced"):
        raise HTTPException(status_code=400, detail="Cannot discard an already-sent email")
    email.status = "discarded"
    db.add(email)
    await db.commit()
    await db.refresh(email)
    return email


async def _get_or_404(email_id: str, db: AsyncSession) -> Email:
    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email
