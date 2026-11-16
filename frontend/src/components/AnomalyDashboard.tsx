import { useMemo, useState } from "react";
import type { BatchWalletScore, ExperimentalBatchScoreResponse } from "../api/types";
import { FEATURE_GROUPS, FEATURE_REGISTRY } from "../data/featureRegistry";
import {
  filterAndSortWallets,
  robustComparison,
  scoreDistribution,
  shortWallet,
  type WalletFilters,
  type WalletSort,
} from "../utils/anomalyDashboard";

const format = (value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 6 });

function RankedScoreChart({ wallets }: { wallets: BatchWalletScore[] }) {
  const maximum = Math.max(...wallets.map((wallet) => wallet.anomaly_score), 0.000001);
  return <article className="dashboard-panel"><h3>Ranked anomaly scores</h3>
    <p className="panel-note">Actual unitless model scores; longer bars are higher only within this submitted batch.</p>
    <div className="rank-chart" role="img" aria-label={`Ranked anomaly scores for ${wallets.length} filtered wallets`}>
      {wallets.map((wallet) => <div className="rank-chart-row" key={wallet.wallet} title={wallet.wallet}>
        <span><b>#{wallet.rank}</b> <code>{shortWallet(wallet.wallet)}</code></span>
        <span className="rank-track"><span style={{ width: `${Math.max(2, wallet.anomaly_score / maximum * 100)}%` }} /></span>
        <strong>{wallet.anomaly_score.toFixed(6)}</strong>
        <span>{wallet.selected_for_review ? "● Review" : "○ Outside budget"}</span>
      </div>)}
    </div>
  </article>;
}

function DistributionChart({ wallets }: { wallets: BatchWalletScore[] }) {
  const distribution = scoreDistribution(wallets);
  const maxCount = Math.max(...distribution.bins.map((bin) => bin.count), 1);
  return <article className="dashboard-panel"><h3>Score distribution</h3>
    <p className="panel-note">Visible sample n={wallets.length}. {distribution.kind === "dots" ? "Dot view is used because fewer than five wallets are visible." : "Histogram counts use the visible wallet set."}</p>
    <div className={`distribution ${distribution.kind}`} aria-label={`Score distribution for ${wallets.length} filtered wallets`}>
      {distribution.bins.map((bin, index) => <div key={`${bin.minimum}-${index}`} className="distribution-bin">
        <span className="distribution-mark" style={{ height: `${Math.max(8, bin.count / maxCount * 100)}%` }} />
        <strong>{bin.count}</strong><small>{bin.minimum.toFixed(3)}{bin.maximum !== bin.minimum ? `–${bin.maximum.toFixed(3)}` : ""}</small>
      </div>)}
    </div>
    <p className="panel-note">Scores are not probabilities and the shape does not define normal or fraudulent behaviour.</p>
  </article>;
}

