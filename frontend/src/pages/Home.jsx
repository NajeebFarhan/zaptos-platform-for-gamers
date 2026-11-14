import { useEffect, useState } from "react";
import { Link } from "react-router";
import { ArrowRight, BadgePercent, Flame, Layers, Radar, ShieldCheck } from "lucide-react";
import CategoryIcon from "../components/CategoryIcon";
import DealCard, { DealCardSkeleton } from "../components/DealCard";
import GameCard from "../components/GameCard";
import ProductDrawer from "../components/ProductDrawer";
import SearchBar from "../components/SearchBar";
import { SectionTitle } from "../components/ui";
import { useApi, useMeta } from "../lib/api";

export default function Home() {
  const meta = useMeta();
  const deals = useApi("/api/prices/deals");
  const games = useApi("/api/guides/games");
  const [selected, setSelected] = useState(null);
  useEffect(() => {
    document.title = "Zaptos — Gaming gear prices & game guides";
  }, []);

  const topDeals = (deals.data?.deals || []).filter((d) => d.store_count > 1).slice(0, 8);

  return (
    <div>
      {/* hero */}
      <section className="relative overflow-hidden border-b border-line/60">
        <div className="mx-auto max-w-7xl px-4 pb-14 pt-16 sm:px-6 sm:pt-20">
          <div className="max-w-3xl">
            <span className="mb-5 inline-flex items-center gap-2 rounded-full border border-brand/40 bg-brand/10 px-3 py-1 text-xs font-semibold text-brand">
              <Radar className="h-3.5 w-3.5" /> Live prices from {meta?.stores.length || 10} Indian stores
            </span>
            <h1 className="font-display text-4xl font-bold leading-[1.05] sm:text-6xl">
              Stop overpaying for <span className="text-gradient">gaming gear.</span>
            </h1>
            <p className="mt-5 max-w-2xl text-lg text-muted">
              Search once and compare graphics cards, consoles and accessories across Amazon, Flipkart, MD Computers, PrimeABGB and more —
              with ratings from every store, in rupees.
            </p>
          </div>
          <div className="mt-8 max-w-3xl">
            <SearchBar size="lg" />
          </div>
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <span className="mr-1 inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-muted">
              <Flame className="h-3.5 w-3.5 text-warn" /> Trending
            </span>
            {(meta?.trending || []).map((t) => (
              <Link key={t} to={`/search?q=${encodeURIComponent(t)}`} className="chip">
                {t}
              </Link>
            ))}
          </div>

          <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 border-t border-line/60 pt-6">
            {(meta?.stores || []).map((s) => (
              <span key={s.id} className="inline-flex items-center gap-2 text-sm text-muted">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
                {s.name}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl space-y-20 px-4 pt-14 sm:px-6">
        {/* categories */}
        <section>
          <SectionTitle eyebrow="Browse" title="Shop by category" />
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
            {(meta?.categories || Array.from({ length: 10 }, (_, i) => ({ id: i }))).map((c) =>
              c.label ? (
                <Link
                  key={c.id}
                  to={`/search?q=${encodeURIComponent(c.query)}`}
                  className="card group flex items-center gap-3 p-4 transition hover:border-brand/50 hover:bg-panel-2"
                >
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-brand/10 text-brand transition group-hover:bg-brand group-hover:text-ink">
                    <CategoryIcon id={c.id} />
                  </span>
                  <span className="text-sm font-semibold">{c.label}</span>
                </Link>
              ) : (
                <div key={c.id} className="skeleton h-[74px] rounded-2xl" />
              ),
            )}
          </div>
        </section>

        {/* deals */}
        <section>
          <SectionTitle
            eyebrow="Right now"
            title="Best offers across stores"
            action={
              <Link to="/deals" className="btn-ghost hidden sm:inline-flex">
                All offers <ArrowRight className="h-4 w-4" />
              </Link>
            }
          />
          {deals.loading && (
            <>
              <p className="mb-4 text-sm text-muted">Scanning popular products across every store — first load can take a few seconds…</p>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                {Array.from({ length: 8 }, (_, i) => <DealCardSkeleton key={i} />)}
              </div>
            </>
          )}
          {deals.error && <p className="text-sm text-muted">Couldn't load offers right now ({deals.error.message}).</p>}
          {!deals.loading && topDeals.length > 0 && (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
              {topDeals.map((d) => <DealCard key={d.id} group={d} onOpen={setSelected} />)}
            </div>
          )}
        </section>

        {/* how it works */}
        <section className="grid gap-4 md:grid-cols-3">
          {[
            { icon: Radar, title: "We search every store", text: "One query fans out to marketplaces and PC specialists in parallel, live." },
            { icon: Layers, title: "Same product, grouped", text: "Listings are matched by brand, model number and variant — Ti, Super and Pro never get mixed up." },
            { icon: ShieldCheck, title: "Ratings you can trust", text: "Scores are combined across stores and weighted by how many reviews each store has." },
          ].map(({ icon: Icon, title, text }) => (
            <div key={title} className="card p-6">
              <Icon className="mb-4 h-7 w-7 text-brand-2" />
              <h3 className="font-display text-lg font-semibold">{title}</h3>
              <p className="mt-1.5 text-sm text-muted">{text}</p>
            </div>
          ))}
        </section>

        {/* guides */}
        <section>
          <SectionTitle
            eyebrow="Level up"
            title="Game guides"
            action={
              <Link to="/guides" className="btn-ghost hidden sm:inline-flex">
                All guides <ArrowRight className="h-4 w-4" />
              </Link>
            }
          />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {(games.data?.games || []).map((g) => <GameCard key={g.id} game={g} compact />)}
            {games.loading && Array.from({ length: 4 }, (_, i) => <div key={i} className="skeleton h-[150px] rounded-2xl" />)}
          </div>
        </section>

        <section className="card flex flex-col items-start justify-between gap-4 p-6 sm:flex-row sm:items-center">
          <div className="flex items-center gap-4">
            <BadgePercent className="h-9 w-9 text-good" />
            <div>
              <div className="font-display text-lg font-semibold">Building a PC?</div>
              <p className="text-sm text-muted">Check processors, motherboards, RAM and SSDs — specialist stores are often cheaper than marketplaces.</p>
            </div>
          </div>
          <Link to="/search?q=ryzen%20processor" className="btn-primary">
            Start with a CPU <ArrowRight className="h-4 w-4" />
          </Link>
        </section>
      </div>

      <ProductDrawer group={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
