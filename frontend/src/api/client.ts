import { API_BASE_URL } from "./config";
import { firebaseIdTokenProvider } from "../auth/firebase";
import {
  FEATURE_NAMES,
  type AvailabilityResponse,
  type BatchScoreRequest,
  type BatchWalletRejectionCode,
  type ErrorResponse,
  type ExperimentalBatchScoreResponse,
  type ExperimentalScoreResponse,
  type FeatureName,
  type FeaturePreviewRequest,
  type FeaturePreviewResponse,
  type FeatureValue,
  type HealthResponse,
} from "./types";

export class ApiClientError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
    public readonly details: Record<string, unknown> | null = null,
  ) {
    super(message);
    this.name = "ApiClientError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isErrorResponse(value: unknown): value is ErrorResponse {
  return (
    isRecord(value) &&
    isRecord(value.error) &&
    typeof value.error.code === "string" &&
    typeof value.error.message === "string"
  );
}

async function readJson(response: Response): Promise<unknown> {
  try {
    return await response.json();
  } catch {
    throw new ApiClientError(
      "The backend returned an unreadable response.",
      response.status,
      "INVALID_RESPONSE",
    );
  }
}

function toApiError(status: number, payload: unknown): ApiClientError {
  if (isErrorResponse(payload)) {
    return new ApiClientError(
      payload.error.message,
      status,
      payload.error.code,
      isRecord(payload.error.details) ? payload.error.details : null,
    );
  }
  return new ApiClientError(
    "The backend request did not complete successfully.",
    status,
    "HTTP_ERROR",
  );
}

function isFeatureValue(value: unknown): value is FeatureValue {
  return value === null || typeof value === "boolean" || (typeof value === "number" && Number.isFinite(value));
}

function isNonnegativeInteger(value: unknown): value is number {
  return typeof value === "number" && Number.isInteger(value) && value >= 0;
}

