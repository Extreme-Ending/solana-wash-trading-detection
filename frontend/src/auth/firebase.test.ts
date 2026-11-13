import { describe, expect, it } from "vitest";
import { loadFirebaseConfig } from "./firebase";

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
});
