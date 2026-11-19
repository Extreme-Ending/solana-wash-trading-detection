# Phase 10 dataset provenance and licensing assessment

## Decision

**Source identity: RESOLVED. Extraction metadata and redistribution status: INCOMPLETE.** The dataset creator confirms that the supplied file was extracted from Dune Analytics query 6561080 in multiple batches of approximately 1,000 rows. The repository does not contain the exact historical SQL revision, execution identifiers, parameters, extraction timestamps, or permission to redistribute the raw or derived row-level data. The file must remain untracked and must not be published as a project dataset.

## Locally verified facts

| Item | Evidence | Finding |
|---|---|---|
| File | local byte inspection | `nft.csv`, 4,195,387 bytes, SHA-256 `8f387709...e81271` |
| Shape | deterministic audit | 10,800 rows, 18 columns, 2,312 wallet identifiers |
| Time | parsed `block_time` | 2025-01-01 00:42:47 through 2025-11-30 23:16:57 UTC |
| Event semantics | schema and values | DEX/token swap observations, not NFT marketplace sales |
| Source categories | file audit | `dex_trade` and `jupiter_swap`; these are row labels, not provider names |
| Outcomes | schema/lineage audit | no verified fraud/wash-trading target or adjudication timestamp |
| Network evidence | schema audit | no direct counterparty-wallet edge |
| Source identity | dataset creator confirmation | Dune Analytics query `6561080` |
| Embedded extraction record | metadata search | no historical SQL revision, execution IDs, parameters, extraction timestamps, batch manifest, licence or terms snapshot |

The filename is not semantic evidence. The token-in/out, DEX, amount and instruction fields support a swap interpretation; the absence of NFT mint, collection, marketplace sale, buyer/seller and ownership-transfer fields prevents an NFT-sale interpretation.

## Public-chain corroboration performed

On 16 November 2026, a read-only call to Solana mainnet's public `getTransaction` method was made for the first CSV transaction signature. The returned confirmed transaction matched the CSV's signature, slot `313204200`, block time `1736559391` (2025-01-11 01:36:31 UTC), signer wallet, mint and token amount `74234497.5342`. Solana's official RPC documentation defines `getTransaction` as returning a confirmed transaction and its slot, block time, transaction and metadata ([Solana, `getTransaction`](https://solana.com/docs/rpc/http/gettransaction)).

This is **single-record field corroboration only**. It does not show:

- the exact extraction-time state of Dune query 6561080;
- how DEX names, token-pair labels, USD amounts, fees or `source` were derived;
- why these particular 10,800 events and 2,312 wallets were selected;
- whether omitted events exist;
- who authored the derivative table; or
- which terms permit its research use or redistribution.

Exact public-web searches for the signature, sample wallet and distinctive schema combinations did not locate a separately published dataset record. This does not contradict the confirmed Dune query source.

## Collection-method assessment

Solana documents public JSON-RPC methods capable of reading confirmed transactions and transaction metadata ([Solana RPC overview](https://solana.com/docs/rpc); [transaction structures](https://solana.com/docs/rpc/json-structures)). Therefore, independently collecting raw on-chain transaction evidence is technically possible in principle. Recreating this CSV exactly is not currently possible because the historical query revision, executions, parameters, address/sample selection, decoding, enrichment, price source, DEX classification and snapshot procedure are not archived.

The public RPC endpoint is shared, rate-limited infrastructure and is not an acquisition licence for this derivative file. Public visibility of a blockchain record and the public Dune query URL do not by themselves establish permission to redistribute a curated dataset or inferred wallet profiles.

## Licence and permitted-use findings

| Question | Finding |
|---|---|
| Is a licence bundled with `nft.csv`? | No |
| Is a provider/query identified? | Yes, Dune Analytics query `6561080` |
| Is academic analysis expressly permitted? | Not evidenced locally |
| Is raw redistribution permitted? | Not evidenced; treat as prohibited pending confirmation |
| Are derived wallet-level tables publishable? | Not evidenced; they retain address-level behavioural data |
| Can a reviewer lawfully reacquire the exact sample? | No documented route |
| Does an on-chain match cure the rights gap? | No |

## Reproducibility consequence

Local computational reproducibility is strong because checksums bind every stage. Independent acquisition reproducibility is blocked: a clone lacks the raw file and no lawful, deterministic acquisition recipe exists. The tracked Phase 9 aggregate figures/tables avoid publishing row-level wallets, but even aggregate publication should be reviewed under the actual source terms once known.

## Evidence required to close the blocker

Obtain and preserve:

1. exact historical SQL revision, parameters, execution identifiers and extraction timestamps;
2. original batch files or a batch manifest;
3. address-selection and sampling logic;
4. decoding/enrichment code and price/DEX mapping sources;
5. source and derivative-data licence/terms version;
6. explicit academic-use and submission/redistribution permission;
7. a data dictionary and completeness limitations; and
8. immutable checksums for the acquired source and any authorized shareable sample.

Until those records exist, the academically defensible statement is: **the analysis uses a private Solana DEX swap-event sample extracted from Dune Analytics query 6561080. Its local identity is checksum-verified, but its exact historical extraction configuration and reuse rights are not independently archived.**
