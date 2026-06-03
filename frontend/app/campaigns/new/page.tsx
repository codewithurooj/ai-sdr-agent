import Link from "next/link";
import { CampaignForm } from "@/components/campaigns/CampaignForm";
import { ArrowLeft } from "lucide-react";

export default function NewCampaignPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" />
          Dashboard
        </Link>
        <h1 className="text-2xl font-bold text-slate-900 mt-2">New Campaign</h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe your target and the AI will research prospects and write personalised email sequences automatically.
        </p>
      </div>
      <CampaignForm />
    </div>
  );
}
