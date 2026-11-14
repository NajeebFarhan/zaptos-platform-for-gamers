import { useEffect } from "react";
import { Link, useParams, useSearchParams } from "react-router";
import { ArrowLeft, Calendar, Clock, ExternalLink, User } from "lucide-react";
import SafeHtml from "../components/SafeHtml";
import { ErrorState, Img } from "../components/ui";
import { useApi } from "../lib/api";
import { formatDate } from "../lib/format";

export default function Reader() {
  const { gameId } = useParams();
  const [params] = useSearchParams();
  const url = params.get("url") || "";
  const game = useApi(`/api/guides/${gameId}`).data;
  const { data: a, error, loading, reload } = useApi(url ? `/api/guides/article?url=${encodeURIComponent(url)}` : null);

  useEffect(() => {
    if (a) document.title = `${a.title} · LootScout`;
  }, [a]);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 sm:px-6">
      <Link to={`/guides/${gameId}`} className="mb-6 inline-flex items-center gap-1.5 text-sm text-muted hover:text-text">
        <ArrowLeft className="h-4 w-4" /> {game?.name || "Guides"}
      </Link>

      {error && <ErrorState title="This article can't be shown in the reader" message={error.message} onRetry={reload} />}
      {error && url && (
        <div className="mt-4 text-center">
          <a href={url} target="_blank" rel="noopener noreferrer" className="btn-primary">
            Open it on the original site <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      )}

      {loading && (
        <div className="space-y-4">
          <div className="skeleton h-4 w-32" />
          <div className="skeleton h-10 w-full" />
          <div className="skeleton h-10 w-3/4" />
          <div className="skeleton mt-6 h-64 w-full" />
          {Array.from({ length: 8 }, (_, i) => <div key={i} className="skeleton h-4" />)}
        </div>
      )}

      {a && (
        <article>
          <div className="mb-3 flex items-center gap-2 text-sm">
            <img src={`https://icons.duckduckgo.com/ip3/${a.domain}.ico`} alt="" className="h-4 w-4 rounded" referrerPolicy="no-referrer" />
            <span className="font-semibold text-brand-2">{a.sitename}</span>
          </div>
          <h1 className="font-display text-3xl font-bold leading-tight sm:text-4xl">{a.title}</h1>
          <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted">
            {a.author && <span className="inline-flex items-center gap-1.5"><User className="h-4 w-4" />{a.author}</span>}
            {a.date && <span className="inline-flex items-center gap-1.5"><Calendar className="h-4 w-4" />{formatDate(a.date)}</span>}
            <span className="inline-flex items-center gap-1.5"><Clock className="h-4 w-4" />{a.minutes} min read</span>
            <a href={a.url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-text hover:text-brand-2">
              Original article <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>
          {a.image && !a.html.includes(a.image) && (
            <Img src={a.image} alt="" fit="cover" className="mt-6 max-h-[380px] w-full rounded-2xl border border-line" />
          )}
          <div className="mt-8">
            <SafeHtml html={a.html} />
          </div>
          <div className="mt-10 rounded-2xl border border-line bg-panel-2/60 p-5 text-sm text-muted">
            This is a reader view of an article published by <span className="text-text">{a.sitename}</span>. All rights belong to the
            original publisher —{" "}
            <a href={a.url} target="_blank" rel="noopener noreferrer" className="text-brand-2 hover:underline">
              read and support it on {a.domain}
            </a>
            .
          </div>
        </article>
      )}
    </div>
  );
}
