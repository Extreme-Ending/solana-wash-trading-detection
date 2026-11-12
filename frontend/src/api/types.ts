export const FEATURE_NAMES = [
  "historical_event_count",
  "unique_transaction_count",
  "active_day_count",
  "events_per_active_day",
  "observed_activity_duration_days",
  "total_usd_volume",
  "mean_usd_volume",
  "median_usd_volume",
  "max_usd_volume",
  "std_usd_volume",
  "time_since_last_event_hours",
  "inter_event_mean_seconds",
  "inter_event_median_seconds",
  "inter_event_std_seconds",
  "events_last_24h",
  "events_last_7d",
  "events_last_30d",
  "unique_token_count",
  "unique_token_pair_count",
  "unique_dex_count",
  "token_concentration",
  "dex_concentration",
  "missing_fee_proportion",
  "multi_instruction_transaction_count",
  "single_event_history",
  "insufficient_history_7d",
  "insufficient_history_30d",
  "observable_history_days",
  "history_coverage_30d_fraction",
] as const;

export type FeatureName = (typeof FEATURE_NAMES)[number];
export type FeatureValue = number | boolean | null;

export interface EventInput {
  source_row_number: number;
  wallet: string;
  block_time: string;
  block_slot: number;
  tx_hash: string;
  dex: string;
  token_pair: string | null;
  token_in: string;
  token_out: string;
  amount_usd: number;
  fee_usd?: number | null;
  outer_instruction_index?: number | null;
  inner_instruction_index?: number | null;
}

export type EventDraft = Omit<EventInput, "wallet">;

export interface FeaturePreviewRequest {
  as_of: string;
  events: EventInput[];
}

export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
}

export interface ErrorIssue {
  location: string[];
  message: string;
  type: string;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown> | null;
  };
}

export interface AvailabilityResponse {
  available: false;
  code: "MODEL_NOT_APPROVED";
  message: string;
}

export interface FeaturePreviewResponse {
  status: "descriptive_features";
  source: "user_supplied_unverified_events";
  interpretation: string;
  wallet: string;
  as_of: string;
  supplied_event_count: number;
  included_historical_event_count: number;
  excluded_at_or_after_cutoff_count: number;
  feature_rules_version: string;
  feature_registry_sha256: string;
  feature_order: FeatureName[];
  features: Record<FeatureName, FeatureValue>;
}
