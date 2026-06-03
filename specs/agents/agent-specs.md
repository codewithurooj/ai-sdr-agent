# Agent Specifications

## Overview

The pipeline uses **CrewAI** with `Process.sequential` — agents run one after
another, each receiving the previous agent's output. The entire crew is
triggered as a FastAPI background task and takes **30–90 seconds** to complete.

```
CreateCampaignRequest
        │
        ▼
┌─────────────────────┐
│  Researcher Agent   │  Apollo API + Tavily API
│  status: researching│  → List[EnrichedProspect]
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│   Writer Agent      │  Groq API (Llama 3.1 70B)
│  status: writing    │  → List[EmailSequence]
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Sequencer Agent    │  Resend API + DB writes
│  status: sequencing │  → Campaign(status=completed)
└─────────────────────┘
```

---

## Agent 1 — Researcher Agent

### Identity
```
role:      "B2B Prospect Researcher"
goal:      "Find real, reachable decision-makers that match the search query
            and enrich each one with enough context for a hyper-personalized email."
backstory: "You are an expert sales researcher with 10 years of experience
            finding the right people at the right companies. You never guess —
            you only use verified data sources."
```

### Tools Available
| Tool | Source | Free Tier Limit |
|------|--------|-----------------|
| `ApolloSearchTool` | Apollo.io People Search API | 50 credits/month |
| `TavilyResearchTool` | Tavily Search API | 1,000 searches/month |
| `DuckDuckGoTool` | DuckDuckGo (no key needed) | Unlimited |

### Input
Receives the `CreateCampaignRequest` fields:
```python
{
  "campaign_id": "uuid",
  "search_query": "SaaS companies in Dubai hiring sales managers",
  "max_prospects": 10,
  "sender_company": "TechFlow Agency",
  "value_proposition": "We help SaaS companies cut lead research time by 80%"
}
```

### Step-by-Step Behaviour

**Step 1 — Apollo Search**
- Translate `search_query` into Apollo People Search filters:
  - Extract job title keywords → `person_titles[]`
  - Extract location → `person_locations[]`
  - Extract industry keywords → `organization_industry_tag_ids[]`
- Call Apollo `/people/search` with `per_page = max_prospects`
- If Apollo returns < 5 results: fall back to DuckDuckGo company search
  + manual prospect construction from public LinkedIn profiles

**Step 2 — Deduplication**
- Drop any prospect whose email domain matches `sender_company`
- Drop any prospect with `email = null` or `email_status = "invalid"`

**Step 3 — Per-Prospect Enrichment (Tavily)**
For each prospect run **2 Tavily searches**:
1. `"{company_name} news 2026"` → extract recent company news, funding, product launches
2. `"{company_name} {job_title} hiring site:linkedin.com OR site:glassdoor.com"` → extract job postings as buying signals

**Step 4 — Insight Extraction**
For each prospect, the agent synthesises:
- `recent_news`: one sentence summary of the most relevant recent company event
- `job_postings`: list of relevant open roles (max 3)
- `pain_points`: 2–3 pain points inferred from job postings + company stage
- `personalisation_hook`: one opening hook sentence the Writer can use directly

  Hook formula: *[Specific trigger] + [Relevant observation] + [Bridge to value prop]*

  Examples:
  ```
  "Saw that {company} just raised a Series B — congrats! Scaling a sales team
   that fast usually means lead research becomes a bottleneck."

  "Noticed {company} is hiring 3 Sales Development Reps right now — that's a
   strong growth signal."

  "Read about {company}'s expansion into Saudi Arabia last month — new markets
   always bring new prospecting challenges."
  ```

### Output
Returns `List[EnrichedProspect]` — passed directly to Writer Agent.

```python
[
  {
    "first_name": "Sara",
    "last_name": "Al-Mansouri",
    "email": "sara@growthsaas.ae",
    "title": "VP of Sales",
    "company": "GrowthSaaS",
    "company_size": "51-200",
    "country": "UAE",
    "linkedin_url": "https://linkedin.com/in/sara-al-mansouri",
    "recent_news": "GrowthSaaS launched an AI-powered CRM add-on in March 2026.",
    "job_postings": ["Senior SDR", "Sales Ops Manager"],
    "pain_points": [
      "Scaling outbound without increasing headcount",
      "SDR ramp time is too long",
      "Manual prospect research eating into selling time"
    ],
    "personalisation_hook": "Saw that GrowthSaaS is hiring a Sales Ops Manager — "
                            "usually a sign the team is hitting process limits at scale."
  }
]
```

### Error Handling
| Condition | Behaviour |
|-----------|-----------|
| Apollo returns 0 results | Switch entirely to DuckDuckGo + manual enrichment |
| Apollo rate limit hit | Log warning, proceed with however many prospects found |
| Tavily returns no results for a prospect | Skip enrichment, set `recent_news = null`, continue |
| Prospect email bounces (detected post-send) | Handled by Sequencer, not Researcher |

---

## Agent 2 — Writer Agent

