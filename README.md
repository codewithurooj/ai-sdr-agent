# AI SDR Agent

An autonomous Sales Development Representative powered by AI. Input a target audience — the system finds real prospects, researches each one, writes three personalised outreach emails per person, and queues a Day 1 / Day 4 / Day 7 send sequence. No manual work required.

Built entirely on free-tier APIs for portfolio and demo purposes.

---

## What it does

```
"SaaS companies in Dubai hiring sales managers"
        │
        ▼
┌─────────────────────┐
│   Researcher Agent  │  Finds prospects via Apollo · Enriches with Tavily web search
└────────┬────────────┘  (recent news, job postings, company signals)
         │
         ▼
┌─────────────────────┐
│    Writer Agent     │  Calls Groq / Llama 3.1 70B · Generates 3 emails per prospect
└────────┬────────────┘  (Day 1 intro · Day 4 follow-up · Day 7 breakup)
         │
         ▼
┌─────────────────────┐
│  Sequencer Agent    │  Saves to database · Schedules sends via Gmail SMTP
└─────────────────────┘  Tracks status per email (draft → approved → sent)
```

Each email references a specific personalisation hook — recent funding, new product launch, active hiring — rather than generic templates.

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Groq API — `llama-3.1-70b-versatile` |
| Prospect data | Apollo.io REST API |
| Web research | Tavily Search API |
| Email sending | Gmail SMTP (no custom domain needed) |
| Backend | FastAPI + Python 3.12 · async SQLAlchemy |
| Database | SQLite (dev) → PostgreSQL (prod) |
| Frontend | Next.js 16 · TypeScript · Tailwind CSS v4 |
| Deployment | Vercel (frontend) + Railway (backend) |

---

## Features

- **One-input campaign creation** — describe your target in plain English
- **Real prospect search** — Apollo.io people search with job title, industry, and location filters
- **Automatic enrichment** — Tavily pulls recent news and open job postings for each company
- **Hyper-personalised emails** — Groq/Llama writes subject + body referencing specific company signals
- **3-email sequences** — Day 1 intro, Day 4 follow-up, Day 7 breakup, all generated automatically
- **Approve before sending** — review and approve drafts individually or all at once
- **Live pipeline progress** — real-time status updates while the agents run
- **Demo mode** — mock prospects automatically used when Apollo free tier returns no results
- **Delete campaigns** — remove failed or unwanted campaigns from the dashboard

---

## Prerequisites

- Python 3.12+
- Node.js 18+
- A Gmail account with [2-Step Verification enabled](https://myaccount.google.com/security)
- Free API keys (all free tier, no credit card required for basic use):

| Service | Where to get it | Free limit |
|---|---|---|
| [Groq](https://console.groq.com) | console.groq.com → API Keys | Rate-limited, generous |
| [Apollo.io](https://app.apollo.io) | app.apollo.io → Settings → API | 50 credits/month |
| [Tavily](https://app.tavily.com) | app.tavily.com → API Keys | 1,000 searches/month |
| Gmail App Password | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) | Free |

---

## Getting started

### 1. Clone the repo

```bash
git clone https://github.com/codewithurooj/ai-sdr-agent.git
cd ai-sdr-agent
```

### 2. Set up environment variables

```bash
cp .env.example backend/.env
```

Open `backend/.env` and fill in your keys:

```env
GROQ_API_KEY=gsk_...
APOLLO_API_KEY=...
TAVILY_API_KEY=tvly-...
GMAIL_USER=you@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx   # 16-char App Password, not your Gmail password
DATABASE_URL=sqlite+aiosqlite:///./sdr_agent.db
CORS_ORIGINS=http://localhost:3000
```

> **Gmail App Password**: Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords), create a new app called "AI SDR", and paste the 16-character password above. This is separate from your Gmail login password.

Create the frontend env file:

```bash
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
```

### 3. Run the backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000**. Interactive API docs at **http://localhost:8000/docs**.

### 4. Run the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000**.

---

## How to use

1. Open **http://localhost:3000**
2. Click **New Campaign** in the sidebar
3. Fill in the form:
   - **Campaign name** — e.g. "Dubai SaaS Outreach June 2026"
   - **Search query** — e.g. "SaaS companies in UAE hiring sales managers"
   - **Your name and company** — appears in the email signatures
   - **Value proposition** — one sentence about what you offer
   - **Tone** — professional / conversational / bold
4. Click **Launch Campaign**
5. Watch the pipeline run in real time (takes 30–90 seconds)
6. Open the **Emails** tab, review drafts, click **Approve All Drafts** to queue sends
7. Approved emails are sent via Gmail on schedule (Day 1 immediately, Day 4 and Day 7 scheduled)

> **Apollo free tier note:** Apollo's free plan restricts the people search API. When it returns 0 results, the system automatically switches to built-in demo prospects (3 realistic UAE SaaS profiles) so the full pipeline still runs end-to-end.

---

## Project structure

```
ai-sdr-agent/
├── backend/
│   ├── app/
│   │   ├── agents/          # The three agents (researcher, writer, sequencer)
│   │   ├── api/             # FastAPI route handlers
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Apollo, Tavily, Groq, Gmail integrations
│   │   ├── db/              # Database engine and session factory
│   │   ├── config.py        # Settings loaded from .env
│   │   └── main.py          # App entry point, router registration, CORS
│   ├── migrations/          # Alembic database migrations
│   ├── tests/               # pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   │   ├── page.tsx         # Landing page
│   │   ├── dashboard/       # Campaign list + stats
│   │   ├── campaigns/       # New campaign form + campaign detail
│   │   └── prospects/       # Individual prospect view
│   ├── components/
│   │   ├── campaigns/       # CampaignForm, EmailCard, PipelineProgressBar
│   │   └── ui/              # Sidebar, StatCard, EmptyState, LoadingSpinner
│   └── lib/
│       ├── api-client.ts    # All backend fetch calls — single source of truth
│       └── types.ts         # TypeScript types mirroring backend models
├── specs/                   # API contracts, agent specs, data models, UI specs
├── mocks/                   # Mock JSON data for local frontend development
└── .env.example             # Environment variable template
```

---

## Running tests

```bash
cd backend
pytest tests/ -v
```

---

## Deployment

### Backend → Railway

1. Create a project on [railway.app](https://railway.app)
2. Connect this GitHub repo, select the `backend/` root directory
3. Add all environment variables from `backend/.env`
4. Change `DATABASE_URL` to a PostgreSQL connection string (Railway provides one free)
5. Deploy — Railway uses `railway.toml` for build config automatically

### Frontend → Vercel

```bash
cd frontend
npx vercel
```

Set `NEXT_PUBLIC_API_URL` in the Vercel dashboard to your Railway backend URL.

---

## Architecture decisions

- **No agent framework** — agents are plain async Python functions. This keeps the code readable and debuggable without the overhead of CrewAI or LangGraph. The pipeline is sequential by design.
- **Async pipeline via background tasks** — the agent crew takes 30–90 seconds. FastAPI background tasks handle the run; the frontend polls `GET /campaigns/{id}` every 3 seconds until status is `completed`.
- **Gmail SMTP instead of Resend** — avoids the requirement of a custom domain for email sending. Works with any Gmail account using an App Password.
- **SQLite in dev, PostgreSQL in prod** — SQLAlchemy handles both without any code changes, just swap the `DATABASE_URL`.
- **Mock prospect fallback** — Apollo's free tier silently returns empty results for people search. The fallback ensures the full pipeline (including Groq email generation) can be demonstrated without a paid Apollo plan.

---

## License

MIT
