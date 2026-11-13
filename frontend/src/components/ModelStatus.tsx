import { useEffect, useRef, useState } from "react";
import { ApiClientError, apiClient } from "../api/client";
import type { FeaturePreviewRequest } from "../api/types";
import { useAuth } from "../auth/AuthContext";

interface ModelStatusProps {
  request: FeaturePreviewRequest | null;
}

export function ModelStatus({ request }: ModelStatusProps) {
  const { user, loading } = useAuth();
  const [message, setMessage] = useState<string | null>(null);
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
    try {
      const response = await apiClient.scoringAvailability(request, active.signal);
      setMessage(response.message);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") return;
      setMessage(
        error instanceof ApiClientError
          ? error.status === 401
            ? "Your sign-in session is missing or expired. Sign in again."
            : error.status === 403
              ? "Your account is authenticated but is not approved for this API."
              : error.message
          : "The scoring gate could not be checked.",
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
        <p className="eyebrow">Model capability</p>
        <h2 id="model-heading">Anomaly scoring is not enabled</h2>
        <p>
          This phase exposes validated descriptive features only. Offline unsupervised experiments
          exist as research artifacts, but none is loaded or served; the service intentionally
          returns HTTP 503 for readiness and scoring requests.
        </p>
        <p className="model-rule"><strong>Interpretation rule:</strong> unusual activity would not, by itself, establish wash trading or fraud.</p>
        <button className="button secondary" type="button" onClick={check} disabled={!request || checking || loading || !user}>
          {checking ? "Checking gate…" : "Check scoring gate with last request"}
        </button>
        {!user && !loading
          ? <small>Sign in with an approved Google account to check the protected endpoint.</small>
          : !request && <small>Generate a valid feature preview to enable this check.</small>}
        {message && <p className="gate-message" role="status">{message}</p>}
      </div>
    </section>
  );
}
