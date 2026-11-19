# Dataset provenance resolution

## Resolution status

**Source identified; extraction metadata and sharing permission incomplete.** The dataset creator confirms that the supplied file was extracted from Dune Analytics query 6561080 in multiple batches of approximately 1,000 rows. The repository can describe the file and reproduce its processing, but it does not contain the exact historical SQL revision, execution identifiers, parameters, extraction timestamps, or permission to redistribute the result.

## Verified repository evidence

The locally supplied, Git-ignored `nft.csv` has SHA-256 `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271` and size 4,195,387 bytes. Direct inspection found:

- 10,800 event rows and 18 columns for 2,312 unique `wallet` values;
- UTC event times from `2025-01-01T00:42:47+00:00` through `2025-11-30T23:16:57+00:00`;
- swap-oriented fields including `dex`, `token_pair`, `token_in`, `token_out`, `amount_in`, `amount_out`, `amount_usd`, `fee_usd` and instruction indexes;
- 9,864 records with source value `dex_trade` and 936 with `jupiter_swap`;
- no buyer, seller, NFT mint, collection, marketplace or sale-price fields;
- no label, target, fraud, wash-trading, flag or class field; and
- no direct wallet-to-counterparty relationship from which collusion edges could be asserted.

These observations support the description **Solana wallet-attributed DEX swap events**. They do not support the description NFT marketplace transactions. The earlier Phase 1 audit records two quarantined records during deterministic cleaning, leaving 10,798 events; it also documents event-grain and repeated-transaction-hash checks in [`data_audit_findings.md`](data_audit_findings.md).

`nft.csv` is ignored by Git and has no repository history. The only file under `data/raw/` is a small ignored local JSON sample. Neither location contains the original extraction batches, historical SQL revision, execution manifest, licence, data dictionary issued by the source, or cryptographically signed source record.

## What is not verified

| Question | Repository evidence | Status |
|---|---|---|
| Data provider or originating platform | Dune Analytics | Confirmed by the dataset creator |
| Extraction query | Dune query `6561080` | Confirmed by the dataset creator |
| Exact extraction timestamps and batch procedure | Not archived | Unresolved |
| Historical query revision, execution IDs and parameters | Not archived | Unresolved |
| Licence and permission for academic use or redistribution | None | **Blocking** |
| Whether every `dex` value is a protocol, venue or parser label | No extraction-time field dictionary archived | Unresolved |
| Completeness relative to Solana activity | No sampling frame or coverage statement | Unresolved |
| Wallet ownership or real-world identity | None | Not available and not required for the current analysis |
| The proposed 249 independently verified positives | No label register or evidence records | **Not available** |

The project notebooks show that the number 249 was previously produced by behavioural rules involving burst ratio, alternation ratio and mean time gap. This establishes heuristic origin, not independent verification. Because related behaviours are also candidate predictors, treating those flags as ground truth would be circular.

## Consequence for title and objectives

The original title, *Detecting Coordinated Wash Trading on Solana: A Reproducible Wallet-Risk Scoring Service*, is aspirational beyond the evidence. The present implementation can investigate **unusual wallet behaviour in a supplied Solana DEX swap-event sample**. It cannot verify NFT wash trading, coordination, intent, fraud, or detector effectiveness against true outcomes.

The defensible working framing is *Unsupervised wallet anomaly analysis in supplied Solana DEX swap events*. This wording is an evidence recommendation, not a silent amendment to an approved title or methodology. Documentary authorization for any formal title/methodology change is not present locally.

## Evidence required to close the provenance gap

The student should obtain and retain, subject to repository privacy rules:

1. the exact acquisition/export procedure, historical query revision, parameters, execution identifiers, extraction timestamps and sampling frame;
2. the original batch files or an extraction manifest;
3. the provider's data dictionary or a documented field mapping;
4. licence terms or written permission covering academic analysis, derived results and any intended redistribution;
5. an immutable source manifest containing filename, byte size, SHA-256 and acquisition metadata; and
6. if supervised claims are ever proposed, a separate timestamped label register with evidence provenance, decision rules, reviewer identity and wallet/domain matching.

Until items 1–4 are supplied, the raw data and trained artifact should not be published as research assets. The current checksum supports local integrity and query 6561080 establishes source identity, but neither establishes data-sharing permission.

## Claim boundary

This resolution does not manufacture a source, licence, label or NFT interpretation. All subsequent documents use “supplied DEX swap-event sample,” “experimental anomaly score” and “review candidate.” They do not call a high-ranked wallet fraudulent or a confirmed wash trader.
