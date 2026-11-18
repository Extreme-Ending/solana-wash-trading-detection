import type { ExperimentalBatchScoreResponse } from "../../api/types";
import { shortWallet } from "../../utils/anomalyDashboard";

interface AnalysisSummaryProps {
  result: ExperimentalBatchScoreResponse;
  onDetails: () => void;
  onNewAnalysis: () => void;
}

function score(value: number): string {
  return value.toLocaleString(undefined, { minimumFractionDigits: 3, maximumFractionDigits: 6 });
}

export function AnalysisSummary({ result, onDetails, onNewAnalysis }: AnalysisSummaryProps) {
  const events = result.ranked_wallets.reduce(
    (total, wallet) => total + wallet.included_historical_event_count,
    0,
  );
  const warningWallets = result.ranked_wallets.filter((wallet) => wallet.warnings.length > 0).length;
  const highest = result.ranked_wallets[0];
  const maximum = Math.max(...result.ranked_wallets.map((wallet) => wallet.anomaly_score), 0.000001);
  const single = result.wallets_scored === 1;

  return (
    <section className="analysis-summary" id="analysis-summary" tabIndex={-1} aria-labelledby="summary-heading">
      <div className="summary-heading-row">
        <div>
          <p className="overline burgundy">Latest analysis</p>
          <h2 id="summary-heading">Analysis summary</h2>
        </div>
        <button className="quiet-button" type="button" onClick={onNewAnalysis}>Start new analysis</button>
      </div>
      <div className="summary-metrics">
        <article><span>{single ? "Wallet analyzed" : "Wallets analyzed"}</span><strong>{result.wallets_scored}</strong><small>{result.wallets_rejected ? `${result.wallets_rejected} rejected` : "All submitted histories scored"}</small></article>
        <article><span>Historical events</span><strong>{events.toLocaleString()}</strong><small>Strictly before the scoring cutoff</small></article>
        <article><span>Selected for review</span><strong>{result.review_candidates.length}</strong><small>Capacity, not a fraud threshold</small></article>
        <article><span>{single ? "Anomaly score" : "Highest score"}</span><strong>{highest ? score(highest.anomaly_score) : "—"}</strong><small>Unitless experimental output</small></article>
      </div>
      <div className="summary-content">
        <article className="insight-card">
          <span className="insight-icon" aria-hidden="true">◇</span>
          <div>
            <h3>What this analysis shows</h3>
            <p>
              {single
                ? `One wallet was analyzed using ${events.toLocaleString()} historical event${events === 1 ? "" : "s"}. Its model-specific anomaly score is ${highest ? score(highest.anomaly_score) : "unavailable"}.`
                : `${result.wallets_scored} wallets were analyzed using ${events.toLocaleString()} historical events. ${highest ? shortWallet(highest.wallet) : "No wallet"} ranked highest within this submitted group.`}
              {` ${result.review_candidates.length} wallet${result.review_candidates.length === 1 ? " was" : "s were"} selected for manual review.`}
            </p>
            {warningWallets > 0 && <p className="summary-warning">{warningWallets} scored wallet{warningWallets === 1 ? " has" : "s have"} incomplete-history or data-quality warnings that limit interpretation.</p>}
            <details>
              <summary>How to interpret this result</summary>
              <p>Scores are relative, model-specific anomaly indicators derived from user-supplied DEX events. A higher score is not a probability, verified label or confirmation of wash trading.</p>
            </details>
          </div>
        </article>
        <article className="summary-chart-card">
          <div className="card-heading"><div><p className="overline">Score comparison</p><h3>{single ? "Submitted wallet" : "Wallet ranking"}</h3></div><span>n={result.wallets_scored}</span></div>
          <div className="mini-rank-chart" role="img" aria-label={`Anomaly score comparison for ${result.wallets_scored} wallets`}>
            {result.ranked_wallets.slice(0, 6).map((wallet) => (
              <div className="mini-rank-row" key={wallet.wallet} title={`${wallet.wallet}: ${score(wallet.anomaly_score)}`}>
                <span><b>#{wallet.rank}</b> {shortWallet(wallet.wallet)}</span>
                <span className="mini-track"><i style={{ width: `${Math.max(4, wallet.anomaly_score / maximum * 100)}%` }} /></span>
                <strong>{score(wallet.anomaly_score)}</strong>
              </div>
            ))}
          </div>
        </article>
      </div>
      <div className="summary-actions">
        <button className="primary-action" type="button" onClick={onDetails}>View detailed analysis</button>
        <p>Experimental anomaly results. Selected wallets require manual review; these results do not confirm fraud or wash trading.</p>
      </div>
    </section>
  );
}
