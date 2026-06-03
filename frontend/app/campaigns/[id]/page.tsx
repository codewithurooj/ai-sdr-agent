"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { approveEmail, getCampaign, getCampaignEmails, getCampaignProspects } from "@/lib/api-client";
import { isCampaignRunning, isWellEnriched, getProspectFullName, getProspectInitials, Email } from "@/lib/types";
import { CampaignStatusBadge } from "@/components/campaigns/CampaignStatusBadge";
import { PipelineProgressBar } from "@/components/campaigns/PipelineProgressBar";
import { EmailCard } from "@/components/campaigns/EmailCard";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { toast } from "sonner";
import { ArrowLeft, Users, Mail, CheckCheck, ChevronRight } from "lucide-react";

export default function CampaignDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [tab, setTab] = useState<"prospects" | "emails">("prospects");
  const qc = useQueryClient();

  const { data: campaign, isLoading } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => getCampaign(id),
    refetchInterval: (q) => (q.state.data && isCampaignRunning(q.state.data.status) ? 3000 : false),
  });

  const isRunning = campaign ? isCampaignRunning(campaign.status) : false;

  const { data: prospectsData } = useQuery({
    queryKey: ["campaign-prospects", id],
    queryFn: () => getCampaignProspects(id),
    enabled: !!campaign && !isRunning,
  });

  const { data: emailsData, refetch: refetchEmails } = useQuery({
    queryKey: ["campaign-emails", id],
    queryFn: () => getCampaignEmails(id),
    enabled: !!campaign && !isRunning,
  });

  const handleEmailUpdate = (updated: Email) => {
    qc.setQueryData(["campaign-emails", id], (old: typeof emailsData) => {
      if (!old) return old;
      return {
        ...old,
        grouped_by_prospect: old.grouped_by_prospect.map((g) => ({
          ...g,
          emails: g.emails.map((e) => (e.id === updated.id ? updated : e)),
        })),
      };
    });
  };

  const approveAll = async () => {
    const drafts = emailsData?.grouped_by_prospect.flatMap((g) => g.emails.filter((e) => e.status === "draft")) ?? [];
    if (!drafts.length) { toast.info("No draft emails to approve"); return; }
    await Promise.all(drafts.map((e) => approveEmail(e.id)));
    toast.success(`${drafts.length} emails approved`);
    refetchEmails();
  };

  if (isLoading) return <LoadingSpinner />;
  if (!campaign) return <ErrorBanner message="Campaign not found." />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
          Dashboard
        </Link>
        <div className="flex items-start justify-between gap-4 mt-2">
          <div className="min-w-0">
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl font-bold text-slate-900">{campaign.name}</h1>
              <CampaignStatusBadge status={campaign.status} />
            </div>
            <p className="text-sm text-slate-400 mt-1 italic">"{campaign.search_query}"</p>
          </div>
          {campaign.status === "completed" && (
            <Link href={`/campaigns/${id}/stats`} className="shrink-0 text-xs font-medium text-indigo-600 hover:text-indigo-700 border border-indigo-200 px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition-colors">
              View Stats
            </Link>
          )}
        </div>
      </div>

      {/* Stats row */}
      {campaign.status === "completed" && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3">
            <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600"><Users className="h-4 w-4" /></div>
            <div>
              <p className="text-xl font-bold text-slate-900">{campaign.prospect_count}</p>
              <p className="text-xs text-slate-400">Prospects</p>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3">
            <div className="p-2 bg-violet-50 rounded-lg text-violet-600"><Mail className="h-4 w-4" /></div>
            <div>
              <p className="text-xl font-bold text-slate-900">{campaign.email_count}</p>
              <p className="text-xs text-slate-400">Emails</p>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-3">
            <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600"><CheckCheck className="h-4 w-4" /></div>
            <div>
              <p className="text-xl font-bold text-slate-900">{emailsData?.grouped_by_prospect.flatMap(g => g.emails).filter(e => e.status !== "draft" && e.status !== "discarded").length ?? 0}</p>
              <p className="text-xs text-slate-400">Approved</p>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline progress */}
      {isRunning && (
        <PipelineProgressBar status={campaign.status} progressMessage={campaign.progress_message} />
      )}

      {/* Error */}
      {campaign.status === "failed" && campaign.error && (
        <ErrorBanner message={campaign.error} />
      )}

      {/* Tabs */}
      {!isRunning && campaign.status === "completed" && (
        <>
          <div className="flex items-center gap-1 border-b border-slate-200">
            {(["prospects", "emails"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px ${
                  tab === t
                    ? "border-indigo-600 text-indigo-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                {t === "prospects"
                  ? `Prospects (${prospectsData?.total ?? 0})`
                  : `Emails (${campaign.email_count})`}
              </button>
            ))}
          </div>

          {/* Prospects tab */}
          {tab === "prospects" && (
            prospectsData?.items.length === 0 ? (
              <EmptyState title="No prospects found" description="Try a broader search query." />
            ) : (
              <div className="space-y-2">
                {prospectsData?.items.map((p) => (
                  <Link key={p.id} href={`/prospects/${p.id}`} className="group block">
                    <div className="bg-white rounded-xl border border-slate-200 px-5 py-4 hover:border-indigo-300 hover:shadow-sm transition-all">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-bold shrink-0">
                            {getProspectInitials(p)}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">{getProspectFullName(p)}</p>
                            <p className="text-xs text-slate-500">{p.title} · {p.company}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 shrink-0">
                          <div className="hidden sm:block text-right">
                            <p className="text-xs text-slate-500">{p.company_size ?? "—"}</p>
                            <p className="text-xs text-slate-400">{p.country}</p>
                          </div>
                          {isWellEnriched(p)
                            ? <span className="hidden sm:block text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Enriched</span>
                            : <span className="hidden sm:block text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">Partial</span>
                          }
                          <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-indigo-400 transition-colors" />
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )
          )}

          {/* Emails tab */}
          {tab === "emails" && (
            <div className="space-y-8">
              <div className="flex justify-end">
                <button onClick={approveAll} className="flex items-center gap-2 px-4 py-2 text-sm font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors">
                  <CheckCheck className="h-4 w-4" />
                  Approve All Drafts
                </button>
              </div>
              {emailsData?.grouped_by_prospect.map((group) => (
                <div key={group.prospect.id}>
                  <div className="flex items-center gap-3 mb-4">
                    <div className="h-9 w-9 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-bold shrink-0">
                      {getProspectInitials(group.prospect)}
                    </div>
                    <div>
                      <p className="font-semibold text-slate-900">{getProspectFullName(group.prospect)}</p>
                      <p className="text-xs text-slate-400">{group.prospect.email}</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {group.emails.map((email) => (
                      <EmailCard key={email.id} email={email} onUpdate={handleEmailUpdate} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {isRunning && (
        <div className="text-center py-16 text-sm text-slate-400">
          Emails will appear here once the pipeline completes...
        </div>
      )}
    </div>
  );
}
