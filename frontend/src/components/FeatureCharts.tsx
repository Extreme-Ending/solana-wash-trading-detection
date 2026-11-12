import type { FeatureName, FeaturePreviewResponse } from "../api/types";

interface FeatureChartsProps {
  preview: FeaturePreviewResponse;
}

interface BarDatum {
  name: FeatureName;
  label: string;
}

const ACTIVITY: BarDatum[] = [
  { name: "historical_event_count", label: "Events" },
  { name: "unique_transaction_count", label: "Transactions" },
  { name: "active_day_count", label: "Active days" },
];

const WINDOWS: BarDatum[] = [
  { name: "events_last_24h", label: "24 hours" },
  { name: "events_last_7d", label: "7 days" },
  { name: "events_last_30d", label: "30 days" },
];

const VOLUME: BarDatum[] = [
  { name: "total_usd_volume", label: "Total USD" },
  { name: "mean_usd_volume", label: "Mean USD" },
  { name: "median_usd_volume", label: "Median USD" },
  { name: "max_usd_volume", label: "Maximum USD" },
];

const DIVERSITY: BarDatum[] = [
  { name: "unique_token_count", label: "Tokens" },
  { name: "unique_token_pair_count", label: "Token pairs" },
  { name: "unique_dex_count", label: "DEX labels" },
];

function numericValue(preview: FeaturePreviewResponse, name: FeatureName): number | null {
  const value = preview.features[name];
  return typeof value === "number" ? value : null;
}

function BarChart({ title, data, preview }: { title: string; data: BarDatum[]; preview: FeaturePreviewResponse }) {
  const values = data.map((item) => numericValue(preview, item.name));
  const maximum = Math.max(...values.map((value) => value ?? 0), 1);

  return (
    <article className="chart-card">
      <h3>{title}</h3>
      <div className="bar-chart" role="img" aria-label={`${title}: ${data.map((item, index) => `${item.label} ${values[index] ?? "unavailable"}`).join(", ")}`}>
        {data.map((item, index) => {
          const value = values[index];
          const width = value === null ? 0 : Math.max((value / maximum) * 100, value === 0 ? 0 : 3);
          return (
            <div className="bar-row" key={item.name}>
              <span>{item.label}</span>
              <div className="bar-track" aria-hidden="true"><span style={{ width: `${width}%` }} /></div>
              <strong>{value === null ? "—" : value.toLocaleString()}</strong>
            </div>
          );
        })}
      </div>
    </article>
  );
}

function ProportionMeter({ label, value }: { label: string; value: number | null }) {
  const percent = value === null ? null : Math.max(0, Math.min(value * 100, 100));
  return (
    <div className="meter-row">
      <div><span>{label}</span><strong>{percent === null ? "Unavailable" : `${percent.toFixed(1)}%`}</strong></div>
      <div className="meter-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent ?? undefined}>
        <span style={{ width: `${percent ?? 0}%` }} />
      </div>
    </div>
  );
}

export function FeatureCharts({ preview }: FeatureChartsProps) {
  return (
    <section className="section-shell" aria-labelledby="charts-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Visual comparison</p>
          <h2 id="charts-heading">Feature patterns at a glance</h2>
        </div>
        <p>Charts show only values returned by the feature-preview API.</p>
      </div>
      <div className="chart-grid">
        <BarChart title="Observed activity" data={ACTIVITY} preview={preview} />
        <BarChart title="USD volume summaries" data={VOLUME} preview={preview} />
        <BarChart title="Closed-open lookback windows" data={WINDOWS} preview={preview} />
        <BarChart title="Market diversity" data={DIVERSITY} preview={preview} />
        <article className="chart-card">
          <h3>Coverage, completeness and concentration</h3>
          <div className="meter-list">
            <ProportionMeter label="30-day history coverage" value={numericValue(preview, "history_coverage_30d_fraction")} />
            <ProportionMeter label="Token concentration" value={numericValue(preview, "token_concentration")} />
            <ProportionMeter label="DEX concentration" value={numericValue(preview, "dex_concentration")} />
            <ProportionMeter label="Missing fee values" value={numericValue(preview, "missing_fee_proportion")} />
          </div>
        </article>
      </div>
      <p className="chart-caveat">Relative bar lengths are local to each chart. They are descriptive comparisons, not thresholds or risk indicators.</p>
    </section>
  );
}
