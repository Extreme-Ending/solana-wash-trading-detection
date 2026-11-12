import { API_BASE_URL } from "./config";
import {
  FEATURE_NAMES,
  type AvailabilityResponse,
  type ErrorResponse,
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

export class ApiClient {
  constructor(private readonly baseUrl = API_BASE_URL) {}

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
    const response = await this.request("/v1/features/preview", {
      method: "POST",
      body: JSON.stringify(request),
      signal,
    });
    const payload = await readJson(response);
    if (!response.ok) throw toApiError(response.status, payload);
    return assertFeaturePreview(payload);
  }

  async scoringAvailability(
    request: FeaturePreviewRequest,
    signal?: AbortSignal,
  ): Promise<AvailabilityResponse> {
    const response = await this.request("/v1/score", {
      method: "POST",
      body: JSON.stringify(request),
      signal,
    });
    const payload = await readJson(response);
    if (response.status === 503 && isErrorResponse(payload) && payload.error.code === "MODEL_NOT_APPROVED") {
      return { available: false, code: "MODEL_NOT_APPROVED", message: payload.error.message };
    }
    if (!response.ok) throw toApiError(response.status, payload);
    throw new ApiClientError(
      "Scoring output is not supported by this frontend phase.",
      response.status,
      "UNSUPPORTED_MODEL_RESPONSE",
    );
  }
}

export function featureNameList(): readonly FeatureName[] {
  return FEATURE_NAMES;
}

export const apiClient = new ApiClient();
