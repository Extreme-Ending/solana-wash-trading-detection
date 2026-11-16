# Phase 10 local demonstration validation

## Decision

**Local academic demonstration: READY WITH AN AUTHENTICATION CONDITION.** Automated and local browser paths remain functional. A genuine Firebase Google sign-in followed by a protected backend request was not verified because Application Default Credentials were unavailable in the Phase 10 environment. No credential, token or access-control bypass was requested.

## Environment prerequisite check

| Prerequisite | Observed state |
|---|---|
| Backend local configuration | `.env` present with expected variable names; values not printed |
| Frontend Firebase configuration | ignored `.env` and `.env.local` present with expected public configuration names; values not printed |
| Google Cloud CLI | installed |
| Firebase CLI | installed |
| Docker | installed and local daemon usable after sandbox approval |
| Headless Chrome | installed |
| Application Default Credentials | token acquisition unavailable |
| Legitimate approved browser session | not established during Phase 10 |

The presence of configuration files does not prove that their project IDs, UID allowlist and browser account are mutually valid. Firebase CLI availability also does not substitute for Firebase Admin credentials in the backend.

## API and scoring rehearsal

`scripts/audit_local_integration.py` exercised the current real experimental artifact through the FastAPI ASGI application and observed:

| Path/condition | Result |
|---|---:|
| `/healthz` | HTTP 200 |
| `/readyz` | HTTP 503 |
| Missing, invalid and expired authentication | HTTP 401 |
| Authorized feature preview through test-only verifier | HTTP 200 |
| Authorized batch and single experimental scoring | HTTP 200 in local development |
| Production scoring | HTTP 503 |
| Feature contract | exact 29 fields |
| Single/batch parity | exact |

The verifier seam was injected inside the audit process; Firebase was not contacted. The resulting synthetic scores verify wiring and determinism only.

The batch demonstration, rerun with the required artifact path, manifest and SHA-256, passed deterministic repetition and single-endpoint equivalence. It returned `is_probability=false` and the expected non-fraud interpretation. An initial invocation omitted required arguments and exited with argparse status 2; the corrected invocation passed, so this was a command-use error rather than a software failure.

## Frontend rehearsal

- All 72 frontend tests passed, including authentication states, 401/403/503 handling, feature validation, ranking, filters, detail views and scientific wording.
- TypeScript checking passed.
- The production build passed with 49 modules transformed.
- Vite was started on loopback port 4178 and stopped after inspection.
- Headless Chrome rendered the dashboard after a five-second virtual-time budget and exposed the phrases “Features and gated anomaly scores,” “Experimental local mode only,” and “Verified experimental snapshot.”
- A Chrome NSS root-certificate warning was emitted but did not prevent the loopback page from rendering; no external authentication was attempted.

This validates dashboard navigation/presentation at the unauthenticated shell level. It does not validate Google popup behaviour, an issued ID token, revocation lookup or an approved UID round-trip.

## Container rehearsal

A fresh local `solana-wallet-risk-api:phase10` image was built from the digest-pinned Dockerfile. The smoke test verified:

- installed API import and excluded-content checks;
- configured/runtime UID `10001`;
- health HTTP 200 and readiness HTTP 503;
- protected preview and score HTTP 401 without credentials;
- custom internal port 9090;
- graceful exit code 0; and
- image size 415,754,874 bytes.

The production-shaped image intentionally excludes experimental artifact/model dependencies. No image was pushed and no service was deployed.

## Safe demonstration sequence

1. State that the data are a provenance-unresolved DEX sample with no verified fraud target.
2. Show the Phase 9 aggregate evidence and Phase 10 interpretation captions.
3. Demonstrate public health and fail-closed readiness.
4. If the student has a legitimate configured session, sign in without exposing tokens and preview synthetic events.
5. Use local experimental scoring only when the checksum-pinned development artifact is enabled.
6. Describe rankings as batch-relative review candidates, never wallet flags.
7. End with provenance, label, coverage and external-validity limitations.

If Firebase authentication is unavailable, run the integration auditor and explicitly disclose its test-only verifier. Do not bypass authentication or present that path as a live Firebase acceptance test.

## Remaining acceptance action

The student must conduct one private rehearsal with the intended Firebase project, approved Google account, allowlisted UID and backend ADC. Observe successful preview, local experimental score where authorised, 403 for a valid but unapproved user, token refresh/revocation behaviour and absence of credentials in the recording. This is an academic demonstration prerequisite, not authorisation to deploy.
