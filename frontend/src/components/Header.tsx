import { useAuth } from "../auth/AuthContext";

export function Header() {
  const { user, loading, busy, error, signIn, signOut } = useAuth();

  return (
    <header className="site-header">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <div className="header-inner">
        <a className="brand" href="#overview" aria-label="Solana wallet research dashboard home">
          <span className="brand-mark" aria-hidden="true">S</span>
          <span>
            <strong>Solana Wallet Research</strong>
            <small>Point-in-time feature explorer</small>
          </span>
        </a>
        <nav aria-label="Primary navigation">
          <a href="#status">Service</a>
          <a href="#preview">Preview</a>
          <a href="#results">Results</a>
          <a href="#methodology">Methodology</a>
        </nav>
        <div className="auth-control" aria-live="polite">
          {loading ? (
            <span className="auth-state">Checking sign-in…</span>
          ) : user ? (
            <>
              <span className="auth-identity" title={user.email ?? undefined}>
                {user.displayName || user.email || "Approved user"}
              </span>
              <button className="button secondary auth-button" type="button" onClick={() => void signOut()} disabled={busy}>
                {busy ? "Signing out…" : "Sign out"}
              </button>
            </>
          ) : (
            <button className="button primary auth-button" type="button" onClick={() => void signIn()} disabled={busy}>
              {busy ? "Signing in…" : "Sign in with Google"}
            </button>
          )}
          {error && <span className="auth-error" role="alert">{error}</span>}
        </div>
      </div>
    </header>
  );
}
