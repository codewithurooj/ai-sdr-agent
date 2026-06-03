import axios from "axios";
import type {
  Campaign,
  CampaignEmailsResponse,
  CampaignListResponse,
  CampaignStats,
  CreateCampaignRequest,
  Email,
  Prospect,
  ProspectListResponse,
  UpdateEmailRequest,
} from "./types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

// ── Campaigns ───────────────────────────────────────────────────────────────
export const createCampaign = async (data: CreateCampaignRequest): Promise<Campaign> =>
  (await api.post("/campaigns", data)).data;

export const listCampaigns = async (page = 1, limit = 20): Promise<CampaignListResponse> =>
  (await api.get("/campaigns", { params: { page, limit } })).data;

export const getCampaign = async (id: string): Promise<Campaign> =>
  (await api.get(`/campaigns/${id}`)).data;

export const deleteCampaign = async (id: string): Promise<void> =>
  api.delete(`/campaigns/${id}`);

export const getCampaignProspects = async (
  campaignId: string,
  page = 1,
  limit = 20,
): Promise<ProspectListResponse> =>
  (await api.get(`/campaigns/${campaignId}/prospects`, { params: { page, limit } })).data;

export const getCampaignEmails = async (
  campaignId: string,
  prospectId?: string,
): Promise<CampaignEmailsResponse> =>
  (await api.get(`/campaigns/${campaignId}/emails`, {
    params: prospectId ? { prospect_id: prospectId } : {},
  })).data;

export const getCampaignStats = async (campaignId: string): Promise<CampaignStats> =>
  (await api.get(`/campaigns/${campaignId}/stats`)).data;

// ── Prospects ───────────────────────────────────────────────────────────────
export const getProspect = async (id: string): Promise<Prospect> =>
  (await api.get(`/prospects/${id}`)).data;

// ── Emails ──────────────────────────────────────────────────────────────────
export const getEmail = async (id: string): Promise<Email> =>
  (await api.get(`/emails/${id}`)).data;

export const updateEmail = async (id: string, data: UpdateEmailRequest): Promise<Email> =>
  (await api.patch(`/emails/${id}`, data)).data;

export const approveEmail = async (id: string): Promise<Email> =>
  (await api.post(`/emails/${id}/approve`)).data;

export const sendEmailNow = async (id: string): Promise<Email> =>
  (await api.post(`/emails/${id}/send`)).data;

export const discardEmail = async (id: string): Promise<Email> =>
  (await api.post(`/emails/${id}/discard`)).data;
