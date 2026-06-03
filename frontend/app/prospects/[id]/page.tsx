"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getCampaignEmails, getProspect } from "@/lib/api-client";
import { getProspectFullName, getProspectInitials } from "@/lib/types";
import { EmailCard } from "@/components/campaigns/EmailCard";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { useQueryClient } from "@tanstack/react-query";
import type { Email } from "@/lib/types";
import { ArrowLeft, ExternalLink, Newspaper, Briefcase, Target, AlertCircle } from "lucide-react";

export default function ProspectDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const qc = useQueryClient();

  const { data: prospect, isLoading } = useQuery({
    queryKey: ["prospect", id],
    queryFn: () => getProspect(id),
  });

  const { data: emailsData } = useQuery({
    queryKey: ["prospect-emails", id],
    queryFn: () => getCampaignEmails(prospect!.campaign_id, id),
    enabled: !!prospect,
  });

  const emails = emailsData?.grouped_by_prospect[0]?.emails ?? [];

  const handleEmailUpdate = (updated: Email) => {
    qc.setQueryData(["prospect-emails", id], (old: typeof emailsData) => {
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

  if (isLoading) return <LoadingSpinner />;
  if (!prospect) return <ErrorBanner message="Prospect not found." />;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Back */}
      <Link href={`/campaigns/${prospect.campaign_id}`} className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors">
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to Campaign
      </Link>

      {/* Profile header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex items-center gap-5">
          <div className="h-16 w-16 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center text-2xl font-bold shrink-0">
            {getProspectInitials(prospect)}
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-2xl font-bold text-slate-900">{getProspectFullName(prospect)}</h1>
            <p className="text-sm text-slate-500 mt-0.5">{prospect.title} · {prospect.company}</p>
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              {prospect.company_size && (
                <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full font-medium">{prospect.company_size} employees</span>
              )}
              {prospect.country && (
                <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-full font-medium">{prospect.country}</span>
              )}
              {prospect.linkedin_url && (
                <a href={prospect.linkedin_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-xs text-indigo-600 hover:text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-full font-medium transition-colors">
                  <ExternalLink className="h-3 w-3" />
                  LinkedIn
                </a>
              )}
            </div>
          </div>
          <div className="shrink-0 text-right">
            <p className="text-xs text-slate-400">Email</p>
            <p className="text-sm font-medium text-slate-700 mt-0.5">{prospect.email}</p>
          </div>
        </div>
      </div>

      {/* Research summary */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100">
          <h2 className="text-sm font-semibold text-slate-900">Research Summary</h2>
          <p className="text-xs text-slate-400 mt-0.5">Intelligence gathered by the AI researcher</p>
        </div>
        <div className="divide-y divide-slate-100">
          {prospect.recent_news && (
            <ResearchRow icon={<Newspaper className="h-4 w-4" />} label="Recent News" color="text-blue-600 bg-blue-50">
              {prospect.recent_news}
            </ResearchRow>
          )}
          {prospect.personalisation_hook && (
            <ResearchRow icon={<Target className="h-4 w-4" />} label="Personalisation Hook" color="text-indigo-600 bg-indigo-50">
              <em className="not-italic text-indigo-700 font-medium">"{prospect.personalisation_hook}"</em>
            </ResearchRow>
          )}
          {prospect.job_postings.length > 0 && (
            <ResearchRow icon={<Briefcase className="h-4 w-4" />} label="Open Roles" color="text-violet-600 bg-violet-50">
              <div className="flex flex-wrap gap-1.5 mt-1">
                {prospect.job_postings.map((j, i) => (
                  <span key={i} className="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full">{j}</span>
                ))}
              </div>
            </ResearchRow>
          )}
          {prospect.pain_points.length > 0 && (
            <ResearchRow icon={<AlertCircle className="h-4 w-4" />} label="Pain Points" color="text-amber-600 bg-amber-50">
              <ul className="space-y-1 mt-1">
                {prospect.pain_points.map((p, i) => (
                  <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                    <span className="text-amber-400 mt-0.5">•</span>{p}
                  </li>
                ))}
              </ul>
            </ResearchRow>
          )}
        </div>
      </div>

      {/* Email sequence */}
      <div>
        <h2 className="text-base font-semibold text-slate-900 mb-4">Email Sequence</h2>
        {emails.length === 0 ? (
          <p className="text-sm text-slate-400">No emails generated yet.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {emails.map((email) => (
              <EmailCard key={email.id} email={email} onUpdate={handleEmailUpdate} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ResearchRow({ icon, label, color, children }: {
  icon: React.ReactNode;
  label: string;
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-4 px-5 py-4">
      <div className={`p-2 rounded-lg shrink-0 h-fit ${color}`}>{icon}</div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">{label}</p>
        <div className="text-sm text-slate-700">{children}</div>
      </div>
    </div>
  );
}
