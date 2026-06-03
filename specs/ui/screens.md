# UI Screen Specifications

## Tech
- **Framework:** Next.js 14 App Router
- **Styling:** Tailwind CSS + shadcn/ui components
- **Charts:** Recharts
- **Data fetching:** TanStack Query (auto polling, caching)
- **Types:** import from `specs/data-models/` (copied to `lib/types.ts`)

---

## Screen Map

```
/                          → Dashboard (campaign list + global stats)
/campaigns/new             → New Campaign form
/campaigns/[id]            → Campaign Detail (prospects + emails)
/campaigns/[id]/stats      → Campaign Stats
/prospects/[id]            → Prospect Detail
```

---

## Screen 1 — Dashboard `/`

### Purpose
Entry point. Shows all campaigns at a glance and global performance numbers.

### Layout
```
┌─────────────────────────────────────────────────────┐
│  Header: "AI SDR Agent"        [+ New Campaign]     │
├─────────────────────────────────────────────────────┤
│  Stats Row (4 cards)                                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │Campaigns │ │Prospects │ │  Emails  │ │Reply % │ │
│  │   12     │ │   143    │ │   429    │ │  8.4%  │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
├─────────────────────────────────────────────────────┤
│  Campaign List                     [Filter: status] │
│  ┌───────────────────────────────────────────────┐  │
│  │ Campaign Name    Status     Prospects  Created │  │
│  │ Dubai SaaS...   Completed     10      May 20  │  │
│  │ London Fintech  Researching    3/10   May 19  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Components
| Component | Description |
|-----------|-------------|
| `StatsCard` | Single number + label + optional trend arrow |
| `CampaignTable` | Sortable table with status badge, prospect count, created date |
| `CampaignStatusBadge` | Coloured pill using `CAMPAIGN_STATUS_COLOR` |

### Data
- `GET /campaigns?limit=20&page=1` — polled every 5s if any campaign is `isCampaignRunning()`
- Global stats computed client-side by summing across all fetched campaigns

### States
| State | UI |
|-------|----|
| No campaigns yet | Empty state illustration + "Create your first campaign" button |
| Campaign running | Row shows animated pulse badge + live `progress_message` |
| Campaign failed | Row shows red badge; clicking opens detail with error message |

---

## Screen 2 — New Campaign `/campaigns/new`

### Purpose
Form to create a new campaign and trigger the agent pipeline.

### Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Back    New Campaign                             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Campaign Name        [________________________]    │
│                                                     │
│  Search Query         [________________________]    │
│  "SaaS companies in Dubai hiring sales managers"    │
│                                                     │
│  Max Prospects        [10 ▾]  (1–50)                │
│                                                     │
│  ── Sender Details ──────────────────────────────   │
│  Your Name            [________________________]    │
│  Your Title           [________________________]    │
│  Your Company         [________________________]    │
│                                                     │
│  Value Proposition    [________________________]    │
│                       [________________________]    │
│  "We help SaaS companies cut lead research time..."│
│                                                     │
│  Email Tone           ● Professional  ○ Casual      │
│                       ○ Direct                      │
│                                                     │
│             [Cancel]  [🚀 Launch Campaign]          │
└─────────────────────────────────────────────────────┘
```

### Components
| Component | Description |
|-----------|-------------|
| `CampaignForm` | Controlled form with Zod validation |
| `ToneSelector` | Radio group for email tone |

### Validation (client-side, Zod)
- `name`: required, max 120 chars
- `search_query`: required, min 10 chars, max 300 chars
- `max_prospects`: integer 1–50
- `sender_name`, `sender_title`, `sender_company`: required
- `value_proposition`: required, min 20 chars, max 500 chars

### Behaviour
1. User submits → `POST /campaigns`
2. On `202` response → redirect to `/campaigns/{id}` immediately
3. Campaign Detail screen handles polling automatically

### States
| State | UI |
|-------|----|
| Submitting | Button shows spinner, all fields disabled |
| API error | Toast notification with error message |

