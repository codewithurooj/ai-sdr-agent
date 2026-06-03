"""Integration tests for API routes using an in-memory SQLite DB."""
import pytest
from unittest.mock import AsyncMock, patch

CAMPAIGN_PAYLOAD = {
    "name": "Dubai SDR Campaign",
    "search_query": "SaaS companies in Dubai hiring sales managers",
    "max_prospects": 5,
    "sender_name": "Alice",
    "sender_title": "CEO",
    "sender_company": "AcmeCorp",
    "value_proposition": "We help B2B sales teams book 3x more meetings with less effort.",
    "email_tone": "professional",
}


# ── Health ────────────────────────────────────────────────────────────────────

async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "database" in data["services"]


# ── Campaigns — create ────────────────────────────────────────────────────────

async def test_create_campaign_returns_202(client):
    with patch("app.api.campaigns.run_pipeline", new_callable=AsyncMock):
        response = await client.post("/campaigns", json=CAMPAIGN_PAYLOAD)
    assert response.status_code == 202
    data = response.json()
    assert data["name"] == "Dubai SDR Campaign"
    assert data["status"] == "pending"
    assert data["prospect_count"] == 0
    assert "id" in data


async def test_create_campaign_rejects_short_value_prop(client):
    payload = {**CAMPAIGN_PAYLOAD, "value_proposition": "Too short."}
    with patch("app.api.campaigns.run_pipeline", new_callable=AsyncMock):
        response = await client.post("/campaigns", json=payload)
    assert response.status_code == 422


async def test_create_campaign_rejects_short_query(client):
    payload = {**CAMPAIGN_PAYLOAD, "search_query": "short"}
    with patch("app.api.campaigns.run_pipeline", new_callable=AsyncMock):
        response = await client.post("/campaigns", json=payload)
    assert response.status_code == 422


# ── Campaigns — list ──────────────────────────────────────────────────────────

async def test_list_campaigns_empty(client):
    response = await client.get("/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_campaigns_returns_created(client):
    with patch("app.api.campaigns.run_pipeline", new_callable=AsyncMock):
        await client.post("/campaigns", json=CAMPAIGN_PAYLOAD)
    response = await client.get("/campaigns")
    assert response.status_code == 200
    assert response.json()["total"] == 1


# ── Campaigns — get ───────────────────────────────────────────────────────────

async def test_get_campaign_not_found(client):
    response = await client.get("/campaigns/nonexistent-id")
    assert response.status_code == 404


async def test_get_campaign_found(client):
    with patch("app.api.campaigns.run_pipeline", new_callable=AsyncMock):
        created = (await client.post("/campaigns", json=CAMPAIGN_PAYLOAD)).json()
    response = await client.get(f"/campaigns/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


# ── Campaigns — delete ────────────────────────────────────────────────────────

async def test_delete_campaign(client):
    with patch("app.api.campaigns.run_pipeline", new_callable=AsyncMock):
        created = (await client.post("/campaigns", json=CAMPAIGN_PAYLOAD)).json()
    response = await client.delete(f"/campaigns/{created['id']}")
    assert response.status_code == 204
    # Confirm it's gone
    assert (await client.get(f"/campaigns/{created['id']}")).status_code == 404


async def test_delete_campaign_not_found(client):
    response = await client.delete("/campaigns/nonexistent-id")
    assert response.status_code == 404


# ── Webhooks — Resend outbound events ─────────────────────────────────────────

async def test_resend_webhook_unknown_event(client):
    payload = {"type": "email.unknown", "data": {"email_id": "abc"}}
    response = await client.post("/webhooks/resend", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is True


async def test_resend_webhook_missing_email_id(client):
    payload = {"type": "email.sent", "data": {}}
    response = await client.post("/webhooks/resend", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is False


async def test_resend_webhook_email_not_found(client):
    payload = {"type": "email.sent", "data": {"email_id": "no-such-resend-id"}}
    response = await client.post("/webhooks/resend", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is True  # gracefully ignored


# ── Webhooks — inbound reply ──────────────────────────────────────────────────

async def test_inbound_reply_no_reply_address(client):
    payload = {"from": "sender@example.com", "to": ["outreach@example.com"]}
    response = await client.post("/webhooks/inbound-reply", json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is False


async def test_inbound_reply_email_not_found(client):
    payload = {"from": "sender@example.com", "to": ["reply+nonexistent-id@mail.example.com"]}
    response = await client.post("/webhooks/inbound-reply", json=payload)
    assert response.status_code == 200
    # gracefully ignored
    assert response.json()["ok"] is True
