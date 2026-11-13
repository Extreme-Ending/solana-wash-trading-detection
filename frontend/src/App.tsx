import { useEffect, useState } from "react";
import type { FeaturePreviewRequest, FeaturePreviewResponse } from "./api/types";
import { useAuth } from "./auth/AuthContext";
import { EventWorkbench } from "./components/EventWorkbench";
import { FeatureCharts } from "./components/FeatureCharts";
import { FeatureResults } from "./components/FeatureResults";
import { Header } from "./components/Header";
import { Methodology } from "./components/Methodology";
import { ModelStatus } from "./components/ModelStatus";
import { ProjectOverview } from "./components/ProjectOverview";
import { ServiceStatus } from "./components/ServiceStatus";

export function App() {
  const { user } = useAuth();
  const [preview, setPreview] = useState<FeaturePreviewResponse | null>(null);
  const [lastRequest, setLastRequest] = useState<FeaturePreviewRequest | null>(null);

  const handlePreview = (
    response: FeaturePreviewResponse,
    request: FeaturePreviewRequest,
  ) => {
    setPreview(response);
    setLastRequest(request);
  };

  const clearPreview = () => {
    setPreview(null);
    setLastRequest(null);
  };

  useEffect(() => {
    clearPreview();
  }, [user?.uid]);

  return (
    <>
      <Header />
      <main id="main-content">
        <ProjectOverview />
        <ServiceStatus />
        <EventWorkbench onPreview={handlePreview} onClear={clearPreview} />
        {preview ? (
          <>
            <FeatureResults preview={preview} />
            <FeatureCharts preview={preview} />
          </>
        ) : (
          <section className="empty-state" aria-labelledby="results-placeholder-heading">
            <p className="eyebrow">Feature output</p>
            <h2 id="results-placeholder-heading">No descriptive preview yet</h2>
            <p>
              Submit one wallet's historical DEX swap events to inspect the registered
              point-in-time features. No anomaly score or fraud conclusion is generated.
            </p>
          </section>
        )}
        <ModelStatus request={lastRequest} />
        <Methodology />
      </main>
      <footer>
        <p>DSA 8401 Applied Machine Learning capstone · Local research interface</p>
        <p>Submitted events remain in this browser session and are sent only to the configured API.</p>
      </footer>
    </>
  );
}
