import { useEffect, useRef, useState, type FormEvent } from "react";
import { ApiClientError, apiClient } from "../api/client";
import type {
  BatchScoreRequest,
  BatchWalletHistory,
  ExperimentalBatchScoreResponse,
} from "../api/types";
import { useAuth } from "../auth/AuthContext";
import {
  SYNTHETIC_BATCH_AS_OF,
  SYNTHETIC_BATCH_HISTORIES,
  SYNTHETIC_BATCH_JSON,
} from "../data/syntheticBatch";

const MAX_BATCH_WALLETS = 20;
const MAX_BATCH_EVENTS = 100;
const MAX_EVENTS_PER_WALLET = 50;
const MAX_REQUEST_BYTES = 262_144;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseHistories(text: string): BatchWalletHistory[] {
  if (new TextEncoder().encode(text).length > MAX_REQUEST_BYTES) {
    throw new Error(`JSON exceeds ${MAX_REQUEST_BYTES.toLocaleString()} bytes.`);
  }
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Error("Wallet histories must be valid JSON.");
  }
  if (!Array.isArray(value) || value.length === 0) {
    throw new Error("Provide a non-empty JSON array of wallet-history groups.");
  }
  if (value.length > MAX_BATCH_WALLETS) {
    throw new Error(`At most ${MAX_BATCH_WALLETS} wallets may be submitted.`);
  }
  let totalEvents = 0;
  const wallets = new Set<string>();
  for (const group of value) {
    if (!isRecord(group) || typeof group.wallet !== "string" || !group.wallet.trim()) {
      throw new Error("Every group must contain a non-empty wallet identifier.");
    }
    if (wallets.has(group.wallet)) {
      throw new Error("Each wallet may appear in only one group.");
    }
    wallets.add(group.wallet);
    if (!Array.isArray(group.events)) {
      throw new Error(`Wallet ${group.wallet} must contain an events array.`);
    }
    if (group.events.length > MAX_EVENTS_PER_WALLET) {
      throw new Error(`Wallet ${group.wallet} exceeds ${MAX_EVENTS_PER_WALLET} events.`);
    }
    totalEvents += group.events.length;
  }
  if (totalEvents > MAX_BATCH_EVENTS) {
    throw new Error(`The batch exceeds ${MAX_BATCH_EVENTS} total events.`);
  }
  return value as BatchWalletHistory[];
}

function errorMessage(error: unknown): string {
  if (!(error instanceof ApiClientError)) return "The batch scoring request failed.";
  if (error.status === 401) return "Your sign-in session is missing or expired. Sign in again.";
  if (error.status === 403) return "Your account is authenticated but is not approved for this API.";
  if (error.status === 413) return `The batch exceeds a service limit. ${error.message}`;
  if (error.status === 429) return "Too many requests reached this service instance. Wait before trying again.";
  if (error.status === 503 && error.code.startsWith("AUTH_")) {
    return "Authentication verification is temporarily unavailable.";
  }
  return error.message;
}

