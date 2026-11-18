import { useEffect, useMemo, useState } from "react";
import type {
  BatchWalletScore,
  ExperimentalBatchScoreResponse,
  FeatureName,
} from "../api/types";
import {
  FEATURE_BY_NAME,
  FEATURE_GROUPS,
  FEATURE_REGISTRY,
  type FeatureGroupId,
} from "../data/featureRegistry";
import {
  filterAndSortWallets,
  robustComparison,
  scoreDistribution,
  shortWallet,
  type WalletFilters,
  type WalletSort,
} from "../utils/anomalyDashboard";

const OVERVIEW_FEATURES: readonly FeatureName[] = [
  "historical_event_count",
  "total_usd_volume",
  "events_per_active_day",
  "unique_token_count",
  "time_since_last_event_hours",
  "observable_history_days",
];

const format = (value: number) =>
  value.toLocaleString(undefined, { maximumFractionDigits: 6 });

function defaultFilters(wallets: BatchWalletScore[]): WalletFilters {
  const scores = wallets.map((wallet) => wallet.anomaly_score);
  return {
    wallet: "",
    selectedOnly: false,
    warningsOnly: false,
    minEvents: 0,
    minHistoryDays: 0,
    minScore: Math.min(...scores),
    maxScore: Math.max(...scores),
  };
}

function RankedScoreChart({ wallets }: { wallets: BatchWalletScore[] }) {
  const maximum = Math.max(
    ...wallets.map((wallet) => wallet.anomaly_score),
    0.000001,
  );
  return (
    <article className="dashboard-panel">
      <div className="panel-heading">
        <div><p className="overline burgundy">Relative ordering</p><h2>Ranked anomaly scores</h2></div>
        <span>{wallets.length} visible</span>
      </div>
      <p className="panel-note">Actual unitless model scores. Bar lengths are comparable only within this submission.</p>
      {wallets.length ? (
        <div className="rank-chart" role="img" aria-label={`Ranked anomaly scores for ${wallets.length} filtered wallets`}>
          {wallets.map((wallet) => (
            <div className="rank-chart-row" key={wallet.wallet} title={wallet.wallet}>
              <span><b>#{wallet.rank}</b> <code>{shortWallet(wallet.wallet)}</code></span>
              <span className="rank-track"><span style={{ width: `${Math.max(2, (wallet.anomaly_score / maximum) * 100)}%` }} /></span>
              <strong>{wallet.anomaly_score.toFixed(6)}</strong>
              <span className={wallet.selected_for_review ? "chart-review selected" : "chart-review"}>
                {wallet.selected_for_review ? "Review" : "Outside capacity"}
              </span>
            </div>
          ))}
        </div>
      ) : <p className="empty-filter">No visible scores to chart.</p>}
    </article>
  );
}

function DistributionChart({ wallets }: { wallets: BatchWalletScore[] }) {
  const distribution = scoreDistribution(wallets);
  const maxCount = Math.max(...distribution.bins.map((bin) => bin.count), 1);
  return (
    <article className="dashboard-panel">
      <div className="panel-heading"><div><p className="overline burgundy">Visible sample</p><h2>Score distribution</h2></div><span>n={wallets.length}</span></div>
      <p className="panel-note">
        {distribution.kind === "dots"
          ? "A dot view is used for fewer than five visible wallets."
          : "Histogram counts use only the currently visible wallets."}
      </p>
      <div className={`distribution ${distribution.kind}`} role="img" aria-label={`Score distribution for ${wallets.length} filtered wallets`}>
        {distribution.bins.map((bin, index) => (
          <div key={`${bin.minimum}-${index}`} className="distribution-bin">
            <span className="distribution-mark" style={{ height: `${Math.max(8, (bin.count / maxCount) * 100)}%` }} />
            <strong>{bin.count}</strong>
            <small>{bin.minimum.toFixed(3)}{bin.maximum !== bin.minimum ? `–${bin.maximum.toFixed(3)}` : ""}</small>
          </div>
        ))}
      </div>
      <p className="panel-note">The distribution does not define normal behaviour or confirmed misconduct.</p>
    </article>
  );
}

