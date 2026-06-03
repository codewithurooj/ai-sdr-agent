# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI SDR (Sales Development Representative) Agent** — a multi-agent system that autonomously researches prospects, writes hyper-personalized outreach emails, and schedules follow-up sequences. Built entirely on free-tier services for portfolio/demo purposes; production upgrades are funded by the client.

**Core value proposition:** Input a target (e.g. "SaaS companies in Dubai hiring sales managers") → system finds prospects, researches each one, writes 3 personalized emails, and queues a Day 1 / Day 4 / Day 7 send sequence.

---

## Development Approach: Spec-Driven Development

Build order is strictly:
1. **Write specs first** (`specs/`) — API contracts, agent I/O, data models, UI screens
2. **Build with mocks** (`mocks/`) — frontend and backend work against mock data
3. **Integrate real services** — swap mocks for live Apollo, Tavily, Groq, Resend calls

Never skip to implementation before the relevant spec exists.

---

## Tech Stack (All Free Tier)

| Layer | Technology |
|-------|-----------|
| LLM | Groq API — `llama-3.1-70b-versatile` (free tier) |
| Agent Framework | CrewAI (open source) |
| Web Research | Tavily API (free tier) |
| Prospect Data | Apollo.io REST API (free tier, 50 credits/month) |
| Email Sending | Resend API (3,000 emails/month free) or Gmail SMTP |
| Backend | FastAPI + Python 3.12 |
| Database | SQLite (dev) → PostgreSQL (prod) via SQLAlchemy |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui |
| Deployment | Vercel (frontend) + Railway free tier (backend) |

---

## Commands

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload  # runs on http://localhost:8000
```

### Run a single backend test
```bash
cd backend
pytest tests/test_agents.py::test_researcher_agent -v
```

### Frontend
```bash
cd frontend
npm install
npm run dev     # runs on http://localhost:3000
npm run build
npm run lint
```

### Environment
Copy `.env.example` to `.env` and fill in keys before running either service.

---

## Architecture

### Agent Pipeline (3 agents, sequential)

```
User Input (search query)
        ↓
[Researcher Agent]
  - Calls Apollo.io API → raw prospect list
  - Calls Tavily → recent news, job postings, LinkedIn data per prospect
  - Output: enriched_prospects[]
        ↓
[Writer Agent]
  - Receives enriched prospect data
  - Calls Groq/Llama → generates 3 emails per prospect (Day 1, 4, 7)
  - Each email references specific prospect intel (news, role, company trigger)
  - Output: email_sequences[]
        ↓
[Sequencer Agent]
  - Stores sequences in DB
  - Schedules sends via Resend API
  - Tracks open/reply status via webhooks
  - Output: campaign record with status
```

All agents are defined in `backend/app/agents/`. Each agent is a CrewAI `Agent` with specific `tools`, `goal`, and `backstory`. The pipeline is a CrewAI `Crew` with `Process.sequential`.

### Backend Structure
```
backend/app/
├── main.py              # FastAPI app, router registration, CORS
├── config.py            # Settings loaded from .env via pydantic-settings
├── api/                 # Route handlers (thin — delegate to services)
│   ├── campaigns.py     # POST /campaigns, GET /campaigns/{id}
│   ├── prospects.py     # GET /prospects, POST /prospects/search
│   └── emails.py        # GET /emails/{campaign_id}, POST /emails/{id}/send
├── agents/              # CrewAI agent definitions
│   ├── researcher.py    # ProspectResearcherAgent + ApolloTool + TavilyTool
│   ├── writer.py        # EmailWriterAgent + GroqLLM
│   └── sequencer.py     # SequencerAgent + ResendTool
├── models/              # SQLAlchemy ORM models
│   ├── prospect.py
│   ├── campaign.py
│   └── email_sequence.py
├── services/            # External API integrations
│   ├── apollo_service.py
│   ├── tavily_service.py
│   ├── groq_service.py
│   └── resend_service.py
└── db/
    └── database.py      # SQLAlchemy engine + session factory
```

### Frontend Structure
```
frontend/
├── app/
│   ├── page.tsx              # Dashboard home — campaign list + stats
│   ├── campaigns/
│   │   ├── page.tsx          # All campaigns
│   │   ├── new/page.tsx      # Create campaign (search input → trigger pipeline)
│   │   └── [id]/page.tsx     # Campaign detail — prospects + email previews
│   └── prospects/
│       └── [id]/page.tsx     # Single prospect + all emails for them
├── components/
│   ├── campaigns/
│   │   ├── CampaignCard.tsx
│   │   ├── CampaignForm.tsx  # Search query input + settings
│   │   └── EmailPreview.tsx  # Shows all 3 emails per prospect
│   └── prospects/
│       └── ProspectTable.tsx
└── lib/
    ├── api-client.ts         # All fetch calls to backend — single source of truth
    └── types.ts              # TypeScript types mirroring backend models
```

### Data Flow
- Frontend talks **only** to `lib/api-client.ts` — never raw fetch calls in components
- Backend routes are **thin** — they validate input and delegate to `services/`
- Agents are invoked **async** via FastAPI background tasks (not blocking the HTTP response)
- Frontend polls `GET /campaigns/{id}` every 3 seconds until status = `completed`

---

## Specs Location

All contracts live in `specs/` — read these before implementing any feature:

| File | Covers |
|------|--------|
| `specs/api/openapi.yaml` | All API endpoints, request/response shapes |
| `specs/agents/agent-specs.md` | Each agent's goal, tools, inputs, outputs |
| `specs/data-models/` | TypeScript interfaces for all entities |
| `specs/ui/screens.md` | Every screen's purpose, components, and data requirements |

---

## Key Constraints

- **Free tier limits:** Apollo = 50 credits/month, Resend = 3,000 emails/month, Groq = rate-limited. Mock data is used in tests and demos to avoid burning quota.
- **No LinkedIn direct API.** Prospect enrichment uses Apollo (which aggregates LinkedIn data legally) + Tavily web search.
- **SQLite in dev, PostgreSQL in prod.** SQLAlchemy handles both — never write raw SQL.
- **Async pipeline.** The agent crew run takes 30-90 seconds. Always use background tasks + polling, never block an HTTP request.
