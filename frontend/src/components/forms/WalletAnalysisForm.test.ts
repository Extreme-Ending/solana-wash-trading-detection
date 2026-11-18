import { describe, expect, it } from "vitest";
import { ApiClientError } from "../../api/client";
import { friendlyAnalysisError } from "./WalletAnalysisForm";

describe("wallet analysis error messages", () => {
  it.each([
    [401, "INVALID_TOKEN", /session has expired/i],
    [403, "USER_NOT_ALLOWED", /not approved/i],
    [413, "REQUEST_TOO_LARGE", /request limit/i],
    [429, "RATE_LIMITED", /wait briefly/i],
    [503, "MODEL_NOT_APPROVED", /unavailable in this environment/i],
    [503, "AUTH_VERIFICATION_UNAVAILABLE", /authentication verification/i],
    [500, "INTERNAL_ERROR", /temporary error/i],
  ])("maps HTTP %i %s without exposing technical detail", (status, code, expected) => {
    const message = friendlyAnalysisError(new ApiClientError("Sensitive backend detail", status, code));
    expect(message).toMatch(expected);
    expect(message).not.toContain("Sensitive backend detail");
  });

  it("uses a safe message for network failures", () => {
    expect(friendlyAnalysisError(new TypeError("Failed to fetch"))).toBe(
      "Analysis could not be completed. Try again.",
    );
  });
});
