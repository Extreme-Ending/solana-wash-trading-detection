import { getApps, initializeApp, type FirebaseOptions } from "firebase/app";
import {
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  type Auth,
  type User,
} from "firebase/auth";

export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
}

export interface FirebaseAuthGateway {
  subscribe(listener: (user: AuthUser | null) => void): () => void;
  signIn(): Promise<void>;
  signOut(): Promise<void>;
  getIdToken(): Promise<string | null>;
}

export interface FirebaseAuthFailure {
  code: string | null;
  message: string;
}

type FirebaseEnvironment = Partial<Record<
  | "VITE_FIREBASE_API_KEY"
  | "VITE_FIREBASE_AUTH_DOMAIN"
  | "VITE_FIREBASE_PROJECT_ID"
  | "VITE_FIREBASE_APP_ID",
  string | undefined
>>;

const REQUIRED_KEYS = [
  "VITE_FIREBASE_API_KEY",
  "VITE_FIREBASE_AUTH_DOMAIN",
  "VITE_FIREBASE_PROJECT_ID",
  "VITE_FIREBASE_APP_ID",
] as const;

const PLACEHOLDER_VALUE = /(?:^|[_<{])(your|replace|example|changeme)(?:[_>}]|$)/i;

const SIGN_IN_ERROR_MESSAGES: Readonly<Record<string, string>> = {
  "auth/unauthorized-domain":
    "Google sign-in is not authorized for this website. Ask the project administrator to add this hostname to Firebase Authentication.",
  "auth/invalid-api-key":
    "Firebase sign-in configuration is invalid. Ask the project administrator to verify the web app configuration.",
  "auth/api-key-not-valid.-please-pass-a-valid-api-key.":
    "Firebase sign-in configuration is invalid. Ask the project administrator to verify the web app configuration.",
  "auth/operation-not-allowed":
    "Google sign-in is not enabled for this Firebase project. Ask the project administrator to enable the Google provider.",
  "auth/popup-blocked":
    "Your browser blocked the Google sign-in popup. Allow popups for this site and try again.",
  "auth/popup-closed-by-user":
    "Google sign-in was cancelled before completion. Try again when you are ready.",
  "auth/cancelled-popup-request":
    "A newer Google sign-in attempt replaced this one. Wait for the current attempt to finish, then try again.",
  "auth/network-request-failed":
    "Google sign-in could not reach Firebase. Check your connection and browser privacy settings, then try again.",
  "auth/account-exists-with-different-credential":
    "This email is already linked to a different sign-in method. Ask the project administrator for help linking the account.",
  "auth/operation-not-supported-in-this-environment":
    "This browser environment does not support Google popup sign-in. Use a standard HTTP or HTTPS browser window with web storage enabled.",
  "auth/web-storage-unsupported":
    "Google sign-in requires browser storage. Enable browser storage for this site and try again.",
};

function firebaseErrorCode(error: unknown): string | null {
  if (typeof error !== "object" || error === null || !("code" in error)) return null;
  const code = (error as { code?: unknown }).code;
  if (typeof code !== "string" || !/^auth\/[a-z0-9.-]+$/i.test(code)) return null;
  return code.toLowerCase();
}

export function describeFirebaseAuthFailure(
  action: "sign in" | "sign out",
  error: unknown,
): FirebaseAuthFailure {
  const code = firebaseErrorCode(error);
  if (action === "sign in" && code !== null && code in SIGN_IN_ERROR_MESSAGES) {
    return { code, message: SIGN_IN_ERROR_MESSAGES[code] };
  }
  if (
    error instanceof Error &&
    (error.message.toLowerCase().includes("configuration") ||
      error.message.includes("VITE_FIREBASE_"))
  ) {
    return {
      code,
      message: "Authentication is not configured for this environment.",
    };
  }
  return {
    code,
    message: `Unable to ${action}. Please try again or contact the project administrator.`,
  };
}

