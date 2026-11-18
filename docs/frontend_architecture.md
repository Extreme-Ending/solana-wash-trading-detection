# Frontend architecture

## Purpose and boundary

The React application is an authenticated research interface for bounded, user-supplied Solana DEX event histories. Its primary journey is now:

```text
Google sign-in → Analyze one or many wallet histories → Immediate summary → Detailed analytics
```

The browser does not retrieve live wallet history, calculate model scores, load model artifacts, persist analysis input, or infer a fraud class. It submits the existing typed `POST /v1/score/batch` contract for both one-wallet and multi-wallet input. This keeps one user workflow while preserving the backend's point-in-time feature builder, trusted-artifact checks, Firebase authorization, request limits, review-budget contract, and production `MODEL_NOT_APPROVED` gate.

A successful local result is a unitless, model-specific anomaly score. Rank is relative only to the submitted wallets. Review selection represents analyst capacity, not a threshold, fraud probability, verified label, wash-trading conclusion, or evidence of intent.

## Runtime shape

```text
Browser (React + TypeScript)
  ├─ Firebase Web SDK
  │    └─ Google popup, auth-state observer, current ID token
  ├─ App state (memory only)
  │    └─ active view, latest validated request, latest API response
  ├─ Unified input parser
  │    ├─ grouped wallet-history arrays
  │    ├─ raw event arrays grouped by their wallet field
  │    └─ complete {as_of, review_budget, wallet_histories|events} payloads
  ├─ typed authenticated API client
  │    └─ POST /v1/score/batch
  └─ hash navigation
       ├─ #home
       └─ #analytics
```

The root-relative default `VITE_API_BASE_URL=/api` keeps local requests same-origin and lets the Vite proxy reach the loopback API. Production accepts only a validated HTTP(S) origin. Hash navigation requires no server route and remains compatible with the existing Firebase Hosting SPA rewrite.

Firebase Web identifiers are public project configuration. Firebase ID tokens, service-account keys, Admin credentials and other secrets never belong in `VITE_*` variables or the static bundle.

## Component responsibilities

| Source | Responsibility |
|---|---|
| `src/App.tsx` | Auth gate, memory-only result/request state and Home/Analytics navigation |
| `src/pages/LoginPage.tsx` | Burgundy-and-white Google-only sign-in experience |
| `src/pages/HomePage.tsx` | Wallet-check hero, unified form, empty state and immediate summary |
| `src/pages/AnalyticsPage.tsx` | Detailed result view and server-confirmed review-capacity resubmission |
| `src/components/layout/AppShell.tsx` | Brand, responsive navigation, account menu and sign-out |
| `src/components/forms/WalletAnalysisForm.tsx` | JSON import/paste, synthetic demo, validation, authenticated submission and safe errors |
| `src/components/results/AnalysisSummary.tsx` | API-derived summary cards, concise interpretation and ranking preview |
| `src/components/AnomalyDashboard.tsx` | Summary metrics, accurate charts, filters, table, warnings and wallet-detail drawer |
| `src/utils/analysisInput.ts` | Supported input-shape normalization and browser-side limit/schema validation |
| `src/utils/anomalyDashboard.ts` | Pure filtering, sorting, distribution and descriptive-reference comparisons |
| `src/api/client.ts` | Token-bearing requests and strict response-contract validation |
| `src/auth/*` | Firebase configuration, auth-state lifecycle and safe auth errors |

Earlier descriptive-preview and separate batch components remain covered by regression tests, but they are no longer separate primary user journeys.

## Unified analysis contract

The form accepts JSON only. It supports:

1. An array of `{wallet, events}` histories.
2. A raw event array in which every event includes its wallet.
3. A complete object containing `as_of`, optional `review_budget`, and either `wallet_histories` or `events`.

Raw events are grouped by exact wallet identifier in first-seen order. Grouped events must match their enclosing wallet; mismatches are rejected rather than repaired. Each event must retain the backend-supported closed schema: source row, UTC block time, slot, transaction hash, DEX, nullable token pair, input/output token, positive USD amount and supported optional fee/instruction indices.

