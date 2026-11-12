import { useEffect, useState } from "react";
import { ApiClientError, apiClient } from "../api/client";

type LoadState = "checking" | "available" | "unavailable";

interface StatusState {
  backend: LoadState;
  backendDetail: string;
  scoring: LoadState;
  scoringDetail: string;
}

const INITIAL_STATUS: StatusState = {
  backend: "checking",
  backendDetail: "Contacting the configured API…",
  scoring: "checking",
  scoringDetail: "Checking the model gate…",
};

export function ServiceStatus() {
  const [status, setStatus] = useState(INITIAL_STATUS);

  useEffect(() => {
    const controller = new AbortController();

    void apiClient.health(controller.signal)
      .then((response) => setStatus((current) => ({
        ...current,
        backend: "available",
        backendDetail: `${response.service} v${response.version}`,
      })))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const detail = error instanceof ApiClientError ? error.message : "Health check failed.";
        setStatus((current) => ({ ...current, backend: "unavailable", backendDetail: detail }));
      });

    void apiClient.readiness(controller.signal)
      .then((response) => setStatus((current) => ({
        ...current,
        scoring: "unavailable",
        scoringDetail: response.message,
      })))
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const detail = error instanceof ApiClientError ? error.message : "Readiness check failed.";
        setStatus((current) => ({ ...current, scoring: "unavailable", scoringDetail: detail }));
      });

    return () => controller.abort();
  }, []);

  return (
    <section className="section-shell" id="status" aria-labelledby="status-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Runtime status</p>
          <h2 id="status-heading">Service and capability gates</h2>
        </div>
        <p>API availability and scoring availability are deliberately reported separately.</p>
      </div>
      <div className="status-grid" aria-live="polite">
        <article className="status-card">
          <div className={`status-dot ${status.backend}`} aria-hidden="true" />
          <div>
            <p className="status-label">Feature API</p>
            <h3>{status.backend === "checking" ? "Checking" : status.backend === "available" ? "Available" : "Unavailable"}</h3>
            <p>{status.backendDetail}</p>
          </div>
        </article>
        <article className="status-card">
          <div className={`status-dot ${status.scoring}`} aria-hidden="true" />
          <div>
            <p className="status-label">Model scoring</p>
            <h3>{status.scoring === "checking" ? "Checking" : "Unavailable by design"}</h3>
            <p>{status.scoringDetail}</p>
          </div>
        </article>
      </div>
    </section>
  );
}
