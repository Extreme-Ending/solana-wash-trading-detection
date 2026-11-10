# Label evidence and supervised-modelling readiness

## Phase 4A decision

**Overall decision: REVISION REQUIRED.** The tracked evidence cannot currently support the approved NFT wash-trading classification claim. The available root file is DEX swap-event data, not an NFT marketplace sales table, and no independently verified binary labels are available. Moving the research domain from NFT marketplace trading to generic DEX swaps, or changing the task to anomaly/weak-supervision research, would be a methodological revision and requires student and supervisor approval.

**Supervised gate: BLOCKED.** No classifier may be trained until a versioned label table passes the contract below and each proposed temporal split has enough independently verified positives and negatives for the planned evaluation. This decision does not assert that any wallet is fraudulent.

## Materials reviewed

The Phase 4A review covered all tracked steering files, Phase 0–3 source, tests, notebooks, generated local Phase 1–3 reports, feature definitions, and research documentation. It also inspected, read-only and without executing old modelling code:

- the lecturer's AML Lab 2 and relevant end-to-end, evaluation, pipeline, and deployment examples;
- the local DSA 8401 capstone rubric PDF;
- `Nft_Wash_Trading_Detection_On_Solana_Final.pdf` and the related local dissertation notebooks and roadmaps;
- the local files named `224174-Research-Proposal*.pdf` and `224174_Patrick_Kosewe_Proposal.pdf`.

The repository still has no `references/` directory containing the approved NFT wash-trading proposal. The `224174-*` proposal documents found outside this repository concern a different, later cross-chain scam-token study and do not establish approval for this capstone. The NFT PDF is a completed-paper-style document, not identifiable as the approved proposal. Therefore proposal approval status and exact approved target wording remain unresolved. No external data was downloaded.

## Provenance finding for the claimed 249 wallets

### Confirmed facts

1. The approved root `nft.csv` has SHA-256 `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`. It is byte-for-byte identical to the local dissertation copy used by `SolanaNftWashTrade.ipynb`.
2. The file contains 10,800 rows and 2,312 wallet identifiers. None of its 18 columns is a target, evidence status, adjudication result, case reference, or label timestamp.
3. A saved output in `SolanaNftWashTrade.ipynb` creates the reported 249/2,063 split with this weak-supervision rule:

   ```text
   burst_ratio > 0.4
   AND alternation_ratio > 0.4
   AND mean_time_gap < 600 seconds
   ```

4. In a different cell, the same notebook creates `heuristic_wash` from `total_events >= 6`, `alternation_ratio >= 0.5`, `mean_time_gap <= 3600`, and `abs(net_flow) <= mean_abs_flow`. Its saved output is 18 candidate positives and 2,294 negatives—not 249.
5. The local `README2.md` attributes 249 positives to the second, four-condition rule. That statement conflicts with the notebook's saved outputs. The same roadmap says label-generation inconsistency still needs resolution.
6. The local NFT paper describes the 249 wallets as candidates produced from heuristic trading behaviour. It does not supply an independent adjudication protocol, evidence table, evidence timestamps, label version, or a persisted wallet-label file.
7. All three variables in the 249 rule are calculated from the same event history later supplied to models as predictors. This is direct target leakage/circular validation: a model can learn the label rule without learning independently evidenced wash trading.
8. The same problem applies to the alternative 18-wallet rule because its label conditions are also engineered behavioural predictors.
9. The local Solana CSV inventory contains no explicit label field. The current repository contains no materialized list of the 249 wallets, no case evidence, and no independently verified negative class.

### What cannot be concluded

- The 249 wallets are not verified wash traders. They are deterministic candidates under one notebook rule.
- The remaining 2,063 wallets are not verified legitimate traders. Failure to meet a suspicion heuristic is not negative ground truth.
- The exact 249 wallet identities cannot be validated against a supplied evidence register because no such register exists.
- There is no evidence that an independent investigator, marketplace, regulator, or data provider reviewed either class.
- There are no evidence or knowledge timestamps from which to determine whether a label was available at a proposed scoring time.
- There is no verified source snapshot, extraction query, licence, provider/API record, or label-version history.

## Domain and identity mismatch

