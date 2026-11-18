import { useEffect, useState, type FormEvent } from "react";
import { apiClient } from "../api/client";
import type { BatchScoreRequest, ExperimentalBatchScoreResponse } from "../api/types";
import { AnomalyDashboard } from "../components/AnomalyDashboard";
import { friendlyAnalysisError } from "../components/forms/WalletAnalysisForm";

interface AnalyticsPageProps {
  result: ExperimentalBatchScoreResponse | null;
  request: BatchScoreRequest | null;
  onResult: (result: ExperimentalBatchScoreResponse, request: BatchScoreRequest) => void;
  onHome: () => void;
}

export function AnalyticsPage({ result, request, onResult, onHome }: AnalyticsPageProps) {
  const [budget, setBudget] = useState(String(result?.review_budget ?? 1));
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => setBudget(String(result?.review_budget ?? 1)), [result?.review_budget]);

  const updateBudget = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!request || !result) return;
    const parsed = Number(budget);
    if (!Number.isInteger(parsed) || parsed < 1 || parsed > 20) {
      setMessage("Review capacity must be an integer from 1 to 20.");
      return;
    }
    const nextRequest = { ...request, review_budget: parsed };
    setSubmitting(true);
    setMessage("Submitting the histories again so the server can confirm the selection…");
    try {
      const response = await apiClient.scoreBatch(nextRequest);
      if ("available" in response) {
        setMessage(response.message);
      } else {
        onResult(response, nextRequest);
        setMessage("Review capacity updated from a new authenticated API response.");
      }
    } catch (error) {
      setMessage(friendlyAnalysisError(error));
    } finally {
      setSubmitting(false);
    }
  };

  if (!result) {
    return (
      <main id="main-content" className="analytics-page">
        <section className="analytics-empty">
          <span className="insight-icon" aria-hidden="true">◇</span>
          <p className="overline burgundy">Analytics</p>
          <h1>No analysis is available</h1>
          <p>Results are kept only in this browser session. Run a wallet analysis to populate charts, rankings and wallet details.</p>
          <button className="primary-action" type="button" onClick={onHome}>Go to wallet check</button>
        </section>
      </main>
    );
  }

  return (
    <main id="main-content" className="analytics-page">
      <header className="analytics-heading">
        <div><p className="overline burgundy">Detailed review</p><h1>Analytics</h1><p>Explore the latest submitted group without changing its stored scores or original ranks.</p></div>
        <button className="secondary-action" type="button" onClick={onHome}>← Back to summary</button>
      </header>
      <div className="method-notice" role="note"><strong>Experimental anomaly results.</strong> Selected wallets require manual review; these results do not confirm fraud or wash trading.</div>
      <form className="review-budget-control" onSubmit={(event) => void updateBudget(event)}>
        <div><strong>Manual review capacity</strong><span>Changing this resubmits the original histories; selections are never recalculated in the browser.</span></div>
        <label><span>Wallets to select</span><input type="number" min="1" max="20" step="1" value={budget} onChange={(event) => { setBudget(event.target.value); setMessage(null); }} /></label>
        <button className="secondary-action" type="submit" disabled={submitting || !request}>{submitting ? "Updating…" : "Update capacity"}</button>
      </form>
      {message && <p className="review-budget-message" role="status">{message}</p>}
      <AnomalyDashboard result={result} />
    </main>
  );
}
