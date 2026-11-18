# Frontend revamp validation

## 1. Design objectives and direction

The revamp makes the research interface understandable before exposing technical detail. It uses a restrained burgundy, blush and white system; compact labels; generous spacing; white content cards; clear focus treatment; and semantic success/warning/error colors. Burgundy indicates brand, navigation and primary actions—not wallet risk or fraud.

The intended journey is:

```text
Google sign-in → Unified wallet analysis → Immediate summary → Detailed analytics
```

The title, event-domain and model boundaries are unchanged. The interface remains an experimental DEX wallet-anomaly review tool and does not claim confirmed wash trading.

## 2. Before and after

Previously, the root page stacked project overview, service status, research evidence, a one-wallet feature-preview form, feature charts, a single-score gate, a separate batch form and methodology content. Users needed to understand which technical flow to choose and received extensive metadata before a result.

The new experience has three focused states:

- a Google-only split-screen login;
- a Home page with one **Analyze wallets** form and immediate summary; and
- an Analytics page with charts, filters, a ranked table and progressive wallet detail.

Historical descriptive-preview and separate batch components remain in the source and regression suite, but are no longer competing primary entry points.

## 3. Component architecture

`App.tsx` owns only authenticated navigation plus the latest validated request/response in memory. `LoginPage`, `HomePage` and `AnalyticsPage` define the screens. `AppShell` owns navigation/account controls. `WalletAnalysisForm` owns input and API interaction. `AnalysisSummary` derives concise response metrics. `AnomalyDashboard` owns detailed review presentation, while pure input and dashboard transformations remain in `utils/`.

No routing package was added. `#home` and `#analytics` provide reload-safe SPA navigation under the existing Firebase Hosting rewrite without creating server paths.

## 4. Unified analysis workflow

The form accepts one of three JSON shapes:

1. An array of `{wallet, events}` histories.
2. A raw event array with a wallet on every event.
3. A complete object with `as_of`, optional `review_budget`, and `wallet_histories` or `events`.

Raw events are grouped by wallet, so the valid unique-wallet count determines whether the result is a one-wallet or multi-wallet presentation. Both cases use the existing authenticated `POST /v1/score/batch` endpoint. The form cannot perform address-only blockchain lookup and says so before submission. The demonstration action loads deterministic synthetic histories and labels them as demonstration data.

## 5. Form-validation rules

The browser checks:

- non-empty, valid JSON in a supported shape;
- exact, non-empty wallet identifiers with a 128-character/control-character boundary;
- a valid ISO-8601 UTC scoring timestamp ending in `Z` or `+00:00`;
- review capacity as an integer from 1 to 20;
- the supported event object fields and types;
- positive finite `amount_usd`, valid nonnegative optional values and UTC event time;
- unique source-row numbers within each wallet;
- exact wallet agreement between a group and its events;
- at most 20 wallets, 100 total events and 50 events per wallet;
- at most 256 KiB for imported text and the serialized request; and
- `.json` for file import.

Errors preserve the user's input. Duplicate submissions are disabled while pending, and replacement/unmount cancels the main analysis request. Backend validation remains authoritative for duplicate records, history eligibility and point-in-time inclusion.

HTTP 400/422, 401, 403, 413, 429, model/authentication 503, generic server and network failures have safe user messages. Raw stack traces and generic server detail are not rendered.

## 6. Summary-card definitions

| Card | API derivation |
|---|---|
| Wallet(s) analyzed | `wallets_scored`; rejected count shown separately |
| Historical events | Sum of ranked wallets' `included_historical_event_count` |
| Selected for review | Length of `review_candidates` |
| Anomaly/highest score | First item under the validated server ranking contract |

The wording changes for one scored wallet. The insight sentence and warnings are deterministic response summaries, not generated findings.

## 7. Chart definitions and data sources

The Home comparison and Analytics ranking chart use the raw `anomaly_score` values from the current response. Bar widths normalize only against the highest visible value; printed scores remain the source values. The distribution uses visible response scores: a dot view below five wallets and a bounded histogram otherwise. Filters change visibility only. Sorting does not mutate the stored scores or original ranks.

