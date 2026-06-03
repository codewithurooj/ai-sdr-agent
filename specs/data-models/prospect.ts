// Prospect data models
// A Prospect is one person discovered and enriched by the Researcher Agent.
// Prospects are always scoped to a Campaign (one prospect can't appear in two campaigns).

// ── Core Model ─────────────────────────────────────────────────────────────

export interface Prospect {
  id: string;                        // UUID
  campaign_id: string;               // UUID — parent campaign

  // ── Identity (from Apollo) ───────────────────────────────────────────────
  first_name: string;
  last_name: string;
  email: string;
  title: string;                     // e.g. "VP of Sales"
  company: string;
  company_size: string | null;       // e.g. "51-200", "201-500"
  country: string;                   // e.g. "UAE", "Saudi Arabia"
  linkedin_url: string | null;

  // ── Enrichment (from Tavily + LLM synthesis) ─────────────────────────────
  recent_news: string | null;        // one-sentence company news summary
  job_postings: string[];            // open roles at the company (max 3)
  pain_points: string[];             // inferred by Researcher agent (2–3 items)
  personalisation_hook: string | null; // opening line the Writer uses in Email 1

  enriched_at: string;               // ISO 8601 — when Tavily research completed
}

// ── Derived Helpers ────────────────────────────────────────────────────────

/** Full display name */
export const getProspectFullName = (p: Prospect): string =>
  `${p.first_name} ${p.last_name}`;

/** Initials for avatar fallback */
export const getProspectInitials = (p: Prospect): string =>
  `${p.first_name[0]}${p.last_name[0]}`.toUpperCase();

/** True if the prospect has enough enrichment data to personalise well */
export const isWellEnriched = (p: Prospect): boolean =>
  p.personalisation_hook !== null &&
  p.pain_points.length >= 1 &&
  p.recent_news !== null;

// ── List Response ──────────────────────────────────────────────────────────

export interface ProspectListResponse {
  items: Prospect[];
  total: number;
  page: number;
  limit: number;
}

// ── Company Size Options (for display / filtering) ─────────────────────────

export const COMPANY_SIZE_ORDER = [
  "1-10",
  "11-50",
  "51-200",
  "201-500",
  "501-1000",
  "1001-5000",
  "5001+",
] as const;

export type CompanySize = (typeof COMPANY_SIZE_ORDER)[number];
