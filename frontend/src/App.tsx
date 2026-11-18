import { useEffect, useState } from "react";
import type { BatchScoreRequest, ExperimentalBatchScoreResponse } from "./api/types";
import { useAuth } from "./auth/AuthContext";
import { AppShell, type AppView } from "./components/layout/AppShell";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";

function viewFromHash(): AppView {
  return window.location.hash === "#analytics" ? "analytics" : "home";
}

export function App() {
  const { user, loading } = useAuth();
  const [view, setView] = useState<AppView>(viewFromHash);
  const [result, setResult] = useState<ExperimentalBatchScoreResponse | null>(null);
  const [lastRequest, setLastRequest] = useState<BatchScoreRequest | null>(null);

  useEffect(() => {
    const synchronizeView = () => setView(viewFromHash());
    window.addEventListener("hashchange", synchronizeView);
    return () => window.removeEventListener("hashchange", synchronizeView);
  }, []);

  useEffect(() => {
    setResult(null);
    setLastRequest(null);
    window.location.hash = "home";
  }, [user?.uid]);

  const navigate = (next: AppView) => {
    window.location.hash = next;
    setView(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleResult = (
    response: ExperimentalBatchScoreResponse,
    request: BatchScoreRequest,
  ) => {
    setResult(response);
    setLastRequest(request);
  };

  if (loading) {
    return (
      <main className="auth-loading" id="main-content" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        <p>Checking secure access…</p>
      </main>
    );
  }

  if (!user) return <LoginPage />;

  return (
    <AppShell view={view} hasAnalysis={Boolean(result)} onNavigate={navigate}>
      {view === "analytics" ? (
        <AnalyticsPage
          result={result}
          request={lastRequest}
          onResult={handleResult}
          onHome={() => navigate("home")}
        />
      ) : (
        <HomePage
          result={result}
          onResult={handleResult}
          onClear={() => {
            setResult(null);
            setLastRequest(null);
          }}
          onDetails={() => navigate("analytics")}
        />
      )}
      {lastRequest && (
        <span className="sr-only">
          Latest analysis used a review capacity of {lastRequest.review_budget}.
        </span>
      )}
    </AppShell>
  );
}
