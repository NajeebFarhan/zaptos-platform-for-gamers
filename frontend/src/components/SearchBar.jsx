import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { Search } from "lucide-react";

export default function SearchBar({ initial = "", size = "md", placeholder, to = (q) => `/search?q=${encodeURIComponent(q)}`, autoFocus }) {
  const [q, setQ] = useState(initial);
  const navigate = useNavigate();
  useEffect(() => setQ(initial), [initial]);

  const submit = (e) => {
    e.preventDefault();
    const v = q.trim();
    if (v.length >= 2) navigate(to(v));
  };

  const big = size === "lg";
  return (
    <form onSubmit={submit} role="search" className="relative flex w-full items-center">
      <Search className={`pointer-events-none absolute left-4 text-muted ${big ? "h-6 w-6" : "h-5 w-5"}`} />
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        autoFocus={autoFocus}
        placeholder={placeholder || "Search GPUs, consoles, headsets, keyboards…"}
        aria-label="Search"
        className={`w-full rounded-2xl border border-line bg-panel-2/90 text-text placeholder:text-dim shadow-xl shadow-black/30
          outline-none transition focus:border-brand focus:ring-4 focus:ring-brand/20
          ${big ? "py-4 pl-13 pr-36 text-lg" : "py-2.5 pl-11 pr-28 text-sm"}`}
      />
      <button type="submit" className={`btn-primary absolute right-2 ${big ? "px-6 py-2.5 text-base" : "px-4 py-1.5"}`}>
        Search
      </button>
    </form>
  );
}
