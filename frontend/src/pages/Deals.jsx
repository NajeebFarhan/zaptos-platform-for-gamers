import { useEffect, useMemo, useState } from "react";
import { BadgePercent, RefreshCw } from "lucide-react";
import CategoryIcon from "../components/CategoryIcon";
import DealCard, { DealCardSkeleton } from "../components/DealCard";
import ProductDrawer from "../components/ProductDrawer";
import { EmptyState, ErrorState } from "../components/ui";
import { api, useMeta } from "../lib/api";
import { timeAgo } from "../lib/format";

const SORTS = {
  score: { label: "Best deal", fn: (a, b) => b.deal_score - a.deal_score },
  discount: { label: "Biggest % off", fn: (a, b) => (b.discount_pct || 0) - (a.discount_pct || 0) },
  savings: { label: "Most saved vs other stores", fn: (a, b) => b.savings - a.savings },
  price: { label: "Lowest price", fn: (a, b) => a.min_price - b.min_price },
};

export default function Deals() {
  const meta = useMeta();
  const [state, setState] = useState({ data: null, error: null, loading: true });
  const [category, setCategory] = useState("all");
  const [sort, setSort] = useState("score");
  const [multi, setMulti] = useState(true);
  const [selected, setSelected] = useState(null);

  const load = (refresh = false) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    api(`/api/prices/deals${refresh ? "?refresh=true" : ""}`)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }));
  };
  useEffect(() => {
    document.title = "Best offers · LootScout";
    load();
  }, []);

  const deals = state.data?.deals || [];
  const cats = useMemo(() => {
    const ids = [...new Set(deals.map((d) => d.category))];
    return ids.map((id) => meta?.categories.find((c) => c.id === id) || { id, label: id });
  }, [deals, meta]);
  const shown = useMemo(
    () =>
      deals
        .filter((d) => category === "all" || d.category === category)
        .filter((d) => !multi || d.store_count > 1)
        .sort(SORTS[sort].fn),
    [deals, category, sort, multi],
  );

  return (
    <div className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="mb-2 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-good">
            <BadgePercent className="h-4 w-4" /> Best offers
          </div>
          <h1 className="font-display text-3xl font-bold sm:text-4xl">Today's best gaming deals in India</h1>
          <p className="mt-2 max-w-2xl text-muted">
            Ranked by discount off MRP, how much cheaper the best store is than the others, and buyer ratings.
            {state.data?.generated_at && <> Updated {timeAgo(state.data.generated_at)}.</>}
          </p>
        </div>
        <button className="btn-ghost" onClick={() => load(true)} disabled={state.loading}>
          <RefreshCw className={`h-4 w-4 ${state.loading ? "animate-spin" : ""}`} /> Refresh
        </button>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-2">
        <button className={`chip ${category === "all" ? "chip-active" : ""}`} onClick={() => setCategory("all")}>All</button>
        {cats.map((c) => (
          <button key={c.id} className={`chip ${category === c.id ? "chip-active" : ""}`} onClick={() => setCategory(c.id)}>
            <CategoryIcon id={c.id} className="h-3.5 w-3.5" /> {c.label}
          </button>
        ))}
        <div className="ml-auto flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-muted">
            <input type="checkbox" checked={multi} onChange={(e) => setMulti(e.target.checked)} className="h-4 w-4 accent-[#8b6cff]" />
            Compared at 2+ stores
          </label>
          <select value={sort} onChange={(e) => setSort(e.target.value)} className="rounded-xl border border-line bg-panel-2 px-3 py-2 text-sm outline-none focus:border-brand" aria-label="Sort deals">
            {Object.entries(SORTS).map(([id, s]) => <option key={id} value={id}>{s.label}</option>)}
          </select>
        </div>
      </div>

      {state.error && <ErrorState message={state.error.message} onRetry={() => load()} />}
      {state.loading && !state.data && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 12 }, (_, i) => <DealCardSkeleton key={i} />)}
        </div>
      )}
      {state.data && shown.length === 0 && <EmptyState icon={BadgePercent} title="No offers in this view">Try another category or include single-store deals.</EmptyState>}
      {shown.length > 0 && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {shown.map((d) => <DealCard key={d.id} group={d} onOpen={setSelected} />)}
        </div>
      )}
      <ProductDrawer group={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
