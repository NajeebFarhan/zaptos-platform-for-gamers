import { useStores } from "./ui";

export const DEFAULT_FILTERS = {
  sort: "relevance",
  minPrice: "",
  maxPrice: "",
  stores: [],
  minRating: 0,
  inStock: false,
  multiStore: false,
  hideAccessories: false,
};

export const SORTS = [
  { id: "relevance", label: "Best match" },
  { id: "price_asc", label: "Price: low to high" },
  { id: "price_desc", label: "Price: high to low" },
  { id: "rating", label: "Top rated" },
  { id: "savings", label: "Biggest savings" },
  { id: "stores", label: "Most stores" },
];

/** Restrict a product to the chosen stores and recompute its best price. */
function restrict(group, stores) {
  if (!stores.length) return group;
  const offers = group.offers.filter((o) => stores.includes(o.store));
  if (!offers.length) return null;
  if (offers.length === group.offers.length) return group;
  const best = offers[0];
  const live = offers.filter((o) => o.in_stock !== false).map((o) => o.price);
  const prices = live.length ? live : offers.map((o) => o.price);
  const max = Math.max(...prices);
  return {
    ...group, offers, best, store_count: offers.length, min_price: best.price, max_price: max,
    savings: max - best.price, savings_pct: max ? Math.round(((max - best.price) / max) * 1000) / 10 : 0,
    discount_pct: group.mrp ? Math.round(((group.mrp - best.price) / group.mrp) * 1000) / 10 : null,
  };
}

export function applyFilters(groups, f) {
  const min = Number(f.minPrice) || 0;
  const max = Number(f.maxPrice) || Infinity;
  let out = groups
    .map((g) => restrict(g, f.stores))
    .filter(Boolean)
    .filter((g) => g.min_price >= min && g.min_price <= max)
    .filter((g) => !f.minRating || (g.rating ?? 0) >= f.minRating)
    .filter((g) => !f.inStock || g.best.in_stock !== false)
    .filter((g) => !f.multiStore || g.store_count > 1)
    .filter((g) => !f.hideAccessories || g.kind !== "accessory");

  const by = {
    relevance: (a, b) => b.relevance - a.relevance || a.min_price - b.min_price,
    price_asc: (a, b) => a.min_price - b.min_price,
    price_desc: (a, b) => b.min_price - a.min_price,
    rating: (a, b) => (b.rating ?? 0) - (a.rating ?? 0) || b.rating_count - a.rating_count,
    savings: (a, b) => b.savings - a.savings,
    stores: (a, b) => b.store_count - a.store_count || b.relevance - a.relevance,
  }[f.sort];
  return [...out].sort(by);
}

export default function Filters({ filters, setFilters, storeCounts }) {
  const stores = useStores();
  const set = (patch) => setFilters((f) => ({ ...f, ...patch }));
  const toggleStore = (id) =>
    set({ stores: filters.stores.includes(id) ? filters.stores.filter((s) => s !== id) : [...filters.stores, id] });

  return (
    <div className="space-y-6">
      <Group title="Price (₹)">
        <div className="flex items-center gap-2">
          <PriceInput placeholder="Min" value={filters.minPrice} onChange={(v) => set({ minPrice: v })} />
          <span className="text-dim">–</span>
          <PriceInput placeholder="Max" value={filters.maxPrice} onChange={(v) => set({ maxPrice: v })} />
        </div>
      </Group>

      <Group title="Rating">
        <div className="flex flex-wrap gap-2">
          {[0, 3.5, 4, 4.5].map((r) => (
            <button key={r} onClick={() => set({ minRating: r })} className={`chip ${filters.minRating === r ? "chip-active" : ""}`}>
              {r ? `${r}+ ★` : "Any"}
            </button>
          ))}
        </div>
      </Group>

      <Group title="Show">
        <Toggle label="In stock only" checked={filters.inStock} onChange={(v) => set({ inStock: v })} />
        <Toggle label="Compared at 2+ stores" checked={filters.multiStore} onChange={(v) => set({ multiStore: v })} />
        <Toggle label="Hide accessories" checked={filters.hideAccessories} onChange={(v) => set({ hideAccessories: v })} />
      </Group>

      <Group
        title="Stores"
        action={
          filters.stores.length > 0 && (
            <button className="text-xs text-brand hover:underline" onClick={() => set({ stores: [] })}>
              All stores
            </button>
          )
        }
      >
        <div className="space-y-1">
          {Object.values(stores).map((s) => {
            const count = storeCounts[s.id] || 0;
            const on = filters.stores.includes(s.id);
            return (
              <label
                key={s.id}
                className={`flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm hover:bg-panel-2 ${count ? "" : "opacity-50"}`}
              >
                <input type="checkbox" checked={on} onChange={() => toggleStore(s.id)} className="h-4 w-4 accent-[#8b6cff]" />
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
                <span className="flex-1 text-text">{s.name}</span>
                <span className="text-xs text-dim">{count}</span>
              </label>
            );
          })}
        </div>
      </Group>

      <button className="btn-ghost w-full" onClick={() => setFilters((f) => ({ ...DEFAULT_FILTERS, sort: f.sort }))}>
        Reset filters
      </button>
    </div>
  );
}

function Group({ title, action, children }) {
  return (
    <section>
      <div className="mb-2.5 flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted">{title}</h3>
        {action}
      </div>
      <div className="space-y-2">{children}</div>
    </section>
  );
}

function PriceInput({ value, onChange, placeholder }) {
  return (
    <input
      inputMode="numeric"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value.replace(/[^\d]/g, ""))}
      className="w-full rounded-lg border border-line bg-panel-2 px-3 py-2 text-sm outline-none focus:border-brand"
    />
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 text-sm text-text">
      {label}
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-5 w-9 rounded-full transition ${checked ? "bg-brand" : "bg-panel-3"}`}
      >
        <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition ${checked ? "left-4.5" : "left-0.5"}`} />
      </button>
    </label>
  );
}
