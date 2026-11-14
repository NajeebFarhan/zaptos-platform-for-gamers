import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import * as wl from "./wishlist";

const KEY = "zaptos:wishlist:v1";

const group = (id, extra = {}) => ({
  id,
  title: `Product ${id}`,
  min_price: 1000,
  offers: [{ store: "alpha", url: `https://alpha.example/${id}`, price: 1000 }],
  // fields that only deals carry; the wishlist should not keep them
  relevance: 90, deal_score: 12, category: "gpu", source_query: "rtx 5060",
  ...extra,
});

const stored = () => JSON.parse(localStorage.getItem(KEY));

beforeEach(() => {
  wl.clearAll();
  localStorage.clear();
});
afterEach(cleanup);

/** Run a mutation and read the hook's snapshot afterwards. */
function setup() {
  const hook = renderHook(() => wl.useWishlist());
  const items = () => hook.result.current.items;
  const mutate = (fn) => act(() => fn());
  return { hook, items, mutate, snap: () => hook.result.current };
}

describe("saving", () => {
  it("snapshots the product with the price at save time and drops deal-only fields", () => {
    const { items, mutate } = setup();
    mutate(() => wl.addItem(group("a"), "  rtx 5060 "));
    expect(items()).toHaveLength(1);
    const [it] = items();
    expect(it).toMatchObject({ key: "a", query: "rtx 5060", saved_price: 1000, status: "ok" });
    expect(it.group).not.toHaveProperty("relevance");
    expect(it.group).not.toHaveProperty("deal_score");
    expect(it.group).not.toHaveProperty("source_query");
    expect(it.group.title).toBe("Product a");
  });

  it("falls back to the deal's source query, then to null", () => {
    const { items, mutate } = setup();
    mutate(() => wl.addItem(group("a")));
    mutate(() => wl.addItem(group("b", { source_query: undefined }), "   "));
    expect(items().find((i) => i.key === "a").query).toBe("rtx 5060");
    expect(items().find((i) => i.key === "b").query).toBeNull();
  });

  it("never saves the same product twice", () => {
    const { items, mutate } = setup();
    mutate(() => wl.addItem(group("a")));
    mutate(() => wl.addItem(group("a")));
    expect(items()).toHaveLength(1);
  });

  it("puts the newest first and caps the list at 60", () => {
    const { items, mutate } = setup();
    mutate(() => { for (let i = 0; i < 65; i++) wl.addItem(group(`p${i}`)); });
    expect(items()).toHaveLength(60);
    expect(items()[0].key).toBe("p64");
    expect(items().some((i) => i.key === "p0")).toBe(false);
  });

  it("toggleItem saves, then removes, and reports the new state", () => {
    const { items, mutate } = setup();
    let result;
    mutate(() => { result = wl.toggleItem(group("a")); });
    expect([result, items().length]).toEqual([true, 1]);
    mutate(() => { result = wl.toggleItem(group("a")); });
    expect([result, items().length]).toEqual([false, 0]);
  });

  it("removeItem and clearAll", () => {
    const { items, mutate } = setup();
    mutate(() => { wl.addItem(group("a")); wl.addItem(group("b")); });
    mutate(() => wl.removeItem("a"));
    expect(items().map((i) => i.key)).toEqual(["b"]);
    mutate(() => wl.clearAll());
    expect(items()).toEqual([]);
  });
});

describe("recognising saved products", () => {
  it("finds a product by id, and by any shared store listing when the id has changed", () => {
    const { snap, mutate } = setup();
    mutate(() => wl.addItem(group("a")));
    expect(wl.findSaved(snap(), group("a"))).toBeDefined();
    // same listing, but a different group id (another store joined the group)
    const regrouped = group("zzz", { offers: [{ store: "alpha", url: "https://alpha.example/a" }, { store: "beta", url: "https://beta.example/a" }] });
    expect(wl.findSaved(snap(), regrouped)?.key).toBe("a");
    expect(wl.findSaved(snap(), group("other"))).toBeUndefined();
    expect(wl.findSaved(snap(), null)).toBeUndefined();
  });

  it("toggling a regrouped product removes the original save instead of adding a duplicate", () => {
    const { items, mutate } = setup();
    mutate(() => wl.addItem(group("a")));
    mutate(() => wl.toggleItem(group("zzz", { offers: [{ url: "https://alpha.example/a" }] })));
    expect(items()).toEqual([]);
  });
});

