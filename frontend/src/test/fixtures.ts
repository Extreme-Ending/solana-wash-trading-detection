import {
  FEATURE_NAMES,
  type FeatureName,
  type FeaturePreviewRequest,
  type FeaturePreviewResponse,
  type FeatureValue,
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
