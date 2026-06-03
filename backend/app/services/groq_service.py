import json
import re

import httpx

from app.config import settings

GROQ_BASE = "https://api.groq.com/openai/v1"

BANNED_PHRASES = [
    "just following up",
    "hope this finds you",
    "hope this email finds you",
    "quick question",
    "synergy",
    "leverage",
    "circle back",
    "touch base",
    "reach out",
    "per my last email",
]


async def generate_email(prompt: str) -> dict | None:
    """
    Call Groq API and return parsed {subject, body} dict.
    Returns None after 2 failed retries.
    """
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{GROQ_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.groq_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.groq_model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                        "max_tokens": 400,
                    },
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = _parse_json(content)
                if parsed:
                    issues = _validate_email(parsed)
                    if not issues:
                        return parsed
                    # Append issues to prompt and retry
                    prompt += f"\n\nPrevious attempt had issues: {', '.join(issues)}. Fix them."
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                import asyncio
                await asyncio.sleep(5 * (attempt + 1))
            else:
                print(f"[Groq] HTTP {e.response.status_code}: {e.response.text}")
                break
        except Exception as e:
            print(f"[Groq] Error on attempt {attempt + 1}: {e}")

    return None


def _parse_json(content: str) -> dict | None:
    """Strip markdown fences and parse JSON."""
    content = re.sub(r"```(?:json)?", "", content).strip().rstrip("`").strip()
    try:
        data = json.loads(content)
        if "subject" in data and "body" in data:
            return data
    except json.JSONDecodeError:
        pass
    return None


def _validate_email(email: dict) -> list[str]:
    """Return a list of validation issues. Empty list = pass."""
    issues = []
    subject = email.get("subject", "")
    body = email.get("body", "")

    if len(subject) > 60:
        issues.append(f"subject too long ({len(subject)} chars, max 60)")

    if body.strip().startswith("I "):
        issues.append("body must not start with 'I'")

    body_lower = body.lower()
    for phrase in BANNED_PHRASES:
        if phrase in body_lower:
            issues.append(f"contains banned phrase: '{phrase}'")

    return issues


def build_email_prompt(
    prospect: dict,
    sequence_day: int,
    sender_name: str,
    sender_title: str,
    sender_company: str,
    value_proposition: str,
    tone: str,
) -> str:
    day_rules = {
        1: (
            "Write a FIRST TOUCH cold email (80-120 words). "
            "Structure: 1) Open with the personalisation hook rewritten naturally. "
            "2) One sentence connecting their situation to the value prop. "
            "3) One brief social proof. "
            "4) Soft CTA: ask for a 15-min call or reply to confirm interest. "
            "Do NOT start the body with 'I'."
        ),
        4: (
            "Write a FOLLOW-UP email (60-90 words). "
            "Briefly reference the first email in one clause. "
            "Add ONE concrete piece of value: an insight, stat, or tip related to their pain. "
            "Repeat the CTA from email 1 but reworded. "
            "Do NOT start the body with 'I'."
        ),
        7: (
            "Write a BREAK-UP email (40-60 words). "
            "Acknowledge they are busy. "
            "Offer to reconnect in Q3 if timing is off. "
            "Soft close: offer to stop if not relevant. "
            "Warm tone — never guilt-trip. "
            "Do NOT start the body with 'I'."
        ),
    }

    return f"""You are writing a {tone} B2B cold email on behalf of {sender_name}, {sender_title} at {sender_company}.

PROSPECT:
Name: {prospect['first_name']} {prospect['last_name']}
Title: {prospect['title']} at {prospect['company']} ({prospect.get('company_size', 'unknown size')}, {prospect.get('country', '')})
Personalisation hook: {prospect.get('personalisation_hook', 'No specific hook available')}
Recent company news: {prospect.get('recent_news', 'None available')}
Pain points: {', '.join(prospect.get('pain_points', []))}

OUR VALUE PROPOSITION:
{value_proposition}

TASK: {day_rules[sequence_day]}

Output ONLY valid JSON with no markdown:
{{"subject": "...", "body": "..."}}"""
