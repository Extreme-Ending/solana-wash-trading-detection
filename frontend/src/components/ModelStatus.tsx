import { useEffect, useRef, useState } from "react";
import { ApiClientError, apiClient } from "../api/client";
import type { ExperimentalScoreResponse, FeaturePreviewRequest } from "../api/types";
import { useAuth } from "../auth/AuthContext";

interface ModelStatusProps {
  request: FeaturePreviewRequest | null;
}

export function ModelStatus({ request }: ModelStatusProps) {
  const { user, loading } = useAuth();
  const [message, setMessage] = useState<string | null>(null);
  const [result, setResult] = useState<ExperimentalScoreResponse | null>(null);
  const [checking, setChecking] = useState(false);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => () => controller.current?.abort(), []);

  const check = async () => {
    if (!request) return;
    controller.current?.abort();
    const active = new AbortController();
    controller.current = active;
    setChecking(true);
    setMessage(null);
    setResult(null);
    try {
      const response = await apiClient.score(request, active.signal);
      if ("available" in response) setMessage(response.message);
      else setResult(response);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setMessage(
        error instanceof ApiClientError
          ? error.status === 401
            ? "Your sign-in session is missing or expired. Sign in again."
            : error.status === 403
              ? "Your account is authenticated but is not approved for this API."
              : error.status === 429
                ? "Too many requests reached this service instance. Wait before trying again."
              : error.message
          : "The experimental scoring request could not be completed.",
      );
    } finally {
      if (controller.current === active) {
        controller.current = null;
        setChecking(false);
      }
    }
  };

  return (
    <section className="model-gate" aria-labelledby="model-heading">
      <div className="model-icon" aria-hidden="true">◇</div>
      <div>
        <p className="eyebrow">Experimental model capability</p>
        <h2 id="model-heading">Anomaly scoring</h2>
        <p>
          When explicitly enabled, this section submits the same validated event history to the
          checksum-pinned Phase 4B Isolation Forest. The service refuses scoring if the artifact
          or its release configuration fails validation.
        </p>
        <p className="model-rule"><strong>Interpretation rule:</strong> a larger model-specific score means more unusual relative to the training reference. It is not a probability, label, or fraud determination.</p>
        <button className="button secondary" type="button" onClick={check} disabled={!request || checking || loading || !user}>
          {checking ? "Scoring…" : "Request experimental score"}
        </button>
        {!user && !loading
          ? <small>Sign in with an approved Google account to use the protected endpoint.</small>
          : !request && <small>Generate a valid feature preview before requesting a score.</small>}
        {message && <p className="gate-message" role="status">{message}</p>}
        {result && (
          <div className="score-result" role="status" aria-label="Experimental anomaly score">
            <p className="score-value">{result.anomaly_score.toFixed(6)}</p>
            <p><strong>Unit:</strong> model-specific, unitless Isolation Forest score</p>
            <dl>
              <div><dt>Model</dt><dd>{result.model_id} · {result.model_version}</dd></div>
              <div><dt>Methodology</dt><dd>Experimental unsupervised research only</dd></div>
              <div><dt>Training cutoff</dt><dd>{result.training_cutoff}</dd></div>
              <div><dt>Observable history</dt><dd>{result.observable_history_days.toFixed(2)} days</dd></div>
              <div><dt>Feature rules</dt><dd>{result.feature_rules_version}</dd></div>
            </dl>
            <p>{result.interpretation}</p>
            {result.warnings.length > 0 && (
              <div>
                <strong>Input and history warnings</strong>
                <ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
