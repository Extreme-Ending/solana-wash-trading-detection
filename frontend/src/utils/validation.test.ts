import { describe, expect, it } from "vitest";
import { SYNTHETIC_AS_OF, SYNTHETIC_EVENTS_JSON, SYNTHETIC_WALLET } from "../data/syntheticExample";
import {
  buildPreviewRequest,
  InputValidationError,
  parseEventsJson,
  parseImportedPayload,
  validateUtcTimestamp,
} from "./validation";

describe("input validation", () => {
  it("builds an API request from the deterministic synthetic example", () => {
    const request = buildPreviewRequest(SYNTHETIC_WALLET, SYNTHETIC_AS_OF, SYNTHETIC_EVENTS_JSON);
    expect(request.events).toHaveLength(3);
    expect(request.events.every((event) => event.wallet === SYNTHETIC_WALLET)).toBe(true);
    expect(request.events[0].amount_usd).toBe(125.5);
  });

  it.each(["not-a-date", "2025-02-01T00:00:00", "2025-02-01T03:00:00+03:00"])(
    "rejects non-UTC cutoff %s",
    (value) => expect(() => validateUtcTimestamp(value)).toThrow(InputValidationError),
  );

  it("rejects duplicate source rows, unsupported fields, and invalid amounts", () => {
    const events = JSON.parse(SYNTHETIC_EVENTS_JSON) as Array<Record<string, unknown>>;
    events[1].source_row_number = events[0].source_row_number;
    expect(() => parseEventsJson(JSON.stringify(events))).toThrow("source_row_number values must be unique");

    const extra = JSON.parse(SYNTHETIC_EVENTS_JSON) as Array<Record<string, unknown>>;
    extra[0].risk_score = 0.99;
    expect(() => parseEventsJson(JSON.stringify(extra))).toThrow("unsupported field risk_score");

    const invalid = JSON.parse(SYNTHETIC_EVENTS_JSON) as Array<Record<string, unknown>>;
    invalid[0].amount_usd = -1;
    expect(() => parseEventsJson(JSON.stringify(invalid))).toThrow("amount_usd");
  });

  it("imports a complete one-wallet payload but rejects mixed wallets", () => {
    const request = buildPreviewRequest(SYNTHETIC_WALLET, SYNTHETIC_AS_OF, SYNTHETIC_EVENTS_JSON);
    const imported = parseImportedPayload(JSON.stringify(request));
    expect(imported.wallet).toBe(SYNTHETIC_WALLET);
    expect(imported.asOf).toBe(SYNTHETIC_AS_OF);

    request.events[1].wallet = "another-wallet";
    expect(() => parseImportedPayload(JSON.stringify(request))).toThrow("exactly one wallet");
  });
});
