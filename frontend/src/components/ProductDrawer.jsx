import { useEffect } from "react";
import { Check, ExternalLink, Info, PackageX, X } from "lucide-react";
import { inr, KIND_LABELS, num } from "../lib/format";
import { Img, RatingBadge, Stars, StoreBadge } from "./ui";

/** Full price comparison for one product: every store, price bars, ratings, stock. */
export default function ProductDrawer({ group, onClose }) {
  useEffect(() => {
    if (!group) return;
    const onKey = (e) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [group, onClose]);

  if (!group) return null;
  const max = Math.max(...group.offers.map((o) => o.price));
  const rated = group.offers.filter((o) => o.rating != null);

  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label="Price comparison">
      <button className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} aria-label="Close" />
      <div className="relative flex h-full w-full max-w-2xl flex-col overflow-y-auto border-l border-line bg-panel scrollbar-thin">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-line bg-panel/95 px-5 py-3 backdrop-blur">
          <div className="font-display text-lg font-semibold">Compare prices</div>
          <button className="btn-ghost px-2.5 py-2" onClick={onClose} aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-6 p-5">
          <div className="flex gap-4">
            <div className="w-32 shrink-0 overflow-hidden rounded-xl bg-white sm:w-40">
              <Img src={group.image} srcs={group.images} alt={group.title} className="h-32 w-full p-2 sm:h-40" />
            </div>
            <div className="min-w-0 space-y-2">
              <div className="flex flex-wrap gap-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
                {group.brand && <span className="text-brand-2">{group.brand}</span>}
                {group.kind && <span>{KIND_LABELS[group.kind] || group.kind}</span>}
              </div>
              <h2 className="text-lg font-semibold leading-snug">{group.title}</h2>
              <RatingBadge rating={group.rating} count={group.rating_count} />
              {rated.length > 1 && <p className="text-xs text-muted">Combined score from {rated.length} stores, weighted by review count.</p>}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <Stat label="Best price" value={inr(group.min_price)} tone="text-good" />
            <Stat label="Highest" value={inr(group.max_price)} />
            <Stat label="You save" value={group.savings > 0 ? inr(group.savings) : "—"} tone="text-brand-2" sub={group.savings_pct ? `${group.savings_pct}%` : null} />
          </div>

          <div>
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted">
              {group.offers.length} {group.offers.length === 1 ? "store" : "stores"} · cheapest first
            </h3>
            <ul className="space-y-2.5">
              {group.offers.map((o, i) => {
                const inStock = o.in_stock !== false;
                const width = Math.max(8, (o.price / max) * 100);
                return (
                  <li key={o.store} className={`rounded-xl border p-3.5 ${i === 0 && inStock ? "border-good/50 bg-good/5" : "border-line bg-panel-2/60"}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <StoreBadge id={o.store} size="lg" />
                          {i === 0 && inStock && <span className="rounded bg-good px-1.5 py-0.5 text-[10px] font-bold uppercase text-ink">Best</span>}
                        </div>
                        <p className="line-clamp-2 text-xs text-muted">{o.title}</p>
                      </div>
                      <div className="shrink-0 text-right">
                        <div className={`font-display text-xl font-bold ${inStock ? "text-text" : "text-dim line-through"}`}>{inr(o.price)}</div>
                        {o.mrp && <div className="text-xs text-dim line-through">{inr(o.mrp)}</div>}
                      </div>
                    </div>
                    <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-panel-3">
                      <div className={`h-full rounded-full ${i === 0 && inStock ? "bg-good" : "bg-brand/70"}`} style={{ width: `${width}%` }} />
                    </div>
                    <div className="mt-2.5 flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-3 text-muted">
                        <Stars rating={o.rating} />
                        {o.rating_count ? <span>{num(o.rating_count)} ratings</span> : null}
                        {o.in_stock === false ? (
                          <span className="inline-flex items-center gap-1 text-bad"><PackageX className="h-3.5 w-3.5" /> Out of stock</span>
                        ) : o.in_stock ? (
                          <span className="inline-flex items-center gap-1 text-good"><Check className="h-3.5 w-3.5" /> In stock</span>
                        ) : (
                          <span className="text-dim">Stock unknown</span>
                        )}
                      </div>
                      <a href={o.url} target="_blank" rel="noopener noreferrer nofollow" className="btn-ghost px-3 py-1.5 text-xs">
                        Go to store <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>

          <p className="flex gap-2 rounded-xl border border-line bg-panel-2/50 p-3 text-xs text-muted">
            <Info className="h-4 w-4 shrink-0 text-brand-2" />
            Listings were matched across stores by brand, model number and variant. Sellers, bundles and warranty can differ —
            check the listing before you buy.
          </p>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, tone = "text-text", sub }) {
  return (
    <div className="rounded-xl border border-line bg-panel-2/60 p-3">
      <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">{label}</div>
      <div className={`font-display text-lg font-bold ${tone}`}>{value}</div>
      {sub && <div className="text-xs text-muted">{sub}</div>}
    </div>
  );
}
