import httpx

from app.config import settings

TAVILY_BASE = "https://api.tavily.com"


async def search(query: str, max_results: int = 3) -> list[dict]:
    """
    Run a Tavily search and return a list of result dicts with
    keys: title, url, content (snippet).
    Returns [] on any error so the pipeline degrades gracefully.
    """
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{TAVILY_BASE}/search",
                json={
                    "api_key": settings.tavily_api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_answer": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": r.get("content", ""),
                }
                for r in results
            ]
    except Exception as e:
        print(f"[Tavily] Search failed for '{query}': {e}")
        return []


async def research_prospect(company: str, title: str) -> dict:
    """
    Run two targeted searches for a prospect and return enrichment data.
    """
    news_results = await search(f"{company} news 2026", max_results=3)
    jobs_results = await search(
        f"{company} {title} hiring site:linkedin.com OR site:glassdoor.com",
        max_results=3,
    )

    recent_news = _extract_news_summary(news_results, company)
    job_postings = _extract_job_titles(jobs_results)

    return {
        "recent_news": recent_news,
        "job_postings": job_postings,
    }


def _extract_news_summary(results: list[dict], company: str) -> str | None:
    """Return the first useful news snippet, or None."""
    for r in results:
        content = r.get("content", "").strip()
        if content and company.lower() in content.lower():
            # Trim to one sentence
            sentence = content.split(".")[0].strip()
            if len(sentence) > 20:
                return sentence + "."
    return None


def _extract_job_titles(results: list[dict]) -> list[str]:
    """Extract job title strings from search snippets."""
    import re
    titles = []
    seen = set()
    for r in results:
        content = r.get("title", "") + " " + r.get("content", "")
        # Common job title patterns
        matches = re.findall(
            r"\b(?:Senior |Junior |Lead |Principal )?"
            r"(?:Sales|SDR|Account Executive|BDR|Business Development|"
            r"Revenue|Growth|Marketing|Engineer|Developer|Manager|Director|"
            r"Analyst|Specialist|Consultant|VP|Head)[^\n,|•·]{0,40}",
            content,
        )
        for m in matches:
            m = m.strip()
            if 5 < len(m) < 60 and m not in seen:
                titles.append(m)
                seen.add(m)
        if len(titles) >= 3:
            break
    return titles[:3]