export function BatchScoring() {
  const { user, loading } = useAuth();
  const [asOf, setAsOf] = useState("");
  const [reviewBudget, setReviewBudget] = useState("2");
  const [historiesJson, setHistoriesJson] = useState("[]");
  const [message, setMessage] = useState<string | null>(null);
  const [result, setResult] = useState<ExperimentalBatchScoreResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);
  useEffect(() => {
    controller.current?.abort();
    setResult(null);
    setMessage(null);
    setSubmitting(false);
  }, [user?.uid]);

  const loadSynthetic = () => {
    controller.current?.abort();
    setAsOf(SYNTHETIC_BATCH_AS_OF);
    setReviewBudget("2");
    setHistoriesJson(SYNTHETIC_BATCH_JSON);
    setResult(null);
    setMessage(
      `${SYNTHETIC_BATCH_HISTORIES.length} synthetic wallet histories loaded. Review before submitting.`,
    );
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!user) {
      setMessage("Authentication required: sign in with an approved Google account.");
      return;
    }
    if (!asOf.trim()) {
      setMessage("Validation failed: provide one explicit UTC scoring timestamp.");
      return;
    }
    const parsedBudget = Number(reviewBudget);
    if (!Number.isInteger(parsedBudget) || parsedBudget < 1 || parsedBudget > MAX_BATCH_WALLETS) {
      setMessage(`Validation failed: review budget must be an integer from 1 to ${MAX_BATCH_WALLETS}.`);
      return;
    }
    let walletHistories: BatchWalletHistory[];
    try {
      walletHistories = parseHistories(historiesJson);
    } catch (error) {
      setMessage(`Validation failed: ${error instanceof Error ? error.message : "invalid JSON."}`);
      return;
    }

    controller.current?.abort();
    const active = new AbortController();
    controller.current = active;
    const request: BatchScoreRequest = {
      as_of: asOf.trim(),
      wallet_histories: walletHistories,
      review_budget: parsedBudget,
    };
    setSubmitting(true);
    setResult(null);
    setMessage(null);
    try {
      const response = await apiClient.scoreBatch(request, active.signal);
      if ("available" in response) setMessage(response.message);
      else setResult(response);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setMessage(`Batch scoring unavailable: ${errorMessage(error)}`);
    } finally {
      if (controller.current === active) {
        controller.current = null;
        setSubmitting(false);
      }
    }
  };

  return (
    <section className="section-shell batch-scoring" id="batch-scoring" aria-labelledby="batch-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Experimental local capability</p>
          <h2 id="batch-heading">Rank a bounded wallet batch</h2>
        </div>
        <p>Compare anomaly scores within one submitted batch and select only the stated analyst review capacity.</p>
      </div>

      <div className="notice" role="note">
        <strong>Interpretation boundary:</strong> rankings are relative statistical anomalies, not probabilities,
        labels, confirmed wash trading, fraud findings, or evidence of intent. Production keeps this capability disabled.
      </div>
      {!loading && !user && (
        <div className="auth-required" role="status">
          Sign in with an approved Google account to submit a protected batch request.
        </div>
      )}

      <form onSubmit={submit} noValidate>
        <div className="form-grid">
          <label>
            <span>Shared scoring timestamp (UTC)</span>
            <input
              name="batch_as_of"
              value={asOf}
              onChange={(event) => setAsOf(event.target.value)}
              placeholder="2025-11-01T00:00:00Z"
              autoComplete="off"
              required
            />
          </label>
          <label>
            <span>Analyst review budget</span>
            <input
              name="review_budget"
              type="number"
              min="1"
              max={MAX_BATCH_WALLETS}
              step="1"
              value={reviewBudget}
              onChange={(event) => setReviewBudget(event.target.value)}
              required
            />
          </label>
        </div>
        <label className="json-field">
          <span>Wallet histories (JSON array)</span>
          <textarea
            name="wallet_histories"
            value={historiesJson}
            onChange={(event) => setHistoriesJson(event.target.value)}
            rows={18}
            spellCheck={false}
            aria-describedby="batch-guidance"
          />
        </label>
        <p className="field-guidance" id="batch-guidance">
          Maximum {MAX_BATCH_WALLETS} wallets, {MAX_BATCH_EVENTS} events total, and {MAX_EVENTS_PER_WALLET} events per wallet.
          The API includes only events with <code>block_time &lt; as_of</code>; wallet groups never share features.
        </p>
        <div className="form-actions">
          <button className="button primary" type="submit" disabled={submitting || loading || !user}>
            {submitting ? "Ranking wallets…" : "Request batch ranking"}
          </button>
          <button className="button secondary" type="button" onClick={loadSynthetic} disabled={submitting}>
            Load synthetic batch
          </button>
        </div>
        {message && <p className="form-message" role="status" aria-live="polite">{message}</p>}
      </form>

      {result && (
        <div className="batch-results" aria-live="polite">
          <div className="batch-summary">
            <p><strong>{result.wallets_scored}</strong> scored</p>
            <p><strong>{result.review_budget}</strong> selected for review</p>
            <p><strong>{result.wallets_rejected}</strong> rejected</p>
          </div>
          <p className="batch-interpretation">{result.interpretation}</p>
          <div className="table-scroll">
            <table>
              <caption>Wallet anomaly ranking within this submitted batch</caption>
              <thead><tr><th scope="col">Rank</th><th scope="col">Wallet</th><th scope="col">Anomaly score</th><th scope="col">History</th><th scope="col">Review</th></tr></thead>
              <tbody>
                {result.ranked_wallets.map((wallet) => (
                  <tr key={wallet.wallet}>
                    <td>{wallet.rank}</td>
                    <td><code>{wallet.wallet}</code></td>
                    <td>{wallet.anomaly_score.toFixed(6)}</td>
                    <td>
                      {wallet.included_historical_event_count} event(s) · {wallet.observable_history_days.toFixed(2)} days
                      {wallet.warnings.length > 0 && (
                        <ul className="wallet-warnings">
                          {wallet.warnings.map((warning) => <li key={warning}>{warning}</li>)}
                        </ul>
                      )}
                    </td>
                    <td>{wallet.selected_for_review ? <strong className="review-badge">Review candidate</strong> : "Outside budget"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {result.rejected_wallets.length > 0 && (
            <div className="rejected-wallets">
              <h3>Rejected wallet histories</h3>
              <ul>
                {result.rejected_wallets.map((wallet) => (
                  <li key={wallet.wallet}><code>{wallet.wallet}</code>: <strong>{wallet.code}</strong> — {wallet.message}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="batch-warnings">
            <h3>Batch warnings</h3>
            <ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
          </div>
        </div>
      )}
    </section>
  );
}
