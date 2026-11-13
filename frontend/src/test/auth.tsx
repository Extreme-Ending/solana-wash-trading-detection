import type { ReactElement, ReactNode } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { AuthProvider } from "../auth/AuthContext";
import type { AuthUser, FirebaseAuthGateway } from "../auth/firebase";

export const APPROVED_TEST_USER: AuthUser = {
  uid: "approved-test-uid",
  email: "approved@example.test",
  displayName: "Approved Researcher",
};

export function authGateway(
  user: AuthUser | null = APPROVED_TEST_USER,
  token = "valid-test-firebase-token",
): FirebaseAuthGateway {
  let currentUser = user;
  let listener: (next: AuthUser | null) => void = () => undefined;
  return {
    subscribe(nextListener) {
      listener = nextListener;
      listener(currentUser);
      return () => undefined;
    },
    async signIn() {
      currentUser = APPROVED_TEST_USER;
      listener(currentUser);
    },
    async signOut() {
      currentUser = null;
      listener(null);
    },
    async getIdToken() {
      return currentUser ? token : null;
    },
  };
}

export function renderWithAuth(
  element: ReactElement,
  gateway: FirebaseAuthGateway = authGateway(),
  options?: Omit<RenderOptions, "wrapper">,
) {
  function Wrapper({ children }: { children: ReactNode }) {
    return <AuthProvider gateway={gateway}>{children}</AuthProvider>;
  }
  return render(element, { wrapper: Wrapper, ...options });
}
