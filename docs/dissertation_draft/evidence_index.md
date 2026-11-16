# Dissertation evidence index

| Draft claim | Primary repository evidence | Figure/table | Qualification |
|---|---|---|---|
| 10,800 rows, 2,312 wallets, DEX schema | `reports/data_audit/audit.json`; `docs/data_audit_findings.md` | Phase 9 table 01 | Source/licence unknown |
| 10,798 retained, two quarantined | cleaning report; `docs/preprocessing_findings.md` | Phase 9 table 01 | Zero silent removals |
| 29 features and 5,996 snapshots | feature report; `docs/feature_registry.md` | Tables 01–02 | Strict `block_time < as_of` |
| Three chronological cohorts | feature report; model manifest | Figure 01 | Repeated-wallet dependence |
| IF sensitivity `0.9923–0.9980` | anomaly evaluation JSON | Figure 04; table 03 | Validation stability, not accuracy |
| Holdout correlations `0.0488`, `0.8662`, `-0.0187` | anomaly evaluation JSON | Figure 03; table 03 | Agreement, not truth |
| No all-three top-10; seven all-three top-100 | anomaly evaluation JSON | Table 03 | Budget- and detector-dependent |
| Later entrant/coverage effects | feature/evaluation reports | Figures 02 and 05 | Descriptive association only |
| Byte-identical two-run outputs | `docs/phase9_reproducibility.md`; validation record | Manifest | Pinned local environment |
| API and production fail-closed | API/auth tests; integration auditor; container smoke | Validation docs | No cloud deployment |
| Dashboard evidence separation | frontend tests; browser render record | Dashboard validation | Real Firebase session unverified |
| No fraud outcome or graph edge | feature report integrity section; label gate | None | Prohibits fraud/coordination claims |
| First-row on-chain corroboration | Phase 10 read-only RPC check | None | Does not establish dataset provenance |

## Citation sources

The working scholarly bibliography is in [`../phase10_literature_review.md`](../phase10_literature_review.md), with metadata checks in [`../phase10_reference_audit.md`](../phase10_reference_audit.md). The lecturer repository is mapped separately in [`../lab_traceability.md`](../lab_traceability.md).

## Submission blockers

Do not remove the following from the final limitations unless primary evidence resolves them: dataset source/licence, formal amendment record, AI-use disclosure requirement, missing outcomes/edges, clone-only reproduction and real authenticated browser acceptance.
