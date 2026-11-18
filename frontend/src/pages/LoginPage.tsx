import { useAuth } from "../auth/AuthContext";
import { Brand } from "../components/layout/AppShell";

export function LoginPage() {
  const { busy, error, signIn } = useAuth();
  return (
    <main className="login-page" id="main-content">
      <section className="login-hero" aria-labelledby="login-hero-heading">
        <div className="login-brand"><Brand /></div>
        <div className="login-hero-copy">
          <p className="overline">Solana wallet analysis</p>
          <h1 id="login-hero-heading">Welcome back</h1>
          <p>Sign in to continue to secure wallet analysis.</p>
        </div>
        <div className="login-orbit orbit-one" aria-hidden="true" />
        <div className="login-orbit orbit-two" aria-hidden="true" />
        <p className="login-boundary">Anomaly results support review. They do not confirm fraud or wash trading.</p>
      </section>
      <section className="login-auth" aria-labelledby="login-heading">
        <div className="login-card">
          <div className="login-symbol" aria-hidden="true"><i /><i /></div>
          <p className="overline burgundy">Secure access</p>
          <h2 id="login-heading">Sign in to Wallet Insights</h2>
          <p>Continue with your approved Google account.</p>
          <button className="google-button" type="button" onClick={() => void signIn()} disabled={busy}>
            <span className="google-mark" aria-hidden="true">G</span>
            {busy ? "Opening Google sign-in…" : "Continue with Google"}
          </button>
          {error && <div className="auth-alert" role="alert">{error}</div>}
          <p className="login-help">Access is limited to approved Google accounts. No password is stored by this application.</p>
        </div>
      </section>
    </main>
  );
}
