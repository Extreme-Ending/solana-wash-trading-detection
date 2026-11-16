import {
  FEATURE_NAMES,
  type FeatureName,
  type FeaturePreviewRequest,
  type FeaturePreviewResponse,
  type FeatureValue,
  type BatchScoreRequest,
  type ExperimentalBatchScoreResponse,
  type ExperimentalScoreResponse,
} from "../api/types";

export const VALID_REQUEST: FeaturePreviewRequest = {
  as_of: "2025-02-01T00:00:00Z",
  events: [
    {
      source_row_number: 1,
      wallet: "synthetic-wallet-demo-001",
      block_time: "2025-01-31T18:00:00Z",
      block_slot: 1001,
      tx_hash: "synthetic-transaction-001",
      dex: "synthetic-dex-a",
      token_pair: "TOKEN-A/TOKEN-B",
      token_in: "synthetic-token-a",
      token_out: "synthetic-token-b",
      amount_usd: 125.5,
      fee_usd: null,
      outer_instruction_index: 1,
      inner_instruction_index: 0,
    },
  ],
};

const FEATURE_VALUES = Object.fromEntries(
  FEATURE_NAMES.map((name, index) => [name, index + 1]),
) as Record<FeatureName, FeatureValue>;

FEATURE_VALUES.single_event_history = true;
FEATURE_VALUES.insufficient_history_7d = true;
FEATURE_VALUES.insufficient_history_30d = true;
FEATURE_VALUES.inter_event_mean_seconds = null;
FEATURE_VALUES.inter_event_median_seconds = null;
FEATURE_VALUES.inter_event_std_seconds = null;
FEATURE_VALUES.token_concentration = 0.5;
FEATURE_VALUES.dex_concentration = 0.75;
FEATURE_VALUES.missing_fee_proportion = 0;
FEATURE_VALUES.history_coverage_30d_fraction = 0.8;

const BINARY_FEATURES = new Set<FeatureName>([
  "single_event_history",
  "insufficient_history_7d",
  "insufficient_history_30d",
]);

const FEATURE_REFERENCE_STATISTICS = Object.fromEntries(
  FEATURE_NAMES.map((name, index) => {
    const binary = BINARY_FEATURES.has(name);
    return [name, {
      observed_count: 40,
      missing_count: 0,
      minimum: 0,
      quartile_1: binary ? 0 : index + 1,
      median: binary ? 0 : index + 2,
      mean: binary ? 0.25 : index + 2,
      quartile_3: binary ? 1 : index + 3,
      maximum: binary ? 1 : index + 4,
      is_binary: binary,
      is_constant: false,
    }];
  }),
) as ExperimentalBatchScoreResponse["feature_reference"]["statistics"];

export const VALID_PREVIEW: FeaturePreviewResponse = {
  status: "descriptive_features",
  source: "user_supplied_unverified_events",
  interpretation: "These descriptive features do not establish wash trading or fraud.",
  wallet: "synthetic-wallet-demo-001",
  as_of: "2025-02-01T00:00:00Z",
  supplied_event_count: 1,
  included_historical_event_count: 1,
  excluded_at_or_after_cutoff_count: 0,
  feature_rules_version: "1.0.0",
  feature_registry_sha256: "synthetic-registry-digest",
  feature_order: [...FEATURE_NAMES],
  features: FEATURE_VALUES,
};

export function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

export const MODEL_NOT_APPROVED = {
  error: {
    code: "MODEL_NOT_APPROVED",
    message: "Prediction capability is unavailable.",
    details: { prediction_available: false },
  },
};

