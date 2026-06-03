// ── Campaign ────────────────────────────────────────────────────────────────

export type CampaignStatus =
  | "pending"
  | "researching"
  | "writing"
  | "sequencing"
  | "completed"
  | "failed";

export type EmailTone = "professional" | "casual" | "direct";

export interface CreateCampaignRequest {
  name: string;
  search_query: string;
  max_prospects?: number;
  sender_name: string;
  sender_title: string;
  sender_company: string;
  value_proposition: string;
  email_tone?: EmailTone;
}

export interface Campaign {
  id: string;
  name: string;
  search_query: string;
  status: CampaignStatus;
  progress_message: string | null;
  max_prospects: number;
  prospect_count: number;
  email_count: number;
  sender_name: string;
  sender_title: string;
  sender_company: string;
  value_proposition: string;
  email_tone: EmailTone;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface CampaignListResponse {
  items: Campaign[];
  total: number;
  page: number;
  limit: number;
}

export interface CampaignStats {
  campaign_id: string;
  total_prospects: number;
  total_emails: number;
  emails_sent: number;
  emails_opened: number;
  emails_replied: number;
  emails_bounced: number;
  open_rate: number;
  reply_rate: number;
}

// ── Prospect ────────────────────────────────────────────────────────────────

export interface Prospect {
  id: string;
  campaign_id: string;
  first_name: string;
  last_name: string;
  email: string;
  title: string;
  company: string;
  company_size: string | null;
  country: string;
  linkedin_url: string | null;
  recent_news: string | null;
  job_postings: string[];
  pain_points: string[];
  personalisation_hook: string | null;
  enriched_at: string;
}

export interface ProspectListResponse {
  items: Prospect[];
  total: number;
  page: number;
  limit: number;
}

// ── Email ───────────────────────────────────────────────────────────────────

export type EmailStatus =
  | "draft"
  | "scheduled"
  | "sent"
  | "opened"
  | "clicked"
  | "replied"
  | "bounced"
  | "discarded";

export type SequenceDay = 1 | 4 | 7;

export interface Email {
  id: string;
  campaign_id: string;
  prospect_id: string;
  prospect_email: string;
  prospect_name: string;
  sequence_day: SequenceDay;
  subject: string;
  body: string;
  status: EmailStatus;
  resend_email_id: string | null;
  scheduled_at: string | null;
  sent_at: string | null;
  opened_at: string | null;
  replied_at: string | null;
  created_at: string;
}

export interface UpdateEmailRequest {
  subject?: string;
  body?: string;
}

export interface ProspectEmailGroup {
  prospect: Prospect;
  emails: Email[];
}

export interface CampaignEmailsResponse {
  campaign_id: string;
  grouped_by_prospect: ProspectEmailGroup[];
}

// ── UI helpers ──────────────────────────────────────────────────────────────

export const isCampaignRunning = (status: CampaignStatus): boolean =>
  ["pending", "researching", "writing", "sequencing"].includes(status);

export const CAMPAIGN_STATUS_LABEL: Record<CampaignStatus, string> = {
  pending: "Starting...",
  researching: "Researching",
  writing: "Writing Emails",
  sequencing: "Scheduling",
  completed: "Completed",
  failed: "Failed",
};

export const CAMPAIGN_STATUS_COLOR: Record<CampaignStatus, string> = {
  pending: "bg-gray-100 text-gray-600",
  researching: "bg-blue-100 text-blue-700",
  writing: "bg-purple-100 text-purple-700",
  sequencing: "bg-yellow-100 text-yellow-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export const EMAIL_STATUS_LABEL: Record<EmailStatus, string> = {
  draft: "Draft",
  scheduled: "Scheduled",
  sent: "Sent",
  opened: "Opened",
  clicked: "Clicked",
  replied: "Replied",
  bounced: "Bounced",
  discarded: "Discarded",
};

export const EMAIL_STATUS_COLOR: Record<EmailStatus, string> = {
  draft: "bg-gray-100 text-gray-600",
  scheduled: "bg-blue-100 text-blue-700",
  sent: "bg-indigo-100 text-indigo-700",
  opened: "bg-yellow-100 text-yellow-700",
  clicked: "bg-orange-100 text-orange-700",
  replied: "bg-green-100 text-green-700",
  bounced: "bg-red-100 text-red-700",
  discarded: "bg-gray-100 text-gray-400",
};

export const SEQUENCE_DAY_LABEL: Record<SequenceDay, string> = {
  1: "Day 1 — First Touch",
  4: "Day 4 — Follow-up",
  7: "Day 7 — Break-up",
};

export const getProspectFullName = (p: Prospect) =>
  `${p.first_name} ${p.last_name}`;

export const getProspectInitials = (p: Prospect) =>
  `${p.first_name[0]}${p.last_name[0]}`.toUpperCase();

export const isWellEnriched = (p: Prospect) =>
  p.personalisation_hook !== null &&
  p.pain_points.length >= 1 &&
  p.recent_news !== null;
