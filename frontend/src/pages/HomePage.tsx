import { useEffect, useRef } from "react";
import type { BatchScoreRequest, ExperimentalBatchScoreResponse } from "../api/types";
import { WalletAnalysisForm } from "../components/forms/WalletAnalysisForm";
import { AnalysisSummary } from "../components/results/AnalysisSummary";

interface HomePageProps {
  result: ExperimentalBatchScoreResponse | null;
  onResult: (result: ExperimentalBatchScoreResponse, request: BatchScoreRequest) => void;
  onClear: () => void;
  onDetails: () => void;
}

export function HomePage({ result, onResult, onClear, onDetails }: HomePageProps) {
  const previousResult = useRef(result);
  useEffect(() => {
    if (result && result !== previousResult.current) {
      const summary = document.getElementById("analysis-summary");
      summary?.focus();
      summary?.scrollIntoView?.({ behavior: "smooth", block: "start" });
    }
    previousResult.current = result;
  }, [result]);

  return (
    <main id="main-content">
      <section className="home-hero" aria-labelledby="home-heading">
        <div className="hero-inner">
          <div className="hero-copy">
            <p className="overline light">Wallet anomaly analysis</p>
            <h1 id="home-heading">Check a wallet</h1>
            <p>Explore wallet activity and identify unusual patterns.</p>
          </div>
          <div className="analysis-card">
            <div className="analysis-card-heading">
              <div><h2>Analyze wallets</h2><p>Supply bounded Solana DEX transaction histories for one or more wallets.</p></div>
              <span className="secure-label">Protected analysis</span>
            </div>
            <WalletAnalysisForm onSuccess={onResult} onStart={onClear} />
          </div>
        </div>
      </section>
      {result ? (
        <AnalysisSummary result={result} onDetails={onDetails} onNewAnalysis={onClear} />
      ) : (
        <section className="home-empty" aria-labelledby="home-empty-heading">
          <div className="empty-illustration" aria-hidden="true"><span /><span /><span /></div>
          <div><p className="overline burgundy">Before you begin</p><h2 id="home-empty-heading">Historical events are required</h2><p>This interface does not look up live wallet activity. Import or paste authorized transaction-history JSON, or load the clearly labelled demonstration dataset to explore the workflow.</p></div>
          <dl><div><dt>One workflow</dt><dd>One or many wallets are detected automatically.</dd></div><div><dt>Point in time</dt><dd>Only events before your UTC cutoff are included.</dd></div><div><dt>Review support</dt><dd>Results prioritize manual inspection without assigning fraud labels.</dd></div></dl>
        </section>
      )}
    </main>
  );
}