export const VALID_EXPERIMENTAL_SCORE: ExperimentalScoreResponse = {
  status: "experimental_anomaly_score",
  methodology_status: "experimental_unsupervised_research_only",
  source: "user_supplied_unverified_events",
  wallet: "synthetic-wallet-demo-001",
  as_of: "2025-02-01T00:00:00Z",
  supplied_event_count: 1,
  included_historical_event_count: 1,
  excluded_at_or_after_cutoff_count: 0,
  model_id: "isolation_forest",
  model_version: "4B.1",
  anomaly_score: 0.413245,
  score_direction: "higher_means_more_anomalous_relative_to_training_reference",
  score_units: "model_specific_unitless_isolation_forest_score",
  is_probability: false,
  training_cutoff: "2025-09-01T00:00:00Z",
  feature_rules_version: "1.0.0",
  feature_registry_sha256: "synthetic-registry-digest",
  observable_history_days: 0,
  warnings: ["The submitted event history is user-supplied and may be incomplete or unverified."],
  interpretation: "Experimental anomaly score; not a probability or fraud determination.",
};

export const VALID_BATCH_REQUEST: BatchScoreRequest = {
  as_of: "2025-11-01T00:00:00Z",
  review_budget: 2,
  wallet_histories: [
    { wallet: "wallet-a", events: [{ ...VALID_REQUEST.events[0], wallet: "wallet-a" }] },
    { wallet: "wallet-b", events: [{ ...VALID_REQUEST.events[0], wallet: "wallet-b" }] },
    { wallet: "wallet-c", events: [{ ...VALID_REQUEST.events[0], wallet: "wallet-c" }] },
  ],
};

export const VALID_EXPERIMENTAL_BATCH_SCORE: ExperimentalBatchScoreResponse = {
  status: "experimental_batch_anomaly_ranking",
  methodology_status: "experimental_unsupervised_research_only",
  source: "user_supplied_unverified_events",
  model_id: "isolation_forest",
  model_version: "4B.1",
  as_of: "2025-11-01T00:00:00Z",
  training_cutoff: "2025-09-01T00:00:00Z",
  score_direction: "higher_means_more_anomalous_relative_to_training_reference",
  score_units: "model_specific_unitless_isolation_forest_score",
  is_probability: false,
  feature_rules_version: "1.0.0",
  feature_registry_sha256: "synthetic-registry-digest",
  feature_reference: {
    version: "training_reference_v1",
    source: "phase_3_training_snapshots",
    training_cutoff: "2025-09-01T00:00:00Z",
    snapshot_sha256: "synthetic-training-snapshot-digest",
    wallet_count: 40,
    feature_registry_sha256: "synthetic-registry-digest",
    feature_order: [...FEATURE_NAMES],
    statistics: FEATURE_REFERENCE_STATISTICS,
    comparison_method: "robust_iqr_distance_for_nonbinary_nonconstant_features",
  },
  wallets_submitted: 3,
  wallets_scored: 3,
  wallets_rejected: 0,
  review_budget_requested: 2,
  review_budget: 2,
  review_candidates: ["wallet-a", "wallet-b"],
  ranked_wallets: [
    {
      wallet: "wallet-a",
      anomaly_score: 0.63,
      rank: 1,
      selected_for_review: true,
      supplied_event_count: 1,
      included_historical_event_count: 1,
      excluded_at_or_after_cutoff_count: 0,
      observable_history_days: 10,
      features: { ...FEATURE_VALUES, historical_event_count: 14 },
      warnings: [],
    },
    {
      wallet: "wallet-b",
      anomaly_score: 0.51,
      rank: 2,
      selected_for_review: true,
      supplied_event_count: 1,
      included_historical_event_count: 1,
      excluded_at_or_after_cutoff_count: 0,
      observable_history_days: 5,
      features: { ...FEATURE_VALUES, historical_event_count: 8 },
      warnings: [],
    },
    {
      wallet: "wallet-c",
      anomaly_score: 0.4,
      rank: 3,
      selected_for_review: false,
      supplied_event_count: 1,
      included_historical_event_count: 1,
      excluded_at_or_after_cutoff_count: 0,
      observable_history_days: 1,
      features: { ...FEATURE_VALUES, historical_event_count: 1 },
      warnings: ["Less than seven days of observable history are available."],
    },
  ],
  rejected_wallets: [],
  warnings: [
    "Ranks are relative only to the wallets scored in this submitted batch.",
    "The review budget represents analyst capacity, not a validated decision threshold.",
  ],
  interpretation: "Experimental statistical anomalies requiring review; not confirmed wash trading or fraud.",
};
