import { cn } from "@/lib/utils";

const colorMap = {
  indigo: { bg: "bg-indigo-50", text: "text-indigo-600", bar: "bg-indigo-600" },
  violet: { bg: "bg-violet-50", text: "text-violet-600", bar: "bg-violet-600" },
  blue: { bg: "bg-blue-50", text: "text-blue-600", bar: "bg-blue-600" },
  emerald: { bg: "bg-emerald-50", text: "text-emerald-600", bar: "bg-emerald-500" },
  gray: { bg: "bg-slate-50", text: "text-slate-500", bar: "bg-slate-400" },
};

interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: React.ReactNode;
  color?: keyof typeof colorMap;
  pulse?: boolean;
}

export function StatCard({ label, value, sub, icon, color = "indigo", pulse }: StatCardProps) {
  const c = colorMap[color];
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 relative overflow-hidden">
      <div className={`absolute top-0 left-0 right-0 h-0.5 ${c.bar}`} />
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</p>
          <div className="flex items-end gap-2 mt-2">
            <p className="text-3xl font-bold text-slate-900 leading-none">{value}</p>
            {pulse && Number(value) > 0 && (
              <span className="mb-0.5 relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
            )}
          </div>
          {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
        </div>
        {icon && (
          <div className={cn("p-2.5 rounded-lg shrink-0", c.bg, c.text)}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
