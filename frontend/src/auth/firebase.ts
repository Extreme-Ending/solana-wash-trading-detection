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
