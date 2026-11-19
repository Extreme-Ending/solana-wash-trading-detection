# Final deliverables checklist

Validated on 19 November 2026 against the working tree based on repository revision `6dd168578422c55ad4a56ad75015d348b75bc0c2`. The closeout documentation changes are uncommitted. The live Cloud Run service remains revision `solana-wallet-risk-api-00007-4mh`, labelled with code revision `d7363b2412439b0e3b15387e4407db0046f28b8d`.

| Requirement | Status | Verified evidence | Remaining action |
| --- | --- | --- | --- |
| README | COMPLETE | Current overview, live link, Dune query 6561080, evidenced batch pattern, pipeline, models, evaluation, architecture, setup, reproduction, API, deployment and limitations | Student review |
| AI-use disclosure | COMPLETE | Root `AI_USE.md`, 99 words, factual and tracked | Student confirms institutional wording |
| Reproducible data pipeline | PARTIAL | Confirmed query source, reference checksum, evidenced 11-block extraction pattern, audit, cleaning, features, training, evaluation and prediction are documented | Archive missing extraction metadata and provide lawful source acquisition or restricted reviewer handover |
| Training code and serialized model | COMPLETE LOCALLY | Training code plus the selected-model-only 4B.1 artifact, manifest, checksums and tested inference commands are ready at `artifacts/release/4B.1/`; the release excludes LOF's retained row arrays | Student reviews, commits and pushes the release files |
| Docker and Compose | COMPLETE | Standard and scoring Dockerfiles, Compose, configuration tests and container smoke coverage | None for local delivery |
| Deployed model-serving API | PARTIAL | Live health/readiness and model loading verified; protected routes reject anonymous calls; `/healthz` is a documented Cloud Run reserved-path conflict, not the production health route | Student captures one sanitized authenticated numerical response |
| Final report | COMPLETE | Editable report source, DOCX and PDF under `reports/submission/` | Student reviews authorship, cover-page details and institutional formatting |

## Readiness decision

**READY AFTER STUDENT PUBLICATION, with one partial reproducibility limitation.** All seven required deliverable categories are present or ready to track locally. Exact clone-only retraining remains partial because the raw experiment CSV cannot be published without confirmed redistribution permission and the historical extraction metadata is incomplete. The public selected-model artifact supports checksum-verified numerical inference without the private CSV.

The system is an unsupervised anomaly-analysis service. It does not establish fraud or wash-trading detection effectiveness.

The live API is labelled with revision `d7363b2412439b0e3b15387e4407db0046f28b8d`. The closeout work changes documentation and generated submission materials, not runtime behavior, so no deployment is required for this checkpoint.

## Evidence still required

- The repository has no `references/` directory and contains no primary approved proposal, assignment brief or capstone rubric. Compliance is assessed against the verified steering summary; the student must compare the submission with the institution's originals.
- Dune query 6561080 is the confirmed dataset source. The exact historical SQL revision, execution identifiers, parameters, extraction timestamps, original batch files, and data-sharing permission are not available locally.
- A genuine authenticated live numerical response has not been independently captured because no Firebase user token was supplied to this validation process.
- The older tracked presentation files are not required because the final report satisfies the report-or-slides requirement. The student requested separate presentation submission, so remove `reports/submission/solana_wallet_risk_presentation.pptx` and `reports/submission/solana_wallet_risk_presentation_outline.md` from the public repository before the final commit.

## Secure authenticated acceptance

After signing in with an allowlisted Firebase account, copy a fresh ID token from the browser's protected API request into a hidden terminal prompt. Do not paste the token into source files, shell history, screenshots or chat.

```bash
read -rsp "Firebase ID token: " SOLANA_RISK_FIREBASE_ID_TOKEN
echo
export SOLANA_RISK_FIREBASE_ID_TOKEN
python scripts/verify_live_authenticated_scoring.py
unset SOLANA_RISK_FIREBASE_ID_TOKEN
```

The script sends only synthetic demonstration events and prints a sanitized response. The token remains process-local and is neither printed nor written.

## Dune evidence to recover

If historical extraction records are available, preserve:

- exact extraction-time SQL from version history;
- Solana source tables, filters, parameters, ordering and row-limit or sampling rules;
- execution IDs, export timestamp in UTC, file format and month-filter extraction steps;
- the original batch files or a batch manifest; and
- applicable Dune terms and data-sharing permission.

Bind the evidence to the local source by recording the filename, row and column counts, observation window and SHA-256 `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`.

Local evidence supports 11 contiguous month-labelled blocks: 1,000 rows for ten months and 800 for April. Query 6561080 was executed again after the original extraction, so its current SQL is not a preserved extraction-time snapshot. The source identity is resolved, but the exact historical extraction sequence is not independently archived.

## Restricted reviewer data handover

If the query cannot be made public, place the original unmodified CSV, its checksum, the recovered provenance record and access instructions in an institution-controlled restricted submission area. Grant access only to the named reviewer. The reviewer should place the file at repository-root `nft.csv`, run `sha256sum nft.csv`, require the expected digest above, and then run the documented pipeline. Do not send the CSV through public GitHub, chat, screenshots or an unrestricted link. Retain or delete the reviewer copy according to institutional policy.
