"use client";

import { useState } from "react";
import { toast } from "sonner";
import { approveEmail, discardEmail, sendEmailNow, updateEmail } from "@/lib/api-client";
import { Badge } from "@/components/ui/Badge";
import { EMAIL_STATUS_COLOR, EMAIL_STATUS_LABEL, SEQUENCE_DAY_LABEL } from "@/lib/types";
import type { Email } from "@/lib/types";
import { Check, Edit2, Send, Trash2, X, Calendar } from "lucide-react";

const DAY_BAR: Record<number, string> = {
  1: "bg-indigo-600",
  4: "bg-violet-600",
  7: "bg-slate-400",
};

interface Props {
  email: Email;
  onUpdate: (updated: Email) => void;
}

export function EmailCard({ email, onUpdate }: Props) {
  const [editing, setEditing] = useState(false);
  const [subject, setSubject] = useState(email.subject);
  const [body, setBody] = useState(email.body);
  const [loading, setLoading] = useState(false);

  const act = async (fn: () => Promise<Email>, successMsg: string) => {
    setLoading(true);
    try {
      const updated = await fn();
      onUpdate(updated);
      toast.success(successMsg);
    } catch {
      toast.error("Action failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const saveEdit = () => act(() => updateEmail(email.id, { subject, body }), "Email updated");
  const accent = DAY_BAR[email.sequence_day] ?? "bg-slate-400";

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden flex flex-col">
      {/* Top accent */}
      <div className={`h-1 w-full ${accent}`} />

      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between gap-2">
        <div>
          <p className="text-xs font-bold text-slate-800 uppercase tracking-wide">
            {SEQUENCE_DAY_LABEL[email.sequence_day]}
          </p>
          {email.scheduled_at && (
            <div className="flex items-center gap-1 mt-0.5">
              <Calendar className="h-3 w-3 text-slate-400" />
              <p className="text-[11px] text-slate-400">
                {new Date(email.scheduled_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })} @ 9:00 AM
              </p>
            </div>
          )}
        </div>
        <Badge label={EMAIL_STATUS_LABEL[email.status]} colorClass={EMAIL_STATUS_COLOR[email.status]} />
      </div>

      {/* Body */}
      <div className="p-4 flex-1">
        {editing ? (
          <div className="space-y-2">
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm font-semibold focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Subject line"
            />
            <textarea
              rows={8}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono resize-none"
            />
            <div className="flex gap-2">
              <button onClick={saveEdit} disabled={loading} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
                <Check className="h-3 w-3" /> Save
              </button>
              <button onClick={() => { setEditing(false); setSubject(email.subject); setBody(email.body); }} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-slate-300 rounded-lg hover:bg-slate-50">
                <X className="h-3 w-3" /> Cancel
              </button>
            </div>
          </div>
        ) : (
          <>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Subject</p>
            <p className="text-sm font-semibold text-slate-900 mb-3">{email.subject}</p>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Body</p>
            <p className="text-sm text-slate-600 whitespace-pre-line leading-relaxed">{email.body}</p>
          </>
        )}
      </div>

      {/* Actions */}
      {!editing && (
        <div className="px-4 py-3 border-t border-slate-100 bg-slate-50 flex items-center gap-2 flex-wrap">
          {email.status === "draft" && (
            <>
              <button onClick={() => act(() => approveEmail(email.id), "Email approved")} disabled={loading} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors">
                <Check className="h-3 w-3" /> Approve
              </button>
              <button onClick={() => setEditing(true)} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-slate-300 text-slate-700 rounded-lg hover:bg-white transition-colors">
                <Edit2 className="h-3 w-3" /> Edit
              </button>
              <button onClick={() => act(() => discardEmail(email.id), "Email discarded")} disabled={loading} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-50 rounded-lg disabled:opacity-50 transition-colors">
                <Trash2 className="h-3 w-3" /> Discard
              </button>
            </>
          )}
          {email.status === "scheduled" && (
            <button onClick={() => act(() => sendEmailNow(email.id), "Email sent!")} disabled={loading} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors">
              <Send className="h-3 w-3" /> Send Now
            </button>
          )}
          {email.sent_at && (
            <span className="text-xs text-slate-400">
              Sent {new Date(email.sent_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}
            </span>
          )}
          {email.opened_at && <span className="text-xs font-medium text-amber-600">• Opened</span>}
          {email.replied_at && <span className="text-xs font-bold text-emerald-600">• Replied!</span>}
        </div>
      )}
    </div>
  );
}
