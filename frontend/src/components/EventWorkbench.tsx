import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { ApiClientError, apiClient } from "../api/client";
import type { FeaturePreviewRequest, FeaturePreviewResponse } from "../api/types";
import {
  SYNTHETIC_AS_OF,
  SYNTHETIC_EVENTS_JSON,
  SYNTHETIC_WALLET,
} from "../data/syntheticExample";
import {
  buildPreviewRequest,
  InputValidationError,
  MAX_EVENTS,
  MAX_REQUEST_BYTES,
  parseImportedPayload,
} from "../utils/validation";

interface EventWorkbenchProps {
  onPreview: (response: FeaturePreviewResponse, request: FeaturePreviewRequest) => void;
  onClear: () => void;
}

export function EventWorkbench({ onPreview, onClear }: EventWorkbenchProps) {
  const [wallet, setWallet] = useState("");
  const [asOf, setAsOf] = useState("");
  const [eventsJson, setEventsJson] = useState("[]");
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const requestController = useRef<AbortController | null>(null);

  useEffect(() => () => requestController.current?.abort(), []);

  const loadSynthetic = () => {
    requestController.current?.abort();
    setWallet(SYNTHETIC_WALLET);
    setAsOf(SYNTHETIC_AS_OF);
    setEventsJson(SYNTHETIC_EVENTS_JSON);
    setMessage("Synthetic demonstration loaded. Review the values before submitting.");
    onClear();
  };

  const clear = () => {
    requestController.current?.abort();
    setWallet("");
    setAsOf("");
    setEventsJson("[]");
    setMessage(null);
    setSubmitting(false);
    onClear();
  };

  const importFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (file.size > MAX_REQUEST_BYTES) {
      setMessage(`Import rejected: the file exceeds ${MAX_REQUEST_BYTES.toLocaleString()} bytes.`);
      return;
    }
    try {
      const imported = parseImportedPayload(await file.text());
      if (imported.wallet) setWallet(imported.wallet);
      if (imported.asOf) setAsOf(imported.asOf);
      setEventsJson(imported.eventsJson);
      setMessage("JSON imported locally. Nothing has been submitted yet.");
      onClear();
    } catch (error) {
      setMessage(error instanceof Error ? `Import rejected: ${error.message}` : "Import rejected.");
    }
  };

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    requestController.current?.abort();
    let request: FeaturePreviewRequest;
    try {
      request = buildPreviewRequest(wallet, asOf, eventsJson);
    } catch (error) {
      const detail = error instanceof InputValidationError ? error.message : "The submitted values are invalid.";
      setMessage(`Validation failed: ${detail}`);
      return;
    }

    const controller = new AbortController();
    requestController.current = controller;
    setSubmitting(true);
    setMessage(null);
    try {
      const response = await apiClient.preview(request, controller.signal);
      onPreview(response, request);
      setMessage(`Preview generated from ${response.included_historical_event_count} historical event(s).`);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      const detail = error instanceof ApiClientError ? error.message : "The preview request failed.";
      setMessage(`Preview unavailable: ${detail}`);
      onClear();
    } finally {
      if (requestController.current === controller) {
        requestController.current = null;
        setSubmitting(false);
      }
    }
  };

  return (
    <section className="section-shell workbench" id="preview" aria-labelledby="preview-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">User-supplied events</p>
          <h2 id="preview-heading">Build a point-in-time feature preview</h2>
        </div>
        <p>The wallet identifier is applied to every submitted event; no wallet lookup is performed.</p>
      </div>

      <div className="notice" role="note">
        <strong>Privacy boundary:</strong> input is held only in page memory and sent to the configured
        API when you submit. Use synthetic or appropriately authorised research data.
      </div>

      <form onSubmit={submit} noValidate>
        <div className="form-grid">
          <label>
            <span>Wallet identifier</span>
            <input
              name="wallet"
              value={wallet}
              onChange={(event) => setWallet(event.target.value)}
              placeholder="Enter one wallet identifier"
              autoComplete="off"
              maxLength={128}
              required
            />
          </label>
          <label>
            <span>Scoring timestamp (UTC)</span>
            <input
              name="as_of"
              value={asOf}
              onChange={(event) => setAsOf(event.target.value)}
              placeholder="2025-02-01T00:00:00Z"
              autoComplete="off"
              required
            />
          </label>
        </div>

        <label className="json-field">
          <span>Event records (JSON array)</span>
          <textarea
            name="events"
            value={eventsJson}
            onChange={(event) => setEventsJson(event.target.value)}
            spellCheck={false}
            rows={16}
            aria-describedby="event-guidance"
          />
        </label>
        <p className="field-guidance" id="event-guidance">
          Between 1 and {MAX_EVENTS} events, maximum request size {MAX_REQUEST_BYTES.toLocaleString()} bytes.
          Timestamps must include <code>Z</code> or <code>+00:00</code>. Events at or after the cutoff are excluded by the API.
        </p>

        <div className="form-actions">
          <button className="button primary" type="submit" disabled={submitting}>
            {submitting ? "Generating preview…" : "Generate feature preview"}
          </button>
          <button className="button secondary" type="button" onClick={loadSynthetic} disabled={submitting}>
            Load synthetic example
          </button>
          <label className="button secondary file-button">
            Import local JSON
            <input type="file" accept="application/json,.json" onChange={importFile} disabled={submitting} />
          </label>
          <button className="text-button" type="button" onClick={clear}>Clear</button>
        </div>
        {message && <p className="form-message" role="status" aria-live="polite">{message}</p>}
      </form>
    </section>
  );
}
