import { Check, Clock, LoaderCircle, ShieldAlert, X } from "lucide-react";
import { timeAgo } from "../lib/format";
import { useStores } from "./ui";

/** Live strip showing each store as it is being searched (fed by the SSE stream). */
export default function SearchProgress({ storeIds, statuses, loading }) {
  const stores = useStores();
  const done = Object.keys(statuses).length;
  const total = storeIds.length || 1;

  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between text-xs">
        <span className="font-semibold text-text">
          {loading ? `Checking stores… ${done}/${total}` : `Compared ${total} stores`}
        </span>
        {loading && <span className="text-muted">Results appear when every store has answered</span>}
      </div>
      <div className="mb-3 h-1 overflow-hidden rounded-full bg-panel-3">
        <div className="h-full rounded-full bg-gradient-to-r from-brand to-brand-2 transition-all duration-500" style={{ width: `${(done / total) * 100}%` }} />
      </div>
      <div className="flex flex-wrap gap-2">
        {storeIds.map((id) => {
          const s = statuses[id];
          const meta = stores[id];
          let icon = <LoaderCircle className="h-3.5 w-3.5 animate-spin text-muted" />;
          let note = "";
          let tone = "border-line text-muted";
          if (s) {
            if (s.status === "ok") {
              icon = <Check className="h-3.5 w-3.5 text-good" />;
              note = `${s.count}`;
              tone = s.count ? "border-good/30 text-text" : "border-line text-muted";
            } else if (s.stale) {
              icon = <Clock className="h-3.5 w-3.5 text-warn" />;
              note = `cached ${timeAgo(s.fetched_at)}`;
              tone = "border-warn/40 text-text";
            } else if (s.status === "blocked") {
              icon = <ShieldAlert className="h-3.5 w-3.5 text-bad" />;
              note = "blocked";
              tone = "border-bad/40 text-muted";
            } else {
              icon = <X className="h-3.5 w-3.5 text-bad" />;
              note = s.status;
              tone = "border-bad/40 text-muted";
            }
          }
          return (
            <span
              key={id}
              title={s?.error || (s?.cached ? "served from cache" : "")}
              className={`inline-flex items-center gap-1.5 rounded-lg border bg-panel-2/60 px-2.5 py-1 text-xs ${tone}`}
            >
              <span className="h-2 w-2 rounded-full" style={{ background: meta?.color || "#64748b" }} />
              {meta?.name || id}
              {icon}
              {note && <span className="text-[11px] text-muted">{note}</span>}
            </span>
          );
        })}
      </div>
    </div>
  );
}
