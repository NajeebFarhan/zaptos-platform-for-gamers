import { useEffect } from "react";
import { Link, useParams } from "react-router";
import { ArrowLeft, ExternalLink, Globe } from "lucide-react";
import SafeHtml from "../components/SafeHtml";
import WebResult, { WebResultSkeleton } from "../components/WebResult";
import { ErrorState, Img } from "../components/ui";
import { useApi } from "../lib/api";

const SLOT = { Ability1: "Q", Ability2: "E", Grenade: "C", Ultimate: "X", Passive: "Passive" };

export default function WikiPage() {
  const { gameId, title } = useParams();
  const game = useApi(`/api/guides/${gameId}`).data;
  const page = useApi(`/api/guides/${gameId}/wiki?title=${encodeURIComponent(title)}`);
  const related = useApi(`/api/guides/${gameId}/related?title=${encodeURIComponent(title)}`);
  const d = page.data;
  const accent = game?.accent || "#22e584";
  const agent = d?.agent;

  useEffect(() => {
    document.title = `${title} — ${game?.name || "Guide"} · Zaptos`;
  }, [title, game]);

  return (
    <div>
      <section
        className="relative overflow-hidden border-b border-line/60"
        style={{
          background: agent?.colors?.length
            ? `linear-gradient(120deg, ${agent.colors[0]}55, #040605 70%)`
            : `radial-gradient(900px 300px at 0% 0%, ${accent}30, transparent 70%)`,
        }}
      >
        {agent?.portrait && (
          <img src={agent.portrait} alt="" className="pointer-events-none absolute -right-10 top-0 hidden h-[130%] opacity-90 md:block" referrerPolicy="no-referrer" />
        )}
        <div className="relative mx-auto max-w-7xl px-4 pb-8 pt-8 sm:px-6">
          <Link to={`/guides/${gameId}`} className="mb-5 inline-flex items-center gap-1.5 text-sm text-muted hover:text-text">
            <ArrowLeft className="h-4 w-4" /> {game?.name || "Back"}
          </Link>
          <div className="flex flex-col gap-6 md:flex-row md:items-end">
            {!agent && (d?.image || page.loading) && (
              <div className="h-40 w-40 shrink-0 overflow-hidden rounded-2xl border border-line bg-panel-2">
                {d?.image ? <Img src={d.image} alt={d.title} fit="cover" className="h-full w-full" /> : <div className="skeleton h-full w-full" />}
              </div>
            )}
            <div className="max-w-2xl">
              {agent?.subtitle && (
                <div className="text-xs font-semibold uppercase tracking-[0.18em]" style={{ color: accent }}>{agent.subtitle}</div>
              )}
              <h1 className="font-display text-4xl font-bold sm:text-5xl">{d?.title || title}</h1>
              {agent?.description && <p className="mt-3 text-muted">{agent.description}</p>}
              {d?.source && (
                <p className="mt-3 text-xs text-dim">
                  From the{" "}
                  <a href={d.source.url} target="_blank" rel="noopener noreferrer" className="text-muted underline hover:text-text">
                    {d.source.name}
                  </a>{" "}
                  · <a href={d.source.license_url} target="_blank" rel="noopener noreferrer" className="hover:text-text">{d.source.license}</a>
                </p>
              )}
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        {page.error && <ErrorState title="Couldn't load this page" message={page.error.message} onRetry={page.reload} />}

        {agent?.abilities?.length > 0 && (
          <section className="mb-10">
            <h2 className="mb-4 font-display text-2xl font-bold">Abilities</h2>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {agent.abilities.map((ab) => (
                <div key={ab.name} className="card p-4">
                  <div className="mb-3 flex items-center gap-3">
                    {ab.icon && (
                      <span className="grid h-11 w-11 place-items-center rounded-xl bg-panel-3">
                        <img src={ab.icon} alt="" className="h-7 w-7" referrerPolicy="no-referrer" />
                      </span>
                    )}
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider" style={{ color: accent }}>{SLOT[ab.slot] || ab.slot}</div>
                      <div className="font-semibold">{ab.name}</div>
                    </div>
                  </div>
                  <p className="text-sm leading-6 text-muted">{ab.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        <div className="grid gap-8 lg:grid-cols-[220px_1fr_320px]">
          <nav className="hidden lg:block">
            <div className="sticky top-24 space-y-1">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-dim">On this page</div>
              {d?.infobox?.rows?.length > 0 && <a href="#facts" className="block rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-panel-2 hover:text-text">Quick facts</a>}
              {d?.sections.map((s) => (
                <a key={s.id} href={`#${s.id}`} className="block rounded-lg px-2.5 py-1.5 text-sm text-muted hover:bg-panel-2 hover:text-text">
                  {s.title}
                </a>
              ))}
            </div>
          </nav>

          <article className="min-w-0 space-y-10">
            {page.loading && (
              <div className="space-y-3">
                {Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton h-4" style={{ width: `${70 + ((i * 13) % 30)}%` }} />)}
              </div>
            )}
            {d?.infobox?.rows?.length > 0 && (
              <section id="facts" className="card scroll-mt-24 p-5">
                <h2 className="mb-4 font-display text-xl font-bold">Quick facts</h2>
                <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
                  {d.infobox.rows.map((r, i) => (
                    <div key={i} className="border-b border-line/60 pb-2">
                      <dt className="text-xs font-semibold uppercase tracking-wider text-dim">{r.label}</dt>
                      <dd className="mt-0.5 text-sm text-text">{r.value}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            )}
            {d?.sections.map((s) => (
              <section key={s.id} id={s.id} className="scroll-mt-24">
                <h2 className="mb-3 font-display text-2xl font-bold">{s.title}</h2>
                <SafeHtml html={s.html} />
                {s.truncated && (
                  <a href={d.source.url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-1 text-sm text-brand-2 hover:underline">
                    Continue reading on the wiki <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </section>
            ))}
            {d && d.sections.length === 0 && <p className="text-muted">This wiki page has no readable sections.</p>}
          </article>

          <aside>
            <div className="sticky top-24">
              <h2 className="mb-3 flex items-center gap-2 font-display text-lg font-semibold">
                <Globe className="h-5 w-5 text-brand-2" /> {d?.title || title} guides
              </h2>
              <div className="space-y-3">
                {related.loading && Array.from({ length: 3 }, (_, i) => <WebResultSkeleton key={i} />)}
                {related.data?.results.slice(0, 5).map((r) => <WebResult key={r.url} result={r} gameId={gameId} />)}
                {related.data?.results.length === 0 && <p className="text-sm text-muted">No guides found on the web.</p>}
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
