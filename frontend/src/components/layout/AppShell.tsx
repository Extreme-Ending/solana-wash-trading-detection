import { useState, type ReactNode } from "react";
import { useAuth } from "../../auth/AuthContext";

export type AppView = "home" | "analytics";

interface AppShellProps {
  view: AppView;
  hasAnalysis: boolean;
  onNavigate: (view: AppView) => void;
  children: ReactNode;
}

export function Brand() {
  return (
    <span className="brand" aria-label="Wallet Insights">
      <span className="brand-mark" aria-hidden="true"><i /><i /><i /></span>
      <span>Wallet Insights</span>
    </span>
  );
}

export function AppShell({ view, hasAnalysis, onNavigate, children }: AppShellProps) {
  const { user, busy, error, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  const navigate = (next: AppView) => {
    setMenuOpen(false);
    setAccountOpen(false);
    onNavigate(next);
  };

  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content">Skip to main content</a>
      <header className="topbar">
        <div className="topbar-inner">
          <button className="brand-button" type="button" onClick={() => navigate("home")}>
            <Brand />
          </button>
          <button
            className="menu-toggle"
            type="button"
            aria-expanded={menuOpen}
            aria-controls="primary-navigation"
            onClick={() => setMenuOpen((current) => !current)}
          >
            <span aria-hidden="true">☰</span><span className="sr-only">Menu</span>
          </button>
          <nav id="primary-navigation" className={menuOpen ? "primary-nav open" : "primary-nav"} aria-label="Primary navigation">
            <button className={view === "home" ? "active" : ""} type="button" onClick={() => navigate("home")}>Home</button>
            <button className={view === "analytics" ? "active" : ""} type="button" onClick={() => navigate("analytics")}>
              Analytics{!hasAnalysis && <span className="sr-only">, no analysis available</span>}
            </button>
          </nav>
          <div className="account-menu">
            <button
              className="account-trigger"
              type="button"
              aria-expanded={accountOpen}
              onClick={() => setAccountOpen((current) => !current)}
            >
              <span className="avatar" aria-hidden="true">{(user?.displayName || user?.email || "U").slice(0, 1).toUpperCase()}</span>
              <span className="account-label">Account</span>
              <span aria-hidden="true">⌄</span>
            </button>
            {accountOpen && (
              <div className="account-popover">
                <strong>{user?.displayName || "Approved user"}</strong>
                <span>{user?.email || "Verified Google account"}</span>
                <button type="button" onClick={() => void signOut()} disabled={busy}>
                  {busy ? "Signing out…" : "Sign out"}
                </button>
                {error && <p className="account-error" role="alert">{error}</p>}
              </div>
            )}
          </div>
        </div>
      </header>
      {children}
      <footer className="site-footer">
        <Brand />
        <p>Experimental wallet anomaly analysis using user-supplied Solana DEX events.</p>
      </footer>
    </div>
  );
}
