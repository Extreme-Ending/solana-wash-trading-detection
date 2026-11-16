import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiClient } from "./client";
import { resolveApiBaseUrl } from "./config";
import { FEATURE_NAMES } from "./types";
import {
  jsonResponse,
  MODEL_NOT_APPROVED,
  VALID_BATCH_REQUEST,
  VALID_EXPERIMENTAL_BATCH_SCORE,
  VALID_EXPERIMENTAL_SCORE,
  VALID_PREVIEW,
  VALID_REQUEST,
} from "../test/fixtures";

describe("API client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("normalizes safe API base URLs and rejects credentialed or protocol-relative values", () => {
    expect(resolveApiBaseUrl(undefined)).toBe("/api");
    expect(resolveApiBaseUrl("http://127.0.0.1:8080/")).toBe("http://127.0.0.1:8080");
    expect(resolveApiBaseUrl("https://service.example.run.app/", true)).toBe("https://service.example.run.app");
    expect(() => resolveApiBaseUrl(undefined, true)).toThrow(/explicit HTTPS origin/);
    expect(() => resolveApiBaseUrl("//untrusted.example")).toThrow();
    expect(() => resolveApiBaseUrl("https://user:pass@example.test")).toThrow();
    expect(() => resolveApiBaseUrl("https://service.example.run.app/api", true)).toThrow(/without a path/);
    expect(() => resolveApiBaseUrl("http://service.example.run.app", true)).toThrow(/HTTPS/);
  });

  it("accepts the expected readiness 503 as an unavailable capability", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MODEL_NOT_APPROVED, 503)));
    const result = await new ApiClient("/api").readiness();
    expect(result).toEqual({ available: false, code: "MODEL_NOT_APPROVED", message: "Prediction capability is unavailable." });
  });

  it("returns all registered features from a schema-compatible preview", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(VALID_PREVIEW)));
    const result = await new ApiClient("/api", async () => "signed-id-token").preview(VALID_REQUEST);
    expect(Object.keys(result.features)).toEqual([...FEATURE_NAMES]);
    const [, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer signed-id-token");
  });

  it("rejects feature-order drift rather than silently displaying mismatched values", async () => {
    const drifted = { ...VALID_PREVIEW, feature_order: [...VALID_PREVIEW.feature_order].reverse() };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(drifted)));
    await expect(new ApiClient("/api", async () => "token").preview(VALID_REQUEST)).rejects.toMatchObject({ code: "SCHEMA_MISMATCH" });
  });

  it("rejects inconsistent preview metadata", async () => {
    const inconsistent = { ...VALID_PREVIEW, supplied_event_count: 99 };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(inconsistent)));
    await expect(new ApiClient("/api", async () => "token").preview(VALID_REQUEST)).rejects.toMatchObject({ code: "SCHEMA_MISMATCH" });
  });

  it("accepts a schema-compatible experimental score and sends authorization", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(VALID_EXPERIMENTAL_SCORE)));
    const result = await new ApiClient("/api", async () => "token").score(VALID_REQUEST);
    expect(result).toEqual(VALID_EXPERIMENTAL_SCORE);
    const [, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer token");
  });

  it("rejects an invalid successful scoring response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ anomaly_score: 0.99 })));
    await expect(new ApiClient("/api", async () => "token").score(VALID_REQUEST)).rejects.toMatchObject({ code: "SCHEMA_MISMATCH" });
  });

  it("preserves disabled experimental scoring as an availability state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MODEL_NOT_APPROVED, 503)));
    await expect(new ApiClient("/api", async () => "token").score(VALID_REQUEST)).resolves.toEqual({
      available: false,
      code: "MODEL_NOT_APPROVED",
      message: "Prediction capability is unavailable.",
    });
  });

  it("accepts a deterministic batch ranking and sends authorization", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(VALID_EXPERIMENTAL_BATCH_SCORE)));
    const result = await new ApiClient("/api", async () => "token").scoreBatch(VALID_BATCH_REQUEST);
    expect(result).toEqual(VALID_EXPERIMENTAL_BATCH_SCORE);
    const [url, init] = vi.mocked(fetch).mock.calls[0] as [string, RequestInit];
    expect(url).toBe("/api/v1/score/batch");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer token");
  });

  it.each([
    { ...VALID_EXPERIMENTAL_BATCH_SCORE, wallets_scored: 4 },
    {
      ...VALID_EXPERIMENTAL_BATCH_SCORE,
      ranked_wallets: [...VALID_EXPERIMENTAL_BATCH_SCORE.ranked_wallets].reverse(),
    },
    { ...VALID_EXPERIMENTAL_BATCH_SCORE, review_candidates: ["wallet-c"] },
    {
      ...VALID_EXPERIMENTAL_BATCH_SCORE,
      feature_reference: {
        ...VALID_EXPERIMENTAL_BATCH_SCORE.feature_reference,
        training_cutoff: "2024-01-01T00:00:00Z",
      },
    },
    {
      ...VALID_EXPERIMENTAL_BATCH_SCORE,
      feature_reference: {
        ...VALID_EXPERIMENTAL_BATCH_SCORE.feature_reference,
        wallet_count: 41,
      },
    },
  ])("rejects inconsistent experimental batch responses", async (payload) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(payload)));
    await expect(
      new ApiClient("/api", async () => "token").scoreBatch(VALID_BATCH_REQUEST),
    ).rejects.toMatchObject({ code: "SCHEMA_MISMATCH" });
  });

  it("preserves disabled batch scoring as an availability state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(MODEL_NOT_APPROVED, 503)));
    await expect(
      new ApiClient("/api", async () => "token").scoreBatch(VALID_BATCH_REQUEST),
    ).resolves.toEqual({
      available: false,
      code: "MODEL_NOT_APPROVED",
      message: "Prediction capability is unavailable.",
    });
  });

  it("converts network failures into a structured backend-unavailable error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("network")));
    await expect(new ApiClient("/api").health()).rejects.toEqual(
      expect.objectContaining({ code: "BACKEND_UNAVAILABLE", status: 0 }),
    );
  });

  it("does not send a protected request when no signed-in token exists", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    await expect(new ApiClient("/api", async () => null).preview(VALID_REQUEST)).rejects.toMatchObject({
      code: "AUTHENTICATION_REQUIRED",
      status: 401,
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    [401, "INVALID_TOKEN"],
    [403, "USER_NOT_ALLOWED"],
    [503, "AUTH_VERIFICATION_UNAVAILABLE"],
  ])("preserves structured protected API errors for HTTP %i", async (status, code) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({
      error: { code, message: "Authentication response", details: null },
    }, status)));
    await expect(new ApiClient("/api", async () => "token").preview(VALID_REQUEST)).rejects.toMatchObject({
      code,
      status,
    });
  });

  it("never adds a Firebase token to public health requests", async () => {
    const tokenProvider = vi.fn().mockResolvedValue("token");
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({
      status: "ok", service: "service", version: "0.1.0",
    }));
    vi.stubGlobal("fetch", fetchMock);
    await new ApiClient("/api", tokenProvider).health();
    expect(tokenProvider).not.toHaveBeenCalled();
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).has("Authorization")).toBe(false);
  });
});
