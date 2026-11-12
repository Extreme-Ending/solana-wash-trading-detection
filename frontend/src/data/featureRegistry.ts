import type { FeatureName } from "../api/types";

export type FeatureGroupId = "activity" | "volume" | "temporal" | "market" | "quality";

export interface FeatureDefinition {
  name: FeatureName;
  label: string;
  group: FeatureGroupId;
  definition: string;
  unit: "count" | "events/day" | "days" | "hours" | "seconds" | "usd" | "usd/event" | "proportion" | "indicator";
}

export const FEATURE_GROUPS: ReadonlyArray<{ id: FeatureGroupId; label: string; description: string }> = [
  { id: "activity", label: "Wallet activity", description: "Observed event and transaction coverage before the cutoff." },
  { id: "volume", label: "Transaction volume", description: "Descriptive USD summaries; large values are not misconduct evidence." },
  { id: "temporal", label: "Temporal behaviour", description: "Recency, event gaps, and closed-open activity windows." },
  { id: "market", label: "Token and DEX activity", description: "Diversity and concentration within the submitted swap history." },
  { id: "quality", label: "Data quality and observable history", description: "Missingness and coverage needed to interpret every other feature." },
];

export const FEATURE_REGISTRY: readonly FeatureDefinition[] = [
  { name: "historical_event_count", label: "Historical events", group: "activity", definition: "Retained events observed strictly before the cutoff.", unit: "count" },
  { name: "unique_transaction_count", label: "Unique transactions", group: "activity", definition: "Distinct transaction hashes before the cutoff.", unit: "count" },
  { name: "active_day_count", label: "Active UTC days", group: "activity", definition: "Distinct UTC calendar days with at least one event.", unit: "count" },
  { name: "events_per_active_day", label: "Events per active day", group: "activity", definition: "Historical event count divided by active UTC days.", unit: "events/day" },
  { name: "observed_activity_duration_days", label: "Observed activity duration", group: "activity", definition: "Elapsed time between first and last observed event.", unit: "days" },
  { name: "total_usd_volume", label: "Total USD volume", group: "volume", definition: "Sum of validated positive USD event amounts.", unit: "usd" },
  { name: "mean_usd_volume", label: "Mean USD volume", group: "volume", definition: "Mean validated USD amount per event.", unit: "usd/event" },
  { name: "median_usd_volume", label: "Median USD volume", group: "volume", definition: "Median validated USD amount per event.", unit: "usd/event" },
  { name: "max_usd_volume", label: "Maximum USD volume", group: "volume", definition: "Largest validated USD event amount.", unit: "usd" },
  { name: "std_usd_volume", label: "USD volume deviation", group: "volume", definition: "Population standard deviation of USD event amounts.", unit: "usd" },
  { name: "time_since_last_event_hours", label: "Time since last event", group: "temporal", definition: "Elapsed time from the latest prior event to the cutoff.", unit: "hours" },
  { name: "inter_event_mean_seconds", label: "Mean inter-event gap", group: "temporal", definition: "Mean gap between consecutive observed events.", unit: "seconds" },
  { name: "inter_event_median_seconds", label: "Median inter-event gap", group: "temporal", definition: "Median gap between consecutive observed events.", unit: "seconds" },
  { name: "inter_event_std_seconds", label: "Inter-event gap deviation", group: "temporal", definition: "Population standard deviation of consecutive event gaps.", unit: "seconds" },
  { name: "events_last_24h", label: "Events in last 24 hours", group: "temporal", definition: "Events in the closed-open 24-hour lookback window.", unit: "count" },
  { name: "events_last_7d", label: "Events in last 7 days", group: "temporal", definition: "Events in the closed-open seven-day lookback window.", unit: "count" },
  { name: "events_last_30d", label: "Events in last 30 days", group: "temporal", definition: "Events in the closed-open 30-day lookback window.", unit: "count" },
  { name: "unique_token_count", label: "Unique tokens", group: "market", definition: "Distinct token identifiers observed on either side of swaps.", unit: "count" },
  { name: "unique_token_pair_count", label: "Unique token pairs", group: "market", definition: "Distinct non-missing directional token-pair labels.", unit: "count" },
  { name: "unique_dex_count", label: "Unique DEX labels", group: "market", definition: "Distinct formatting-normalized DEX labels.", unit: "count" },
  { name: "token_concentration", label: "Token concentration", group: "market", definition: "Share of token-side appearances belonging to the most frequent token.", unit: "proportion" },
  { name: "dex_concentration", label: "DEX concentration", group: "market", definition: "Share of events routed through the most frequent DEX label.", unit: "proportion" },
  { name: "missing_fee_proportion", label: "Missing fee proportion", group: "quality", definition: "Fraction of historical events with unavailable USD fee.", unit: "proportion" },
  { name: "multi_instruction_transaction_count", label: "Multi-instruction transactions", group: "quality", definition: "Distinct transaction hashes represented by multiple events.", unit: "count" },
  { name: "single_event_history", label: "Single-event history", group: "quality", definition: "Whether only one event is observable before the cutoff.", unit: "indicator" },
  { name: "insufficient_history_7d", label: "History shorter than 7 days", group: "quality", definition: "Whether fewer than seven days separate first observation and cutoff.", unit: "indicator" },
  { name: "insufficient_history_30d", label: "History shorter than 30 days", group: "quality", definition: "Whether fewer than 30 days separate first observation and cutoff.", unit: "indicator" },
  { name: "observable_history_days", label: "Observable history", group: "quality", definition: "Elapsed time from first observed event to the cutoff.", unit: "days" },
  { name: "history_coverage_30d_fraction", label: "30-day history coverage", group: "quality", definition: "Observed-history fraction of a 30-day lookback, capped at one.", unit: "proportion" },
] as const;

export const FEATURE_BY_NAME = Object.fromEntries(
  FEATURE_REGISTRY.map((feature) => [feature.name, feature]),
) as Record<FeatureName, FeatureDefinition>;
