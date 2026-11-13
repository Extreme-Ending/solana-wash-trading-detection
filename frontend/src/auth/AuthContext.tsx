import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  getFirebaseAuthGateway,
  registerFirebaseAuthGateway,
  type AuthUser,
  type FirebaseAuthGateway,
} from "./firebase";

export interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  busy: boolean;
  error: string | null;
  signIn: () => Promise<void>;
  signOut: () => Promise<void>;
}

const unavailable = async () => undefined;

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  busy: false,
  error: null,
  signIn: unavailable,
  signOut: unavailable,
});

interface AuthProviderProps {
  children: ReactNode;
  gateway?: FirebaseAuthGateway;
}

function safeAuthMessage(action: "sign in" | "sign out", error: unknown): string {
  if (error instanceof Error && error.message.toLowerCase().includes("configuration")) {
    return "Authentication is not configured for this environment.";
  }
  return `Unable to ${action}. Please try again or contact the project administrator.`;
}

export function AuthProvider({ children, gateway }: AuthProviderProps) {
  if (gateway !== undefined) registerFirebaseAuthGateway(gateway);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const gatewayRef = useRef<FirebaseAuthGateway | null>(gateway ?? null);

  useEffect(() => {
    try {
      gatewayRef.current ??= getFirebaseAuthGateway();
      return gatewayRef.current.subscribe((nextUser) => {
        setUser(nextUser);
        setLoading(false);
        setError(null);
      });
    } catch (caught) {
      setLoading(false);
      setError(safeAuthMessage("sign in", caught));
      return undefined;
    }
  }, []);

  const signIn = useCallback(async () => {
    if (gatewayRef.current === null) {
      setError("Authentication is not configured for this environment.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await gatewayRef.current.signIn();
    } catch (caught) {
      setError(safeAuthMessage("sign in", caught));
    } finally {
      setBusy(false);
    }
  }, []);

  const signOutUser = useCallback(async () => {
    if (gatewayRef.current === null) return;
    setBusy(true);
    setError(null);
    try {
      await gatewayRef.current.signOut();
    } catch (caught) {
      setError(safeAuthMessage("sign out", caught));
    } finally {
      setBusy(false);
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, loading, busy, error, signIn, signOut: signOutUser }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
