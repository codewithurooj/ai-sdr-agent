import { CampaignStatus } from "@/lib/types";

const STAGES: { key: string; label: string }[] = [
  { key: "researching", label: "Research" },
  { key: "writing", label: "Writing" },
  { key: "sequencing", label: "Scheduling" },
  { key: "completed", label: "Done" },
];

const STAGE_ORDER = ["pending", "researching", "writing", "sequencing", "completed"];

interface Props {
  status: CampaignStatus;
  progressMessage: string | null;
}

export function PipelineProgressBar({ status, progressMessage }: Props) {
  const stageIdx = STAGE_ORDER.indexOf(status);
  const pct = Math.round((stageIdx / (STAGE_ORDER.length - 1)) * 100);
  const isFailed = status === "failed";

  return (
    <div className="bg-slate-900 rounded-xl p-5">
      {/* Status message */}
      <div className="flex items-center gap-2.5 mb-5">
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500" />
        </span>
        <p className="text-sm font-medium text-white">{progressMessage ?? "Processing..."}</p>
      </div>

      {/* Step indicators */}
      <div className="flex items-start mb-4">
        {STAGES.map((stage, i) => {
          const stageOrder = STAGE_ORDER.indexOf(stage.key);
          const done = stageOrder < stageIdx;
          const active = stage.key === status;
          const nextDone = i < STAGES.length - 1 && STAGE_ORDER.indexOf(STAGES[i + 1].key) <= stageIdx;

          return (
            <div key={stage.key} className="flex-1 flex flex-col items-center">
              <div className="flex items-center w-full">
                <div className={`h-6 w-6 rounded-full flex items-center justify-center text-[11px] font-bold shrink-0 transition-all ${
                  active ? "bg-indigo-500 text-white ring-4 ring-indigo-500/20" :
                  done ? "bg-indigo-700 text-indigo-300" :
                  "bg-slate-800 text-slate-600"
                }`}>
                  {done ? "✓" : i + 1}
                </div>
                {i < STAGES.length - 1 && (
                  <div className={`flex-1 h-0.5 mx-1 transition-colors ${nextDone ? "bg-indigo-600" : "bg-slate-800"}`} />
                )}
              </div>
              <p className={`text-[10px] mt-1.5 font-medium text-center ${active ? "text-indigo-400" : done ? "text-slate-400" : "text-slate-600"}`}>
                {stage.label}
              </p>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="w-full bg-slate-800 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full transition-all duration-700 ${isFailed ? "bg-red-500" : "bg-gradient-to-r from-indigo-500 to-violet-500"}`}
          style={{ width: `${isFailed ? 100 : pct}%` }}
        />
      </div>
    </div>
  );
}
