import { beforeEach, describe, expect, it, vi } from "vitest";

/** Import api.js fresh with VITE_API_URL set, since the base URL is read once at load. */
async function loadApi(apiUrl) {
  vi.stubEnv("VITE_API_URL", apiUrl);
  vi.resetModules();
  return import("./api.js");
}

const jsonResponse = (body, init = {}) =>
  ({ ok: true, status: 200, json: async () => body, ...init });

let fetchMock;
beforeEach(() => {
  fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
  vi.stubGlobal("fetch", fetchMock);
});

describe("base URL", () => {
  it("is empty in dev/Docker, so /api goes through the proxy on the same origin", async () => {
    const { api } = await loadApi("");
    await api("/api/prices/meta");
    expect(fetchMock.mock.calls[0][0]).toBe("/api/prices/meta");
  });

  it("points at the hosted backend when VITE_API_URL is set", async () => {
    const { api } = await loadApi("https://zaptos-platform-for-gamers.onrender.com");
    await api("/api/prices/meta");
    expect(fetchMock.mock.calls[0][0]).toBe("https://zaptos-platform-for-gamers.onrender.com/api/prices/meta");
  });

  it("tolerates trailing slashes in the env var (no '//api')", async () => {
    const { api } = await loadApi("https://api.example.com//");
    await api("/api/x");
    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example.com/api/x");
  });
});

describe("api()", () => {
  it("returns the parsed JSON", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ stores: [1, 2] }));
    const { api } = await loadApi("");
    expect(await api("/api/prices/meta")).toEqual({ stores: [1, 2] });
  });

  it("makes a GET unless a body is given, and forwards the abort signal", async () => {
    const { api } = await loadApi("");
    const ctrl = new AbortController();
    await api("/api/x", { signal: ctrl.signal });
    const init = fetchMock.mock.calls[0][1];
    expect(init.method).toBeUndefined();
    expect(init.signal).toBe(ctrl.signal);
  });

  it("POSTs JSON when given a body", async () => {
    const { api } = await loadApi("");
    await api("/api/prices/track", { body: { items: [] } });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(init.body).toBe('{"items":[]}');
  });

  it("surfaces the server's error detail", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "query too short" }, { ok: false, status: 400 }));
    const { api } = await loadApi("");
    await expect(api("/api/prices/search?q=a")).rejects.toThrow("query too short");
  });

  it("falls back to the status code when the error body isn't JSON", async () => {
    fetchMock.mockResolvedValue({ ok: false, status: 502, json: async () => { throw new Error("html"); } });
    const { api } = await loadApi("");
    await expect(api("/api/x")).rejects.toThrow("Request failed (502)");
  });
});
