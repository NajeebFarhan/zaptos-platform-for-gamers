import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";
import { BadgePercent, BookOpen, Crosshair, Menu, Search, X } from "lucide-react";

const NAV = [
  { to: "/search", label: "Compare prices", icon: Search, match: (p) => p.startsWith("/search") },
  { to: "/deals", label: "Best offers", icon: BadgePercent, match: (p) => p.startsWith("/deals") },
  { to: "/guides", label: "Game guides", icon: BookOpen, match: (p) => p.startsWith("/guides") },
];

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2.5" aria-label="LootScout home">
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-brand to-brand-2 shadow-lg shadow-brand/30">
        <Crosshair className="h-5 w-5 text-ink" strokeWidth={2.5} />
      </span>
      <span className="font-display text-xl font-bold tracking-wide">
        Loot<span className="text-gradient">Scout</span>
      </span>
    </Link>
  );
}

export default function Layout() {
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  useEffect(() => {
    setOpen(false);
    window.scrollTo({ top: 0 });
  }, [pathname]);

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-40 border-b border-line/70 bg-ink/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex">
            {NAV.map(({ to, label, icon: Icon, match }) => (
              <NavLink
                key={to}
                to={to}
                className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition ${
                  match(pathname) ? "bg-panel-2 text-text" : "text-muted hover:text-text"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="hidden items-center gap-2 text-xs text-muted md:flex">
            <span className="rounded-full border border-line px-2.5 py-1">🇮🇳 Prices in INR</span>
          </div>
          <button className="btn-ghost px-2.5 md:hidden" onClick={() => setOpen((o) => !o)} aria-label="Menu">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {open && (
          <nav className="border-t border-line px-4 py-3 md:hidden">
            {NAV.map(({ to, label, icon: Icon }) => (
              <Link key={to} to={to} className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-text hover:bg-panel-2">
                <Icon className="h-4 w-4 text-brand" />
                {label}
              </Link>
            ))}
          </nav>
        )}
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="mt-20 border-t border-line/70 bg-panel/40">
        <div className="mx-auto grid max-w-7xl gap-8 px-4 py-10 text-sm text-muted sm:px-6 md:grid-cols-3">
          <div className="space-y-3">
            <Logo />
            <p>Live price comparison for gaming hardware across India's favourite stores, plus guides for the games you play.</p>
          </div>
          <div className="space-y-2">
            <div className="font-semibold text-text">How prices work</div>
            <p>
              Prices are collected from each store's public listings and cached for up to 30 minutes. Always confirm the final price,
              seller and warranty on the store before buying.
            </p>
          </div>
          <div className="space-y-2">
            <div className="font-semibold text-text">Guide sources</div>
            <p>
              Wiki content comes from community Fandom wikis (CC BY-SA) with attribution on every page. Articles are summarised in a
              reader view and always link back to the original publisher.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
