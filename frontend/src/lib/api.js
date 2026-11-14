import { useCallback, useEffect, useState } from "react";

const BASE = import.meta.env.VITE_API_BASE || "";

export async function api(path, { signal, body } = {}) {
  const init = body === undefined
    ? { signal }
    : { signal, method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(BASE + path, init);
  if (!res.ok) {
    let detail;
    try {
      detail = (await res.json()).detail;
    } catch {
      /* not JSON */
    }
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.json();
}

/** Fetch JSON for `path` (null = skip). Re-fetches when path changes. */
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: !!path });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!path) {
      setState({ data: null, error: null, loading: false });
      return;
    }
    const ctrl = new AbortController();
    setState((s) => ({ data: s.data, error: null, loading: true }));
    api(path, { signal: ctrl.signal })
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => {
        if (error.name !== "AbortError") setState({ data: null, error, loading: false });
      });
    return () => ctrl.abort();
  }, [path, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  return { ...state, reload };
}

let metaPromise;
/** Stores, categories and trending searches — loaded once per session. */
export function useMeta() {
  const [meta, setMeta] = useState(null);
  useEffect(() => {
    metaPromise ??= api("/api/prices/meta").catch((e) => {
      metaPromise = undefined;
      throw e;
    });
    let alive = true;
    metaPromise.then((m) => alive && setMeta(m)).catch(() => {});
    return () => {
      alive = false;
    };
  }, []);
  return meta;
}

/**
 * Live price search over Server-Sent Events: per-store progress, then grouped results.
 * Falls back to the plain JSON endpoint if the stream can't be opened.
 */
export function usePriceSearch(query, refresh = { q: null, n: 0 }) {
  const [state, setState] = useState({ status: "idle", stores: {}, result: null, error: null });
  // `refresh` = {q, n}: bypass the cache only when the refresh was requested for *this* query
  const forceRefresh = refresh.q === query && refresh.n > 0;

  useEffect(() => {
    if (!query) return;
    const qs = `q=${encodeURIComponent(query)}${forceRefresh ? "&refresh=true" : ""}`;
    setState({ status: "loading", stores: {}, result: null, error: null });

    let done = false;
    const es = new EventSource(`${BASE}/api/prices/search/stream?${qs}`);
    es.addEventListener("store", (e) => {
      const s = JSON.parse(e.data);
      setState((prev) => ({ ...prev, stores: { ...prev.stores, [s.store]: s } }));
    });
    es.addEventListener("result", (e) => {
      done = true;
      es.close();
      const result = JSON.parse(e.data);
      const stores = Object.fromEntries(result.stores.map((s) => [s.store, s]));
      setState({ status: "done", stores, result, error: null });
    });
    es.onerror = () => {
      if (done) return;
      es.close();
      api(`/api/prices/search?${qs}`)
        .then((result) => {
          const stores = Object.fromEntries(result.stores.map((s) => [s.store, s]));
          setState({ status: "done", stores, result, error: null });
        })
        .catch((error) => setState((prev) => ({ ...prev, status: "error", error })));
    };
    return () => {
      done = true;
      es.close();
    };
  }, [query, forceRefresh, refresh.n]);

  return state;
}