function WalletDetail({ wallet, result, close }: { wallet: BatchWalletScore; result: ExperimentalBatchScoreResponse; close: () => void }) {
  return <section className="wallet-detail" aria-labelledby="wallet-detail-heading">
    <div className="detail-heading"><div><p className="eyebrow">Manual review context</p><h3 id="wallet-detail-heading">Wallet detail</h3></div><button className="button secondary" type="button" onClick={close}>Close detail</button></div>
    <code className="full-wallet">{wallet.wallet}</code>
    <dl className="detail-metadata">
      <div><dt>Original rank</dt><dd>#{wallet.rank}</dd></div><div><dt>Anomaly score</dt><dd>{wallet.anomaly_score.toFixed(6)}</dd></div>
      <div><dt>Review selection</dt><dd>{wallet.selected_for_review ? "Selected" : "Outside budget"}</dd></div><div><dt>Model</dt><dd>{result.model_id} {result.model_version}</dd></div>
      <div><dt>Scoring cutoff</dt><dd>{result.as_of}</dd></div><div><dt>Included events</dt><dd>{wallet.included_historical_event_count}</dd></div>
      <div><dt>Excluded events</dt><dd>{wallet.excluded_at_or_after_cutoff_count}</dd></div><div><dt>Observable history</dt><dd>{format(wallet.observable_history_days)} days</dd></div>
    </dl>
    {wallet.warnings.length > 0 && <div className="detail-warnings"><strong>Data-quality warnings</strong><ul>{wallet.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div>}
    <p className="feature-boundary">Feature comparisons are descriptive context only. They are not SHAP values, model contributions, causal explanations, labels, or evidence of misconduct.</p>
    {FEATURE_GROUPS.map((group) => <div className="detail-feature-group" key={group.id}><h4>{group.label}</h4><div className="table-scroll"><table><thead><tr><th>Feature</th><th>Wallet value</th><th>Training median</th><th>Training Q1–Q3</th><th>Descriptive comparison</th></tr></thead><tbody>
      {FEATURE_REGISTRY.filter((feature) => feature.group === group.id).map((feature) => {
        const value = wallet.features[feature.name]; const reference = result.feature_reference.statistics[feature.name];
        return <tr key={feature.name}><th scope="row"><span>{feature.label}</span><code>{feature.name}</code></th><td>{value === null ? "Missing" : typeof value === "boolean" ? String(value) : format(value)}</td><td>{format(reference.median)}</td><td>{format(reference.quartile_1)}–{format(reference.quartile_3)}</td><td>{robustComparison(value, reference)}</td></tr>;
      })}
    </tbody></table></div></div>)}
    <p className="reference-provenance">Reference: {result.feature_reference.wallet_count.toLocaleString()} earliest-cutoff Phase 3 training snapshots at {result.feature_reference.training_cutoff}; version <code>{result.feature_reference.version}</code>; snapshot <code>{result.feature_reference.snapshot_sha256}</code>.</p>
  </section>;
}

export function AnomalyDashboard({ result }: { result: ExperimentalBatchScoreResponse }) {
  const scores = result.ranked_wallets.map((wallet) => wallet.anomaly_score);
  const [filters, setFilters] = useState<WalletFilters>({ wallet: "", selectedOnly: false, warningsOnly: false, minEvents: 0, minHistoryDays: 0, minScore: Math.min(...scores), maxScore: Math.max(...scores) });
  const [sort, setSort] = useState<WalletSort>("rank");
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);
  const visible = useMemo(() => filterAndSortWallets(result.ranked_wallets, filters, sort), [result.ranked_wallets, filters, sort]);
  const chartWallets = useMemo(
    () => [...visible].sort((left, right) => right.anomaly_score - left.anomaly_score || left.rank - right.rank || left.wallet.localeCompare(right.wallet)),
    [visible],
  );
  const detail = result.ranked_wallets.find((wallet) => wallet.wallet === selectedWallet);
  const update = <K extends keyof WalletFilters>(key: K, value: WalletFilters[K]) => setFilters((current) => ({ ...current, [key]: value }));
  return <div className="batch-results" aria-live="polite">
    <h3>Batch anomaly analysis dashboard</h3>
    <div className="dashboard-summary">
      {[ ["Submitted", result.wallets_submitted], ["Scored", result.wallets_scored], ["Rejected", result.wallets_rejected], ["Review budget", result.review_budget], ["Selected", result.review_candidates.length], ["Model", `${result.model_id} ${result.model_version}`], ["Cutoff", result.as_of] ].map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}
    </div>
    <p className="batch-interpretation">{result.interpretation}</p>
    <div className="dashboard-charts"><RankedScoreChart wallets={chartWallets} /><DistributionChart wallets={visible} /></div>
    <fieldset className="dashboard-filters"><legend>Filter and sort visible wallets</legend>
      <label><span>Wallet identifier</span><input value={filters.wallet} onChange={(event) => update("wallet", event.target.value)} /></label>
      <label><span>Minimum events</span><input type="number" min="0" value={filters.minEvents} onChange={(event) => update("minEvents", Number(event.target.value))} /></label>
      <label><span>Minimum history days</span><input type="number" min="0" value={filters.minHistoryDays} onChange={(event) => update("minHistoryDays", Number(event.target.value))} /></label>
      <label><span>Minimum score</span><input type="number" step="any" value={filters.minScore} onChange={(event) => update("minScore", Number(event.target.value))} /></label>
      <label><span>Maximum score</span><input type="number" step="any" value={filters.maxScore} onChange={(event) => update("maxScore", Number(event.target.value))} /></label>
      <label><span>Sort by</span><select value={sort} onChange={(event) => setSort(event.target.value as WalletSort)}><option value="rank">Original rank</option><option value="score">Score</option><option value="events">Event count</option><option value="history">History duration</option><option value="wallet">Wallet</option></select></label>
      <label className="check-label"><input type="checkbox" checked={filters.selectedOnly} onChange={(event) => update("selectedOnly", event.target.checked)} /> Selected for review only</label>
      <label className="check-label"><input type="checkbox" checked={filters.warningsOnly} onChange={(event) => update("warningsOnly", event.target.checked)} /> Has warnings</label>
    </fieldset>
    <p className="visible-count" role="status">Showing {visible.length} of {result.wallets_scored} scored wallets. Filters never change original ranks or scores.</p>
    <div className="table-scroll"><table><caption>Wallet anomaly ranking within this submitted batch</caption><thead><tr><th>Rank</th><th>Wallet</th><th>Anomaly score</th><th>Events</th><th>History</th><th>Review</th><th>Detail</th></tr></thead><tbody>
      {visible.map((wallet) => <tr key={wallet.wallet}><td>#{wallet.rank}</td><td><code>{wallet.wallet}</code></td><td>{wallet.anomaly_score.toFixed(6)}</td><td>{wallet.included_historical_event_count}</td><td>{wallet.observable_history_days.toFixed(2)} days</td><td>{wallet.selected_for_review ? <strong className="review-badge">Review candidate</strong> : "Outside budget"}</td><td><button className="text-button" type="button" onClick={() => setSelectedWallet(wallet.wallet)}>Inspect</button></td></tr>)}
    </tbody></table></div>
    {visible.length === 0 && <p className="empty-filter">No scored wallets match the current filters.</p>}
    {detail && <WalletDetail wallet={detail} result={result} close={() => setSelectedWallet(null)} />}
    {result.rejected_wallets.length > 0 && <div className="rejected-wallets"><h3>Rejected wallet histories</h3><ul>{result.rejected_wallets.map((wallet) => <li key={wallet.wallet}><code>{wallet.wallet}</code>: <strong>{wallet.code}</strong> — {wallet.message}</li>)}</ul></div>}
    <div className="batch-warnings"><h3>Batch warnings</h3><ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div>
    <div className="notice"><strong>Scientific boundary:</strong> scores are unitless, relative, model-specific anomaly indicators based on the supplied historical data. Incomplete histories can change results; ranks are relative to this submitted batch. The model was trained without independently verified fraud labels. Scores are not fraud probabilities, verified labels, confirmed wash trading, or causal evidence. Review-budget selection expresses analyst capacity, not a validated threshold.</div>
  </div>;
}
