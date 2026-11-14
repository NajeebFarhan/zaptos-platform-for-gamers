import { useEffect } from "react";
import { BookOpen, Globe, Library } from "lucide-react";
import GameCard from "../components/GameCard";
import { ErrorState } from "../components/ui";
import { useApi } from "../lib/api";

export default function GuidesHome() {
  const { data, error, loading, reload } = useApi("/api/guides/games");
  useEffect(() => {
    document.title = "Game guides · LootScout";
  }, []);

  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
      <div className="mb-10 max-w-3xl">
        <div className="mb-2 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-brand-2">
          <BookOpen className="h-4 w-4" /> Game guides
        </div>
        <h1 className="font-display text-4xl font-bold sm:text-5xl">Get better at the games you play</h1>
        <p className="mt-3 text-lg text-muted">
          Agents, heroes, characters, builds and strategy — gathered from community wikis and the most popular guide sites, in one
          clean place.
        </p>
      </div>

      {error && <ErrorState message={error.message} onRetry={reload} />}
      <div className="grid gap-5 md:grid-cols-2">
        {loading && Array.from({ length: 4 }, (_, i) => <div key={i} className="skeleton h-[210px] rounded-2xl" />)}
        {data?.games.map((g) => <GameCard key={g.id} game={g} />)}
      </div>

      <div className="mt-12 grid gap-4 md:grid-cols-2">
        <div className="card flex gap-4 p-5">
          <Library className="h-7 w-7 shrink-0 text-brand" />
          <div>
            <div className="font-semibold">Community wikis</div>
            <p className="mt-1 text-sm text-muted">
              Rosters, abilities and stats come from each game's Fandom wiki (and valorant-api.com for Valorant), with attribution.
            </p>
          </div>
        </div>
        <div className="card flex gap-4 p-5">
          <Globe className="h-7 w-7 shrink-0 text-brand-2" />
          <div>
            <div className="font-semibold">The best guides on the web</div>
            <p className="mt-1 text-sm text-muted">
              We search the web for guides and open articles in a distraction-free reader, always linking back to the publisher.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
