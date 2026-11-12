import type { EventDraft, EventInput, FeaturePreviewRequest } from "../api/types";

export const MAX_EVENTS = 100;
export const MAX_REQUEST_BYTES = 262_144;

const REQUIRED_EVENT_FIELDS = [
  "source_row_number",
  "block_time",
  "block_slot",
  "tx_hash",
  "dex",
  "token_pair",
  "token_in",
  "token_out",
  "amount_usd",
] as const;

const OPTIONAL_EVENT_FIELDS = [
  "fee_usd",
  "outer_instruction_index",
  "inner_instruction_index",
] as const;

const ALLOWED_EVENT_FIELDS = new Set<string>([
  ...REQUIRED_EVENT_FIELDS,
  ...OPTIONAL_EVENT_FIELDS,
]);

export class InputValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InputValidationError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validateText(value: unknown, field: string, maximum: number): string {
  if (typeof value !== "string" || !value || value !== value.trim()) {
    throw new InputValidationError(`${field} must be a non-empty string without surrounding spaces.`);
  }
  if (value.length > maximum || /[\u0000-\u001f\u007f]/.test(value)) {
    throw new InputValidationError(`${field} contains unsupported characters or is too long.`);
  }
  return value;
}

export function validateUtcTimestamp(value: string, field = "Timestamp"): string {
  if (!/(Z|\+00:00)$/.test(value) || Number.isNaN(Date.parse(value))) {
    throw new InputValidationError(`${field} must be a valid ISO-8601 UTC value ending in Z or +00:00.`);
  }
  return value;
}

function validateInteger(value: unknown, field: string, minimum: number): number {
  if (typeof value !== "number" || !Number.isInteger(value) || value < minimum) {
    throw new InputValidationError(`${field} must be an integer greater than or equal to ${minimum}.`);
  }
  return value;
}

function validateFinite(value: unknown, field: string, minimum: number, exclusive = false): number {
  if (
    typeof value !== "number" ||
    !Number.isFinite(value) ||
    (exclusive ? value <= minimum : value < minimum)
  ) {
    const relation = exclusive ? "greater than" : "greater than or equal to";
    throw new InputValidationError(`${field} must be a finite number ${relation} ${minimum}.`);
  }
  return value;
}

function nullableNumber(
  value: unknown,
  field: string,
  validator: (candidate: unknown, name: string) => number,
): number | null | undefined {
  if (value === undefined) return undefined;
  if (value === null) return null;
  return validator(value, field);
}

function validateEvent(value: unknown, index: number): EventDraft {
  if (!isRecord(value)) {
    throw new InputValidationError(`Event ${index + 1} must be a JSON object.`);
  }
  for (const field of REQUIRED_EVENT_FIELDS) {
    if (!(field in value)) throw new InputValidationError(`Event ${index + 1} is missing ${field}.`);
  }
  for (const field of Object.keys(value)) {
    if (!ALLOWED_EVENT_FIELDS.has(field)) {
      throw new InputValidationError(`Event ${index + 1} contains unsupported field ${field}.`);
    }
  }

  return {
    source_row_number: validateInteger(value.source_row_number, `Event ${index + 1} source_row_number`, 1),
    block_time: validateUtcTimestamp(String(value.block_time), `Event ${index + 1} block_time`),
    block_slot: validateInteger(value.block_slot, `Event ${index + 1} block_slot`, 0),
    tx_hash: validateText(value.tx_hash, `Event ${index + 1} tx_hash`, 256),
    dex: validateText(value.dex, `Event ${index + 1} dex`, 128),
    token_pair: value.token_pair === null ? null : validateText(value.token_pair, `Event ${index + 1} token_pair`, 256),
    token_in: validateText(value.token_in, `Event ${index + 1} token_in`, 128),
    token_out: validateText(value.token_out, `Event ${index + 1} token_out`, 128),
    amount_usd: validateFinite(value.amount_usd, `Event ${index + 1} amount_usd`, 0, true),
    fee_usd: nullableNumber(value.fee_usd, `Event ${index + 1} fee_usd`, (candidate, field) => validateFinite(candidate, field, 0)),
    outer_instruction_index: nullableNumber(value.outer_instruction_index, `Event ${index + 1} outer_instruction_index`, (candidate, field) => validateInteger(candidate, field, 0)),
    inner_instruction_index: nullableNumber(value.inner_instruction_index, `Event ${index + 1} inner_instruction_index`, (candidate, field) => validateInteger(candidate, field, 0)),
  };
}

export function parseEventsJson(text: string): EventDraft[] {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new InputValidationError("Event records must be valid JSON.");
  }
  if (!Array.isArray(parsed)) {
    throw new InputValidationError("Event records must be a JSON array.");
  }
  if (parsed.length === 0 || parsed.length > MAX_EVENTS) {
    throw new InputValidationError(`Provide between 1 and ${MAX_EVENTS} events.`);
  }
  const events = parsed.map(validateEvent);
  const rowNumbers = events.map((event) => event.source_row_number);
  if (new Set(rowNumbers).size !== rowNumbers.length) {
    throw new InputValidationError("source_row_number values must be unique.");
  }
  return events;
}

export function buildPreviewRequest(
  walletValue: string,
  asOfValue: string,
  eventsJson: string,
): FeaturePreviewRequest {
  const wallet = validateText(walletValue, "Wallet identifier", 128);
  const as_of = validateUtcTimestamp(asOfValue, "Scoring timestamp");
  const drafts = parseEventsJson(eventsJson);
  const events: EventInput[] = drafts.map((event) => ({ ...event, wallet }));
  const request = { as_of, events };
  if (new Blob([JSON.stringify(request)]).size > MAX_REQUEST_BYTES) {
    throw new InputValidationError(`The request exceeds ${MAX_REQUEST_BYTES} bytes.`);
  }
  return request;
}

export interface ImportedPayload {
  wallet: string | null;
  asOf: string | null;
  eventsJson: string;
}

export function parseImportedPayload(text: string): ImportedPayload {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch {
    throw new InputValidationError("The selected file is not valid JSON.");
  }

  if (Array.isArray(parsed)) {
    const events = parseEventsJson(JSON.stringify(parsed));
    return { wallet: null, asOf: null, eventsJson: JSON.stringify(events, null, 2) };
  }
  if (!isRecord(parsed) || !Array.isArray(parsed.events) || typeof parsed.as_of !== "string") {
    throw new InputValidationError("Import a JSON event array or a complete {as_of, events} payload.");
  }
  validateUtcTimestamp(parsed.as_of, "Imported as_of");
  const wallets = new Set<string>();
  const drafts = parsed.events.map((event, index) => {
    if (!isRecord(event)) throw new InputValidationError(`Event ${index + 1} must be a JSON object.`);
    wallets.add(validateText(event.wallet, `Event ${index + 1} wallet`, 128));
    const { wallet: _wallet, ...draft } = event;
    return validateEvent(draft, index);
  });
  if (wallets.size !== 1) {
    throw new InputValidationError("Imported events must describe exactly one wallet.");
  }
  return {
    wallet: [...wallets][0],
    asOf: parsed.as_of,
    eventsJson: JSON.stringify(drafts, null, 2),
  };
}
