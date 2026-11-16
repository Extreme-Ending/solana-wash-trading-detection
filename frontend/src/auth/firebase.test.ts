import { describe, expect, it } from "vitest";
import { describeFirebaseAuthFailure, loadFirebaseConfig } from "./firebase";

const VALID_ENV = {
  VITE_FIREBASE_API_KEY: "public-web-api-key",
  VITE_FIREBASE_AUTH_DOMAIN: "research-project.firebaseapp.com",
  VITE_FIREBASE_PROJECT_ID: "research-project",
  VITE_FIREBASE_APP_ID: "1:123:web:abc",
};

describe("Firebase web configuration", () => {
  it("loads the public Firebase identifiers without accepting extra credentials", () => {
    expect(loadFirebaseConfig(VALID_ENV, true)).toEqual({
      apiKey: VALID_ENV.VITE_FIREBASE_API_KEY,
      authDomain: VALID_ENV.VITE_FIREBASE_AUTH_DOMAIN,
      projectId: VALID_ENV.VITE_FIREBASE_PROJECT_ID,
      appId: VALID_ENV.VITE_FIREBASE_APP_ID,
    });
  });

  it("fails closed when production Firebase configuration is missing", () => {
    expect(() => loadFirebaseConfig({ VITE_FIREBASE_PROJECT_ID: "research-project" }, true))
      .toThrow(/Production Firebase configuration is incomplete/);
  });

  it("rejects malformed project and auth-domain values", () => {
    expect(() => loadFirebaseConfig({ ...VALID_ENV, VITE_FIREBASE_PROJECT_ID: "WRONG" }))
      .toThrow(/PROJECT_ID/);
    expect(() => loadFirebaseConfig({ ...VALID_ENV, VITE_FIREBASE_AUTH_DOMAIN: "user@host.test" }))
      .toThrow(/AUTH_DOMAIN/);
  });

  it("rejects placeholder, mismatched managed-domain, and malformed app identifiers", () => {
    expect(() => loadFirebaseConfig({ ...VALID_ENV, VITE_FIREBASE_API_KEY: "YOUR_API_KEY" }))
      .toThrow(/placeholder/);
    expect(() => loadFirebaseConfig({
      ...VALID_ENV,
      VITE_FIREBASE_AUTH_DOMAIN: "different-project.firebaseapp.com",
    })).toThrow(/does not match/);
    expect(() => loadFirebaseConfig({ ...VALID_ENV, VITE_FIREBASE_APP_ID: "not-an-app-id" }))
      .toThrow(/APP_ID/);
  });
});

describe("Firebase authentication diagnostics", () => {
  it.each([
    ["auth/unauthorized-domain", "not authorized for this website"],
    ["auth/invalid-api-key", "configuration is invalid"],
    ["auth/operation-not-allowed", "not enabled"],
    ["auth/popup-blocked", "blocked the Google sign-in popup"],
    ["auth/popup-closed-by-user", "cancelled before completion"],
    ["auth/cancelled-popup-request", "newer Google sign-in attempt"],
    ["auth/network-request-failed", "could not reach Firebase"],
    ["auth/account-exists-with-different-credential", "different sign-in method"],
  ])("maps %s to a safe actionable message", (code, expectedText) => {
    const failure = describeFirebaseAuthFailure("sign in", {
      code,
      message: "sensitive Firebase provider detail",
      credential: "sensitive credential",
    });
    expect(failure).toEqual({ code, message: expect.stringContaining(expectedText) });
    expect(failure.message).not.toContain("sensitive");
  });

  it("does not expose unknown Firebase error details", () => {
    const failure = describeFirebaseAuthFailure("sign in", {
      code: "auth/internal-error",
      message: "sensitive internal detail",
    });
    expect(failure.code).toBe("auth/internal-error");
    expect(failure.message).toBe(
      "Unable to sign in. Please try again or contact the project administrator.",
    );
  });
});
