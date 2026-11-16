# Chapter 5 — Discussion and conclusion (working draft)

## 5.1 Discussion

The technical evidence shows that point-in-time wallet anomaly analysis can be made deterministic and inspectable. Isolation Forest rankings were stable under the limited validation settings tested, but model choice remains consequential: LOF ranked the holdout very differently from both Isolation Forest and robust MAD. A review queue should therefore be presented as conditional on a declared detector and budget.

Temporal evaluation exposed dependence that a random split would hide. Every reference wallet recurred in later snapshots, so later scores partly reflect accumulated histories for known wallets. New wallets offer identity-disjoint observations but have shorter coverage and shifted feature distributions. Neither group alone supports broad real-world generalisation.

The results also demonstrate the difference between engineering validity and construct validity. Feature parity, deterministic artifacts and a working API show that the implemented system behaves as designed. They do not show that its scores measure wash trading. That conclusion requires independent outcomes and, for coordination claims, relational evidence.

## 5.2 Contributions

- a deterministic audit and quarantine trail;
- strict pre-cutoff wallet snapshots and a 29-feature registry;
- a transparent three-detector comparison under missing labels;
- temporal, coverage and review-budget diagnostics;
- content-bound reproducibility evidence; and
- secure local research delivery with fail-closed production semantics.

## 5.3 Limitations

The greatest limitations are unresolved source/licence, absent ground truth, missing counterparty edges, sparse histories, detector disagreement, one sample and no live deployment evaluation. The held-out period has already been used for descriptive reporting and should not become an iterative tuning set. A real Firebase browser acceptance session remains unverified in the Phase 10 environment.

## 5.4 Ethical implications

An anomaly score can create reputational harm if presented as criminal evidence. The interface must remain access-controlled, purpose-limited and review-oriented. Wallet rankings should not be published with allegations, used to deanonymise participants or trigger automated sanctions. Independent evidence and due process are required outside research exploration.

## 5.5 Future work

Priority future work is to establish lawful repeatable acquisition, evaluate an independent time/source cohort and obtain expert review outcomes. Verified timestamped labels could enable a separately approved supervised study. Direct counterparties and validated ownership evidence would be prerequisites for graph coordination analysis. Prospective drift monitoring should be added only with an operational data source and predeclared governance.

## 5.6 Conclusion

The project demonstrates a reproducible local service for ranking wallet-time observations that are unusual relative to a historical Solana DEX reference. It does not demonstrate effective wash-trading detection. The most defensible conclusion is methodological: rigorous data contracts, temporal boundaries, comparative diagnostics and honest uncertainty make an unlabelled anomaly study useful without turning unusual activity into unsupported ground truth.

## 5.7 Student work required

**[STUDENT INPUT REQUIRED]** Write the final reflective conclusion, connect findings to the official approved objectives and incorporate any supervisor feedback. **[DOCUMENT REQUIRED]** Resolve or explicitly accept the provenance/licensing limitation under institutional guidance.