---

## Screen 3 — Campaign Detail `/campaigns/[id]`

### Purpose
Primary working screen. Shows pipeline progress, all prospects, and all
generated emails for review and approval.

### Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Back    Dubai SaaS Outreach     [Completed ✓]   │
├─────────────────────────────────────────────────────┤
│  [PIPELINE RUNNING — only shown while running]      │
│  ████████████░░░░  Writing emails for Sara...       │
├─────────────────────────────────────────────────────┤
│  Tabs: [Prospects (10)]  [Emails (30)]  [Stats]     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  TAB: Prospects                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Name          Company      Title     Enriched │  │
│  │ Sara Al-M...  GrowthSaaS   VP Sales  ✓        │  │
│  │ James Park    Loopify      CRO       ✓        │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  TAB: Emails                                        │
│  ┌──────────────────────────────────────────────┐   │
│  │ Sara Al-Mansouri — sara@growthsaas.ae        │   │
│  │ ┌─────────────┐┌─────────────┐┌────────────┐│   │
│  │ │Day 1 [Draft]││Day 4 [Draft]││Day 7[Draft]││   │
│  │ │ Subject...  ││ Subject...  ││ Subject... ││   │
│  │ │ Body...     ││ Body...     ││ Body...    ││   │
│  │ │[Edit][✓ App]││[Edit][✓ App]││[Edit][✓App]││  │
│  │ └─────────────┘└─────────────┘└────────────┘│   │
│  └──────────────────────────────────────────────┘   │
│  [Approve All Drafts]                               │
└─────────────────────────────────────────────────────┘
```

### Components
| Component | Description |
|-----------|-------------|
| `PipelineProgressBar` | Only visible while `isCampaignRunning()`. Shows animated bar + `progress_message`. Disappears on completion. |
| `ProspectTable` | Clickable rows — navigate to `/prospects/{id}` |
| `EnrichmentBadge` | Green ✓ if `isWellEnriched(prospect)`, yellow ⚠ if partial |
| `EmailCard` | Shows subject, body preview, status badge, Edit + Approve + Discard buttons |
| `EmailStatusBadge` | Coloured pill using `EMAIL_STATUS_COLOR` |
| `ApproveAllButton` | Calls `POST /emails/{id}/approve` for every draft email in the campaign |
| `EditEmailModal` | Modal with subject + body textarea, calls `PATCH /emails/{id}` |

### Data
- `GET /campaigns/{id}` — polled every 3s while `isCampaignRunning()`; stop on `completed` or `failed`
- `GET /campaigns/{id}/prospects` — fetched once on mount (after pipeline completes)
- `GET /campaigns/{id}/emails` — fetched once on mount; refetched after any approve/edit action

### States
| State | UI |
|-------|----|
| Pipeline running | Progress bar visible, Emails tab disabled with "Emails will appear here once writing is complete" |
| Pipeline failed | Red error banner with `campaign.error` message + "Try Again" button |
| All emails approved | "All emails scheduled" success banner |
| No prospects found | Empty state: "No prospects found. Try a broader search query." |

---

## Screen 4 — Campaign Stats `/campaigns/[id]/stats`

### Purpose
Visual performance dashboard for a completed campaign.

### Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Dubai SaaS Outreach        Campaign Stats        │
├─────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │  Sent    │ │  Opened  │ │ Replied  │ │Bounced │ │
│  │   28     │ │   12     │ │    3     │ │   1    │ │
│  │          │ │  42.8%   │ │  10.7%   │ │  3.5%  │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
├─────────────────────────────────────────────────────┤
│  Email Funnel (Bar chart)                           │
│  Sent ████████████████████ 28                       │
│  Opened ████████████ 12                             │
│  Replied ███ 3                                      │
├─────────────────────────────────────────────────────┤
│  Per-Prospect Breakdown (table)                     │
│  Prospect    D1        D4        D7                 │
│  Sara A.     Opened    Draft     –                  │
│  James P.    Replied   –         –                  │
└─────────────────────────────────────────────────────┘
```

