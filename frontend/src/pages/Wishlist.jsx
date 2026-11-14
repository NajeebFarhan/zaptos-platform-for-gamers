import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router";
import { ArrowDownRight, ArrowUpRight, ExternalLink, Heart, RefreshCw, Scale, SearchX, Trash2 } from "lucide-react";
import ProductDrawer from "../components/ProductDrawer";
import { EmptyState, Img, RatingBadge, StoreBadge } from "../components/ui";
import { api } from "../lib/api";
import { inr, KIND_LABELS, timeAgo } from "../lib/format";
import { applyTrackResults, clearAll, removeItem, trackPayload, useWishlist } from "../lib/wishlist";

const STALE_MS = 30 * 60 * 1000; // matches the backend price cache
const BATCH = 20;

const SORTS = {
  recent: { label: "Recently saved", fn: (a, b) => b.saved_at - a.saved_at },
  drop: { label: "Biggest price drop", fn: (a, b) => delta(a) - delta(b) },
  price: { label: "Lowest price", fn: (a, b) => a.group.min_price - b.group.min_price },
};

const delta = (it) => it.group.min_price - it.saved_price;

export default function Wishlist() {
  const { items } = useWishlist();
  const [sort, setSort] = useState("recent");
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const autoChecked = useRef(false);

  useEffect(() => {
    document.title = "Wishlist · Zaptos";
  }, []);

  const check = useCallback(async (list, refresh = false) => {
    if (!list.length) return;
    setChecking(true);
    setError(null);
    try {
      for (let i = 0; i < list.length; i += BATCH) {
        const res = await api(`/api/prices/track${refresh ? "?refresh=true" : ""}`, { body: trackPayload(list.slice(i, i + BATCH)) });
        applyTrackResults(res.results, res.generated_at * 1000);
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setChecking(false);
    }
  }, []);

  // refresh items whose prices are older than the cache window, once per visit
  useEffect(() => {
    if (autoChecked.current) return;
    autoChecked.current = true;
    const stale = items.filter((it) => !it.checked_at || Date.now() - it.checked_at > STALE_MS);
    check(stale);
  }, [items, check]);

  const shown = useMemo(() => [...items].sort(SORTS[sort].fn), [items, sort]);
  const drops = items.filter((it) => it.status === "ok" && delta(it) <= -1);
  const total = items.reduce((s, it) => s + it.group.min_price, 0);
  const lastChecked = items.length ? Math.max(...items.map((it) => it.checked_at || 0)) : 0;

  if (!items.length) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16 sm:px-6">
        <EmptyState icon={Heart} title="Your wishlist is empty">
          <p>Tap the heart on any product to save it here. We'll keep checking every store so you can see when the price drops.</p>
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            <Link to="/deals" className="btn-primary">Browse best offers</Link>
            <Link to="/search" className="btn-ghost">Compare prices</Link>
          </div>
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-bad">
            <Heart className="h-4 w-4 fill-bad" /> Wishlist
          </div>
          <h1 className="font-display text-3xl font-bold sm:text-4xl">Saved products</h1>
          <p className="mt-2 text-muted">
            {items.length} {items.length === 1 ? "item" : "items"} · {inr(total)} at today's best prices
            {lastChecked > 0 && <> · checked {timeAgo(lastChecked / 1000)}</>}
          </p>
          <p className="mt-1 text-xs text-dim">Saved on this device only.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="rounded-xl border border-line bg-panel-2 px-3 py-2 text-sm text-text outline-none focus:border-brand"
            aria-label="Sort wishlist"
          >
            {Object.entries(SORTS).map(([id, s]) => <option key={id} value={id}>{s.label}</option>)}
          </select>
          <button className="btn-ghost" onClick={() => check(items, true)} disabled={checking} title="Fetch fresh prices from every store">
            <RefreshCw className={`h-4 w-4 ${checking ? "animate-spin" : ""}`} />
            {checking ? "Checking…" : "Check prices"}
          </button>
        </div>
      </div>

      {drops.length > 0 && (
        <div className="mb-5 flex items-center gap-2 rounded-xl border border-good/40 bg-good/10 px-4 py-3 text-sm text-text">
          <ArrowDownRight className="h-4 w-4 shrink-0 text-good" />
          {drops.length === 1 ? "1 product is" : `${drops.length} products are`} cheaper than when you saved{" "}
          {drops.length === 1 ? "it" : "them"}.
        </div>
      )}
      {error && (
        <div className="mb-5 rounded-xl border border-warn/40 bg-warn/10 px-4 py-3 text-sm text-text">
          Couldn't check the latest prices ({error}). Showing the last known prices.
        </div>
      )}

      <ul className="space-y-3">
        {shown.map((it) => (
          <WishlistRow key={it.key} item={it} checking={checking} onCompare={() => setSelected(it)} />
        ))}
      </ul>

      <div className="mt-8 flex justify-end">
        <button
          className="btn-ghost text-muted hover:border-bad/60 hover:text-bad"
          onClick={() => window.confirm("Remove every product from your wishlist?") && clearAll()}
        >
          <Trash2 className="h-4 w-4" /> Clear wishlist
        </button>
      </div>

      <ProductDrawer group={selected?.group ?? null} query={selected?.query} onClose={() => setSelected(null)} />
    </div>
  );
}