The approved project wording refers to NFT wash trading. The actual root data records token-in/token-out DEX swaps and DEX program names. It does not contain NFT mint/collection identifiers, marketplace sale events, buyer and seller roles, ownership transfers, sale prices, or direct wallet counterparties. Shared token pairs, DEX programs, or transaction hashes do not prove that two wallets traded with one another.

The 249 candidates were calculated from the same byte-identical root file, so they relate to wallets in this file's DEX/swap domain. That establishes input-file lineage only; it does not convert those events into NFT sales or the heuristic results into verified labels. A verified NFT-marketplace label set would also fail the current `dex_swap` domain match unless the underlying events and identities were demonstrably linked.

## Target definition

The existing Phase 3 unit remains `(wallet, scoring_time)`, where features use only events with `block_time < scoring_time`.

### Recommended prospective target, subject to approval

For a genuine risk-scoring/early-warning objective, the proposed binary target is:

> Whether an independently verified wash-trading outcome involving the same wallet in the same transaction domain occurs during a prespecified outcome window beginning at or after `scoring_time`.

`label = 1` requires affirmative independent evidence meeting a fixed wash-trading definition. `label = 0` requires a mature, adequately covered outcome window and defensible negative adjudication; it must not mean merely “not flagged.” The outcome horizon must be selected from the research question and operational review cadence before results are inspected.

Features end strictly before `scoring_time`. Outcome evidence begins at or after it. `knowledge_time` records when the completed label became available and must be on or after the mature outcome-window end. This is a future-activity target, not a claim that unusual past behaviour is fraud.

### Retrospective alternative

If the approved objective is instead to classify previously demonstrated wash trading, the outcome evidence and its `knowledge_time` must both be on or before `scoring_time`. The model would then identify already-evidenced historical status, not predict future activity. Mixing retrospective and prospective labels in one model would change the estimand and is prohibited.

Because the approved proposal is unavailable and the present data domain differs from the NFT title, Phase 4A does not select either alternative as an approved methodological change.

## Minimum label-validation contract

The reusable validator in `src/solana_risk/labels/validate.py` accepts only the following exact schema:

| Field | Required meaning |
|---|---|
| `wallet` | Case-sensitive 32–44 character Base58 identity matching an approved event wallet. |
| `scoring_time` | Timezone-aware feature cutoff for this wallet observation. |
| `label` | Exact integer `0` or `1`; no strings, booleans, probabilities, or heuristic scores. |
| `target_type` | One consistent value: `future_outcome` or `historical_status`. |
| `label_definition` | One nonempty, version-consistent operational definition. |
| `domain` | Exact event domain; Phase 4A expects `dex_swap` for the current file. |
| `outcome_window_start`, `outcome_window_end` | Timezone-aware interval in which the target is adjudicated. |
| `evidence_time` | Time of the supporting event/action or completed negative review, inside the outcome window. |
| `knowledge_time` | Time when the mature label became available. |
| `evidence_source` | Named independent source or reviewing authority. |
| `evidence_reference` | Stable case/reference identifier permitting audit without embedding case details in features. |
| `verification_status` | Must be `independently_verified`; heuristic-only flags are rejected. |
| `review_method` | Documented adjudication method. |
| `label_version` | One immutable label-set version. |

The validator rejects missing or extra columns, whitespace repair, malformed or unknown wallets, duplicate `(wallet, scoring_time)` observations, unsupported domains or target types, inconsistent definitions/versions, unverified heuristics, nonbinary values, single-class tables, naive/invalid timestamps, evidence outside its outcome window, immature knowledge times, and target-specific temporal leakage. It normalizes valid timezone-aware timestamps to UTC but does not alter the caller's table or write a labelled research dataset.

Passing structural validation is necessary but not sufficient. Human evidence audit must also confirm source independence, lawful use, identity resolution, domain equivalence, complete negative-class ascertainment, conflict/adjudication handling, and class counts within every proposed temporal split.

## Readiness recommendation

Supervised modelling must not proceed with the 249 weak labels, the 18 alternative heuristic labels, or any scores derived from them. The next acceptable input is either:

1. a versioned, independently verified label/evidence register for the same wallets and DEX/swap domain that passes the contract and supports the approved temporal target; or
2. the correct approved NFT marketplace event data plus matching independently verified NFT wash-trading evidence.

If neither can be obtained, any change to anomaly detection, positive-unlabelled learning, weak supervision, or a DEX-manipulation research question requires supervisor approval before implementation.
