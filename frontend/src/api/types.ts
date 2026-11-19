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

export interface BatchWalletHistory {
  wallet: string;
  events: EventInput[];
}

export interface BatchScoreRequest {
  as_of: string;
  wallet_histories: BatchWalletHistory[];
  review_budget?: number;
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

export interface UnavailableResponse {
  available: false;
  code: "MODEL_NOT_APPROVED" | "EXPERIMENTAL_MODEL_UNAVAILABLE";
  message: string;
}

export interface ExperimentalReadinessResponse {
  status: "ready";
  available: true;
  capability: "experimental_anomaly_scoring";
  methodology_status: "experimental_unsupervised_research_only";
  is_probability: false;
  message: string;
}

export type AvailabilityResponse = UnavailableResponse | ExperimentalReadinessResponse;

export interface ExperimentalScoreResponse {
  status: "experimental_anomaly_score";
  methodology_status: "experimental_unsupervised_research_only";
  source: "user_supplied_unverified_events";
  wallet: string;
  as_of: string;
  supplied_event_count: number;
  included_historical_event_count: number;
  excluded_at_or_after_cutoff_count: number;
  model_id: "isolation_forest";
  model_version: string;
  anomaly_score: number;
  score_direction: "higher_means_more_anomalous_relative_to_training_reference";
  score_units: "model_specific_unitless_isolation_forest_score";
  is_probability: false;
  training_cutoff: string;
  feature_rules_version: string;
  feature_registry_sha256: string;
  observable_history_days: number;
  warnings: string[];
  interpretation: string;
}

export type BatchWalletRejectionCode =
  | "EMPTY_WALLET_HISTORY"
  | "WALLET_EVENT_MISMATCH"
  | "DUPLICATE_SOURCE_ROW"
  | "DUPLICATE_EVENT_RECORD"
  | "INSUFFICIENT_HISTORY"
  | "FEATURE_INPUT_INVALID";

export interface BatchWalletScore {
  wallet: string;
  anomaly_score: number;
  rank: number;
  selected_for_review: boolean;
  supplied_event_count: number;
  included_historical_event_count: number;
  excluded_at_or_after_cutoff_count: number;
  observable_history_days: number;
  features: Record<FeatureName, FeatureValue>;
  warnings: string[];
}

export interface FeatureReferenceStatistic {
  observed_count: number;
  missing_count: number;
  minimum: number;
  quartile_1: number;
  median: number;
  mean: number;
  quartile_3: number;
  maximum: number;
  is_binary: boolean;
  is_constant: boolean;
}

export interface FeatureTrainingReference {
  version: "training_reference_v1";
  source: "phase_3_training_snapshots";
  training_cutoff: string;
  snapshot_sha256: string;
  wallet_count: number;
  feature_registry_sha256: string;
  feature_order: FeatureName[];
  statistics: Record<FeatureName, FeatureReferenceStatistic>;
  comparison_method: "robust_iqr_distance_for_nonbinary_nonconstant_features";
}

export interface BatchWalletRejection {
  wallet: string;
  code: BatchWalletRejectionCode;
  message: string;
  supplied_event_count: number;
}

export interface ExperimentalBatchScoreResponse {
  status: "experimental_batch_anomaly_ranking";
  methodology_status: "experimental_unsupervised_research_only";
  source: "user_supplied_unverified_events";
  model_id: "isolation_forest";
  model_version: string;
  as_of: string;
  training_cutoff: string;
  score_direction: "higher_means_more_anomalous_relative_to_training_reference";
  score_units: "model_specific_unitless_isolation_forest_score";
  is_probability: false;
  feature_rules_version: string;
  feature_registry_sha256: string;
  feature_reference: FeatureTrainingReference;
  wallets_submitted: number;
  wallets_scored: number;
  wallets_rejected: number;
  review_budget_requested: number | null;
  review_budget: number;
  review_candidates: string[];
  ranked_wallets: BatchWalletScore[];
  rejected_wallets: BatchWalletRejection[];
  warnings: string[];
  interpretation: "Experimental statistical anomalies requiring review; not confirmed wash trading or fraud.";
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
