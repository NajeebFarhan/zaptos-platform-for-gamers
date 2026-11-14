import { Link } from "react-router";
import { BookOpen, ExternalLink, MessageSquare, Play, Sparkles } from "lucide-react";

const KIND = {
  video: { icon: Play, label: "Video" },
  forum: { icon: MessageSquare, label: "Discussion" },
  wiki: { icon: BookOpen, label: "Wiki" },
};

/** One guide found on the web. Articles open in our reader; videos/forums open the source. */
export default function WebResult({ result, gameId }) {
  const kind = KIND[result.kind];
  const readable = result.kind === "article" || result.kind === "wiki";
  const readerHref = `/guides/${gameId}/read?url=${encodeURIComponent(result.url)}`;

  return (
    <article className="card p-4 transition hover:border-brand/40">
      <div className="mb-1.5 flex flex-wrap items-center gap-2 text-xs text-muted">
        <img src={result.favicon} alt="" className="h-4 w-4 rounded" loading="lazy" referrerPolicy="no-referrer" onError={(e) => (e.currentTarget.style.display = "none")} />
        <span className="font-medium text-text/80">{result.domain}</span>
        {result.popular && (
          <span className="inline-flex items-center gap-1 rounded-md bg-brand/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand">
            <Sparkles className="h-3 w-3" /> Popular source
          </span>
        )}
        {kind && (
          <span className="inline-flex items-center gap-1 rounded-md bg-panel-3 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide">
            <kind.icon className="h-3 w-3" /> {kind.label}
          </span>
        )}
      </div>
      {readable ? (
        <Link to={readerHref} className="font-semibold leading-snug text-text hover:text-brand-2">
          {result.title}
        </Link>
      ) : (
        <a href={result.url} target="_blank" rel="noopener noreferrer" className="font-semibold leading-snug text-text hover:text-brand-2">
          {result.title}
        </a>
      )}
      {result.snippet && <p className="mt-1.5 line-clamp-2 text-sm text-muted">{result.snippet}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        {readable && (
          <Link to={readerHref} className="btn-ghost px-3 py-1.5 text-xs">
            <BookOpen className="h-3.5 w-3.5" /> Read here
          </Link>
        )}
        <a href={result.url} target="_blank" rel="noopener noreferrer" className="btn-ghost px-3 py-1.5 text-xs">
          <ExternalLink className="h-3.5 w-3.5" /> {result.kind === "video" ? "Watch" : "Open original"}
        </a>
      </div>
    </article>
  );
}

export function WebResultSkeleton() {
  return (
    <div className="card space-y-2.5 p-4">
      <div className="skeleton h-3 w-32" />
      <div className="skeleton h-5 w-4/5" />
      <div className="skeleton h-4 w-full" />
      <div className="skeleton h-7 w-48" />
    </div>
  );
}
