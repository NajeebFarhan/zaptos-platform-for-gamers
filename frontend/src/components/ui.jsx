import { useState } from "react";
import { AlertTriangle, ImageOff, LoaderCircle, Star } from "lucide-react";
import { useMeta } from "../lib/api";
import { num, ratingWord } from "../lib/format";

export function useStores() {
  const meta = useMeta();
  return Object.fromEntries((meta?.stores || []).map((s) => [s.id, s]));
}

export function StoreBadge({ id, size = "sm", className = "" }) {
  const stores = useStores();
  const s = stores[id];
  const name = s?.name || id;
  const color = s?.color || "#64748b";
  const text = size === "lg" ? "text-sm" : "text-xs";
  return (
    <span className={`inline-flex items-center gap-1.5 font-medium text-text ${text} ${className}`}>
      <span className="h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-white/10" style={{ background: color }} />
      {name}
    </span>
  );
}

/** trivago-style score box: "4.6 Excellent · 1,346 reviews" */
export function RatingBadge({ rating, count, compact = false }) {
  if (rating == null) return <span className="text-xs text-dim">No ratings yet</span>;
  const tone = rating >= 4.5 ? "bg-good" : rating >= 4 ? "bg-[#4ade80]/80" : rating >= 3.5 ? "bg-warn" : "bg-bad";
  return (
    <span className="inline-flex items-center gap-2">
      <span className={`rounded-md px-1.5 py-0.5 text-xs font-bold text-ink ${tone}`}>{rating.toFixed(1)}</span>
      {!compact && <span className="text-xs font-semibold text-text">{ratingWord(rating)}</span>}
      {count > 0 && <span className="text-xs text-muted">({num(count)} reviews)</span>}
    </span>
  );
}

export function Stars({ rating }) {
  if (rating == null) return <span className="text-xs text-dim">—</span>;
  return (
    <span className="inline-flex items-center gap-1 text-xs text-text">
      <Star className="h-3.5 w-3.5 fill-warn text-warn" />
      {rating.toFixed(1)}
    </span>
  );
}

export function Spinner({ className = "h-5 w-5" }) {
  return <LoaderCircle className={`animate-spin text-brand ${className}`} />;
}

/** Image with graceful fallback; `srcs` lists alternates tried in order (stores that block hotlinking). */
export function Img({ src, srcs, alt = "", className = "", fit = "contain" }) {
  const list = (srcs?.length ? srcs : [src]).filter(Boolean);
  const [idx, setIdx] = useState(0);
  const current = list[idx];
  if (!current) {
    return (
      <div className={`flex items-center justify-center bg-panel-3/50 text-dim ${className}`}>
        <ImageOff className="h-6 w-6" />
      </div>
    );
  }
  return (
    <img
      key={current}
      src={current}
      alt={alt}
      loading="lazy"
      referrerPolicy="no-referrer"
      onError={() => setIdx((i) => i + 1)}
      className={`${fit === "cover" ? "object-cover" : "object-contain"} ${className}`}
    />
  );
}

export function ErrorState({ title = "Something went wrong", message, onRetry }) {
  return (
    <div className="card flex flex-col items-center gap-3 p-8 text-center">
      <AlertTriangle className="h-8 w-8 text-warn" />
      <div className="font-display text-lg font-semibold">{title}</div>
      {message && <p className="max-w-md text-sm text-muted">{message}</p>}
      {onRetry && (
        <button className="btn-ghost" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, children }) {
  return (
    <div className="card flex flex-col items-center gap-3 p-10 text-center">
      {Icon && <Icon className="h-9 w-9 text-dim" />}
      <div className="font-display text-lg font-semibold">{title}</div>
      {children && <div className="max-w-md text-sm text-muted">{children}</div>}
    </div>
  );
}

export function SectionTitle({ eyebrow, title, action }) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4">
      <div>
        {eyebrow && <div className="mb-1 text-xs font-semibold uppercase tracking-[0.18em] text-brand-2">{eyebrow}</div>}
        <h2 className="font-display text-2xl font-bold sm:text-3xl">{title}</h2>
      </div>
      {action}
    </div>
  );
}
