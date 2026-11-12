import type { EventDraft } from "../api/types";

export const SYNTHETIC_WALLET = "synthetic-wallet-demo-001";
export const SYNTHETIC_AS_OF = "2025-02-01T00:00:00Z";

export const SYNTHETIC_EVENTS: readonly EventDraft[] = [
  {
    source_row_number: 1,
    block_time: "2025-01-10T09:15:00Z",
    block_slot: 1001,
    tx_hash: "synthetic-transaction-001",
    dex: "synthetic-dex-a",
    token_pair: "TOKEN-A/TOKEN-B",
    token_in: "synthetic-token-a",
    token_out: "synthetic-token-b",
    amount_usd: 125.5,
    fee_usd: 0.25,
    outer_instruction_index: 1,
    inner_instruction_index: 0
  },
  {
    source_row_number: 2,
    block_time: "2025-01-20T14:30:00Z",
    block_slot: 1002,
    tx_hash: "synthetic-transaction-002",
    dex: "synthetic-dex-b",
    token_pair: "TOKEN-B/TOKEN-C",
    token_in: "synthetic-token-b",
    token_out: "synthetic-token-c",
    amount_usd: 310.75,
    fee_usd: null,
    outer_instruction_index: 2,
    inner_instruction_index: 0
  },
  {
    source_row_number: 3,
    block_time: "2025-01-31T18:00:00Z",
    block_slot: 1003,
    tx_hash: "synthetic-transaction-003",
    dex: "synthetic-dex-a",
    token_pair: "TOKEN-C/TOKEN-A",
    token_in: "synthetic-token-c",
    token_out: "synthetic-token-a",
    amount_usd: 80,
    fee_usd: 0.12,
    outer_instruction_index: 1,
    inner_instruction_index: 1
  }
];

export const SYNTHETIC_EVENTS_JSON = JSON.stringify(SYNTHETIC_EVENTS, null, 2);
