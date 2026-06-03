"""Tests for pure helper functions inside agent modules."""
from datetime import datetime, timezone

import pytest
import pytz

from app.agents.researcher import _build_hook, _infer_pain_points
from app.agents.sequencer import _calculate_send_time, _get_timezone


# ── Researcher helpers ────────────────────────────────────────────────────────

class TestInferPainPoints:
    def test_sdr_hiring_detected(self):
        points = _infer_pain_points(
            job_postings=["SDR Manager", "Sales Development Rep"],
            company_size="51-200",
            recent_news=None,
        )
        assert any("SDR" in p or "scaling" in p.lower() for p in points)

    def test_small_company_budget_pain(self):
        points = _infer_pain_points(job_postings=[], company_size="11-50", recent_news=None)
        assert any("lean" in p.lower() or "budget" in p.lower() for p in points)

    def test_funding_news_triggers_growth_pain(self):
        points = _infer_pain_points(job_postings=[], company_size=None, recent_news="Acme Corp raised $10M funding.")
        assert any("scaling" in p.lower() or "growth" in p.lower() for p in points)

    def test_returns_default_when_nothing_matches(self):
        points = _infer_pain_points(job_postings=[], company_size=None, recent_news=None)
        assert points == ["Improving outbound sales efficiency"]

    def test_caps_at_three_pain_points(self):
        points = _infer_pain_points(
            job_postings=["SDR Manager", "Sales Ops", "Account Executive"],
            company_size="11-50",
            recent_news="Acme raised funding.",
        )
        assert len(points) <= 3


class TestBuildHook:
    def test_uses_recent_news_first(self):
        hook = _build_hook(
            prospect={"company": "Acme", "title": "VP Sales"},
            recent_news="announced a new product launch",
            job_postings=["Sales Manager"],
            value_proposition="We book meetings.",
        )
        assert hook is not None
        assert "Acme" in hook
        assert "product launch" in hook

    def test_falls_back_to_job_postings(self):
        hook = _build_hook(
            prospect={"company": "Acme", "title": "VP Sales"},
            recent_news=None,
            job_postings=["Sales Manager"],
            value_proposition="We book meetings.",
        )
        assert hook is not None
        assert "Sales Manager" in hook

    def test_falls_back_to_company_name(self):
        hook = _build_hook(
            prospect={"company": "Acme", "title": "VP Sales"},
            recent_news=None,
            job_postings=[],
            value_proposition="We book meetings.",
        )
        assert hook is not None
        assert "Acme" in hook

    def test_returns_none_when_no_company(self):
        hook = _build_hook(
            prospect={"company": "", "title": ""},
            recent_news=None,
            job_postings=[],
            value_proposition="We book meetings.",
        )
        assert hook is None


# ── Sequencer helpers ─────────────────────────────────────────────────────────

class TestGetTimezone:
    def test_known_country(self):
        tz = _get_timezone("UAE")
        assert tz.zone == "Asia/Dubai"

    def test_known_country_full_name(self):
        tz = _get_timezone("United Kingdom")
        assert tz.zone == "Europe/London"

    def test_unknown_country_returns_utc(self):
        tz = _get_timezone("Narnia")
        assert tz == pytz.UTC


class TestCalculateSendTime:
    def test_day1_is_same_day_9am_local(self):
        start = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        tz = pytz.timezone("Asia/Dubai")  # UTC+4
        result = _calculate_send_time(start, sequence_day=1, tz=tz)
        # 9 AM Dubai = 5 AM UTC
        assert result.hour == 5
        assert result.minute == 0

    def test_day4_is_offset_3_days(self):
        start = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        tz = pytz.timezone("Asia/Dubai")
        result = _calculate_send_time(start, sequence_day=4, tz=tz)
        assert result.day == 4  # June 1 + 3 days = June 4

    def test_day7_is_offset_6_days(self):
        start = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
        tz = pytz.UTC
        result = _calculate_send_time(start, sequence_day=7, tz=tz)
        assert result.day == 7  # June 1 + 6 days = June 7
