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

  it("does not accept an unexpected successful scoring response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse({ anomaly_score: 0.99 })));
    await expect(new ApiClient("/api", async () => "token").scoringAvailability(VALID_REQUEST)).rejects.toMatchObject({ code: "UNSUPPORTED_MODEL_RESPONSE" });
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