### Identity
```
role:      "B2B Cold Email Copywriter"
goal:      "Write three short, personalised, human-sounding emails for each
            prospect that reference their specific situation and lead naturally
            to a reply."
backstory: "You are a world-class cold email copywriter who has written emails
            with 40%+ reply rates. You never use generic openers like 'I hope
            this email finds you well'. Every email you write feels like it
            was written specifically for that one person."
```

### LLM
- **Model:** `llama-3.1-70b-versatile` via Groq API
- **Temperature:** 0.7 (creative but controlled)
- **Max tokens per email:** 300

### Tools Available
| Tool | Purpose |
|------|---------|
| `GroqLLMTool` | Generate email content |

No external API calls — this agent only uses the LLM.

### Input
Receives `List[EnrichedProspect]` + campaign sender context:
```python
{
  "prospects": [ ...EnrichedProspect list from Researcher... ],
  "sender_name": "Ahmed Khan",
  "sender_title": "AI Solutions Consultant",
  "sender_company": "TechFlow Agency",
  "value_proposition": "We help SaaS companies cut lead research time by 80% using AI",
  "email_tone": "professional"
}
```

### Email Sequence Rules

Each prospect gets exactly **3 emails**:

#### Email 1 — Day 1 (First Touch)
- **Purpose:** Open with a personalised hook, introduce the value prop gently, end with a low-friction CTA
- **Length:** 80–120 words
- **Structure:**
  1. Opening line = `personalisation_hook` (rewritten naturally, not copy-pasted)
  2. One sentence connecting their situation to the value prop
  3. One sentence social proof or result (e.g. "We helped a similar SaaS in Riyadh cut research time in half")
  4. CTA: soft ask for a 15-minute call or to reply with interest
- **Must NOT:** Use "I hope this finds you well", "just following up", "quick question", "synergy", "leverage"

#### Email 2 — Day 4 (Follow-up)
- **Purpose:** Add value — share something useful, not just "bumping this up"
- **Length:** 60–90 words
- **Structure:**
  1. Brief reference to Email 1 (one clause, not a whole sentence)
  2. One concrete piece of value: a relevant insight, stat, or short tip related to their pain point
  3. Repeat the CTA from Email 1 but reworded
- **Example value add:** "One thing I've seen work for teams your size: dedicating one agent to research so reps only touch warm leads."

#### Email 3 — Day 7 (Break-up)
- **Purpose:** Create urgency or close the loop gracefully — break-up emails get surprisingly high reply rates
- **Length:** 40–60 words
- **Structure:**
  1. Acknowledge they're busy
  2. One-line offer: "If timing's off, happy to reconnect in Q3."
  3. Soft close: "If this isn't relevant, just say the word and I'll stop reaching out."
- **Tone:** Warm, not passive-aggressive. Never guilt-trip.

### Prompt Template (per prospect)
```
You are writing a {tone} cold email on behalf of {sender_name},
{sender_title} at {sender_company}.

ABOUT THE PROSPECT:
Name: {first_name} {last_name}
Title: {title} at {company} ({company_size} employees, {country})
Personalisation hook: {personalisation_hook}
Recent company news: {recent_news}
Their pain points: {pain_points}

OUR VALUE PROPOSITION:
{value_proposition}

Write Email {sequence_day} of 3 following these rules:
{rules_for_this_day}

Output ONLY valid JSON:
{
  "subject": "...",
  "body": "..."
}
```

### Output
Returns `List[EmailSequence]` — one per prospect × 3 emails each.

```python
[
  {
    "prospect_email": "sara@growthsaas.ae",
    "prospect_id": "uuid",
    "emails": [
      {
        "sequence_day": 1,
        "subject": "GrowthSaaS's Sales Ops hire caught my eye",
        "body": "Sara,\n\nNoticed GrowthSaaS is hiring a Sales Ops Manager — ..."
      },
      {
        "sequence_day": 4,
        "subject": "Re: GrowthSaaS's Sales Ops hire caught my eye",
        "body": "Sara,\n\nOne thing I've seen work for SaaS teams ..."
      },
      {
        "sequence_day": 7,
        "subject": "Closing the loop",
        "body": "Sara,\n\nI know you're busy — totally get it. ..."
      }
    ]
  }
]
```

### Quality Rules (enforced post-generation)
After generation, validate each email:
- [ ] Word count within spec range — if over, ask LLM to shorten
- [ ] Does NOT contain banned phrases (`just following up`, `hope this finds you`, `quick question`, `synergy`, `leverage`, `circle back`, `touch base`)
- [ ] Subject line ≤ 60 characters
- [ ] Body does NOT start with "I" (reader-first, not sender-first)
- [ ] Has exactly one CTA (not two asks in one email)

If validation fails → retry the LLM call with the failure reason appended to prompt. Max 2 retries per email.

