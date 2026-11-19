# Final deliverables checklist

Validated on 19 November 2026 against repository revision `a3a2b795d7d5a3e589bcd66f6a1cddbe95fc53ac`. The live Cloud Run service remains revision `solana-wallet-risk-api-00007-4mh`, labelled with code revision `d7363b2412439b0e3b15387e4407db0046f28b8d`.

| Requirement | Status | Verified evidence | Remaining action |
| --- | --- | --- | --- |
| README | COMPLETE | Current overview, live link, Dune description, pipeline, models, evaluation, architecture, setup, reproduction, API, deployment and limitations | Student review |
| AI-use disclosure | COMPLETE | Root `AI_USE.md`, 99 words, factual and tracked | Student confirms institutional wording |
| Reproducible data pipeline | PARTIAL | Fresh audit, cleaning, features, training, evaluation and prediction work with the private source | Supply lawful Dune acquisition or restricted reviewer handover |
| Training code and serialized model | PARTIAL | Training code, local artifact, manifest, exact hashes and reproducible reviewer package | Confirm the accepted delivery channel and upload package personally |
| Docker and Compose | COMPLETE | Standard and scoring Dockerfiles, Compose, configuration tests and container smoke coverage | None for local delivery |
| Deployed model-serving API | PARTIAL | Live health/readiness and model loading verified; protected routes reject anonymous calls; `/healthz` is a documented Cloud Run reserved-path conflict, not the production health route | Student captures one sanitized authenticated numerical response |
| Final report and presentation | COMPLETE | Editable report source, DOCX, PDF, editable PPTX and 12-slide outline under `reports/submission/` | Student reviews authorship, cover-page details and institutional formatting |

## Readiness decision

**PARTIAL, NO-GO for final submission.** Four deliverables have complete repository evidence. Clone-only data reproduction, approved artifact distribution, dataset rights, and independent capture of a genuine authenticated live numerical response remain open.

The system is an unsupervised anomaly-analysis service. It does not establish fraud or wash-trading detection effectiveness.

The live API is labelled with revision `d7363b2412439b0e3b15387e4407db0046f28b8d`. The only committed changes between that revision and the validated repository revision are documentation files, so no later committed runtime change is awaiting deployment.

## Evidence still required

- The repository has no `references/` directory and contains no primary approved proposal, assignment brief or capstone rubric. Compliance is assessed against the verified steering summary; the student must compare the submission with the institution's originals.
- Dune query URL or ID, SQL, extraction date, export procedure, sampling method, licence and redistribution permission are not available locally.
- A genuine authenticated live numerical response has not been independently captured because no Firebase user token was supplied to this validation process.

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

From the Dune account or workspace, record:

- query URL and numeric query ID;
- exact SQL or an exported query revision;
- Solana source tables, filters, parameters, ordering and row-limit or sampling rules;
- export timestamp in UTC, file format and extraction steps;
- account or workspace ownership evidence; and
- applicable Dune terms, dataset-specific licence and redistribution permission.

Bind the evidence to the local source by recording the filename, row and column counts, observation window and SHA-256 `8f387709c6742f2fc31c19fc32dac27474b6b27b9304786c367a8d8bece81271`.

## Restricted reviewer data handover

If the query cannot be made public, place the original unmodified CSV, its checksum, the recovered provenance record and access instructions in an institution-controlled restricted submission area. Grant access only to the named reviewer. The reviewer should place the file at repository-root `nft.csv`, run `sha256sum nft.csv`, require the expected digest above, and then run the documented pipeline. Do not send the CSV through public GitHub, chat, screenshots or an unrestricted link. Retain or delete the reviewer copy according to institutional policy.
