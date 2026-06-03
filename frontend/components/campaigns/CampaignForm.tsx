"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { createCampaign } from "@/lib/api-client";
import type { CreateCampaignRequest, EmailTone } from "@/lib/types";
import { Search, User, FileText, Sliders, Rocket } from "lucide-react";

const TONES: { value: EmailTone; label: string; desc: string }[] = [
  { value: "professional", label: "Professional", desc: "Formal & polished" },
  { value: "casual", label: "Casual", desc: "Friendly & warm" },
  { value: "direct", label: "Direct", desc: "Concise & bold" },
];

export function CampaignForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<CreateCampaignRequest>({
    name: "",
    search_query: "",
    max_prospects: 5,
    sender_name: "",
    sender_title: "",
    sender_company: "",
    value_proposition: "",
    email_tone: "professional",
  });

  const set = (key: keyof CreateCampaignRequest, value: string | number) =>
    setForm((f) => ({ ...f, [key]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const campaign = await createCampaign(form);
      toast.success("Campaign launched! Pipeline is starting...");
      router.push(`/campaigns/${campaign.id}`);
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? "Failed to create campaign";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Campaign section */}
      <Section icon={<Search className="h-4 w-4" />} title="Campaign" description="Name it and define your target audience">
        <div className="space-y-4">
          <Field label="Campaign Name">
            <input
              required maxLength={120}
              value={form.name}
              onChange={(e) => set("name", e.target.value)}
              placeholder="Dubai SaaS Outreach — June 2026"
              className={inputCls}
            />
          </Field>
          <Field label="Target Audience" hint="Natural language description of who you want to reach">
            <textarea
              required minLength={10} maxLength={300} rows={2}
              value={form.search_query}
              onChange={(e) => set("search_query", e.target.value)}
              placeholder="SaaS companies in Dubai hiring sales managers"
              className={inputCls}
            />
          </Field>
          <Field label="Max Prospects">
            <div className="flex items-center gap-3">
              <input
                type="number" min={1} max={50}
                value={form.max_prospects}
                onChange={(e) => set("max_prospects", Number(e.target.value))}
                className={`${inputCls} w-24`}
              />
              <p className="text-xs text-slate-400">Apollo free tier = 50 credits/month</p>
            </div>
          </Field>
        </div>
      </Section>

      {/* Sender section */}
      <Section icon={<User className="h-4 w-4" />} title="Sender" description="Your details — used in every email signature">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Field label="Your Name">
            <input required value={form.sender_name} onChange={(e) => set("sender_name", e.target.value)} placeholder="Fatima" className={inputCls} />
          </Field>
          <Field label="Your Title">
            <input required value={form.sender_title} onChange={(e) => set("sender_title", e.target.value)} placeholder="Sales Consultant" className={inputCls} />
          </Field>
          <Field label="Your Company">
            <input required value={form.sender_company} onChange={(e) => set("sender_company", e.target.value)} placeholder="OutreachAI" className={inputCls} />
          </Field>
        </div>
      </Section>

      {/* Value prop section */}
      <Section icon={<FileText className="h-4 w-4" />} title="Messaging" description="What you offer — the AI uses this to personalise every email">
        <Field label="Value Proposition">
          <textarea
            required minLength={20} maxLength={500} rows={3}
            value={form.value_proposition}
            onChange={(e) => set("value_proposition", e.target.value)}
            placeholder="We help SaaS teams book 3x more meetings using AI outreach"
            className={inputCls}
          />
        </Field>
      </Section>

      {/* Tone section */}
      <Section icon={<Sliders className="h-4 w-4" />} title="Email Tone" description="How you want the AI to write your emails">
        <div className="grid grid-cols-3 gap-3">
          {TONES.map((t) => (
            <label
              key={t.value}
              className={`flex flex-col p-3.5 rounded-lg border-2 cursor-pointer transition-all ${
                form.email_tone === t.value
                  ? "border-indigo-600 bg-indigo-50"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <input
                type="radio" name="tone" value={t.value}
                checked={form.email_tone === t.value}
                onChange={() => set("email_tone", t.value)}
                className="sr-only"
              />
              <span className={`text-sm font-semibold ${form.email_tone === t.value ? "text-indigo-700" : "text-slate-700"}`}>
                {t.label}
              </span>
              <span className="text-xs text-slate-400 mt-0.5">{t.desc}</span>
            </label>
          ))}
        </div>
      </Section>

      {/* Actions */}
      <div className="flex items-center gap-3 pt-1">
        <button
          type="button"
          onClick={() => router.back()}
          className="px-5 py-2.5 text-sm font-medium rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="flex items-center gap-2 px-6 py-2.5 text-sm font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Rocket className="h-4 w-4" />
          )}
          {loading ? "Launching..." : "Launch Campaign"}
        </button>
      </div>
    </form>
  );
}

function Section({ icon, title, description, children }: {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
        <div className="p-1.5 bg-indigo-50 text-indigo-600 rounded-lg">{icon}</div>
        <div>
          <p className="text-sm font-semibold text-slate-900">{title}</p>
          <p className="text-xs text-slate-400">{description}</p>
        </div>
      </div>
      <div className="p-5">{children}</div>
    </div>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">
        {label}
        {hint && <span className="text-slate-400 font-normal ml-1 normal-case tracking-normal">— {hint}</span>}
      </label>
      {children}
    </div>
  );
}

const inputCls = "w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow bg-white";
