import type { BatchScoreRequest, BatchWalletHistory, EventInput } from "../api/types";
import {
  buildPreviewRequest,
  InputValidationError,
  MAX_REQUEST_BYTES,
  validateUtcTimestamp,
} from "./validation";

export const MAX_BATCH_WALLETS = 20;
export const MAX_BATCH_EVENTS = 100;
export const MAX_EVENTS_PER_WALLET = 50;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function byteLength(value: unknown): number {
  return new TextEncoder().encode(JSON.stringify(value)).length;
}

function walletValue(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim() || value !== value.trim()) {
    throw new InputValidationError(`${label} must be a non-empty identifier without surrounding spaces.`);
  }
  if (value.length > 128 || /[\u0000-\u001f\u007f]/.test(value)) {
    throw new InputValidationError(`${label} contains unsupported characters or is too long.`);
  }
  return value;
}

function normalizedEvents(wallet: string, values: unknown[], groupIndex: number): EventInput[] {
  if (values.length === 0) {
    throw new InputValidationError(`Wallet group ${groupIndex + 1} must contain at least one event.`);
  }
  if (values.length > MAX_EVENTS_PER_WALLET) {
    throw new InputValidationError(
      `Wallet ${wallet} exceeds the ${MAX_EVENTS_PER_WALLET}-event limit.`,
    );
  }
  const drafts = values.map((value, eventIndex) => {
    if (!isRecord(value)) {
      throw new InputValidationError(
        `Wallet group ${groupIndex + 1}, event ${eventIndex + 1} must be a JSON object.`,
      );
    }
    if ("wallet" in value && value.wallet !== wallet) {
      throw new InputValidationError(
        `Wallet group ${groupIndex + 1}, event ${eventIndex + 1} does not match ${wallet}.`,
      );
    }
    const { wallet: _wallet, ...draft } = value;
    return draft;
  });
  return buildPreviewRequest(wallet, "2099-01-01T00:00:00Z", JSON.stringify(drafts)).events;
}

function groupedInput(value: unknown[]): BatchWalletHistory[] {
  const looksGrouped = value.every(
    (item) => isRecord(item) && "wallet" in item && "events" in item,
  );
  if (looksGrouped) {
    return value.map((item, groupIndex) => {
      const group = item as Record<string, unknown>;
      const wallet = walletValue(group.wallet, `Wallet group ${groupIndex + 1}`);
      if (!Array.isArray(group.events)) {
        throw new InputValidationError(`Wallet ${wallet} must contain an events array.`);
      }
      return { wallet, events: normalizedEvents(wallet, group.events, groupIndex) };
    });
  }

  const groups = new Map<string, unknown[]>();
  value.forEach((item, index) => {
    if (!isRecord(item)) {
      throw new InputValidationError(`Event ${index + 1} must be a JSON object.`);
    }
    const wallet = walletValue(item.wallet, `Event ${index + 1} wallet`);
    groups.set(wallet, [...(groups.get(wallet) ?? []), item]);
  });
  return [...groups.entries()].map(([wallet, events], index) => ({
    wallet,
    events: normalizedEvents(wallet, events, index),
  }));
}

export interface ParsedAnalysisInput {
  request: BatchScoreRequest;
  walletsDetected: number;
  eventsDetected: number;
}

export function parseAnalysisInput(
  text: string,
  asOfValue: string,
  reviewBudgetValue: string,
): ParsedAnalysisInput {
  if (!text.trim()) throw new InputValidationError("Paste or import wallet-history JSON.");
  if (new TextEncoder().encode(text).length > MAX_REQUEST_BYTES) {
    throw new InputValidationError(`Input exceeds ${MAX_REQUEST_BYTES.toLocaleString()} bytes.`);
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new InputValidationError("Wallet history must be valid JSON.");
  }

  let embeddedAsOf: unknown;
  let embeddedBudget: unknown;
  let source: unknown = parsed;
  if (isRecord(parsed)) {
    embeddedAsOf = parsed.as_of;
    embeddedBudget = parsed.review_budget;
    source = parsed.wallet_histories ?? parsed.events;
  }
  if (!Array.isArray(source) || source.length === 0) {
    throw new InputValidationError(
      "Provide a non-empty event array or wallet-history array.",
    );
  }

  const asOf = validateUtcTimestamp(
    asOfValue.trim() || (typeof embeddedAsOf === "string" ? embeddedAsOf : ""),
    "Scoring timestamp",
  );
  const requestedBudget = Number(
    reviewBudgetValue.trim() ||
      (typeof embeddedBudget === "number" ? String(embeddedBudget) : ""),
  );
  if (!Number.isInteger(requestedBudget) || requestedBudget < 1 || requestedBudget > 20) {
    throw new InputValidationError("Review budget must be an integer from 1 to 20.");
  }

  const histories = groupedInput(source);
  const walletSet = new Set(histories.map((history) => history.wallet));
  if (walletSet.size !== histories.length) {
    throw new InputValidationError("Each wallet may appear in only one history group.");
  }
  if (histories.length > MAX_BATCH_WALLETS) {
    throw new InputValidationError(`At most ${MAX_BATCH_WALLETS} wallets may be analyzed.`);
  }
  const eventsDetected = histories.reduce((total, history) => total + history.events.length, 0);
  if (eventsDetected > MAX_BATCH_EVENTS) {
    throw new InputValidationError(`Input exceeds the ${MAX_BATCH_EVENTS}-event batch limit.`);
  }

  const request: BatchScoreRequest = {
    as_of: asOf,
    wallet_histories: histories,
    review_budget: Math.min(requestedBudget, histories.length),
  };
  if (byteLength(request) > MAX_REQUEST_BYTES) {
    throw new InputValidationError(`Request exceeds ${MAX_REQUEST_BYTES.toLocaleString()} bytes.`);
  }
  return { request, walletsDetected: histories.length, eventsDetected };
}

export function importAnalysisFile(text: string): {
  json: string;
  asOf: string | null;
  reviewBudget: string | null;
} {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new InputValidationError("The selected file is not valid JSON.");
  }
  if (isRecord(parsed)) {
    const source = parsed.wallet_histories ?? parsed.events;
    if (!Array.isArray(source)) {
      throw new InputValidationError(
        "Import an event array, wallet-history array, or complete analysis payload.",
      );
    }
    return {
      json: JSON.stringify(source, null, 2),
      asOf: typeof parsed.as_of === "string" ? parsed.as_of : null,
      reviewBudget:
        typeof parsed.review_budget === "number" ? String(parsed.review_budget) : null,
    };
  }
  if (!Array.isArray(parsed)) {
    throw new InputValidationError("The selected JSON must contain an array.");
  }
  return { json: JSON.stringify(parsed, null, 2), asOf: null, reviewBudget: null };
}
