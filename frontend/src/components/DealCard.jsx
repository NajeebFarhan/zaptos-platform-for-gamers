import { TrendingDown } from "lucide-react";
import { inr } from "../lib/format";
import { Img, RatingBadge, StoreBadge } from "./ui";
import WishlistButton from "./WishlistButton";

export default function DealCard({ group, onOpen }) {
  const pct = group.discount_pct >= 1 ? Math.round(group.discount_pct) : null;
  return (
    <div className="relative h-full transition hover:-translate-y-0.5">
      <button
        onClick={() => onOpen(group)}
        className="card group flex h-full w-full flex-col overflow-hidden text-left transition hover:border-brand/50"
      >
        <div className="relative bg-white">
          <Img src={group.image} srcs={group.images} alt={group.title} className="h-40 w-full p-4 transition group-hover:scale-105" />
          {pct && (
            <span className="absolute left-3 top-3 rounded-lg bg-good px-2 py-1 text-xs font-bold text-ink shadow">−{pct}%</span>
          )}
          {group.store_count > 1 && (
            <span className="absolute right-3 top-3 rounded-lg bg-ink/85 px-2 py-1 text-[11px] font-semibold text-brand-2">
              {group.store_count} stores
            </span>
          )}
        </div>
        <div className="flex flex-1 flex-col gap-2 p-4">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-brand-2">{group.brand || " "}</div>
          <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-text">{group.title}</h3>
          <RatingBadge rating={group.rating} count={group.rating_count} compact />
          <div className="mt-auto pt-2">
            <div className="flex items-baseline gap-2">
              <span className="font-display text-2xl font-bold text-good">{inr(group.min_price)}</span>
              {group.mrp && <span className="text-xs text-dim line-through">{inr(group.mrp)}</span>}
            </div>
            <div className="mt-1 flex items-center justify-between gap-2 text-xs text-muted">
              <StoreBadge id={group.best.store} />
              {group.savings >= 100 && (
                <span className="inline-flex items-center gap-1 text-brand-2">
                  <TrendingDown className="h-3.5 w-3.5" /> {inr(group.savings)}
                </span>
              )}
            </div>
          </div>
        </div>
      </button>
      {/* a sibling of the card button (buttons can't nest), pinned to the image's bottom-right corner */}
      <WishlistButton group={group} variant="overlay" className="absolute right-3 top-[7.25rem]" />
    </div>
  );
}

export function DealCardSkeleton() {
  return (
    <div className="card overflow-hidden">
      <div className="skeleton h-40 rounded-none" />
      <div className="space-y-2 p-4">
        <div className="skeleton h-3 w-16" />
        <div className="skeleton h-4 w-full" />
        <div className="skeleton h-4 w-2/3" />
        <div className="skeleton mt-4 h-7 w-28" />
      </div>
    </div>
  );
}
