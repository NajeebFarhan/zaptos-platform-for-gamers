import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import { ArrowLeft, BookOpen, ExternalLink, Newspaper, Search as SearchIcon, X } from "lucide-react";
import SearchBar from "../components/SearchBar";
import WebResult, { WebResultSkeleton } from "../components/WebResult";
import { EmptyState, ErrorState, Img } from "../components/ui";
import { useApi } from "../lib/api";
import { formatDate } from "../lib/format";

export default function GameHub() {
  const { gameId } = useParams();
  const [params, setParams] = useSearchParams();
  const { data: game, error, reload } = useApi(`/api/guides/${gameId}`);
  const q = params.get("q") || "";
  const tab = params.get("tab") || "guides";

  useEffect(() => {
    if (game) document.title = `${game.name} guides · Zaptos`;
  }, [game]);

  if (error) return <div className="mx-auto max-w-3xl px-4 py-16"><ErrorState title="Game not found" message={error.message} onRetry={reload} /></div>;
  if (!game) return <HubSkeleton />;

  const setTab = (t) => setParams(t === "guides" ? {} : { tab: t });
  const tabs = [{ id: "guides", label: "Guides" }, ...game.roster];

  return (
    <div>
      <section
        className="border-b border-line/60"
        style={{ background: `radial-gradient(900px 300px at 0% 0%, ${game.accent}30, transparent 70%)` }}
      >
        <div className="mx-auto max-w-7xl px-4 pb-6 pt-8 sm:px-6">
          <Link to="/guides" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted hover:text-text">
            <ArrowLeft className="h-4 w-4" /> All games
          </Link>
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: game.accent }}>
                {game.publisher} · {game.genre}
              </div>
              <h1 className="mt-1 font-display text-4xl font-bold sm:text-5xl">{game.name}</h1>
              <p className="mt-2 max-w-2xl text-muted">{game.tagline}</p>
            </div>
            <div className="w-full max-w-md">
              <SearchBar
                initial={q}
                placeholder={`Search ${game.short} guides — ${game.search_hint}`}
                to={(v) => `/guides/${game.id}?q=${encodeURIComponent(v)}`}
              />
            </div>
          </div>

          {!q && (
            <div className="scrollbar-thin -mx-1 mt-7 flex gap-1 overflow-x-auto px-1">
              {tabs.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`whitespace-nowrap rounded-xl px-4 py-2 text-sm font-semibold transition ${
                    tab === t.id ? "bg-text text-ink" : "text-muted hover:bg-panel-2 hover:text-text"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        {q ? (
          <SearchResults game={game} q={q} onClear={() => setParams({})} />
        ) : tab === "guides" ? (
          <GuidesTab game={game} />
        ) : (
          <RosterTab key={tab} game={game} rosterId={tab} label={tabs.find((t) => t.id === tab)?.label} />
        )}
      </div>
    </div>
  );
}

function GuidesTab({ game }) {
  const [topic, setTopic] = useState(game.topics[0]?.id);
  const topicRes = useApi(topic ? `/api/guides/${game.id}/topic/${topic}` : null);
  const latest = useApi(`/api/guides/${game.id}/latest`);

  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_340px]">
      <section>
        <h2 className="mb-3 font-display text-xl font-semibold">Popular guide topics</h2>
        <div className="mb-5 flex flex-wrap gap-2">
          {game.topics.map((t) => (
            <button key={t.id} onClick={() => setTopic(t.id)} className={`chip ${topic === t.id ? "chip-active" : ""}`}>
              {t.label}
            </button>
          ))}
        </div>
        {topicRes.loading && <div className="space-y-3">{Array.from({ length: 5 }, (_, i) => <WebResultSkeleton key={i} />)}</div>}
        {topicRes.error && <ErrorState message={topicRes.error.message} onRetry={topicRes.reload} />}
        {topicRes.data && (
          <div className="space-y-3">
            {topicRes.data.results.map((r) => <WebResult key={r.url} result={r} gameId={game.id} />)}
          </div>
        )}
      </section>

      <aside>
        <h2 className="mb-3 flex items-center gap-2 font-display text-xl font-semibold">
          <Newspaper className="h-5 w-5 text-brand-2" /> Latest guides
        </h2>
        {latest.loading && <div className="space-y-3">{Array.from({ length: 4 }, (_, i) => <div key={i} className="skeleton h-24" />)}</div>}
        {latest.data?.items.length === 0 && <p className="text-sm text-muted">No recent articles found.</p>}
        <div className="space-y-3">
          {latest.data?.items.map((a) => (
            <Link
              key={a.url}
              to={`/guides/${game.id}/read?url=${encodeURIComponent(a.url)}`}
              className="card flex gap-3 overflow-hidden p-3 transition hover:border-brand/40"
            >
              {a.image && <Img src={a.image} alt="" fit="cover" className="h-20 w-24 shrink-0 rounded-lg" />}
              <div className="min-w-0">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-brand-2">{a.source}</div>
                <div className="line-clamp-2 text-sm font-semibold leading-snug">{a.title}</div>
                {a.date && <div className="mt-1 text-xs text-dim">{formatDate(a.date)}</div>}
              </div>
            </Link>
          ))}
        </div>
        <a href={game.wiki_url} target="_blank" rel="noopener noreferrer" className="btn-ghost mt-5 w-full">
          <BookOpen className="h-4 w-4" /> Browse the {game.wiki_name} <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </aside>
    </div>
  );
}

function RosterTab({ game, rosterId, label }) {
  const { data, error, loading, reload } = useApi(`/api/guides/${game.id}/roster/${rosterId}`);
  const [filter, setFilter] = useState("");
  const [active, setActive] = useState({}); // {groupLabel: tag}

  const items = data?.items || [];
  const groups = useMemo(() => {
    const g = {};
    for (const it of items) for (const [label, tags] of Object.entries(it.tags || {})) for (const t of tags) (g[label] ??= new Set()).add(t);
    return Object.entries(g).map(([label, set]) => [label, [...set]]).filter(([, tags]) => tags.length > 1 && tags.length < 12);
  }, [items]);
  const shown = items.filter(
    (it) =>
      it.title.toLowerCase().includes(filter.toLowerCase()) &&
      Object.entries(active).every(([label, tag]) => !tag || (it.tags?.[label] || []).includes(tag)),
  );

  if (error) return <ErrorState message={error.message} onRetry={reload} />;

  return (
    <div>
      <div className="mb-5 flex flex-wrap items-center gap-3">
        <div className="relative w-full sm:w-64">
          <SearchIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-dim" />
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder={`Filter ${label?.toLowerCase() || "list"}…`}
            className="w-full rounded-xl border border-line bg-panel-2 py-2 pl-9 pr-3 text-sm outline-none focus:border-brand"
          />
        </div>
        {groups.map(([groupLabel, tags]) => (
          <div key={groupLabel} className="flex flex-wrap items-center gap-1.5">
            <span className="mr-1 text-xs font-semibold uppercase tracking-wider text-dim">{groupLabel}</span>
            {tags.sort().map((t) => (
              <button
                key={t}
                onClick={() => setActive((a) => ({ ...a, [groupLabel]: a[groupLabel] === t ? null : t }))}
                className={`chip py-1 ${active[groupLabel] === t ? "chip-active" : ""}`}
              >
                {t}
              </button>
            ))}
          </div>
        ))}
        {data && <span className="ml-auto text-xs text-muted">{shown.length} of {items.length}</span>}
      </div>

      {loading && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {Array.from({ length: 18 }, (_, i) => <div key={i} className="skeleton aspect-[3/4] rounded-2xl" />)}
        </div>
      )}
      {data && shown.length === 0 && (
        <EmptyState icon={X} title="Nothing matches">
          Clear a filter to see more.
        </EmptyState>
      )}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
        {shown.map((it) => (
          <Link
            key={it.title}
            to={`/guides/${game.id}/wiki/${encodeURIComponent(it.wiki_title || it.title)}`}
            className="card group overflow-hidden transition hover:-translate-y-0.5 hover:border-brand/50"
          >
            <div
              className="relative aspect-square overflow-hidden"
              style={{ background: it.colors?.length ? `linear-gradient(160deg, ${it.colors.slice(0, 2).join(",")})` : `linear-gradient(160deg, ${game.accent}26, #191c27)` }}
            >
              <Img src={it.image} alt={it.title} fit={rosterId === "weapons" || rosterId === "equipment" ? "contain" : "cover"} className="h-full w-full p-1 transition duration-300 group-hover:scale-105" />
            </div>
            <div className="p-3">
              <div className="truncate text-sm font-semibold">{it.title}</div>
              {it.subtitle && <div className="truncate text-xs text-muted">{it.subtitle}</div>}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function SearchResults({ game, q, onClear }) {
  const { data, error, loading, reload } = useApi(`/api/guides/${game.id}/search?q=${encodeURIComponent(q)}`);
  return (
    <div>
      <div className="mb-5 flex items-center gap-3">
        <h2 className="font-display text-xl font-semibold">
          Results for <span className="text-gradient">"{q}"</span>
        </h2>
        <button className="chip" onClick={onClear}>
          <X className="h-3.5 w-3.5" /> Clear
        </button>
      </div>
      {error && <ErrorState message={error.message} onRetry={reload} />}
      <div className="grid gap-8 lg:grid-cols-[1fr_320px]">
        <section>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">Guides from around the web</h3>
          {loading && <div className="space-y-3">{Array.from({ length: 5 }, (_, i) => <WebResultSkeleton key={i} />)}</div>}
          {data && data.web.length === 0 && <p className="text-sm text-muted">No web guides found — try different words.</p>}
          <div className="space-y-3">
            {data?.web.map((r) => <WebResult key={r.url} result={r} gameId={game.id} />)}
          </div>
        </section>
        <aside>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted">On the {game.wiki_name}</h3>
          {loading && <div className="space-y-2">{Array.from({ length: 5 }, (_, i) => <div key={i} className="skeleton h-16" />)}</div>}
          {data && data.wiki.length === 0 && <p className="text-sm text-muted">No wiki pages matched.</p>}
          <div className="space-y-2">
            {data?.wiki.map((w) => (
              <Link
                key={w.title}
                to={`/guides/${game.id}/wiki/${encodeURIComponent(w.title)}`}
                className="card flex items-center gap-3 p-2.5 transition hover:border-brand/40"
              >
                <Img src={w.image} alt="" fit="cover" className="h-12 w-12 shrink-0 rounded-lg" />
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold">{w.title}</div>
                  <div className="line-clamp-1 text-xs text-muted">{w.snippet}</div>
                </div>
              </Link>
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}

function HubSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-4 px-4 py-10 sm:px-6">
      <div className="skeleton h-4 w-24" />
      <div className="skeleton h-12 w-80" />
      <div className="skeleton h-5 w-96" />
      <div className="skeleton mt-8 h-64" />
    </div>
  );
}
