"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { listCampaigns, deleteCampaign } from "@/lib/api-client";
import { isCampaignRunning, Campaign } from "@/lib/types";
import { CampaignStatusBadge } from "@/components/campaigns/CampaignStatusBadge";
import { StatCard } from "@/components/ui/StatCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { timeAgo } from "@/lib/utils";
import { Target, Users, Mail, Activity, ChevronRight, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { useState } from "react";

export default function DashboardPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: () => listCampaigns(),
    refetchInterval: (query) => {
      const campaigns = query.state.data?.items ?? [];
      return campaigns.some((c) => isCampaignRunning(c.status)) ? 5000 : false;
    },
  });

  const campaigns = data?.items ?? [];
  const totalProspects = campaigns.reduce((s, c) => s + c.prospect_count, 0);
  const totalEmails = campaigns.reduce((s, c) => s + c.email_count, 0);
  const activeCount = campaigns.filter((c) => isCampaignRunning(c.status)).length;

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return;
    try {
      await deleteCampaign(id);
      qc.setQueryData(["campaigns"], (old: typeof data) => {
        if (!old) return old;
        return { ...old, items: old.items.filter((c) => c.id !== id), total: old.total - 1 };
      });
      toast.success("Campaign deleted");
    } catch {
      toast.error("Failed to delete campaign");
    }
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Monitor your AI outreach campaigns</p>
        </div>
        <Link
          href="/campaigns/new"
          className="md:hidden flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus className="h-4 w-4" />
          New Campaign
        </Link>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Campaigns" value={campaigns.length} icon={<Target className="h-5 w-5" />} color="indigo" />
        <StatCard label="Prospects" value={totalProspects} icon={<Users className="h-5 w-5" />} color="violet" />
        <StatCard label="Emails" value={totalEmails} icon={<Mail className="h-5 w-5" />} color="blue" />
        <StatCard label="Active Now" value={activeCount} icon={<Activity className="h-5 w-5" />} color="emerald" pulse={activeCount > 0} sub="pipelines running" />
      </div>

      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-4">All Campaigns</h2>
        {campaigns.length === 0 ? (
          <EmptyState
            title="No campaigns yet"
            description="Create your first campaign and watch the AI research prospects and write personalised emails."
            action={
              <Link href="/campaigns/new" className="px-5 py-2.5 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition-colors">
                Create your first campaign
              </Link>
            }
          />
        ) : (
          <div className="space-y-2">
            {campaigns.map((c) => (
              <CampaignCard key={c.id} campaign={c} onDelete={handleDelete} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function CampaignCard({ campaign: c, onDelete }: { campaign: Campaign; onDelete: (id: string, name: string) => void }) {
  const [hovered, setHovered] = useState(false);

  return (
    <div
      className="group bg-white rounded-xl border border-slate-200 px-5 py-4 hover:border-indigo-300 hover:shadow-sm transition-all flex items-center gap-4"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Link href={`/campaigns/${c.id}`} className="flex-1 min-w-0">
        <div className="flex items-center gap-3 flex-wrap">
          <p className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors">{c.name}</p>
          <CampaignStatusBadge status={c.status} />
        </div>
        {isCampaignRunning(c.status) && c.progress_message && (
          <p className="text-xs text-indigo-500 mt-0.5">{c.progress_message}</p>
        )}
        {c.status === "failed" && c.error && (
          <p className="text-xs text-red-500 mt-0.5 truncate max-w-sm">{c.error}</p>
        )}
        <p className="text-xs text-slate-400 mt-1 truncate italic">"{c.search_query}"</p>
      </Link>

      <div className="flex items-center gap-5 shrink-0">
        <div className="hidden sm:block text-right">
          <p className="text-sm font-bold text-slate-900">{c.prospect_count}</p>
          <p className="text-xs text-slate-400">prospects</p>
        </div>
        <div className="hidden sm:block text-right">
          <p className="text-sm font-bold text-slate-900">{c.email_count}</p>
          <p className="text-xs text-slate-400">emails</p>
        </div>
        <div className="hidden md:block text-right">
          <p className="text-xs text-slate-400">{timeAgo(c.created_at)}</p>
        </div>

        {/* Delete button — always visible for failed, hover for others */}
        <button
          onClick={() => onDelete(c.id, c.name)}
          className={`p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all ${
            c.status === "failed" || hovered ? "opacity-100" : "opacity-0"
          }`}
          title="Delete campaign"
        >
          <Trash2 className="h-4 w-4" />
        </button>

        <Link href={`/campaigns/${c.id}`}>
          <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-indigo-400 transition-colors" />
        </Link>
      </div>
    </div>
  );
}