type DetailSection = "overview" | FeatureGroupId | "all";

function DetailTable({
  wallet,
  result,
  featureNames,
}: {
  wallet: BatchWalletScore;
  result: ExperimentalBatchScoreResponse;
  featureNames: readonly FeatureName[];
}) {
  return (
    <div className="table-scroll detail-table">
      <table>
        <thead><tr><th>Feature</th><th>Wallet value</th><th>Training median</th><th>Training Q1–Q3</th><th>Descriptive comparison</th></tr></thead>
        <tbody>
          {featureNames.map((name) => {
            const feature = FEATURE_BY_NAME[name];
            const value = wallet.features[name];
            const reference = result.feature_reference.statistics[name];
            return (
              <tr key={name}>
                <th scope="row"><span>{feature.label}</span><code>{name}</code></th>
                <td>{value === null ? "Missing" : typeof value === "boolean" ? String(value) : format(value)}</td>
                <td>{format(reference.median)}</td>
                <td>{format(reference.quartile_1)}–{format(reference.quartile_3)}</td>
                <td>{robustComparison(value, reference)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function WalletDetail({
  wallet,
  result,
  close,
}: {
  wallet: BatchWalletScore;
  result: ExperimentalBatchScoreResponse;
  close: () => void;
}) {
  const [section, setSection] = useState<DetailSection>("overview");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [close]);

  const copyWallet = async () => {
    try {
      await navigator.clipboard.writeText(wallet.wallet);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  };

  const selectedFeatures = section === "overview"
    ? OVERVIEW_FEATURES
    : section === "all"
      ? FEATURE_REGISTRY.map((feature) => feature.name)
      : FEATURE_REGISTRY.filter((feature) => feature.group === section).map((feature) => feature.name);

  return (
    <div className="detail-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget) close();
    }}>
      <section className="wallet-detail" role="dialog" aria-modal="true" aria-labelledby="wallet-detail-heading">
        <div className="detail-heading">
          <div><p className="overline burgundy">Manual review context</p><h2 id="wallet-detail-heading">Wallet detail</h2></div>
          <button className="icon-button" type="button" onClick={close} aria-label="Close wallet detail">×</button>
        </div>
        <div className="wallet-identity">
          <code>{wallet.wallet}</code>
          <button type="button" className="text-button" onClick={() => void copyWallet()}>{copied ? "Copied" : "Copy identifier"}</button>
        </div>
        <dl className="detail-metadata">
          <div><dt>Original rank</dt><dd>#{wallet.rank}</dd></div>
          <div><dt>Anomaly score</dt><dd>{wallet.anomaly_score.toFixed(6)}</dd></div>
          <div><dt>Review selection</dt><dd>{wallet.selected_for_review ? "Selected" : "Outside capacity"}</dd></div>
          <div><dt>Included events</dt><dd>{wallet.included_historical_event_count}</dd></div>
          <div><dt>Excluded at/after cutoff</dt><dd>{wallet.excluded_at_or_after_cutoff_count}</dd></div>
          <div><dt>Observable history</dt><dd>{format(wallet.observable_history_days)} days</dd></div>
        </dl>
        {wallet.warnings.length > 0 && (
          <div className="detail-warnings" role="note"><strong>Data-quality warnings</strong><ul>{wallet.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul></div>
        )}
        <p className="feature-boundary">Feature comparisons are descriptive context—not SHAP values, model contributions, causal explanations, labels or evidence of misconduct.</p>
        <div className="detail-tabs" role="tablist" aria-label="Wallet feature sections">
          <button type="button" role="tab" aria-selected={section === "overview"} onClick={() => setSection("overview")}>Overview</button>
          {FEATURE_GROUPS.map((group) => (
            <button key={group.id} type="button" role="tab" aria-selected={section === group.id} onClick={() => setSection(group.id)}>{group.label}</button>
          ))}
          <button type="button" role="tab" aria-selected={section === "all"} onClick={() => setSection("all")}>All features</button>
        </div>
        <DetailTable wallet={wallet} result={result} featureNames={selectedFeatures} />
        <details className="reference-provenance">
          <summary>Training-reference provenance</summary>
          <p>{result.feature_reference.wallet_count.toLocaleString()} earliest-cutoff Phase 3 training snapshots at {result.feature_reference.training_cutoff}; version <code>{result.feature_reference.version}</code>; snapshot <code>{result.feature_reference.snapshot_sha256}</code>.</p>
        </details>
      </section>
    </div>
  );
}

export function AnomalyDashboard({ result }: { result: ExperimentalBatchScoreResponse }) {
  const initialFilters = useMemo(() => defaultFilters(result.ranked_wallets), [result.ranked_wallets]);
  const [filters, setFilters] = useState<WalletFilters>(initialFilters);
  const [sort, setSort] = useState<WalletSort>("rank");
  const [filtersOpen, setFiltersOpen] = useState(true);
  const [selectedWallet, setSelectedWallet] = useState<string | null>(null);
  const visible = useMemo(
    () => filterAndSortWallets(result.ranked_wallets, filters, sort),
    [result.ranked_wallets, filters, sort],
  );
  const chartWallets = useMemo(
    () => [...visible].sort((left, right) => right.anomaly_score - left.anomaly_score || left.rank - right.rank || left.wallet.localeCompare(right.wallet)),
    [visible],
  );
  const detail = result.ranked_wallets.find((wallet) => wallet.wallet === selectedWallet);
  const update = <K extends keyof WalletFilters>(key: K, value: WalletFilters[K]) =>
    setFilters((current) => ({ ...current, [key]: value }));
  const reset = () => {
    setFilters(initialFilters);
    setSort("rank");
  };

  return (
    <div className="batch-results" aria-live="polite">
      <h2 className="sr-only">Batch anomaly analysis dashboard</h2>
      <section className="dashboard-summary" aria-label="Analysis totals">
        <article><span>Wallets scored</span><strong>{result.wallets_scored}</strong><small>{result.wallets_rejected} rejected</small></article>
        <article><span>Selected for review</span><strong>{result.review_candidates.length}</strong><small>Capacity {result.review_budget}</small></article>
        <article><span>Highest score</span><strong>{result.ranked_wallets[0]?.anomaly_score.toFixed(6) ?? "—"}</strong><small>Unitless output</small></article>
        <article><span>Scoring cutoff</span><strong className="summary-date">{new Date(result.as_of).toLocaleDateString()}</strong><small>{result.as_of}</small></article>
      </section>

      <div className="dashboard-charts"><RankedScoreChart wallets={chartWallets} /><DistributionChart wallets={visible} /></div>

      <section className="ranking-section" aria-labelledby="wallet-ranking-heading">
        <div className="ranking-heading">
          <div><p className="overline burgundy">Manual-review queue</p><h2 id="wallet-ranking-heading">Wallet ranking</h2><p>Original ranks and scores remain fixed when filters change.</p></div>
          <button className="secondary-action" type="button" aria-expanded={filtersOpen} onClick={() => setFiltersOpen((current) => !current)}>{filtersOpen ? "Hide filters" : "Filter and sort"}</button>
        </div>
        {filtersOpen && (
          <fieldset className="dashboard-filters">
            <legend>Filter visible wallets</legend>
            <label><span>Wallet identifier</span><input value={filters.wallet} onChange={(event) => update("wallet", event.target.value)} /></label>
            <label><span>Minimum events</span><input type="number" min="0" value={filters.minEvents} onChange={(event) => update("minEvents", Number(event.target.value))} /></label>
            <label><span>Minimum history days</span><input type="number" min="0" value={filters.minHistoryDays} onChange={(event) => update("minHistoryDays", Number(event.target.value))} /></label>
            <label><span>Minimum score</span><input type="number" step="any" value={filters.minScore} onChange={(event) => update("minScore", Number(event.target.value))} /></label>
            <label><span>Maximum score</span><input type="number" step="any" value={filters.maxScore} onChange={(event) => update("maxScore", Number(event.target.value))} /></label>
            <label><span>Sort by</span><select value={sort} onChange={(event) => setSort(event.target.value as WalletSort)}><option value="rank">Original rank</option><option value="score">Score</option><option value="events">Event count</option><option value="history">History duration</option><option value="wallet">Wallet</option></select></label>
            <label className="check-label"><input type="checkbox" checked={filters.selectedOnly} onChange={(event) => update("selectedOnly", event.target.checked)} /> Selected for review only</label>
            <label className="check-label"><input type="checkbox" checked={filters.warningsOnly} onChange={(event) => update("warningsOnly", event.target.checked)} /> Has warnings</label>
            <button className="quiet-button" type="button" onClick={reset}>Reset filters</button>
          </fieldset>
        )}
        <p className="visible-count" role="status">Showing {visible.length} of {result.wallets_scored} scored wallets.</p>
        <div className="table-scroll ranking-table"><table>
          <caption className="sr-only">Wallet anomaly ranking within this submitted batch</caption>
          <thead><tr><th>Rank</th><th>Wallet</th><th>Anomaly score</th><th>Events</th><th>History</th><th>Review status</th><th><span className="sr-only">Action</span></th></tr></thead>
          <tbody>{visible.map((wallet) => (
            <tr key={wallet.wallet}>
              <td><strong>#{wallet.rank}</strong></td>
              <td><code title={wallet.wallet}>{shortWallet(wallet.wallet)}</code>{wallet.warnings.length > 0 && <span className="warning-dot" title={`${wallet.warnings.length} warning(s)`}>!</span>}</td>
              <td>{wallet.anomaly_score.toFixed(6)}</td>
              <td>{wallet.included_historical_event_count}</td>
              <td>{wallet.observable_history_days.toFixed(2)} days</td>
              <td>{wallet.selected_for_review ? <strong className="review-badge">Review candidate</strong> : <span className="muted-status">Outside capacity</span>}</td>
              <td><button className="text-button" type="button" onClick={() => setSelectedWallet(wallet.wallet)}>Inspect</button></td>
            </tr>
          ))}</tbody>
        </table></div>
        {visible.length === 0 && <p className="empty-filter">No scored wallets match the current filters.</p>}
      </section>

      {(result.rejected_wallets.length > 0 || result.warnings.length > 0) && (
        <details className="batch-messages">
          <summary>Submission warnings and rejected histories ({result.warnings.length + result.rejected_wallets.length})</summary>
          {result.rejected_wallets.length > 0 && <div><h3>Rejected wallet histories</h3><ul>{result.rejected_wallets.map((wallet) => <li key={wallet.wallet}><code>{wallet.wallet}</code>: <strong>{wallet.code}</strong> — {wallet.message}</li>)}</ul></div>}
          {result.warnings.length > 0 && <ul>{result.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul>}
        </details>
      )}
      <details className="methodology-details"><summary>Methodology and scientific boundary</summary><p>{result.interpretation} Scores are model-specific statistical anomaly indicators based on supplied historical data. They are not probabilities, verified labels, confirmed wash trading, fraud findings or causal evidence. Review selection expresses analyst capacity, not a validated decision threshold.</p><p>Model: <code>{result.model_id} {result.model_version}</code>. Training cutoff: <code>{result.training_cutoff}</code>.</p></details>
      {detail && <WalletDetail wallet={detail} result={result} close={() => setSelectedWallet(null)} />}
    </div>
  );
}
