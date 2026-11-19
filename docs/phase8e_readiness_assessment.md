# Phase 8E readiness assessment

## Executive decision

**Phase 8E: CONDITIONAL PASS.** The available evidence has been audited, the research boundary has been made explicit, the existing evaluator reproduced the label-free findings, and a technically viable secure architecture has been defined. Dataset extraction metadata and sharing permission, primary proposal/rubric, documentary methodology approval, AI-use disclosure requirements and live cloud ownership/configuration remain unresolved.

This decision does **not** authorize cloud deployment, model promotion, public access, a formal methodology/title change or fraud/wash-trading effectiveness claims.

| Readiness area | Decision | Basis |
|---|---|---|
| Local engineering demonstration | Conditional pass | Reproducible pipeline/artifact, guarded API, frontend and container are testable; raw input remains local/ignored |
| Unsupervised research evidence | Conditional pass | Rank/sensitivity/temporal evidence is reproducible, but conclusions are dataset- and detector-limited |
| Fraud or wash-trading detection | **Fail / prohibited claim** | No independently verified outcome labels or counterparty evidence |
| Dataset publication/use | **Blocked** | Dune query 6561080 is confirmed; historical extraction metadata and data-sharing permission are incomplete |
| Academic submission package | Conditional / incomplete | Primary proposal, rubric, approval record, AI-use disclosure and final report materials are absent locally |
| Live cloud deployment | **NO-GO** | Architecture is proposed only; identity, IAM, billing, abuse, domain and live acceptance remain unverified |

## Evidence summary

### Dataset provenance

The dataset creator identifies Dune Analytics query 6561080 as the source of the 10,800 Solana wallet-attributed DEX/swap events. The file has no ground-truth field or counterparty edge. Its SHA-256 establishes local file identity, not data-sharing permission. See [`dataset_provenance_resolution.md`](dataset_provenance_resolution.md).

### Methodology

The code supports a point-in-time, unsupervised wallet anomaly research question. It does not support supervised NFT classification or confirmed fraud conclusions. Strict event cutoffs, fitted-pipeline reuse and chronological roles align with lecturer fundamentals; repeated-wallet dependence and later-entrant history coverage limit generalisation. See [`research_methodology_alignment.md`](research_methodology_alignment.md) and [`research_claims_and_limitations.md`](research_claims_and_limitations.md).

### Evaluation

The registered evaluator accepted the current checksums and reproduced parameter sensitivity, cross-detector agreement, top-budget overlap, longitudinal stability, distribution shift and coverage-stratum results. Isolation Forest was stable under the tested parameter variations, but cross-detector agreement was weak except against the robust comparator. No label-based metric was calculated. See [`phase8e_research_evaluation.md`](phase8e_research_evaluation.md).

### Secure deployment

The recommended immediate posture is an IAM-private operator-only pilot if deployment is separately authorized. A later hosted SPA should call a public authentication BFF that verifies Firebase identity/app controls and invokes an IAM-private core using a workload identity. Directly exposing the core is not recommended merely to accommodate the browser. See [`secure_deployment_architecture.md`](secure_deployment_architecture.md).

### Academic compliance

Technical traceability is strong, but primary governance material is incomplete. `AI_USE.md` remains absent and was not recreated because Phase 8E explicitly prohibited that change. See [`academic_compliance_readiness.md`](academic_compliance_readiness.md).

## Observed regression and reproducibility results

