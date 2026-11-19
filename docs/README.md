# Documentation

This index separates current operating documentation from historical research and implementation evidence. Use the authoritative documents below for the present system.

## Current documentation

| Subject | Authoritative document | Purpose |
| --- | --- | --- |
| Data | [Data pipeline](data_pipeline.md) | Source evidence, audit, cleaning, and generated data |
| Features | [Feature registry](feature_registry.md) | Exact 29-feature definitions and leakage controls |
| Models | [Model training and evaluation](model_training_and_evaluation.md) | Split, preprocessing, algorithms, results, and interpretation |
| API | [API contract](api_contract.md) | Routes, authentication, limits, errors, and model availability |
| System | [Architecture](architecture.md) | Frontend, authentication, API, model, and trust boundaries |
| Deployment | [Deployment](deployment.md) | Current cloud design, release controls, and operational checks |
| Reproduction | [Reproducibility](reproducibility.md) | Commands, fingerprints, tests, and environment constraints |
| Claims | [Research claims and limitations](research_claims_and_limitations.md) | Supported conclusions and unresolved limitations |
| Delivery | [Final deliverables checklist](final_deliverables_checklist.md) | Submission evidence, readiness decision and open gates |

The root [README](../README.md) is the concise project entry point. [AI_USE.md](../AI_USE.md) records the use of AI tools.

## Inventory and historical records

The directory contains detailed milestone evidence that remains useful for auditability but is not the current operating guide. It has not been moved because many research records refer to the existing paths.

| Historical group | Examples | Current source |
| --- | --- | --- |
| Data audit and cleaning reports | `data_audit_findings.md`, `preprocessing_findings.md`, `data_provenance_and_limitations.md` | [Data pipeline](data_pipeline.md) |
| Model experiments and scoring integration | `experimental_modelling_findings.md`, `anomaly_model_comparison.md`, `experimental_scoring_integration.md` | [Model training and evaluation](model_training_and_evaluation.md) |
| API, frontend, and container milestones | `api_implementation_findings.md`, `frontend_architecture.md`, `containerization_and_local_deployment.md` | [API contract](api_contract.md) and [architecture](architecture.md) |
| Cloud readiness and deployment records | files beginning with `phase11_`, plus cloud, Firebase, and GitHub Actions reports | [Deployment](deployment.md) |
| Phase 8E, 9, and 10 validation reports | files beginning with `phase8e_`, `phase9_`, or `phase10_` | [Reproducibility](reproducibility.md) |
| Methodology and evidence decisions | label-readiness, methodology, amendment, decision-log, and traceability files | [Research claims and limitations](research_claims_and_limitations.md) |
| Dissertation working material | `dissertation_draft/` and evidence mappings | Historical writing evidence only |
| Compliance and AI-use drafts | `final_capstone_compliance_audit.md`, `proposed_ai_use_disclosure.md` | Root [AI_USE.md](../AI_USE.md) and this index |

Historical files may describe a point-in-time state such as scoring being disabled, deployment being pending, or a methodology being provisional. Their dates and milestone context should not be treated as the current production state. The current documents preserve the verified measurements, security requirements, hashes, and limitations that remain applicable.

## Documentation policy

- Keep one current document per subject.
- Preserve historical evidence when removal would weaken traceability or break references.
- Do not use phase reports as setup or deployment instructions.
- Never place raw data, tokens, credentials, service-account keys, or model binaries in documentation.
- Update the current document when behavior changes, and retain the original evidence if it is needed for review.