The browser checks the existing defaults of 20 wallets, 100 total events, 50 events per wallet, 256 KiB, UTC timestamps and review capacity from 1 to 20. It also rejects malformed JSON, empty inputs, unsupported fields/values, duplicate source-row numbers inside a wallet, invalid numbers and invalid wallet identifiers. The backend remains authoritative and may reject duplicate records, at/after-cutoff evidence, insufficient history or other wallet-local issues.

The effective initial review capacity is bounded by submitted wallets. If the user changes it in Analytics, the frontend resubmits the unchanged validated histories and displays only the new server-confirmed selection. It never relabels the saved response in browser state.

## Result definitions

The immediate summary is derived only from the accepted API response:

- **Wallets analyzed:** `wallets_scored`, with rejected count disclosed.
- **Historical events:** sum of `included_historical_event_count` for ranked wallets.
- **Selected for review:** length of `review_candidates`.
- **Anomaly score / highest score:** first ranked score under the validated descending-order contract.

The compact and detailed ranking bars use the returned raw scores. The detailed distribution uses a dot display for fewer than five visible wallets and a bounded histogram otherwise. Filters change visibility and client display order only; original score and rank values remain intact. Wallet detail reveals six overview features first, then user-selected feature groups or all 29 fields. Training median and interquartile-range comparisons are descriptive context—not SHAP values, model contributions or causal explanations.

## Authentication and failure behavior

1. `AuthProvider` initializes the official Firebase Web SDK from environment-provided public identifiers and subscribes to authentication state.
2. Unauthenticated users see only the Google sign-in page. No email/password, anonymous, or bypass path is added.
3. Before a protected request, the API client requests the current Firebase ID token and sends it as `Authorization: Bearer <token>`.
4. FastAPI continues to verify token/project/email/provider/revocation requirements and the UID allowlist before protected processing.
5. The frontend distinguishes validation failures, 401 session expiry, 403 UID denial, 413 size limits, 429 rate limits, disabled/unavailable models, authentication-infrastructure 503 and generic server/network failures.
6. Signing out clears the latest request and result. Input and results are never written to browser storage.

Default and production scoring remain disabled. The UI does not convert `MODEL_NOT_APPROVED` into a successful result or placeholder score.

## Accessibility and responsive behavior

Semantic landmarks, headings, visible labels, status regions, keyboard-focus styles, a skip link, disabled pending actions, text chart descriptions, non-color review labels and reduced-motion support are included. The wallet panel uses dialog semantics, an explicit close control, Escape dismissal and backdrop dismissal. Wide tables scroll rather than compress values into unreadable cells.

Breakpoints support the required approximate widths:

- **Desktop (1440px):** split login, two-column home hero, chart pairs and four summary cards.
- **Tablet (768px):** single-column login/home content, collapsed navigation, stacked charts and two-column metrics/filters.
- **Mobile (375px):** Google sign-in card, single-column form/cards/filters, horizontal result tables and a full-width detail drawer.

## Security, privacy and scientific integrity

- No Admin credential, remote font, analytics script, raw-event log, token display or browser persistence was added.
- No `dangerouslySetInnerHTML`, automatic retries, anonymous sign-in or authentication bypass is used.
- React escapes rendered wallet and metadata strings.
- Exact-origin CORS, backend byte/count limits, rate limits, UID authorization and trusted model loading remain backend controls.
- The available inputs are user-supplied DEX swaps, not authenticated NFT marketplace transactions.
- Incomplete histories can change scores, and unusualness cannot establish fraud or wash trading.

## Deployment boundary and deferred capability

This redesign made no cloud, Firebase, IAM, billing, model-artifact or deployment change. The private Cloud Run/browser-access constraint remains unresolved. Live provider-backed address lookup, saved analysis history, telemetry, distributed rate limiting/App Check, model promotion, score thresholds and automated wallet flags remain deferred or unsupported.