### Components
| Component | Description |
|-----------|-------------|
| `StatCard` | Number + percentage + label |
| `EmailFunnelChart` | Horizontal bar chart (Recharts `BarChart`) |
| `PerProspectTable` | One row per prospect, one column per sequence day, status badge in each cell |

### Data
- `GET /campaigns/{id}/stats` — fetched once on mount
- `GET /campaigns/{id}/emails` — for per-prospect breakdown table

---

## Screen 5 — Prospect Detail `/prospects/[id]`

### Purpose
Full profile of one prospect — all research data and their email thread.

### Layout
```
┌─────────────────────────────────────────────────────┐
│  ← Back    Sara Al-Mansouri                        │
│            VP of Sales @ GrowthSaaS (UAE)          │
├─────────────────────────────────────────────────────┤
│  Research Summary                                   │
│  ┌───────────────────────────────────────────────┐  │
│  │ 🔗 linkedin.com/in/sara-al-mansouri           │  │
│  │ 📰 News: GrowthSaaS launched AI CRM add-on   │  │
│  │ 💼 Open Roles: Senior SDR, Sales Ops Manager  │  │
│  │ 🎯 Hook: "Saw you're hiring a Sales Ops..."   │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  Pain Points                                        │
│  • Scaling outbound without increasing headcount    │
│  • SDR ramp time is too long                        │
│                                                     │
│  Email Sequence                                     │
│  ┌─ Day 1 [Opened] ─────────────────────────────┐  │
│  │ Subject: GrowthSaaS's Sales Ops hire...       │  │
│  │ Sent: May 20 · Opened: May 20 (2h later)     │  │
│  │ ─────────────────────────────────────────     │  │
│  │ Sara, Noticed GrowthSaaS is hiring a Sales... │  │
│  └───────────────────────────────────────────────┘  │
│  ┌─ Day 4 [Scheduled] ──────────────────────────┐  │
│  │ Subject: Re: GrowthSaaS's Sales Ops...        │  │
│  │ Scheduled: May 23 @ 9:00 AM GST              │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Components
| Component | Description |
|-----------|-------------|
| `ProspectHeader` | Name, title, company, country, LinkedIn link |
| `ResearchPanel` | News, job postings, hook, pain points in card layout |
| `EmailThread` | All 3 emails stacked vertically in timeline style with timestamps |

### Data
- `GET /prospects/{id}` — fetched once on mount
- `GET /campaigns/{id}/emails?prospect_id={id}` — the 3 emails for this prospect

---

## Global Components

| Component | Used On | Description |
|-----------|---------|-------------|
| `AppHeader` | All screens | Logo, nav links, no auth yet |
| `Toast` | All screens | Success/error notifications via `sonner` |
| `LoadingSpinner` | All screens | Centered spinner during initial data fetch |
| `ErrorBanner` | All screens | Red banner with message + optional retry button |
| `EmptyState` | Dashboard, Emails tab | Illustration + message + CTA button |

---

## Polling Strategy

| Screen | Endpoint polled | Interval | Stop condition |
|--------|----------------|----------|----------------|
| Dashboard | `GET /campaigns` | 5s | No campaigns running |
| Campaign Detail | `GET /campaigns/{id}` | 3s | `status === "completed" \| "failed"` |

Use TanStack Query `refetchInterval`:
```ts
useQuery({
  queryKey: ["campaign", id],
  queryFn: () => apiClient.getCampaign(id),
  refetchInterval: (data) =>
    data && isCampaignRunning(data.status) ? 3000 : false,
});
```

---

## Empty & Error States (global rules)

- **Loading:** Always show a spinner — never a blank white page
- **Empty:** Always show an illustration + message + action button (never just text)
- **Error:** Always show the error message from the API + a retry or back button
- **Partial data:** If pipeline is running and 0 emails yet, show "Emails will appear here once writing completes" — not an empty state error
