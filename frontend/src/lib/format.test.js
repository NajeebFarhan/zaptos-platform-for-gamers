import { afterEach, describe, expect, it, vi } from "vitest";
import { formatDate, inr, KIND_LABELS, num, ratingWord, timeAgo } from "./format";

const squash = (s) => s.replace(/\s/g, ""); // Intl may use non-breaking spaces

describe("inr / num", () => {
  it("uses Indian digit grouping", () => {
    expect(squash(inr(117150))).toBe("₹1,17,150");
    expect(squash(inr(999))).toBe("₹999");
    expect(num(1234567)).toBe("12,34,567");
  });

  it("rounds to whole rupees", () => {
    expect(squash(inr(59999.6))).toBe("₹60,000");
  });

  it("shows a dash for missing values but not for zero", () => {
    expect(inr(null)).toBe("—");
    expect(inr(undefined)).toBe("—");
    expect(num(null)).toBe("—");
    expect(squash(inr(0))).toBe("₹0");
  });
});

describe("ratingWord", () => {
  it.each([
    [5, "Excellent"], [4.5, "Excellent"], [4.49, "Very good"], [4.0, "Very good"],
    [3.99, "Good"], [3.5, "Good"], [3.0, "Fair"], [2.99, "Poor"], [0, "Poor"],
  ])("%s -> %s", (rating, word) => expect(ratingWord(rating)).toBe(word));

  it("is null when there is no rating", () => {
    expect(ratingWord(null)).toBeNull();
    expect(ratingWord(undefined)).toBeNull();
  });
});

describe("timeAgo", () => {
  afterEach(() => vi.useRealTimers());

  it("picks the right unit", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T12:00:00Z"));
    const now = Date.now() / 1000;
    expect(timeAgo(now - 30)).toBe("just now");
    expect(timeAgo(now - 120)).toBe("2 min ago");
    expect(timeAgo(now - 7200)).toBe("2 h ago");
    expect(timeAgo(now - 172800)).toBe("2 d ago");
  });

  it("never shows a negative age for a timestamp slightly in the future (clock skew)", () => {
    expect(timeAgo(Date.now() / 1000 + 600)).toBe("just now");
  });

  it("is null without a timestamp", () => {
    expect(timeAgo(null)).toBeNull();
    expect(timeAgo(0)).toBeNull();
  });
});

describe("formatDate", () => {
  it("formats ISO dates for India", () => {
    expect(formatDate("2026-03-05T12:00:00")).toBe("5 Mar 2026");
  });

  it("hands back unparseable input instead of 'Invalid Date'", () => {
    expect(formatDate("last tuesday")).toBe("last tuesday");
  });

  it("is null when empty", () => {
    expect(formatDate(null)).toBeNull();
    expect(formatDate("")).toBeNull();
  });
});

describe("KIND_LABELS", () => {
  it("has a human label for every entry", () => {
    for (const [kind, label] of Object.entries(KIND_LABELS)) {
      expect(label, kind).toMatch(/^[A-Z]/);
    }
  });
});
