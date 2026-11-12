import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "./client";
import { resolveApiBaseUrl } from "./config";
import { FEATURE_NAMES } from "./types";
import { jsonResponse, MODEL_NOT_APPROVED, VALID_PREVIEW, VALID_REQUEST } from "../test/fixtures";

describe("API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("normalizes safe API base URLs and rejects credentialed or protocol-relative values", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("/api");
    expect(resolveApiBaseUrl("http://127.0.0.1:8080/")).toBe("http://127.0.0.1:8080");
    expect(() => resolveApiBaseUrl("//untrusted.example")).toThrow();
    expect(() => resolveApiBaseUrl("https://user:pass@example.test")).toThrow();
  });

  it("accepts the expected readiness 503 as an unavailable capability", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MODEL_NOT_APPROVED, 503)));
    const result = await new ApiClient("/api").readiness();
    expect(result).toEqual({ available: false, code: "MODEL_NOT_APPROVED", message: "Prediction capability is unavailable." });
  });

  it("returns all registered features from a schema-compatible preview", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(VALID_PREVIEW)));
    const result = await new ApiClient("/api").preview(VALID_REQUEST);
    expect(Object.keys(result.features)).toEqual([...FEATURE_NAMES]);
  });

  it("rejects feature-order drift rather than silently displaying mismatched values", async () => {
    const drifted = { ...VALID_PREVIEW, feature_order: [...VALID_PREVIEW.feature_order].reverse() };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(drifted)));
    await expect(new ApiClient("/api").preview(VALID_REQUEST)).rejects.toMatchObject({ code: "SCHEMA_MISMATCH" });
  });

  it("rejects inconsistent preview metadata", async () => {
    const inconsistent = { ...VALID_PREVIEW, supplied_event_count: 99 };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(inconsistent)));
    await expect(new ApiClient("/api").preview(VALID_REQUEST)).rejects.toMatchObject({ code: "SCHEMA_MISMATCH" });
  });

  it("does not accept an unexpected successful scoring response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ anomaly_score: 0.99 })));
    await expect(new ApiClient("/api").scoringAvailability(VALID_REQUEST)).rejects.toMatchObject({ code: "UNSUPPORTED_MODEL_RESPONSE" });
  });

  it("converts network failures into a structured backend-unavailable error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));
    await expect(new ApiClient("/api").health()).rejects.toEqual(
      expect.objectContaining({ code: "BACKEND_UNAVAILABLE", status: 0 }),
    );
  });
});