| Command/check | Observed Phase 8E result |
|---|---|
| `.venv/bin/python -m pytest -q` | **202 passed** in 12.24 s |
| `npm test -- --run` in `frontend/` | **10 files, 72 tests passed** |
| `npm run typecheck` | Passed |
| `VITE_API_BASE_URL=https://api.example.invalid npm run build` | Passed; 48 modules transformed |
| Two independent audit → preprocess → feature → training runs under `/tmp` | Passed; both produced 10,798 clean + 2 quarantined events, 5,996 snapshots, and identical output hashes |
| `cmp` between the two runs and current model/manifest | Passed; byte-identical audit/data/snapshot outputs and artifact/manifest; current artifact also matched |
| `python -m solana_risk.models.evaluate_anomaly ...` | Passed; regenerated label-free evaluation in `/tmp` |
| `PYTHONPATH=src .venv/bin/python scripts/audit_local_integration.py` | Passed; actual-artifact preview/single/batch 200, exact single/batch scores, auth failures 401, production score 503 |
| `.venv/bin/python scripts/validate_deployment_bundle.py frontend/dist` | Passed; 4 files checked |
| Focused API/auth/scoring/deployment/container pytest set | **106 passed** in 3.27 s (also included in the full 202) |
| `docker compose config --quiet` | Passed |
| `docker build -t solana-wallet-risk-api:phase8e .` | Passed after local Docker-daemon access was authorized |
| Container smoke on loopback ports 18084/18085 | Passed; UID 10001, content/import, health 200, readiness 503, protected 401, custom port 9090 and graceful exit 0 |
| `bash -n scripts/deployment.sh commit.sh` and Python script compilation | Passed |
| Required-document/local-link/trailing-whitespace checks | Passed; seven deliverables present, all local links resolve, `AI_USE.md` remains absent |
| `git diff --check` | Passed |

The first two temporary pipeline attempts used the filename copied from the Phase 8D reproduction block and stopped because it named `nft_events_clean.csv`. The preprocessor actually and consistently writes `cleaned_events.csv`. No feature or model output was created in those failed attempts. Phase 8E corrected that documentation-only filename in [`end_to_end_validation.md`](end_to_end_validation.md), started two fresh runs, and obtained the successful results above. This was a pre-existing reproduction-instruction defect, not a data or pipeline regression.

## Blockers ranked by severity

1. **Critical — extraction evidence and use rights:** the source query is confirmed, but the exact historical SQL revision, execution metadata, parameters, sampling procedure and data-sharing permission are incomplete. Resolve before publishing data or artifacts.
2. **Critical — claim validity:** no independent labels and no counterparty evidence. Fraud, wash trading, coordination and classification-effectiveness claims remain prohibited.
3. **High — academic authorization/evidence:** primary proposal, rubric and written method-change evidence are absent locally; the DEX/unsupervised scope must be reconciled through the required academic process.
4. **High — AI-use disclosure:** the prior required disclosure file is absent. Resolution must follow explicit student/institutional instruction; Phase 8E did not recreate it.
5. **High — live security architecture acceptance:** BFF/private-core design, Firebase project/domain, App Check/rate control, runtime identities and least-privilege bindings require review and live acceptance.
6. **High — billing and operational ownership:** project ownership, billing, alerts/spend-cap coverage, max instances, monitoring, incident shutdown and rollback owners are unverified.
7. **Medium — external validity:** one supplied event sample, repeated wallets, short-history entrants and unknown coverage constrain population claims.
8. **Medium — final submission assets:** final report, consolidated bibliography, rubric map, slides and examiner reproducibility/distribution route are absent.

## Phase 9 recommendation

Do not start Phase 9 automatically. If the student explicitly authorizes it, scope it to **submission evidence consolidation**, conditional on first supplying the primary proposal/rubric and any available extraction/licence records. Appropriate work would be a rubric evidence matrix, student-reviewed final reproducibility manifest, bibliography/citation validation, model card with the claim boundary, and report/slide evidence tables.

Phase 9 should not add supervised labels, promote the model, implement the BFF, publish data, or deploy cloud resources unless each is separately supported and authorized. If extraction metadata or data-sharing permission cannot be resolved, the next action is an academic/data-governance decision, not additional modelling.

## Completion statement

Phase 8E resolves every blocker that can be addressed through repository evidence and local validation. It records rather than fabricates external facts. Final completion remains conditional because the highest-severity blockers require student/supervisor/institutional or provider evidence outside the repository.