### Error Handling
| Condition | Behaviour |
|-----------|-----------|
| Groq rate limit (429) | Exponential backoff: 5s, 15s, 30s. Fail after 3 attempts. |
| LLM returns invalid JSON | Strip markdown fences, retry parse. If still invalid, use fallback template. |
| Validation fails after 2 retries | Accept the email, flag `needs_review = true` in DB |
| Prospect has no `personalisation_hook` | Use company name + title as fallback hook |

---

## Agent 3 — Sequencer Agent

### Identity
```
role:      "Email Sequence Scheduler"
goal:      "Save all generated emails to the database, calculate send dates,
            and schedule them via Resend — ensuring no email is ever sent
            without human approval."
backstory: "You are a meticulous operations specialist who never sends an
            email without confirmation. You set everything up perfectly so
            a human can review and approve with one click."
```

### Tools Available
| Tool | Purpose |
|------|---------|
| `DatabaseTool` | Write prospects + emails to SQLite/PostgreSQL |
| `ResendTool` | Schedule emails via Resend API |

### Input
Receives `List[EmailSequence]` from Writer Agent + campaign metadata:
```python
{
  "campaign_id": "uuid",
  "email_sequences": [ ...Writer Agent output... ],
  "campaign_start_date": "2026-05-20T09:00:00Z"
}
```

### Step-by-Step Behaviour

**Step 1 — Persist Prospects**
- `INSERT` each prospect into `prospects` table
- Link to `campaign_id`

**Step 2 — Persist Emails**
- `INSERT` each email into `emails` table
- Initial status = `"draft"` (NOT scheduled yet)
- Calculate `scheduled_at`:
  - Day 1 email → `campaign_start_date`
  - Day 4 email → `campaign_start_date + 3 days`
  - Day 7 email → `campaign_start_date + 6 days`
- Send times are always **9:00 AM in prospect's local timezone** (inferred from country)

**Step 3 — Update Campaign Status**
- Set `campaign.status = "completed"`
- Set `campaign.prospect_count = len(prospects)`
- Set `campaign.email_count = len(emails)`
- Set `campaign.completed_at = now()`

**Step 4 — Human Review Gate**
All emails stay in `status = "draft"` until the user explicitly approves them
via `POST /emails/{id}/approve`. The Sequencer does NOT auto-send.

Only after a human approves does the Sequencer (via a separate scheduled job,
not during the pipeline run) call Resend to actually send.

### Scheduled Send Job (separate from pipeline)
A background cron job runs every **15 minutes**:
```
SELECT * FROM emails
WHERE status = 'scheduled'
AND scheduled_at <= NOW()
```
For each due email:
1. Call `POST https://api.resend.com/emails`
2. On success: update `email.status = "sent"`, `email.resend_email_id = id`
3. On failure: log error, set `email.status = "draft"`, notify via console log

### Timezone Mapping (country → UTC offset for send time)
```python
TIMEZONE_MAP = {
  "UAE": "Asia/Dubai",           # UTC+4
  "Saudi Arabia": "Asia/Riyadh", # UTC+3
  "Pakistan": "Asia/Karachi",    # UTC+5
  "Jordan": "Asia/Amman",        # UTC+3
  "UK": "Europe/London",
  "USA": "America/New_York",
  # default fallback:
  "DEFAULT": "UTC"
}
```

### Output
Returns updated `Campaign` object:
```python
{
  "id": "uuid",
  "status": "completed",
  "prospect_count": 10,
  "email_count": 30,
  "completed_at": "2026-05-20T09:47:23Z"
}
```

### Error Handling
| Condition | Behaviour |
|-----------|-----------|
| DB write fails | Rollback, set `campaign.status = "failed"`, set `campaign.error = message` |
| Resend API down (during scheduled send) | Retry in next cron cycle (15 min) |
| Prospect country not in timezone map | Use UTC, flag for manual review |

---

## Campaign Status Progression

```
created  →  pending  →  researching  →  writing  →  sequencing  →  completed
                                                                  ↘  failed
```

The FastAPI background task updates `campaign.status` and `campaign.progress_message`
at each transition so the frontend polling loop can show live progress:

| Status | Progress Message Example |
|--------|--------------------------|
| `pending` | "Pipeline is starting..." |
| `researching` | "Researching 5 of 10 prospects..." |
| `writing` | "Writing emails for Sara Al-Mansouri..." |
| `sequencing` | "Saving 30 emails to database..." |
| `completed` | "Done! 10 prospects, 30 emails ready for review." |
| `failed` | "Pipeline failed: Apollo API returned 401. Check your API key." |

---

## CrewAI Implementation Notes

```python
# How to wire the crew in backend/app/agents/crew.py
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer, sequencer],
    tasks=[research_task, writing_task, sequencing_task],
    process=Process.sequential,
    verbose=True,    # logs each agent step — useful for debugging
)

# Each task's output feeds the next via context=[]
writing_task = Task(
    description="...",
    agent=writer,
    context=[research_task],   # Writer receives Researcher's output
)
```

- Set `verbose=True` during development — CrewAI logs every LLM call
- Each agent should have `max_iter=3` to prevent infinite loops
- Use `allow_delegation=False` on all agents — they should not re-assign tasks