export function loadFirebaseConfig(
  environment: FirebaseEnvironment,
  production = false,
): FirebaseOptions {
  const values = Object.fromEntries(
    REQUIRED_KEYS.map((key) => [key, environment[key]?.trim() ?? ""]),
  ) as Record<(typeof REQUIRED_KEYS)[number], string>;
  const missing = REQUIRED_KEYS.filter((key) => !values[key]);
  if (missing.length > 0) {
    const prefix = production ? "Production Firebase configuration" : "Firebase configuration";
    throw new Error(`${prefix} is incomplete: ${missing.join(", ")}`);
  }
  const placeholders = REQUIRED_KEYS.filter((key) => PLACEHOLDER_VALUE.test(values[key]));
  if (placeholders.length > 0) {
    throw new Error(`Firebase configuration contains placeholder values: ${placeholders.join(", ")}`);
  }
  if (!/^[a-z][a-z0-9-]{4,28}[a-z0-9]$/.test(values.VITE_FIREBASE_PROJECT_ID)) {
    throw new Error("VITE_FIREBASE_PROJECT_ID is malformed");
  }
  let authDomain: URL;
  try {
    authDomain = new URL(`https://${values.VITE_FIREBASE_AUTH_DOMAIN}`);
  } catch {
    throw new Error("VITE_FIREBASE_AUTH_DOMAIN is malformed");
  }
  if (
    authDomain.hostname !== values.VITE_FIREBASE_AUTH_DOMAIN ||
    authDomain.username ||
    authDomain.password ||
    authDomain.pathname !== "/"
  ) {
    throw new Error("VITE_FIREBASE_AUTH_DOMAIN must be a hostname only");
  }
  const managedDomainSuffix = [".firebaseapp.com", ".web.app"].find((suffix) =>
    values.VITE_FIREBASE_AUTH_DOMAIN.endsWith(suffix),
  );
  if (
    managedDomainSuffix !== undefined &&
    values.VITE_FIREBASE_AUTH_DOMAIN !==
      `${values.VITE_FIREBASE_PROJECT_ID}${managedDomainSuffix}`
  ) {
    throw new Error("VITE_FIREBASE_AUTH_DOMAIN does not match VITE_FIREBASE_PROJECT_ID");
  }
  if (!/^1:\d+:web:[0-9a-f]+$/i.test(values.VITE_FIREBASE_APP_ID)) {
    throw new Error("VITE_FIREBASE_APP_ID is malformed");
  }
  return {
    apiKey: values.VITE_FIREBASE_API_KEY,
    authDomain: values.VITE_FIREBASE_AUTH_DOMAIN,
    projectId: values.VITE_FIREBASE_PROJECT_ID,
    appId: values.VITE_FIREBASE_APP_ID,
  };
}

function toAuthUser(user: User | null): AuthUser | null {
  if (user === null) return null;
  return { uid: user.uid, email: user.email, displayName: user.displayName };
}

class WebFirebaseAuthGateway implements FirebaseAuthGateway {
  private readonly provider = new GoogleAuthProvider();

  constructor(private readonly auth: Auth) {
    this.provider.setCustomParameters({ prompt: "select_account" });
  }

  subscribe(listener: (user: AuthUser | null) => void): () => void {
    return onAuthStateChanged(this.auth, (user) => listener(toAuthUser(user)));
  }

  async signIn(): Promise<void> {
    await signInWithPopup(this.auth, this.provider);
  }

  async signOut(): Promise<void> {
    await signOut(this.auth);
  }

  async getIdToken(): Promise<string | null> {
    return this.auth.currentUser?.getIdToken() ?? null;
  }
}

let cachedGateway: FirebaseAuthGateway | null = null;

export function registerFirebaseAuthGateway(gateway: FirebaseAuthGateway): void {
  cachedGateway = gateway;
}

export function getFirebaseAuthGateway(): FirebaseAuthGateway {
  if (cachedGateway !== null) return cachedGateway;
  const config = loadFirebaseConfig({
    VITE_FIREBASE_API_KEY: import.meta.env.VITE_FIREBASE_API_KEY,
    VITE_FIREBASE_AUTH_DOMAIN: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
    VITE_FIREBASE_PROJECT_ID: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    VITE_FIREBASE_APP_ID: import.meta.env.VITE_FIREBASE_APP_ID,
  }, import.meta.env.PROD);
  const appName = "solana-risk-frontend";
  const existing = getApps().find((candidate) => candidate.name === appName);
  const app = existing ?? initializeApp(config, appName);
  cachedGateway = new WebFirebaseAuthGateway(getAuth(app));
  return cachedGateway;
}

export async function firebaseIdTokenProvider(): Promise<string | null> {
  return getFirebaseAuthGateway().getIdToken();
}
