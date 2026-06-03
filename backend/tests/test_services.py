"""Tests for pure (non-I/O) helper functions in services."""
import pytest

from app.services.apollo_service import _map_employee_range, _normalize, _parse_query_to_filters
from app.services.groq_service import _parse_json, _validate_email, build_email_prompt
from app.services.tavily_service import _extract_job_titles, _extract_news_summary


# ── Apollo helpers ────────────────────────────────────────────────────────────

class TestParseQueryToFilters:
    def test_extracts_title_from_query(self):
        result = _parse_query_to_filters("SaaS companies in dubai hiring vp sales")
        assert "VP of Sales" in result["titles"]

    def test_extracts_location_from_query(self):
        result = _parse_query_to_filters("sales managers in Dubai")
        assert "Dubai, UAE" in result["locations"]

    def test_defaults_to_generic_titles_when_no_match(self):
        result = _parse_query_to_filters("companies in Dubai")
        assert "Manager" in result["titles"]

    def test_no_location_when_none_matched(self):
        result = _parse_query_to_filters("VP sales at tech companies")
        assert result["locations"] == []

    def test_multiple_locations(self):
        result = _parse_query_to_filters("sales leaders in Dubai and Saudi Arabia")
        assert any("Dubai" in loc for loc in result["locations"])
        assert any("Saudi" in loc for loc in result["locations"])


class TestMapEmployeeRange:
    def test_small(self):
        assert _map_employee_range(5) == "1-10"

    def test_medium(self):
        assert _map_employee_range(100) == "51-200"

    def test_large(self):
        assert _map_employee_range(10000) == "5001+"

    def test_none(self):
        assert _map_employee_range(None) is None


class TestNormalizeProspect:
    def test_basic_normalization(self):
        raw = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "title": "VP Sales",
            "organization": {"name": "AcmeCorp", "estimated_num_employees": 75},
            "country": "UAE",
            "linkedin_url": "https://linkedin.com/in/alice",
        }
        result = _normalize(raw)
        assert result["first_name"] == "Alice"
        assert result["company"] == "AcmeCorp"
        assert result["company_size"] == "51-200"
        assert result["country"] == "UAE"

    def test_missing_organization(self):
        raw = {"first_name": "Bob", "last_name": "Jones", "email": "", "title": "", "country": ""}
        result = _normalize(raw)
        assert result["company"] == ""


# ── Groq helpers ──────────────────────────────────────────────────────────────

class TestParseJson:
    def test_valid_json(self):
        content = '{"subject": "Hello", "body": "World"}'
        result = _parse_json(content)
        assert result == {"subject": "Hello", "body": "World"}

    def test_strips_markdown_fences(self):
        content = "```json\n{\"subject\": \"Hi\", \"body\": \"There\"}\n```"
        result = _parse_json(content)
        assert result["subject"] == "Hi"

    def test_returns_none_on_invalid_json(self):
        assert _parse_json("not json at all") is None

    def test_returns_none_when_missing_keys(self):
        assert _parse_json('{"subject": "Hi"}') is None


class TestValidateEmail:
    def test_passes_valid_email(self):
        email = {"subject": "Quick intro", "body": "Saw your recent news and thought we'd be a fit."}
        assert _validate_email(email) == []

    def test_flags_subject_too_long(self):
        email = {"subject": "A" * 61, "body": "Fine body."}
        issues = _validate_email(email)
        assert any("subject too long" in i for i in issues)

    def test_flags_body_starting_with_i(self):
        email = {"subject": "Hi", "body": "I wanted to reach out."}
        issues = _validate_email(email)
        assert any("must not start with 'I'" in i for i in issues)

    def test_flags_banned_phrase(self):
        email = {"subject": "Hi", "body": "Just following up on my previous email."}
        issues = _validate_email(email)
        assert any("just following up" in i for i in issues)


class TestBuildEmailPrompt:
    def test_contains_prospect_name(self):
        prospect = {
            "first_name": "Ali", "last_name": "Hassan",
            "title": "VP Sales", "company": "Acme", "company_size": "51-200",
            "country": "UAE", "personalisation_hook": None,
            "recent_news": None, "pain_points": [],
        }
        prompt = build_email_prompt(
            prospect=prospect, sequence_day=1,
            sender_name="Bob", sender_title="CEO", sender_company="StartupX",
            value_proposition="We help sales teams book more meetings.", tone="professional",
        )
        assert "Ali Hassan" in prompt
        assert "Day 1" in prompt or "FIRST TOUCH" in prompt

    def test_day_7_rules_present(self):
        prospect = {
            "first_name": "X", "last_name": "Y",
            "title": "T", "company": "C", "company_size": None,
            "country": "", "personalisation_hook": None,
            "recent_news": None, "pain_points": [],
        }
        prompt = build_email_prompt(
            prospect=prospect, sequence_day=7,
            sender_name="S", sender_title="T", sender_company="Co",
            value_proposition="Value prop here.", tone="casual",
        )
        assert "BREAK-UP" in prompt


# ── Tavily helpers ────────────────────────────────────────────────────────────

class TestExtractNewsSummary:
    def test_extracts_first_relevant_sentence(self):
        results = [{"content": "Acme Corp raised $5M in Series A funding. They plan to expand.", "title": ""}]
        summary = _extract_news_summary(results, "Acme Corp")
        assert summary is not None
        assert "Acme Corp" in summary

    def test_returns_none_when_no_relevant_content(self):
        results = [{"content": "Unrelated news about other company.", "title": ""}]
        summary = _extract_news_summary(results, "Acme Corp")
        assert summary is None

    def test_returns_none_on_empty_results(self):
        assert _extract_news_summary([], "Acme") is None


class TestExtractJobTitles:
    def test_extracts_sales_titles(self):
        results = [{"title": "Sales Manager job at Acme", "content": "We are hiring a Sales Manager and an Account Executive."}]
        titles = _extract_job_titles(results)
        assert len(titles) > 0
        assert any("Sales" in t or "Account" in t for t in titles)

    def test_returns_empty_on_no_matches(self):
        results = [{"title": "Random article", "content": "Nothing relevant here."}]
        titles = _extract_job_titles(results)
        assert isinstance(titles, list)
