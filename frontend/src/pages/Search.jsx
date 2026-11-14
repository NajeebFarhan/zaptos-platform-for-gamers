import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { PackageSearch, RefreshCw, SlidersHorizontal, X } from "lucide-react";
import CategoryIcon from "../components/CategoryIcon";
import Filters, { applyFilters, DEFAULT_FILTERS, SORTS } from "../components/Filters";
import ProductCard, { ProductCardSkeleton } from "../components/ProductCard";
import ProductDrawer from "../components/ProductDrawer";
import SearchBar from "../components/SearchBar";
import SearchProgress from "../components/SearchProgress";
import { EmptyState, ErrorState } from "../components/ui";
import { useMeta, usePriceSearch } from "../lib/api";
import { num, timeAgo } from "../lib/format";

const PAGE = 15;

export default function Search() {
  const [params] = useSearchParams();
  const q = (params.get("q") || "").trim();
  const meta = useMeta();
  const [refresh, setRefresh] = useState({ q: null, n: 0 });
  const search = usePriceSearch(q, refresh);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [visible, setVisible] = useState(PAGE);
  const [selected, setSelected] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    setFilters(DEFAULT_FILTERS);
    setVisible(PAGE);
  }, [q]);
  useEffect(() => {
    document.title = q ? `${q} — price comparison · Zaptos` : "Compare prices · Zaptos";
  }, [q]);

  const result = search.result;
  const groups = useMemo(() => (result ? applyFilters(result.groups, filters) : []), [result, filters]);
  const storeCounts = useMemo(() => {
    const c = {};
    for (const g of result?.groups || []) for (const o of g.offers) c[o.store] = (c[o.store] || 0) + 1;
    return c;
  }, [result]);
  const category = meta?.categories.find((c) => c.query.toLowerCase() === q.toLowerCase() || c.chips.some((x) => x.toLowerCase() === q.toLowerCase()));
  const storeIds = meta?.stores.map((s) => s.id) || Object.keys(search.stores);
  const loading = search.status === "loading";

  if (!q) return <SearchLanding meta={meta} />;

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <div className="mb-5 max-w-3xl">
        <SearchBar initial={q} />
      </div>

      {category && (
        <div className="mb-5 flex flex-wrap items-center gap-2">
          <span className="mr-1 inline-flex items-center gap-2 text-sm font-semibold text-text">
            <CategoryIcon id={category.id} className="h-4 w-4 text-brand" /> {category.label}
          </span>
          {category.chips.map((chip) => (
            <Link key={chip} to={`/search?q=${encodeURIComponent(chip)}`} className={`chip ${chip.toLowerCase() === q.toLowerCase() ? "chip-active" : ""}`}>
              {chip}
            </Link>
          ))}
        </div>
      )}

      <div className="mb-6">
        <SearchProgress storeIds={storeIds} statuses={search.stores} loading={loading} />
      </div>

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <aside className={`${showFilters ? "fixed inset-0 z-50 overflow-y-auto bg-ink p-5" : "hidden"} lg:static lg:block lg:p-0`}>
          <div className="mb-4 flex items-center justify-between lg:hidden">
            <span className="font-display text-lg font-semibold">Filters</span>
            <button className="btn-ghost px-2.5" onClick={() => setShowFilters(false)} aria-label="Close filters">
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="lg:sticky lg:top-24">
            <Filters filters={filters} setFilters={setFilters} storeCounts={storeCounts} />
          </div>
        </aside>

        <section className="min-w-0">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="text-sm text-muted">
              {result ? (
                <>
                  <span className="font-semibold text-text">{num(groups.length)}</span> products ·{" "}
                  {num(result.total_offers)} listings for <span className="text-text">"{q}"</span>
                  {result.generated_at && <> · updated {timeAgo(Math.min(...result.stores.map((s) => s.fetched_at || result.generated_at)))}</>}
                </>
              ) : (
                <>Searching for <span className="text-text">"{q}"</span>…</>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button className="btn-ghost px-3 py-2 lg:hidden" onClick={() => setShowFilters(true)}>
                <SlidersHorizontal className="h-4 w-4" /> Filters
              </button>
              <select
                value={filters.sort}
                onChange={(e) => setFilters((f) => ({ ...f, sort: e.target.value }))}
                className="rounded-xl border border-line bg-panel-2 px-3 py-2 text-sm text-text outline-none focus:border-brand"
                aria-label="Sort"
              >
                {SORTS.map((s) => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
              <button
                className="btn-ghost px-3 py-2"
                onClick={() => setRefresh((r) => ({ q, n: r.n + 1 }))}
                disabled={loading}
                title="Fetch fresh prices from every store"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                <span className="hidden sm:inline">Refresh</span>
              </button>
            </div>
          </div>

          {search.status === "error" && <ErrorState message={search.error?.message} onRetry={() => setRefresh((r) => ({ q, n: r.n + 1 }))} />}

          {loading && (
            <div className="space-y-4">
              {Array.from({ length: 4 }, (_, i) => <ProductCardSkeleton key={i} />)}
            </div>
          )}

          {result && groups.length === 0 && (
            <EmptyState icon={PackageSearch} title="No matching products">
              {result.groups.length ? "Try loosening the filters." : "None of the stores returned results. Try a broader search, e.g. a model name like “RTX 5060”."}
            </EmptyState>
          )}

          {result && groups.length > 0 && (
            <div className="space-y-4">
              {groups.slice(0, visible).map((g) => (
                <ProductCard key={g.id} group={g} query={q} onCompare={setSelected} />
              ))}
              {visible < groups.length && (
                <button className="btn-ghost w-full py-3" onClick={() => setVisible((v) => v + PAGE)}>
                  Show more ({groups.length - visible} left)
                </button>
              )}
            </div>
          )}
        </section>
      </div>

      <ProductDrawer group={selected} query={q} onClose={() => setSelected(null)} />
    </div>
  );
}

function SearchLanding({ meta }) {
  return (
    <div className="mx-auto max-w-5xl px-4 py-14 sm:px-6">
      <h1 className="mb-2 font-display text-3xl font-bold sm:text-4xl">Compare prices</h1>
      <p className="mb-6 text-muted">Search once — we check {meta?.stores.length || 10} Indian stores at the same time.</p>
      <SearchBar size="lg" autoFocus />
      <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
        {(meta?.categories || []).map((c) => (
          <Link key={c.id} to={`/search?q=${encodeURIComponent(c.query)}`} className="card flex flex-col items-center gap-2 p-4 text-center text-sm hover:border-brand/50">
            <CategoryIcon id={c.id} className="h-6 w-6 text-brand" />
            {c.label}
          </Link>
        ))}
      </div>
    </div>
  );
}
