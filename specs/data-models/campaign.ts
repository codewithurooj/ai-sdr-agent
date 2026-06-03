// Campaign data models
// Source of truth for TypeScript types across the frontend.
// Backend Pydantic models must match these exactly.

export type CampaignStatus =
  | "pending"
  | "researching"
  | "writing"
  | "sequencing"
  | "completed"
  | "failed";

export type EmailTone = "professional" | "casual" | "direct";

// ── Request ────────────────────────────────────────────────────────────────

export interface CreateCampaignRequest {
  name: string;                   // max 120 chars
  search_query: string;           // natural language, max 300 chars
  max_prospects?: number;         // default 10, max 50
  sender_name: string;
  sender_title: string;
  sender_company: string;
  value_proposition: string;      // max 500 chars
  email_tone?: EmailTone;         // default "professional"
}

// ── Core Model ─────────────────────────────────────────────────────────────

export interface Campaign {
  id: string;                     // UUID
  name: string;
  search_query: string;
  status: CampaignStatus;
  progress_message: string | null; // shown in UI progress bar while pipeline runs
  max_prospects: number;
  prospect_count: number;          // increments as Researcher agent finds prospects
  email_count: number;             // increments as Writer agent generates emails
  sender_name: string;
  sender_title: string;
  sender_company: string;
  value_proposition: string;
  email_tone: EmailTone;
  error: string | null;            // populated only when status = "failed"
  created_at: string;              // ISO 8601
  completed_at: string | null;     // ISO 8601
}

// ── Stats ──────────────────────────────────────────────────────────────────

export interface CampaignStats {
  campaign_id: string;
  total_prospects: number;
  total_emails: number;
  emails_sent: number;
  emails_opened: number;
  emails_replied: number;
  emails_bounced: number;
  open_rate: number;               // percentage 0–100
  reply_rate: number;              // percentage 0–100
}

// ── List Response ──────────────────────────────────────────────────────────

export interface CampaignListResponse {
  items: Campaign[];
  total: number;
  page: number;
  limit: number;
}

// ── UI Helpers ─────────────────────────────────────────────────────────────

/** Returns true while the agent pipeline is still running */
export const isCampaignRunning = (status: CampaignStatus): boolean =>
  ["pending", "researching", "writing", "sequencing"].includes(status);

/** Maps status to a human-readable label for badges */
export const CAMPAIGN_STATUS_LABEL: Record<CampaignStatus, string> = {
  pending:     "Starting...",
  researching: "Researching",
  writing:     "Writing Emails",
  sequencing:  "Scheduling",
  completed:   "Completed",
  failed:      "Failed",
};

/** Maps status to a Tailwind colour class for badges */
export const CAMPAIGN_STATUS_COLOR: Record<CampaignStatus, string> = {
  pending:     "bg-gray-100 text-gray-600",
  researching: "bg-blue-100 text-blue-700",
  writing:     "bg-purple-100 text-purple-700",
  sequencing:  "bg-yellow-100 text-yellow-700",
  completed:   "bg-green-100 text-green-700",
  failed:      "bg-red-100 text-red-700",
};
