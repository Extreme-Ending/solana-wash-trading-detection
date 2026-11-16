# Phase 10 dataset provenance and licensing assessment

## Decision

**Provenance and redistribution status: UNRESOLVED.** The supplied file can be used for the current private local analysis subject to the student's institutional direction, but the repository does not establish a provider licence, extraction authority or permission to redistribute the raw or derived row-level data. It must remain untracked and must not be published as a project dataset.

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
| Embedded provenance | metadata search | no provider URL, query, extraction tool, licence, terms snapshot or collector identity |

The filename is not semantic evidence. The token-in/out, DEX, amount and instruction fields support a swap interpretation; the absence of NFT mint, collection, marketplace sale, buyer/seller and ownership-transfer fields prevents an NFT-sale interpretation.

## Public-chain corroboration performed

On 16 November 2026, a read-only call to Solana mainnet's public `getTransaction` method was made for the first CSV transaction signature. The returned confirmed transaction matched the CSV's signature, slot `313204200`, block time `1736559391` (2025-01-11 01:36:31 UTC), signer wallet, mint and token amount `74234497.5342`. Solana's official RPC documentation defines `getTransaction` as returning a confirmed transaction and its slot, block time, transaction and metadata ([Solana, `getTransaction`](https://solana.com/docs/rpc/http/gettransaction)).

This is **single-record field corroboration only**. It does not show:

- that the CSV was collected through Solana's public RPC;
- which indexer or provider was used;
- how DEX names, token-pair labels, USD amounts, fees or `source` were derived;
- why these particular 10,800 events and 2,312 wallets were selected;
- whether omitted events exist;
- who authored the derivative table; or
- which terms permit its research use or redistribution.

Exact public-web searches for the signature, sample wallet and distinctive schema combinations did not locate a published dataset record. A failed search is not proof that no source exists.

## Collection-method assessment

Solana documents public JSON-RPC methods capable of reading confirmed transactions and transaction metadata ([Solana RPC overview](https://solana.com/docs/rpc); [transaction structures](https://solana.com/docs/rpc/json-structures)). Therefore, independently collecting raw on-chain transaction evidence is technically possible in principle. Recreating this CSV is not currently possible because its address/sample selection, decoding, enrichment, price source, DEX classification and snapshot procedure are unknown.

The public RPC endpoint is shared, rate-limited infrastructure and is not an acquisition licence for this derivative file. Solana Developer Platform terms also cannot be retroactively assigned to an unknown data provider or collection route. Public visibility of a blockchain record does not by itself establish permission to redistribute a curated dataset or inferred wallet profiles.

## Licence and permitted-use findings

| Question | Finding |
|---|---|
| Is a licence bundled with `nft.csv`? | No |
| Is a provider/API identified? | No |
| Is academic analysis expressly permitted? | Not evidenced locally |
| Is raw redistribution permitted? | Not evidenced; treat as prohibited pending confirmation |
| Are derived wallet-level tables publishable? | Not evidenced; they retain address-level behavioural data |
| Can a reviewer lawfully reacquire the exact sample? | No documented route |
| Does an on-chain match cure the rights gap? | No |

## Reproducibility consequence

Local computational reproducibility is strong because checksums bind every stage. Independent acquisition reproducibility is blocked: a clone lacks the raw file and no lawful, deterministic acquisition recipe exists. The tracked Phase 9 aggregate figures/tables avoid publishing row-level wallets, but even aggregate publication should be reviewed under the actual source terms once known.

## Evidence required to close the blocker

Obtain and preserve:

1. provider/indexer/API name and stable URL;
2. collector identity and collection date;
3. chain/network and commitment level;
4. exact query, address-selection and sampling logic;
5. decoding/enrichment code and price/DEX mapping sources;
6. source and derivative-data licence/terms version;
7. explicit academic-use and submission/redistribution permission;
8. a data dictionary and completeness limitations; and
9. immutable checksums for the acquired source and any authorized shareable sample.

Until those records exist, the academically defensible statement is: **the analysis uses a privately supplied, provenance-unresolved Solana DEX swap-event sample whose selected on-chain fields can be independently corroborated, but whose complete acquisition and reuse rights are not established.**
