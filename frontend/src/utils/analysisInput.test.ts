import { describe, expect, it } from "vitest";
import { VALID_REQUEST } from "../test/fixtures";
import {
  importAnalysisFile,
  parseAnalysisInput,
} from "./analysisInput";

function event(wallet: string, sourceRowNumber = 1) {
  return { ...VALID_REQUEST.events[0], wallet, source_row_number: sourceRowNumber };
}

describe("unified analysis input", () => {
  it("detects one wallet from a raw event array", () => {
    const parsed = parseAnalysisInput(
      JSON.stringify([event("wallet-one")]),
      "2025-02-01T00:00:00Z",
      "1",
    );
    expect(parsed.walletsDetected).toBe(1);
    expect(parsed.eventsDetected).toBe(1);
    expect(parsed.request.wallet_histories[0].wallet).toBe("wallet-one");
    expect(parsed.request.review_budget).toBe(1);
  });

  it("groups a multi-wallet raw event array deterministically", () => {
    const parsed = parseAnalysisInput(
      JSON.stringify([event("wallet-a", 1), event("wallet-b", 2), event("wallet-a", 3)]),
      "2025-02-01T00:00:00Z",
      "2",
    );
    expect(parsed.request.wallet_histories.map((history) => history.wallet)).toEqual([
      "wallet-a",
      "wallet-b",
    ]);
    expect(parsed.request.wallet_histories[0].events).toHaveLength(2);
  });

  it("accepts a complete payload and uses embedded controls when fields are blank", () => {
    const parsed = parseAnalysisInput(JSON.stringify({
      as_of: "2025-02-01T00:00:00Z",
      review_budget: 1,
      wallet_histories: [{ wallet: "wallet-a", events: [event("wallet-a")] }],
    }), "", "");
    expect(parsed.request.as_of).toBe("2025-02-01T00:00:00Z");
    expect(parsed.request.review_budget).toBe(1);
  });

  it("rejects wallet-event identity mismatches instead of repairing them", () => {
    expect(() => parseAnalysisInput(JSON.stringify([
      { wallet: "wallet-a", events: [event("wallet-b")] },
    ]), "2025-02-01T00:00:00Z", "1")).toThrow(/does not match wallet-a/i);
  });

  it("rejects non-UTC scoring timestamps", () => {
    expect(() => parseAnalysisInput(
      JSON.stringify([event("wallet-a")]),
      "2025-02-01T03:00:00+03:00",
      "1",
    )).toThrow(/UTC/i);
  });

  it("caps the effective review budget at the submitted wallet count", () => {
    const parsed = parseAnalysisInput(
      JSON.stringify([event("wallet-a")]),
      "2025-02-01T00:00:00Z",
      "20",
    );
    expect(parsed.request.review_budget).toBe(1);
  });

  it("imports only supported JSON shapes and extracts embedded controls", () => {
    const imported = importAnalysisFile(JSON.stringify({
      as_of: "2025-02-01T00:00:00Z",
      review_budget: 1,
      events: [event("wallet-a")],
    }));
    expect(imported.asOf).toBe("2025-02-01T00:00:00Z");
    expect(imported.reviewBudget).toBe("1");
    expect(imported.json).toContain("wallet-a");
    expect(() => importAnalysisFile(JSON.stringify({ unsupported: [] }))).toThrow(/Import an event array/i);
  });
});
