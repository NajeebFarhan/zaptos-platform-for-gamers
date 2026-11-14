import { Link } from "react-router";
import { ChevronRight } from "lucide-react";

/** Stylised game tile; colours come from each game's accent. */
export default function GameCard({ game, compact = false }) {
  return (
    <Link
      to={`/guides/${game.id}`}
      className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-line p-5 transition hover:-translate-y-0.5"
      style={{
        background: `linear-gradient(135deg, ${game.accent}33 0%, #12141c 55%), radial-gradient(400px 200px at 100% 0%, ${game.accent}40, transparent)`,
        minHeight: compact ? 150 : 210,
      }}
    >
      <span
        className="pointer-events-none absolute -right-3 -top-6 select-none font-display text-[7rem] font-bold leading-none opacity-[0.12] transition group-hover:opacity-20"
        style={{ color: game.accent }}
        aria-hidden
      >
        {game.short}
      </span>
      <div className="relative">
        <div className="text-xs font-semibold uppercase tracking-[0.16em]" style={{ color: game.accent }}>
          {game.genre}
        </div>
        <h3 className="mt-1 font-display text-2xl font-bold text-text">{game.name}</h3>
        {!compact && <p className="mt-2 max-w-sm text-sm text-muted">{game.tagline}</p>}
      </div>
      <div className="relative mt-4 flex items-center gap-1 text-sm font-semibold text-text">
        Open guides <ChevronRight className="h-4 w-4 transition group-hover:translate-x-1" />
      </div>
    </Link>
  );
}
