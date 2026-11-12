import type { FeaturePreviewResponse, FeatureValue } from "../api/types";
import { FEATURE_GROUPS, FEATURE_REGISTRY, type FeatureDefinition } from "../data/featureRegistry";

interface FeatureResultsProps {
  preview: FeaturePreviewResponse;
}

function formatNumber(value: number, unit: FeatureDefinition["unit"]): string {
  if (unit === "usd" || unit === "usd/event") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      maximumFractionDigits: 2,
    }).format(value);
  }
  if (unit === "proportion") return `${(value * 100).toFixed(1)}%`;
  if (unit === "count") return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

export function formatFeatureValue(value: FeatureValue, definition: FeatureDefinition): string {
  if (value === null) return "Unavailable";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return formatNumber(value, definition.unit);
}

export function FeatureResults({ preview }: FeatureResultsProps) {
  return (
    <section className="section-shell" id="results" aria-labelledby="results-heading">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Registered feature output</p>
          <h2 id="results-heading">All 29 descriptive wallet features</h2>
        </div>
        <p>{preview.included_historical_event_count} of {preview.supplied_event_count} submitted events occurred before the cutoff.</p>
      </div>

      <div className="result-context">
        <dl>
          <div><dt>Wallet</dt><dd>{preview.wallet}</dd></div>
          <div><dt>UTC cutoff</dt><dd>{preview.as_of}</dd></div>
          <div><dt>Rule version</dt><dd>{preview.feature_rules_version}</dd></div>
          <div><dt>Excluded at/after cutoff</dt><dd>{preview.excluded_at_or_after_cutoff_count}</dd></div>
        </dl>
        <p>{preview.interpretation}</p>
      </div>

      {FEATURE_GROUPS.map((group) => {
        const definitions = FEATURE_REGISTRY.filter((feature) => feature.group === group.id);
        return (
          <section className="feature-group" key={group.id} aria-labelledby={`feature-group-${group.id}`}>
            <div className="feature-group-heading">
              <h3 id={`feature-group-${group.id}`}>{group.label}</h3>
              <p>{group.description}</p>
            </div>
            <div className="feature-grid">
              {definitions.map((definition) => {
                const value = preview.features[definition.name];
                return (
                  <article className={`feature-card ${value === null ? "is-missing" : ""}`} key={definition.name}>
                    <p className="feature-label">{definition.label}</p>
                    <p className="feature-value">{formatFeatureValue(value, definition)}</p>
                    <p className="feature-unit">{definition.unit}</p>
                    <p className="feature-definition">{definition.definition}</p>
                    <code>{definition.name}</code>
                  </article>
                );
              })}
            </div>
          </section>
        );
      })}
    </section>
  );
}
