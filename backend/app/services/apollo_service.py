import httpx

from app.config import settings

APOLLO_BASE = "https://api.apollo.io/v1"


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "x-api-key": settings.apollo_api_key,
    }


async def search_people(search_query: str, max_results: int = 10) -> list[dict]:
    """
    Translate a natural language search_query into Apollo People Search filters
    and return raw prospect records.
    Returns an empty list (not an exception) on API errors so the pipeline
    can fall back to DuckDuckGo enrichment.
    """
    filters = _parse_query_to_filters(search_query)

    payload = {
        "q_organization_domains": [],
        "page": 1,
        "per_page": max_results,
        "person_titles": filters.get("titles", []),
        "person_locations": filters.get("locations", []),
        "contact_email_status": ["verified", "guessed"],
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{APOLLO_BASE}/mixed_people/search",
                json=payload,
                headers=_headers(),
            )
            resp.raise_for_status()
            data = resp.json()
            return [_normalize(p) for p in data.get("people", [])]
    except httpx.HTTPStatusError as e:
        print(f"[Apollo] HTTP error {e.response.status_code}: {e.response.text}")
        return []
    except Exception as e:
        print(f"[Apollo] Unexpected error: {e}")
        return []


def _parse_query_to_filters(query: str) -> dict:
    """
    Lightweight keyword extraction from the natural language search query.
    A full implementation would use an LLM; this covers common patterns
    for the free-tier demo without burning Groq calls.
    """
    query_lower = query.lower()

    # Title keywords
    title_keywords = {
        "vp sales": ["VP of Sales", "VP Sales"],
        "head of sales": ["Head of Sales"],
        "cro": ["Chief Revenue Officer", "CRO"],
        "sales manager": ["Sales Manager", "Director of Sales"],
        "cto": ["CTO", "Chief Technology Officer"],
        "ceo": ["CEO", "Chief Executive Officer", "Founder"],
        "head of marketing": ["Head of Marketing", "VP Marketing"],
    }
    titles = []
    for kw, labels in title_keywords.items():
        if kw in query_lower:
            titles.extend(labels)
    if not titles:
        titles = ["Manager", "Director", "VP", "Head", "Chief"]

    # Location keywords
    location_map = {
        "dubai": ["Dubai, UAE"],
        "uae": ["United Arab Emirates"],
        "london": ["London, England"],
        "riyadh": ["Riyadh, Saudi Arabia"],
        "saudi": ["Saudi Arabia"],
        "pakistan": ["Pakistan"],
        "karachi": ["Karachi, Pakistan"],
        "jordan": ["Jordan"],
        "amman": ["Amman, Jordan"],
    }
    locations = []
    for kw, labels in location_map.items():
        if kw in query_lower:
            locations.extend(labels)

    return {"titles": titles, "locations": locations}


def _normalize(raw: dict) -> dict:
    """Map Apollo API response fields to our internal prospect shape."""
    org = raw.get("organization") or {}
    return {
        "first_name": raw.get("first_name", ""),
        "last_name": raw.get("last_name", ""),
        "email": raw.get("email", ""),
        "title": raw.get("title", ""),
        "company": org.get("name", raw.get("organization_name", "")),
        "company_size": _map_employee_range(org.get("estimated_num_employees")),
        "country": raw.get("country", ""),
        "linkedin_url": raw.get("linkedin_url"),
    }


def _map_employee_range(count: int | None) -> str | None:
    if count is None:
        return None
    if count <= 10:
        return "1-10"
    if count <= 50:
        return "11-50"
    if count <= 200:
        return "51-200"
    if count <= 500:
        return "201-500"
    if count <= 1000:
        return "501-1000"
    if count <= 5000:
        return "1001-5000"
    return "5001+"
