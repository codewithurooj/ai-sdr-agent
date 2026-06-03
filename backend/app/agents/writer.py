from app.services.groq_service import build_email_prompt, generate_email


async def run(
    prospects: list[dict],
    sender_name: str,
    sender_title: str,
    sender_company: str,
    value_proposition: str,
    email_tone: str,
    on_progress: callable,
) -> list[dict]:
    """
    Writer agent — generates 3 emails per prospect.
    Returns list of {prospect_id, prospect_email, prospect_name, emails: [{day, subject, body}]}.
    """
    results = []

    for prospect in prospects:
        name = f"{prospect['first_name']} {prospect['last_name']}"
        await on_progress(f"Writing emails for {name}...")

        emails = []
        for day in [1, 4, 7]:
            prompt = build_email_prompt(
                prospect=prospect,
                sequence_day=day,
                sender_name=sender_name,
                sender_title=sender_title,
                sender_company=sender_company,
                value_proposition=value_proposition,
                tone=email_tone,
            )
            generated = await generate_email(prompt)

            if generated:
                emails.append({
                    "sequence_day": day,
                    "subject": generated["subject"],
                    "body": generated["body"],
                })
            else:
                # Fallback template when LLM fails
                emails.append({
                    **_fallback_email(prospect, day, sender_name, sender_company),
                    "sequence_day": day,
                })

        results.append({
            "prospect": prospect,
            "emails": emails,
        })

    return results


def _fallback_email(prospect: dict, day: int, sender_name: str, sender_company: str) -> dict:
    """Minimal template used when LLM fails after all retries."""
    name = prospect.get("first_name", "there")
    company = prospect.get("company", "your company")

    templates = {
        1: {
            "subject": f"Quick question about {company}",
            "body": (
                f"{name},\n\n"
                f"Came across {company} and thought there might be a good fit with what we do at "
                f"{sender_company}.\n\n"
                "Would you be open to a 15-minute call this week?\n\n"
                f"{sender_name}"
            ),
        },
        4: {
            "subject": f"Re: Quick question about {company}",
            "body": (
                f"{name},\n\nFollowing up on my note from a few days ago.\n\n"
                f"Happy to share more about how we've helped similar teams. Worth a quick call?\n\n"
                f"{sender_name}"
            ),
        },
        7: {
            "subject": "Closing the loop",
            "body": (
                f"{name},\n\nLast one from me — if the timing isn't right, no worries at all.\n\n"
                f"Feel free to reach out if things change.\n\n{sender_name}"
            ),
        },
    }
    return templates[day]
