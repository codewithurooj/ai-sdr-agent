"use client";

import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { getCampaign, getCampaignEmails, getCampaignStats } from "@/lib/api-client";
import { StatCard } from "@/components/ui/StatCard";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import { Badge } from "@/components/ui/Badge";
import {
  EMAIL_STATUS_COLOR,
  EMAIL_STATUS_LABEL,
  getProspectFullName,
} from "@/lib/types";
import type { Email } from "@/lib/types";

const FUNNEL_COLORS: Record<string, string> = {
  Sent: "#6366f1",
  Opened: "#f59e0b",
  Replied: "#22c55e",
  Bounced: "#ef4444",
};

export default function CampaignStatsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  const { data: campaign, isLoading: campLoading } = useQuery({
    queryKey: ["campaign", id],
    queryFn: () => getCampaign(id),
  });

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["campaign-stats", id],
    queryFn: () => getCampaignStats(id),
    enabled: !!campaign,
  });

  const { data: emailsData } = useQuery({
    queryKey: ["campaign-emails", id],
    queryFn: () => getCampaignEmails(id),
    enabled: !!campaign,
  });

  if (campLoading || statsLoading) return <LoadingSpinner />;
  if (!campaign || !stats) return <ErrorBanner message="Could not load campaign stats." />;

  const funnelData = [
    { name: "Sent", value: stats.emails_sent },
    { name: "Opened", value: stats.emails_opened },
    { name: "Replied", value: stats.emails_replied },
    { name: "Bounced", value: stats.emails_bounced },
  ];

  const groups = emailsData?.grouped_by_prospect ?? [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          href={`/campaigns/${id}`}
          className="text-sm text-gray-400 hover:text-gray-600"
        >
          ← Back to Campaign
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-2">
          {campaign.name} — Stats
        </h1>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Sent" value={stats.emails_sent} />
        <StatCard
          label="Opened"
          value={stats.emails_opened}
          sub={`${stats.open_rate}% open rate`}
        />
        <StatCard
          label="Replied"
          value={stats.emails_replied}
          sub={`${stats.reply_rate}% reply rate`}
        />
        <StatCard label="Bounced" value={stats.emails_bounced} />
      </div>

      {/* Funnel chart */}
      {stats.emails_sent > 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-5">
            Email Funnel
          </h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart
              data={funnelData}
              layout="vertical"
              margin={{ left: 8, right: 40, top: 0, bottom: 0 }}
            >
              <XAxis type="number" tick={{ fontSize: 12 }} axisLine={false} tickLine={false} />
              <YAxis
                dataKey="name"
                type="category"
                width={64}
                tick={{ fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                cursor={{ fill: "#f9fafb" }}
                formatter={(v) => [v, "emails"]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={28}>
                {funnelData.map((entry) => (
                  <Cell key={entry.name} fill={FUNNEL_COLORS[entry.name] ?? "#94a3b8"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-sm text-gray-400 text-center py-8">
          No emails sent yet — approve emails to start seeing stats here.
        </p>
      )}

      {/* Per-prospect breakdown */}
      {groups.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <h2 className="text-sm font-semibold text-gray-700 px-5 py-4 border-b border-gray-100">
            Per-Prospect Breakdown
          </h2>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {["Prospect", "Day 1", "Day 4", "Day 7"].map((h) => (
                  <th
                    key={h}
                    className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {groups.map(({ prospect, emails }) => {
                const byDay: Record<number, Email> = {};
                emails.forEach((e) => {
                  byDay[e.sequence_day] = e;
                });
                return (
                  <tr key={prospect.id} className="hover:bg-gray-50">
                    <td className="px-5 py-3">
                      <Link
                        href={`/prospects/${prospect.id}`}
                        className="font-medium text-gray-900 hover:text-blue-600"
                      >
                        {getProspectFullName(prospect)}
                      </Link>
                      <p className="text-xs text-gray-400">{prospect.email}</p>
                    </td>
                    {[1, 4, 7].map((day) => {
                      const email = byDay[day];
                      return (
                        <td key={day} className="px-5 py-3">
                          {email ? (
                            <Badge
                              label={EMAIL_STATUS_LABEL[email.status]}
                              colorClass={EMAIL_STATUS_COLOR[email.status]}
                            />
                          ) : (
                            <span className="text-gray-300 text-base">—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