describe("persistence", () => {
  it("writes to localStorage on every change", () => {
    const { mutate } = setup();
    mutate(() => wl.addItem(group("a")));
    expect(stored().map((i) => i.key)).toEqual(["a"]);
    mutate(() => wl.removeItem("a"));
    expect(stored()).toEqual([]);
  });

  it("survives storage being unavailable (private mode / quota)", () => {
    const { items, mutate } = setup();
    vi.spyOn(localStorage, "setItem").mockImplementation(() => { throw new Error("QuotaExceededError"); });
    expect(() => mutate(() => wl.addItem(group("a")))).not.toThrow();
    expect(items()).toHaveLength(1); // still works for this session
  });

  it("follows changes made in another tab", () => {
    const { items } = setup();
    const other = [{ key: "x", query: null, group: group("x"), saved_price: 5 }];
    localStorage.setItem(KEY, JSON.stringify(other));
    act(() => { window.dispatchEvent(new StorageEvent("storage", { key: KEY })); });
    expect(items().map((i) => i.key)).toEqual(["x"]);
  });

  it("ignores storage events for other keys", () => {
    const { mutate, items } = setup();
    mutate(() => wl.addItem(group("a")));
    localStorage.setItem("something-else", "1");
    act(() => { window.dispatchEvent(new StorageEvent("storage", { key: "something-else" })); });
    expect(items()).toHaveLength(1);
  });

  describe("on page load", () => {
    const loadFresh = async () => {
      vi.resetModules();
      return import("./wishlist.js");
    };

    it("restores a saved list", async () => {
      localStorage.setItem(KEY, JSON.stringify([{ key: "a", query: "q", group: group("a") }]));
      const fresh = await loadFresh();
      expect(fresh.trackPayload().items.map((i) => i.key)).toEqual(["a"]);
    });

    it.each([
      ["corrupt JSON", "{not json"],
      ["not an array", '{"a":1}'],
    ])("starts empty on %s instead of crashing", async (_, raw) => {
      localStorage.setItem(KEY, raw);
      expect((await loadFresh()).trackPayload()).toEqual({ items: [] });
    });

    it("drops malformed entries but keeps good ones", async () => {
      localStorage.setItem(KEY, JSON.stringify([null, { key: "no-group" }, { group: {} }, { key: "ok", group: group("ok") }]));
      expect((await loadFresh()).trackPayload().items.map((i) => i.key)).toEqual(["ok"]);
    });
  });
});

describe("price tracking", () => {
  it("trackPayload sends what the backend needs, capped at 20 urls per item", () => {
    const { mutate } = setup();
    const offers = Array.from({ length: 30 }, (_, i) => ({ store: `s${i}`, url: `https://s${i}.example/p` }));
    mutate(() => wl.addItem(group("a", { offers }), "rtx 5060"));
    const [item] = wl.trackPayload().items;
    expect(item).toMatchObject({ key: "a", title: "Product a", query: "rtx 5060" });
    expect(item.urls).toHaveLength(20);
  });

  it("applyTrackResults refreshes found items and flags the ones that disappeared", () => {
    const { items, mutate } = setup();
    mutate(() => { wl.addItem(group("a")); wl.addItem(group("b")); wl.addItem(group("c")); });
    const cheaper = group("a", { min_price: 800, relevance: 99 });
    mutate(() => wl.applyTrackResults({
      a: { status: "ok", group: cheaper },
      b: { status: "missing", group: null },
    }, 123));
    const by = Object.fromEntries(items().map((i) => [i.key, i]));
    expect(by.a.group.min_price).toBe(800);
    expect(by.a.group).not.toHaveProperty("relevance");
    expect(by.a.saved_price).toBe(1000); // what it cost when saved is kept, so the drop can be shown
    expect(by.a).toMatchObject({ status: "ok", checked_at: 123 });
    expect(by.b).toMatchObject({ status: "missing", checked_at: 123 });
    expect(by.b.group.min_price).toBe(1000); // the last known prices stay visible
    expect(by.c.status).toBe("ok"); // not in the results at all: untouched
    expect(by.c.checked_at).not.toBe(123);
  });
});
