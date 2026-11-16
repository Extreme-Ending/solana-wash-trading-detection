import type { BatchWalletHistory, EventInput } from "../api/types";

export const SYNTHETIC_BATCH_AS_OF = "2025-11-01T00:00:00Z";

function event(
  wallet: string,
  row: number,
  blockTime: string,
  amountUsd: number,
  dex = "synthetic-dex-a",
): EventInput {
  return {
    source_row_number: row,
    wallet,
    block_time: blockTime,
    block_slot: 2000 + row,
    tx_hash: `${wallet}-synthetic-transaction-${row}`,
    dex,
    token_pair: "TOKEN-A/TOKEN-B",
    token_in: "synthetic-token-a",
    token_out: "synthetic-token-b",
    amount_usd: amountUsd,
    fee_usd: 0.1,
    outer_instruction_index: 1,
    inner_instruction_index: row,
  };
}

export const SYNTHETIC_BATCH_HISTORIES: readonly BatchWalletHistory[] = [
  {
    wallet: "synthetic-wallet-bursty",
    events: [
      event("synthetic-wallet-bursty", 1, "2025-10-31T23:57:00Z", 4500),
      event("synthetic-wallet-bursty", 2, "2025-10-31T23:58:00Z", 5200),
      event("synthetic-wallet-bursty", 3, "2025-10-31T23:59:00Z", 6100),
    ],
  },
  {
    wallet: "synthetic-wallet-steady",
    events: [
      event("synthetic-wallet-steady", 1, "2025-09-20T10:00:00Z", 110),
      event("synthetic-wallet-steady", 2, "2025-10-05T10:00:00Z", 105),
      event("synthetic-wallet-steady", 3, "2025-10-20T10:00:00Z", 115),
    ],
  },
  {
    wallet: "synthetic-wallet-sparse",
    events: [event("synthetic-wallet-sparse", 1, "2025-10-15T12:00:00Z", 80, "synthetic-dex-b")],
  },
];

export const SYNTHETIC_BATCH_JSON = JSON.stringify(SYNTHETIC_BATCH_HISTORIES, null, 2);