function isPositiveInteger(value: unknown): value is number {
  return isNonnegativeInteger(value) && value > 0;
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function hasExactFeatureKeys(value: Record<string, unknown>): boolean {
  return Object.keys(value).join("|") === FEATURE_NAMES.join("|");
}

function isFeatureMap(value: unknown): boolean {
  return isRecord(value) && hasExactFeatureKeys(value) && FEATURE_NAMES.every((name) => isFeatureValue(value[name]));
}

function isFeatureReference(value: unknown, payload: Record<string, unknown>): boolean {
  if (
    !isRecord(value) ||
    value.version !== "training_reference_v1" ||
    value.source !== "phase_3_training_snapshots" ||
    value.training_cutoff !== payload.training_cutoff ||
    value.feature_registry_sha256 !== payload.feature_registry_sha256 ||
    typeof value.snapshot_sha256 !== "string" ||
    !value.snapshot_sha256 ||
    !isPositiveInteger(value.wallet_count) ||
    !Array.isArray(value.feature_order) ||
    value.feature_order.join("|") !== FEATURE_NAMES.join("|") ||
    value.comparison_method !== "robust_iqr_distance_for_nonbinary_nonconstant_features" ||
    !isRecord(value.statistics) ||
    !hasExactFeatureKeys(value.statistics)
  ) return false;
  const statistics = value.statistics as Record<string, unknown>;
  const binary = new Set(["single_event_history", "insufficient_history_7d", "insufficient_history_30d"]);
  return FEATURE_NAMES.every((name) => {
    const stat = statistics[name];
    if (!isRecord(stat)) return false;
    const values = [stat.minimum, stat.quartile_1, stat.median, stat.mean, stat.quartile_3, stat.maximum];
    return (
      isPositiveInteger(stat.observed_count) &&
      isNonnegativeInteger(stat.missing_count) &&
      stat.observed_count + stat.missing_count === value.wallet_count &&
      values.every((item) => typeof item === "number" && Number.isFinite(item)) &&
      (stat.minimum as number) <= (stat.quartile_1 as number) &&
      (stat.quartile_1 as number) <= (stat.median as number) &&
      (stat.median as number) <= (stat.quartile_3 as number) &&
      (stat.quartile_3 as number) <= (stat.maximum as number) &&
      (stat.minimum as number) <= (stat.mean as number) &&
      (stat.mean as number) <= (stat.maximum as number) &&
      stat.is_binary === binary.has(name) &&
      stat.is_constant === (stat.minimum === stat.maximum)
    );
  });
}

function assertFeaturePreview(payload: unknown): FeaturePreviewResponse {
  if (!isRecord(payload) || !Array.isArray(payload.feature_order) || !isRecord(payload.features)) {
    throw new ApiClientError("The feature response does not match the registered schema.", 200, "SCHEMA_MISMATCH");
  }
  const expected = FEATURE_NAMES.join("|");
  if (payload.feature_order.join("|") !== expected) {
    throw new ApiClientError("The backend feature order does not match this frontend version.", 200, "SCHEMA_MISMATCH");
  }
  for (const name of FEATURE_NAMES) {
    if (!(name in payload.features) || !isFeatureValue(payload.features[name])) {
      throw new ApiClientError(`Feature ${name} is missing or invalid.`, 200, "SCHEMA_MISMATCH");
    }
  }
  if (
    payload.status !== "descriptive_features" ||
    payload.source !== "user_supplied_unverified_events" ||
    typeof payload.wallet !== "string" ||
    typeof payload.as_of !== "string" ||
    typeof payload.interpretation !== "string" ||
    typeof payload.feature_rules_version !== "string" ||
    typeof payload.feature_registry_sha256 !== "string" ||
    !isNonnegativeInteger(payload.supplied_event_count) ||
    !isNonnegativeInteger(payload.included_historical_event_count) ||
    !isNonnegativeInteger(payload.excluded_at_or_after_cutoff_count) ||
    payload.included_historical_event_count + payload.excluded_at_or_after_cutoff_count !== payload.supplied_event_count
  ) {
    throw new ApiClientError("The feature response metadata is invalid.", 200, "SCHEMA_MISMATCH");
  }
  return payload as unknown as FeaturePreviewResponse;
}

function assertExperimentalScore(payload: unknown): ExperimentalScoreResponse {
  if (
    !isRecord(payload) ||
    payload.status !== "experimental_anomaly_score" ||
    payload.methodology_status !== "experimental_unsupervised_research_only" ||
    payload.source !== "user_supplied_unverified_events" ||
    typeof payload.wallet !== "string" ||
    typeof payload.as_of !== "string" ||
    payload.model_id !== "isolation_forest" ||
    typeof payload.model_version !== "string" ||
    typeof payload.anomaly_score !== "number" ||
    !Number.isFinite(payload.anomaly_score) ||
    payload.score_direction !== "higher_means_more_anomalous_relative_to_training_reference" ||
    payload.score_units !== "model_specific_unitless_isolation_forest_score" ||
    payload.is_probability !== false ||
    typeof payload.training_cutoff !== "string" ||
    typeof payload.feature_rules_version !== "string" ||
    typeof payload.feature_registry_sha256 !== "string" ||
    typeof payload.observable_history_days !== "number" ||
    !Number.isFinite(payload.observable_history_days) ||
    payload.observable_history_days < 0 ||
    !isNonnegativeInteger(payload.supplied_event_count) ||
    !isNonnegativeInteger(payload.included_historical_event_count) ||
    !isNonnegativeInteger(payload.excluded_at_or_after_cutoff_count) ||
    payload.included_historical_event_count + payload.excluded_at_or_after_cutoff_count !== payload.supplied_event_count ||
    !Array.isArray(payload.warnings) ||
    !payload.warnings.every((warning) => typeof warning === "string") ||
    typeof payload.interpretation !== "string"
  ) {
    throw new ApiClientError("The experimental score response is invalid.", 200, "SCHEMA_MISMATCH");
  }
  return payload as unknown as ExperimentalScoreResponse;
}

const REJECTION_CODES = new Set<BatchWalletRejectionCode>([
  "EMPTY_WALLET_HISTORY",
  "WALLET_EVENT_MISMATCH",
  "DUPLICATE_SOURCE_ROW",
  "DUPLICATE_EVENT_RECORD",
  "INSUFFICIENT_HISTORY",
  "FEATURE_INPUT_INVALID",
]);

function assertExperimentalBatchScore(payload: unknown): ExperimentalBatchScoreResponse {
  if (
    !isRecord(payload) ||
    payload.status !== "experimental_batch_anomaly_ranking" ||
    payload.methodology_status !== "experimental_unsupervised_research_only" ||
    payload.source !== "user_supplied_unverified_events" ||
    payload.model_id !== "isolation_forest" ||
    typeof payload.model_version !== "string" ||
    typeof payload.as_of !== "string" ||
    typeof payload.training_cutoff !== "string" ||
    payload.score_direction !== "higher_means_more_anomalous_relative_to_training_reference" ||
    payload.score_units !== "model_specific_unitless_isolation_forest_score" ||
    payload.is_probability !== false ||
    typeof payload.feature_rules_version !== "string" ||
    typeof payload.feature_registry_sha256 !== "string" ||
    !isFeatureReference(payload.feature_reference, payload) ||
    !isPositiveInteger(payload.wallets_submitted) ||
    !isPositiveInteger(payload.wallets_scored) ||
    !isNonnegativeInteger(payload.wallets_rejected) ||
    (payload.review_budget_requested !== null && !isPositiveInteger(payload.review_budget_requested)) ||
    !isNonnegativeInteger(payload.review_budget) ||
    !isStringArray(payload.review_candidates) ||
    !Array.isArray(payload.ranked_wallets) ||
    !Array.isArray(payload.rejected_wallets) ||
    !isStringArray(payload.warnings) ||
    payload.interpretation !== "Experimental statistical anomalies requiring review; not confirmed wash trading or fraud."
  ) {
    throw new ApiClientError("The experimental batch response is invalid.", 200, "SCHEMA_MISMATCH");
  }

  if (
    payload.wallets_scored !== payload.ranked_wallets.length ||
    payload.wallets_rejected !== payload.rejected_wallets.length ||
    payload.wallets_submitted !== payload.wallets_scored + payload.wallets_rejected ||
    payload.review_budget > payload.wallets_scored
  ) {
    throw new ApiClientError("The experimental batch counts are inconsistent.", 200, "SCHEMA_MISMATCH");
  }

  const rankedWallets = new Set<string>();
  for (let index = 0; index < payload.ranked_wallets.length; index += 1) {
    const item = payload.ranked_wallets[index];
    if (
      !isRecord(item) ||
      typeof item.wallet !== "string" ||
      !item.wallet ||
      typeof item.anomaly_score !== "number" ||
      !Number.isFinite(item.anomaly_score) ||
      item.rank !== index + 1 ||
      typeof item.selected_for_review !== "boolean" ||
      item.selected_for_review !== (item.rank <= payload.review_budget) ||
      !isNonnegativeInteger(item.supplied_event_count) ||
      !isPositiveInteger(item.included_historical_event_count) ||
      !isNonnegativeInteger(item.excluded_at_or_after_cutoff_count) ||
      item.included_historical_event_count + item.excluded_at_or_after_cutoff_count !== item.supplied_event_count ||
      typeof item.observable_history_days !== "number" ||
      !Number.isFinite(item.observable_history_days) ||
      item.observable_history_days < 0 ||
      !isFeatureMap(item.features) ||
      !isStringArray(item.warnings) ||
      rankedWallets.has(item.wallet)
    ) {
      throw new ApiClientError("A ranked wallet result is invalid.", 200, "SCHEMA_MISMATCH");
    }
    const previous = payload.ranked_wallets[index - 1];
    if (
      index > 0 &&
      isRecord(previous) &&
      typeof previous.anomaly_score === "number" &&
      (previous.anomaly_score < item.anomaly_score ||
        (previous.anomaly_score === item.anomaly_score &&
          typeof previous.wallet === "string" && previous.wallet > item.wallet))
    ) {
      throw new ApiClientError("The wallet ranking order is invalid.", 200, "SCHEMA_MISMATCH");
    }
    rankedWallets.add(item.wallet);
  }

  const rejectedWallets = new Set<string>();
  for (const item of payload.rejected_wallets) {
    if (
      !isRecord(item) ||
      typeof item.wallet !== "string" ||
      !item.wallet ||
      typeof item.code !== "string" ||
      !REJECTION_CODES.has(item.code as BatchWalletRejectionCode) ||
      typeof item.message !== "string" ||
      !isNonnegativeInteger(item.supplied_event_count) ||
      rankedWallets.has(item.wallet) ||
      rejectedWallets.has(item.wallet)
    ) {
      throw new ApiClientError("A rejected wallet result is invalid.", 200, "SCHEMA_MISMATCH");
    }
    rejectedWallets.add(item.wallet);
  }

  const selectedWallets = payload.ranked_wallets
    .filter((item) => isRecord(item) && item.selected_for_review === true)
    .map((item) => String(item.wallet));
  if (
    selectedWallets.length !== payload.review_budget ||
    selectedWallets.join("|") !== payload.review_candidates.join("|")
  ) {
    throw new ApiClientError("The review candidate metadata is inconsistent.", 200, "SCHEMA_MISMATCH");
  }
  return payload as unknown as ExperimentalBatchScoreResponse;
}

export class ApiClient {
  constructor(
    private readonly baseUrl = API_BASE_URL,
    private readonly idTokenProvider: () => Promise<string | null> = firebaseIdTokenProvider,
  ) {}

  private async request(path: string, init: RequestInit = {}): Promise<Response> {
    try {
      return await fetch(`${this.baseUrl}${path}`, {
        ...init,
        headers: {
          Accept: "application/json",
          ...(init.body ? { "Content-Type": "application/json" } : {}),
          ...init.headers,
        },
      });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        throw error;
      }
      throw new ApiClientError(
        "The backend could not be reached. Confirm that the local API is running.",
        0,
        "BACKEND_UNAVAILABLE",
      );
    }
  }

  private async authorizedRequest(path: string, init: RequestInit): Promise<Response> {
    let token: string | null;
    try {
      token = await this.idTokenProvider();
    } catch {
      throw new ApiClientError(
        "Authentication is not configured for this environment.",
        503,
        "AUTH_CONFIGURATION_UNAVAILABLE",
      );
    }
    if (token === null || !token.trim()) {
      throw new ApiClientError(
        "Sign in with an approved Google account before using this feature.",
        401,
        "AUTHENTICATION_REQUIRED",
      );
    }
    return this.request(path, {
      ...init,
      headers: { ...init.headers, Authorization: `Bearer ${token}` },
    });
  }

  async health(signal?: AbortSignal): Promise<HealthResponse> {
    const response = await this.request("/healthz", { signal });
    const payload = await readJson(response);
    if (!response.ok) throw toApiError(response.status, payload);
    if (
      !isRecord(payload) ||
      payload.status !== "ok" ||
      typeof payload.service !== "string" ||
      typeof payload.version !== "string"
    ) {
      throw new ApiClientError("The health response is invalid.", response.status, "SCHEMA_MISMATCH");
    }
    return payload as unknown as HealthResponse;
  }

  async readiness(signal?: AbortSignal): Promise<AvailabilityResponse> {
    const response = await this.request("/readyz", { signal });
    const payload = await readJson(response);
    if (response.status === 503 && isErrorResponse(payload) && payload.error.code === "MODEL_NOT_APPROVED") {
      return { available: false, code: "MODEL_NOT_APPROVED", message: payload.error.message };
    }
    if (!response.ok) throw toApiError(response.status, payload);
    throw new ApiClientError(
      "An unexpected model-ready response was received and will not be displayed.",
      response.status,
      "UNSUPPORTED_MODEL_RESPONSE",
    );
  }

  async preview(
    request: FeaturePreviewRequest,
    signal?: AbortSignal,
  ): Promise<FeaturePreviewResponse> {
    const response = await this.authorizedRequest("/v1/features/preview", {
      method: "POST",
      body: JSON.stringify(request),
      signal,
    });
    const payload = await readJson(response);
    if (!response.ok) throw toApiError(response.status, payload);
    return assertFeaturePreview(payload);
  }

  async score(
    request: FeaturePreviewRequest,
    signal?: AbortSignal,
  ): Promise<AvailabilityResponse | ExperimentalScoreResponse> {
    const response = await this.authorizedRequest("/v1/score", {
      method: "POST",
      body: JSON.stringify(request),
      signal,
    });
    const payload = await readJson(response);
    if (response.status === 503 && isErrorResponse(payload) && payload.error.code === "MODEL_NOT_APPROVED") {
      return { available: false, code: "MODEL_NOT_APPROVED", message: payload.error.message };
    }
    if (response.status === 503 && isErrorResponse(payload) && payload.error.code === "EXPERIMENTAL_MODEL_UNAVAILABLE") {
      return { available: false, code: "EXPERIMENTAL_MODEL_UNAVAILABLE", message: payload.error.message };
    }
    if (!response.ok) throw toApiError(response.status, payload);
    return assertExperimentalScore(payload);
  }

  async scoreBatch(
    request: BatchScoreRequest,
    signal?: AbortSignal,
  ): Promise<AvailabilityResponse | ExperimentalBatchScoreResponse> {
    const response = await this.authorizedRequest("/v1/score/batch", {
      method: "POST",
      body: JSON.stringify(request),
      signal,
    });
    const payload = await readJson(response);
    if (
      response.status === 503 &&
      isErrorResponse(payload) &&
      (payload.error.code === "MODEL_NOT_APPROVED" ||
        payload.error.code === "EXPERIMENTAL_MODEL_UNAVAILABLE")
    ) {
      return {
        available: false,
        code: payload.error.code,
        message: payload.error.message,
      } as AvailabilityResponse;
    }
    if (!response.ok) throw toApiError(response.status, payload);
    return assertExperimentalBatchScore(payload);
  }
}

export function featureNameList(): readonly FeatureName[] {
  return FEATURE_NAMES;
}

export const apiClient = new ApiClient();
