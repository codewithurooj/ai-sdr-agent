from app.services import apollo_service, tavily_service

MOCK_PROSPECTS = [
    {
        "first_name": "Omar",
        "last_name": "Al-Rashid",
        "email": "omar.alrashid@nexuscloud.ae",
        "title": "VP of Sales",
        "company": "NexusCloud",
        "company_size": "51-200",
        "country": "UAE",
        "linkedin_url": "https://linkedin.com/in/omar-alrashid",
    },
    {
        "first_name": "Sara",
        "last_name": "Khalid",
        "email": "sara.khalid@growthpilot.io",
        "title": "Head of Sales",
        "company": "GrowthPilot",
        "company_size": "11-50",
        "country": "UAE",
        "linkedin_url": "https://linkedin.com/in/sara-khalid",
    },
    {
        "first_name": "Ahmed",
        "last_name": "Mansoor",
        "email": "ahmed.mansoor@scalex.ae",
        "title": "Sales Manager",
        "company": "ScaleX Technologies",
        "company_size": "51-200",
        "country": "UAE",
        "linkedin_url": "https://linkedin.com/in/ahmed-mansoor",
    },
]

MOCK_ENRICHMENT = [
    {
        "recent_news": "recently raised a $4M seed round to expand their Gulf operations",
        "job_postings": ["Sales Development Representative", "Account Executive", "Revenue Operations Manager"],
    },
    {
        "recent_news": "launched a new AI-powered analytics product last month",
        "job_postings": ["SDR", "Enterprise Account Executive"],
    },
    {
        "recent_news": "expanded into the Saudi market and doubled headcount this quarter",
        "job_postings": ["Sales Manager", "Business Development Representative"],
    },
]


async def run(
    campaign_id: str,
    search_query: str,
    max_prospects: int,
    value_proposition: str,
    on_progress: callable,
) -> list[dict]:
    await on_progress("Searching for prospects via Apollo...")

    raw_prospects = await apollo_service.search_people(search_query, max_prospects)

    if not raw_prospects:
        print("[Researcher] Apollo returned 0 results — using demo prospects.")
        raw_prospects = MOCK_PROSPECTS[:max_prospects]
        use_mock_enrichment = True
    else:
        use_mock_enrichment = False

    enriched = []
    for i, prospect in enumerate(raw_prospects):
        name = f"{prospect['first_name']} {prospect['last_name']}"
        await on_progress(f"Researching {i + 1} of {len(raw_prospects)}: {name}...")

        if use_mock_enrichment:
            enrichment = MOCK_ENRICHMENT[i % len(MOCK_ENRICHMENT)]
        else:
            enrichment = await tavily_service.research_prospect(
                company=prospect["company"],
                title=prospect["title"],
            )

        pain_points = _infer_pain_points(
            job_postings=enrichment["job_postings"],
            company_size=prospect.get("company_size"),
            recent_news=enrichment["recent_news"],
        )

        hook = _build_hook(
            prospect=prospect,
            recent_news=enrichment["recent_news"],
            job_postings=enrichment["job_postings"],
            value_proposition=value_proposition,
        )

        enriched.append({
            **prospect,
            "campaign_id": campaign_id,
            "recent_news": enrichment["recent_news"],
            "job_postings": enrichment["job_postings"],
            "pain_points": pain_points,
            "personalisation_hook": hook,
        })

    return enriched


def _infer_pain_points(
    job_postings: list[str],
    company_size: str | None,
    recent_news: str | None,
) -> list[str]:
    pain_points = []

    if any("sdr" in j.lower() or "sales development" in j.lower() for j in job_postings):
        pain_points.append("Building or scaling an SDR function")

    if any("ops" in j.lower() or "operations" in j.lower() for j in job_postings):
        pain_points.append("Need for better sales process and tooling")

    if any("enterprise" in j.lower() or "account executive" in j.lower() for j in job_postings):
        pain_points.append("Moving upmarket to enterprise deals")

    if company_size in ("11-50", "51-200"):
        pain_points.append("Generating pipeline with a lean team and limited budget")

    if recent_news and any(w in recent_news.lower() for w in ["expand", "launch", "raised", "funding"]):
        pain_points.append("Scaling outbound to support rapid growth")

    return pain_points[:3] if pain_points else ["Improving outbound sales efficiency"]


def _build_hook(
    prospect: dict,
    recent_news: str | None,
    job_postings: list[str],
    value_proposition: str,
) -> str | None:
    company = prospect.get("company", "")
    title = prospect.get("title", "")

    if recent_news:
        return f"Saw that {company} {recent_news.lower().rstrip('.')} — that caught my attention."

    if job_postings:
        role = job_postings[0]
        return f"Noticed {company} is hiring a {role} — usually a sign the team is scaling fast."

    if company:
        return f"Came across {company} while researching {title.lower()} leaders in the region."

    return None
