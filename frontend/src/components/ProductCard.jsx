import { ExternalLink, Scale, TrendingDown } from "lucide-react";
import { inr, KIND_LABELS } from "../lib/format";
import { Img, RatingBadge, StoreBadge } from "./ui";

/** One product, priced across stores — modelled on trivago's hotel row. */
export default function ProductCard({ group, onCompare }) {
  const { best, offers } = group;
  const others = offers.filter((o) => o !== offers[0] && o.store !== best.store).slice(0, 3);
  const more = offers.length - 1 - others.length;
  const outOfStock = best.in_stock === false;

  return (
    <article className="card group grid gap-4 p-4 transition hover:border-brand/40 sm:grid-cols-[140px_1fr] lg:grid-cols-[160px_1fr_240px]">
      <button onClick={() => onCompare(group)} className="relative block overflow-hidden rounded-xl bg-white" aria-label="Compare prices">
        <Img src={group.image} srcs={group.images} alt={group.title} className="h-36 w-full p-3 transition group-hover:scale-105 sm:h-full lg:h-40" />
        {group.store_count > 1 && (
          <span className="absolute left-2 top-2 rounded-md bg-ink/85 px-2 py-0.5 text-[11px] font-semibold text-brand-2">
            {group.store_count} stores
          </span>
        )}
      </button>

      <div className="min-w-0 space-y-2.5">
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
          {group.brand && <span className="text-brand-2">{group.brand}</span>}
          {group.kind && <span className="rounded-md bg-panel-3 px-1.5 py-0.5">{KIND_LABELS[group.kind] || group.kind}</span>}
        </div>
        <h3 className="line-clamp-2 font-semibold leading-snug text-text">
          <button onClick={() => onCompare(group)} className="text-left hover:text-brand-2">
            {group.title}
          </button>
        </h3>
        <RatingBadge rating={group.rating} count={group.rating_count} />

        {others.length > 0 && (
          <ul className="grid gap-1.5 pt-1 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
            {others.map((o) => (
              <li key={o.store}>
                <a
                  href={o.url}
                  target="_blank"
                  rel="noopener noreferrer nofollow"
                  className="flex items-center justify-between gap-3 rounded-lg border border-line/70 bg-panel-2/60 px-3 py-1.5 text-sm hover:border-brand/50"
                >
                  <StoreBadge id={o.store} />
                  <span className={`font-semibold ${o.in_stock === false ? "text-dim line-through" : "text-text"}`}>{inr(o.price)}</span>
                </a>
              </li>
            ))}
          </ul>
        )}
        {more > 0 && (
          <button onClick={() => onCompare(group)} className="text-xs font-semibold text-brand hover:underline">
            +{more} more {more === 1 ? "offer" : "offers"}
          </button>
        )}
      </div>

      <div className="flex flex-col justify-between gap-3 rounded-xl border border-line/70 bg-panel-2/70 p-4 sm:col-span-2 lg:col-span-1">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">{outOfStock ? "Lowest listed" : "Best price"}</div>
          <div className={`font-display text-3xl font-bold ${outOfStock ? "text-muted" : "text-good"}`}>{inr(best.price)}</div>
          <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
            <span>at</span>
            <StoreBadge id={best.store} />
            {outOfStock && <span className="text-bad">· out of stock</span>}
          </div>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {group.discount_pct >= 1 && (
              <span className="rounded-md bg-good/15 px-2 py-0.5 text-xs font-semibold text-good">
                {Math.round(group.discount_pct)}% off MRP <span className="font-normal text-muted line-through">{inr(group.mrp)}</span>
              </span>
            )}
            {group.savings >= 100 && (
              <span className="inline-flex items-center gap-1 rounded-md bg-brand-2/10 px-2 py-0.5 text-xs font-semibold text-brand-2">
                <TrendingDown className="h-3.5 w-3.5" /> Save {inr(group.savings)} vs priciest
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <a href={best.url} target="_blank" rel="noopener noreferrer nofollow" className="btn-primary flex-1">
            View deal <ExternalLink className="h-4 w-4" />
          </a>
          <button onClick={() => onCompare(group)} className="btn-ghost px-3" title="Compare all prices" aria-label="Compare all prices">
            <Scale className="h-4 w-4" />
          </button>
        </div>
      </div>
    </article>
  );
}

export function ProductCardSkeleton() {
  return (
    <div className="card grid gap-4 p-4 sm:grid-cols-[140px_1fr] lg:grid-cols-[160px_1fr_240px]">
      <div className="skeleton h-36 lg:h-40" />
      <div className="space-y-3">
        <div className="skeleton h-3 w-24" />
        <div className="skeleton h-5 w-11/12" />
        <div className="skeleton h-5 w-2/3" />
        <div className="skeleton h-4 w-40" />
        <div className="grid gap-2 sm:grid-cols-2">
          <div className="skeleton h-8" />
          <div className="skeleton h-8" />
        </div>
      </div>
      <div className="skeleton h-32 sm:col-span-2 lg:col-span-1 lg:h-full" />
    </div>
  );
}
