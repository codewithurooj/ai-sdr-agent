import Link from "next/link";
import { Search, PenLine, CalendarClock, Zap, ArrowRight } from "lucide-react";

const steps = [
  {
    icon: <Search className="h-6 w-6" />,
    title: "Research",
    desc: "Finds real prospects on Apollo.io and enriches each one with news, job postings, and pain points via web search.",
    color: "bg-indigo-50 text-indigo-600",
  },
  {
    icon: <PenLine className="h-6 w-6" />,
    title: "Write",
    desc: "Groq/Llama writes 3 hyper-personalised emails per prospect — Day 1 first touch, Day 4 follow-up, Day 7 break-up.",
    color: "bg-violet-50 text-violet-600",
  },
  {
    icon: <CalendarClock className="h-6 w-6" />,
    title: "Schedule & Send",
    desc: "Sequences are saved, reviewed, and sent via Gmail at 9 AM in the prospect's local timezone.",
    color: "bg-emerald-50 text-emerald-600",
  },
];

export default function LandingPage() {
  return (
    <div className="space-y-16 py-4">
      {/* Hero */}
      <div className="text-center space-y-6 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-indigo-50 text-indigo-700 text-xs font-semibold px-3 py-1.5 rounded-full border border-indigo-100">
          <Zap className="h-3.5 w-3.5" />
          Powered by Groq · Apollo · Gmail
        </div>
        <h1 className="text-5xl font-extrabold text-slate-900 leading-tight">
          Your AI Sales<br />
          <span className="text-indigo-600">Development Rep</span>
        </h1>
        <p className="text-lg text-slate-500 leading-relaxed">
          Input a target audience. The AI researches real prospects, writes hyper-personalised 3-email sequences for each one, and sends them on autopilot.
        </p>
        <div className="flex items-center justify-center gap-3 flex-wrap">
          <Link
            href="/campaigns/new"
            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-colors shadow-lg shadow-indigo-200"
          >
            <Zap className="h-4 w-4" />
            Launch a Campaign
          </Link>
          <Link
            href="/dashboard"
            className="flex items-center gap-2 px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold rounded-xl border border-slate-200 transition-colors"
          >
            Open Dashboard
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>

      {/* Pipeline steps */}
      <div>
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest text-center mb-8">How it works</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {steps.map((step, i) => (
            <div key={i} className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className={`p-3 rounded-xl ${step.color}`}>{step.icon}</div>
                <div>
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Step {i + 1}</p>
                  <p className="text-base font-bold text-slate-900">{step.title}</p>
                </div>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA strip */}
      <div className="bg-slate-900 rounded-2xl p-8 text-center space-y-4">
        <h2 className="text-2xl font-bold text-white">Ready to start?</h2>
        <p className="text-sm text-slate-400">Create your first campaign and watch the AI go to work.</p>
        <Link
          href="/campaigns/new"
          className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-bold rounded-xl transition-colors"
        >
          <Zap className="h-4 w-4" />
          New Campaign
        </Link>
      </div>
    </div>
  );
}
