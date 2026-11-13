# Phase 6 frontend architecture

## Purpose and boundary

The React frontend is a local research interface for the existing FastAPI descriptive-feature service. It accepts one wallet identifier, one explicit UTC cutoff, and a bounded array of user-supplied Solana DEX swap events. It displays the 29 values returned by `POST /v1/features/preview` and does not calculate those features independently.

The interface does not fetch wallet history, persist input, call a blockchain provider, load a model artifact, or present an anomaly score, fraud probability, wash-trading verdict, or threshold. `GET /readyz` and `POST /v1/score` returning HTTP 503 `MODEL_NOT_APPROVED` is an expected capability state, not a frontend crash.

## Runtime shape

```text
Browser (React + TypeScript)
  ├─ Firebase Web SDK: Google popup, auth-state observer, current ID token
  ├─ local state: wallet, UTC cutoff, event JSON, latest preview
  ├─ client validation: closed schema, 1–100 events, 256 KiB limit
  └─ typed fetch client
       └─ /api/* during development
            └─ Vite loopback proxy
                 └─ http://127.0.0.1:8080/* (Firebase-verifying FastAPI container)
```

The default `VITE_API_BASE_URL=/api` keeps local browser requests same-origin and lets the Vite development proxy reach the loopback-only Compose service. A simple root-relative path or an HTTP(S) base URL can be supplied at build time. Protocol-relative URLs, credentials, query strings, and fragments are rejected. The Firebase Web API key, auth domain, project ID, and app ID are intentionally public project configuration. ID tokens, service-account keys, Admin credentials, and other secrets never belong in a `VITE_*` variable because Vite exposes such values to the browser.

## Source responsibilities

| Source | Responsibility |
|---|---|
| `src/api/types.ts` | Exact request, health, availability, and 29-feature response types |
| `src/api/config.ts` | Safe API-base resolution with `/api` as the local default |
| `src/api/client.ts` | Fetch calls, structured errors, response-schema and feature-order checks |
| `src/auth/firebase.ts` | Validated public Firebase configuration, Google provider and ID-token access |
| `src/auth/AuthContext.tsx` | Auth-state subscription, sign-in/out actions, loading and safe error state |
| `src/utils/validation.ts` | Fail-closed local input/import validation and request-size enforcement |
| `src/data/featureRegistry.ts` | Human-readable definitions and grouping for the 29 existing features |
| `src/data/syntheticExample.ts` | Clearly synthetic, deterministic demonstration input |
| `src/components/EventWorkbench.tsx` | Event entry, local JSON import, submission, cancellation, and feedback |
| `src/components/FeatureResults.tsx` | Complete grouped feature output with null and zero distinguished |
| `src/components/FeatureCharts.tsx` | Dependency-free accessible comparisons derived only from API values |
| `src/components/ServiceStatus.tsx` | Independent process-health and scoring-capability status |
| `src/components/ModelStatus.tsx` | Explicit unavailable-scoring gate; never renders model output |

`App.tsx` retains only the most recent response and its validated request in component memory. Reloading or clearing the page removes them. A local JSON file is read with the browser file API, limited to 256 KiB, and is not uploaded until the student explicitly submits the form.

## Authentication flow

1. `AuthProvider` initializes the official modular Firebase Web SDK from four environment-provided public identifiers and subscribes with `onAuthStateChanged`.
2. The header offers Google popup sign-in, sign-out, an initial loading state, the current display identity, and an accessible safe error message.
3. The API client requests a current Firebase ID token immediately before preview or scoring-gate requests and sets `Authorization: Bearer <token>`. It does not send the token on health/readiness requests and does not persist or log it.
4. A missing local user blocks submission. Backend 401 prompts reauthentication, 403 explains that the account is not approved, and authentication-related 503 reports temporary verification/configuration unavailability. `MODEL_NOT_APPROVED` remains the expected scoring 503.
5. Signing out clears the rendered feature preview and last scoring request from React state.

## API contract and fail-closed behavior

The frontend mirrors the Phase 5A request schema rather than accepting arbitrary feature vectors. Each event requires the source row, UTC block time, slot, transaction hash, DEX, token pair, input/output tokens and positive USD amount; fee and instruction indices are optional/nullable according to the API contract. Additional fields, mixed wallets, duplicate source-row numbers, invalid UTC values, nonfinite numbers, and nonpositive required amounts are rejected.

The response guard requires:

- `status=descriptive_features` and `source=user_supplied_unverified_events`;
- the exact registered feature order, not merely 29 arbitrary values;
- a finite number, boolean, or null for every registered field; and
- required wallet, cutoff, and interpretation metadata.

Schema drift is shown as an error instead of being silently reformatted. Network errors do not create placeholder results. Unexpected successful readiness/scoring responses are rejected because model output is outside this phase.

## Interface and accessibility

The responsive dashboard uses semantic landmarks, labelled controls, visible keyboard focus, a skip link, live status messages, disabled loading states, text equivalents for bar charts, labelled progress meters, and a reduced-motion rule. Charts use HTML and CSS instead of canvas, so their values remain available to assistive technology. Missing values display as `Unavailable`; numeric zero remains a real zero.

The visual hierarchy separates evidence from capability: project scope, process health, event entry, descriptive output, charts, the model gate, and methodological limits are distinct sections. Mobile layouts collapse without horizontal data tables.

## Security and privacy

- No Admin credentials, analytics, telemetry, external fonts, or remote scripts are used. Firebase Authentication is the sole added third-party runtime API.
- No `dangerouslySetInnerHTML`, browser storage, cookies, service worker, or raw-event logging is used.
- React escapes displayed wallet and metadata strings.
- Requests are explicit and are not retried automatically.
- Firebase ID tokens remain in Firebase SDK/browser memory and request headers; they are not written to application storage or displayed.
- In-flight preview and model-gate requests are cancellable on replacement or unmount.
- Production CORS remains the backend's exact-origin responsibility; the local proxy does not justify a wildcard origin.

## Scientific interpretation

The available records are DEX swap events, not authenticated NFT marketplace sales. The preview is derived from user-supplied, unverified event history and is only as complete as that history. Feature magnitude, concentration, recency, or unusualness cannot establish wash trading or fraud. The interface preserves this boundary in the overview, results, model gate, charts, and methodology section.

## Deployment limitation

Firebase authentication is application-layer authorization, not Cloud Run IAM authorization. The reviewed Cloud Run service remains private. A normal Firebase-hosted browser cannot supply the separate Google-signed Cloud Run invocation credential required by the platform, even though it can supply a Firebase end-user ID token to FastAPI. Phase 7B therefore does not claim a working hosted end-to-end path and does not enable public invocation.

## Deferred work

Live Firebase/Google Cloud resource configuration, the Cloud Run browser-access architecture, rate limiting/App Check, provider-backed wallet lookup, telemetry, model-artifact promotion, and anomaly scoring remain outside Phase 7B.

The intended later deployment shape is a Vite production build published from `frontend/dist/` to standard Firebase Hosting with a single-page-app rewrite, while the existing container runs independently on Cloud Run. That phase would need an owned Google Cloud/Firebase project, billing and budget controls, an Artifact Registry/image release process, Cloud Run service identity and resource limits, HTTPS API configuration, the exact Firebase origin in backend CORS, environment-specific `VITE_API_BASE_URL`, access/log-retention review, and post-deployment health/readiness/preview tests. It must not place a credential in the static bundle or enable scoring merely because hosting exists.
