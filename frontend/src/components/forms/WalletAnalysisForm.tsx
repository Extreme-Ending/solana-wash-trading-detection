import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { ApiClientError, apiClient } from "../../api/client";
import type { BatchScoreRequest, ExperimentalBatchScoreResponse } from "../../api/types";
import { SYNTHETIC_BATCH_AS_OF, SYNTHETIC_BATCH_JSON } from "../../data/syntheticBatch";
import {
  importAnalysisFile,
  MAX_BATCH_EVENTS,
  MAX_BATCH_WALLETS,
  MAX_EVENTS_PER_WALLET,
  parseAnalysisInput,
} from "../../utils/analysisInput";
import { InputValidationError, MAX_REQUEST_BYTES } from "../../utils/validation";

interface WalletAnalysisFormProps {
  onSuccess: (result: ExperimentalBatchScoreResponse, request: BatchScoreRequest) => void;
  onStart: () => void;
}

export function friendlyAnalysisError(error: unknown): string {
  if (!(error instanceof ApiClientError)) return "Analysis could not be completed. Try again.";
  if (error.status === 401) return "Your session has expired. Sign in again and retry.";
  if (error.status === 403) return "This Google account is not approved to use the analysis service.";
  if (error.status === 413) return "The submitted history exceeds the service request limit.";
  if (error.status === 400 || error.status === 422) return `The transaction history was rejected: ${error.message}`;
  if (error.status === 429) return "Too many requests were sent. Wait briefly before trying again.";
  if (error.code === "MODEL_NOT_APPROVED") return "Experimental scoring is unavailable in this environment.";
  if (error.code === "EXPERIMENTAL_MODEL_UNAVAILABLE") return "The local experimental model is unavailable or failed its integrity checks.";
  if (error.status === 503 && error.code.startsWith("AUTH_")) return "Authentication verification is temporarily unavailable.";
  if (error.status >= 500) return "The analysis service encountered a temporary error. Try again later.";
  return error.message;
}

export function WalletAnalysisForm({ onSuccess, onStart }: WalletAnalysisFormProps) {
  const [asOf, setAsOf] = useState("");
  const [reviewBudget, setReviewBudget] = useState("2");
  const [json, setJson] = useState("[]");
  const [expanded, setExpanded] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const loadDemonstration = () => {
    controller.current?.abort();
    setAsOf(SYNTHETIC_BATCH_AS_OF);
    setReviewBudget("2");
    setJson(SYNTHETIC_BATCH_JSON);
    setExpanded(true);
    setMessage("Demonstration data loaded. These synthetic histories are for interface testing only.");
    onStart();
  };

  const importFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".json")) {
      setMessage("Import failed: select a JSON file.");
      return;
    }
    if (file.size > MAX_REQUEST_BYTES) {
      setMessage(`Import failed: the file exceeds ${MAX_REQUEST_BYTES.toLocaleString()} bytes.`);
      return;
    }
    try {
      const imported = importAnalysisFile(await file.text());
      setJson(imported.json);
      if (imported.asOf) setAsOf(imported.asOf);
      if (imported.reviewBudget) setReviewBudget(imported.reviewBudget);
      setExpanded(true);
      setMessage("JSON imported locally. Nothing has been submitted yet.");
      onStart();
    } catch (error) {
      setMessage(`Import failed: ${error instanceof Error ? error.message : "invalid file."}`);
    }
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    let parsed;
    try {
      parsed = parseAnalysisInput(json, asOf, reviewBudget);
    } catch (error) {
      setMessage(error instanceof InputValidationError ? error.message : "The input is invalid.");
      return;
    }
    controller.current?.abort();
    const active = new AbortController();
    controller.current = active;
    setSubmitting(true);
    setMessage(`Analyzing ${parsed.walletsDetected} wallet${parsed.walletsDetected === 1 ? "" : "s"} across ${parsed.eventsDetected} events…`);
    onStart();
    try {
      const response = await apiClient.scoreBatch(parsed.request, active.signal);
      if ("available" in response) {
        setMessage(response.message);
        return;
      }
      onSuccess(response, parsed.request);
      setMessage(null);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setMessage(friendlyAnalysisError(error));
    } finally {
      if (controller.current === active) {
        controller.current = null;
        setSubmitting(false);
      }
    }
  };

  return (
    <form className="analysis-form" onSubmit={submit} noValidate aria-describedby="analysis-guidance">
      <div className="analysis-form-grid">
        <label>
          <span>Scoring timestamp <small>UTC</small></span>
          <input value={asOf} onChange={(event) => { setAsOf(event.target.value); setMessage(null); onStart(); }} placeholder="2025-11-01T00:00:00Z" required />
        </label>
        <label>
          <span>Manual review capacity</span>
          <input type="number" min="1" max="20" step="1" value={reviewBudget} onChange={(event) => { setReviewBudget(event.target.value); setMessage(null); onStart(); }} required />
        </label>
        <button className="primary-action" type="submit" disabled={submitting}>
          {submitting ? <><span className="spinner" aria-hidden="true" /> Analyzing…</> : "Analyze wallets"}
        </button>
      </div>
      <div className="input-actions">
        <button type="button" className="quiet-button" onClick={() => setExpanded((current) => !current)} aria-expanded={expanded}>
          {expanded ? "Hide transaction-history input" : "Add transaction-history data"}
        </button>
        <label className="quiet-button file-action">Import JSON<input type="file" accept="application/json,.json" onChange={importFile} disabled={submitting} /></label>
        <button type="button" className="quiet-button" onClick={loadDemonstration} disabled={submitting}>Use demonstration data</button>
      </div>
      {expanded && (
        <div className="history-input">
          <label htmlFor="wallet-history-json">Wallet transaction histories</label>
          <textarea id="wallet-history-json" value={json} onChange={(event) => { setJson(event.target.value); setMessage(null); onStart(); }} rows={12} spellCheck={false} aria-describedby="analysis-guidance" />
        </div>
      )}
      <p id="analysis-guidance" className="analysis-guidance">
        Paste or import wallet-history JSON. The app detects one or many wallets; it does not retrieve live blockchain data. Limits: {MAX_BATCH_WALLETS} wallets, {MAX_BATCH_EVENTS} events total, {MAX_EVENTS_PER_WALLET} per wallet and {MAX_REQUEST_BYTES.toLocaleString()} bytes.
      </p>
      {message && <div className={message.startsWith("Analyzing") ? "form-status loading" : "form-status"} role="status" aria-live="polite">{message}</div>}
    </form>
  );
}