Wallet detail first shows six representative fields, then offers the registered feature groups or all 29 features. Values and the training-only aggregate reference come from the validated response. Robust IQR comparisons are descriptive and are suppressed for missing, binary, constant or zero-IQR data.

Changing review capacity sends the original validated histories in a new authenticated request. The browser does not recalculate which wallets the server selected.

## 8. Authentication and security

The official Firebase Web SDK, Google popup sign-in, auth-state observer and existing sign-out flow are preserved. Unauthenticated users do not see analysis controls. The typed client obtains a current Firebase ID token only for protected API requests. The backend continues to verify Firebase/project/email/provider/revocation claims and the UID allowlist.

No password form, anonymous login, token display, browser persistence, credential, external wallet provider, model artifact or authentication bypass was added. Exact CORS, request/rate limits, trusted artifact verification and production `MODEL_NOT_APPROVED` behavior remain server controls.

## 9. Accessibility improvements

- Semantic page landmarks and heading hierarchy.
- Skip link, visible focus states and keyboard-operable controls.
- Visible labels rather than placeholder-only fields.
- Live loading/error/status regions and disabled pending actions.
- Text labels and accessible descriptions for CSS charts.
- Review/warning meaning conveyed by text and symbols, not color alone.
- Dialog semantics, close button, Escape dismissal and backdrop dismissal for wallet detail.
- Horizontal scrolling for wide tables instead of compressed unreadable values.
- Reduced-motion support.

## 10. Responsive verification

The CSS implements explicit desktop, tablet and mobile adaptations at 1024px, 768px and 480px. At desktop width the login and Home hero use split layouts; at tablet width charts stack and navigation collapses; at mobile width forms, metrics and filters become single-column while result tables remain scrollable and wallet detail becomes full width.

Automated DOM tests verify the login, navigation, primary flow, empty state, summary, analytics and component behavior. CSS breakpoint rules were inspected at the required approximate 1440px, 768px and 375px targets. A headless-Chrome attempt reached the real Firebase initialization screen but could not complete authentication-state initialization in the isolated headless environment. Therefore no representative real-browser login/home/analytics screenshot is retained and no real Firebase login is claimed.

## 11. Automated validation evidence

Executed on 17 November 2026:

| Command | Result |
|---|---|
| `npm run typecheck` | PASS |
| `npm test -- --run` | PASS — 90 tests across 13 files after the final test additions |
| `npm run build` | PASS — 45 modules transformed |
| `.venv/bin/python -m pytest -q` | PASS — 205 tests |
| `docker compose config --quiet` | PASS |
| `.venv/bin/python scripts/container_smoke_test.py` | PASS — non-root UID 10001; health 200; readiness 503; unauthenticated preview/score 401; custom-port health 200; graceful exit 0 |
| `.venv/bin/python scripts/validate_deployment_bundle.py frontend/dist` | PASS — 4 files checked |
| `git diff --check` | PASS |

The Docker image contained neither scikit-learn/joblib nor datasets, model artifacts, local instruction files or environment files. No deployment or cloud resource mutation occurred.

## 12. Browser-validation distinction

Component and integration tests use an isolated Firebase gateway and mocked API responses; they validate the UI and token-bearing request contract but are not a live Firebase login. The local Docker smoke suite validates default production gates but does not enable experimental scoring. A complete interactive browser pass with a real approved Firebase session and the development-only experimental API remains a student-operated acceptance check.

## 13. Unsupported features intentionally excluded

- Address-only live blockchain retrieval.
- Wallet balances, holdings or portfolio values.
- Saved searches, saved analysis history or browser persistence.
- Fraud probabilities, risk bands, severity labels or automatic wallet flags.
- Email/password or anonymous authentication.
- Client-side scoring, feature calculation or model loading.
- SHAP/model-contribution claims.
- Cloud deployment or public API invocation.

## 14. Remaining UX limitations

- Users must supply complete, authorized transaction-history JSON.
- Results last only for the authenticated browser session and disappear on refresh/sign-out.
- Very wide feature tables require horizontal scrolling.
- The detail dialog does not implement a full keyboard-focus trap, although it has dialog semantics and keyboard dismissal.
- A real approved-account browser acceptance pass is still required for screenshots and live Firebase/API verification.
- Production scoring remains intentionally unavailable until a separately approved model/deployment milestone.