function WishlistRow({ item, checking, onCompare }) {
  const { group } = item;
  const d = delta(item);
  const outOfStock = group.best.in_stock === false;
  const missing = item.status === "missing";

  return (
    <li className={`card grid gap-4 p-4 sm:grid-cols-[112px_1fr_auto] ${missing ? "opacity-80" : ""}`}>
      <button onClick={onCompare} className="block overflow-hidden rounded-xl bg-white" aria-label="Compare prices">
        <Img src={group.image} srcs={group.images} alt={group.title} className="h-28 w-full p-2" />
      </button>

      <div className="min-w-0 space-y-2">
        <div className="flex flex-wrap items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-muted">
          {group.brand && <span className="text-brand-2">{group.brand}</span>}
          {group.kind && <span className="rounded-md bg-panel-3 px-1.5 py-0.5">{KIND_LABELS[group.kind] || group.kind}</span>}
          <span className="font-normal normal-case tracking-normal text-dim">saved {timeAgo(item.saved_at / 1000)}</span>
        </div>
        <h3 className="line-clamp-2 font-semibold leading-snug">
          <button onClick={onCompare} className="text-left hover:text-brand-2">{group.title}</button>
        </h3>
        <RatingBadge rating={group.rating} count={group.rating_count} compact />
        {missing && (
          <p className="inline-flex items-center gap-1.5 text-xs text-warn">
            <SearchX className="h-3.5 w-3.5" /> Not found in the latest search. Showing the last known prices.
          </p>
        )}
        {item.status === "error" && <p className="text-xs text-warn">Couldn't refresh this one. Showing the last known prices.</p>}
      </div>

      <div className="flex flex-col justify-between gap-3 sm:min-w-[210px] sm:items-end sm:text-right">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-muted">{outOfStock ? "Lowest listed" : "Best price"}</div>
          <div className={`font-display text-2xl font-bold ${outOfStock ? "text-muted" : "text-good"} ${checking ? "animate-pulse" : ""}`}>
            {inr(group.min_price)}
          </div>
          <div className="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-muted sm:justify-end">
            <span>at</span> <StoreBadge id={group.best.store} />
            {group.store_count > 1 && <span>· {group.store_count} stores</span>}
            {outOfStock && <span className="text-bad">· out of stock</span>}
          </div>
          <PriceChange delta={d} saved={item.saved_price} />
        </div>
        <div className="flex gap-2">
          <a href={group.best.url} target="_blank" rel="noopener noreferrer nofollow" className="btn-primary px-3 py-2">
            View deal <ExternalLink className="h-4 w-4" />
          </a>
          <button onClick={onCompare} className="btn-ghost px-3 py-2" title="Compare all prices" aria-label="Compare all prices">
            <Scale className="h-4 w-4" />
          </button>
          <button
            onClick={() => removeItem(item.key)}
            className="btn-ghost px-3 py-2 hover:border-bad/60 hover:text-bad"
            title="Remove from wishlist"
            aria-label="Remove from wishlist"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
    </li>
  );
}

function PriceChange({ delta: d, saved }) {
  if (Math.abs(d) < 1) return <div className="mt-1.5 text-xs text-dim">Same as when saved ({inr(saved)})</div>;
  const down = d < 0;
  const pct = saved ? Math.round((Math.abs(d) / saved) * 100) : 0;
  const Icon = down ? ArrowDownRight : ArrowUpRight;
  return (
    <div className={`mt-1.5 inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-semibold ${down ? "bg-good/15 text-good" : "bg-bad/15 text-bad"}`}>
      <Icon className="h-3.5 w-3.5" />
      {inr(Math.abs(d))} {down ? "less" : "more"}{pct ? ` (${pct}%)` : ""}
      <span className="font-normal text-muted">· was {inr(saved)}</span>
    </div>
  );
}
