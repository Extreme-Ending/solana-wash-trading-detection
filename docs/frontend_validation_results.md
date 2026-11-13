# Phase 6 frontend validation results

## Scope

Validation covers the React/Vite source, the typed browser/API boundary, frontend interactions, a production build, the existing Python regression suite, and local integration through the Vite proxy to the Phase 5B container. Tests use synthetic values only and do not train, load, promote, or score a model.

## Automated frontend coverage

The Vitest and React Testing Library suite covers:

1. deterministic synthetic request construction;
2. UTC cutoff validation;
3. duplicate rows, unsupported fields, and invalid amounts;
4. complete-payload import and mixed-wallet rejection;
5. safe API-base configuration;
6. expected readiness HTTP 503 handling;
7. exact 29-feature response acceptance;
8. feature-order/schema-drift rejection;
9. inconsistent preview-metadata rejection;
10. rejection of unexpected successful scoring output;
11. network-error handling;
12. synthetic form submission and wallet propagation;
13. client-side failure without an API call;
14. backend failure without fabricated output;
15. display of all registered features, including null-versus-zero behavior;
16. accessible chart alternatives;
17. disabled and expected-unavailable scoring gates; and
18. full application rendering, service-state separation, navigation, research boundaries, and end-to-end preview rendering with a mocked API.

## Commands and observed results

The final command results are recorded here after execution:

| Check | Result |
|---|---|
| `npm ci --no-audit` | Passed: clean lockfile installation added 100 packages |
| `npm run typecheck` | Passed: TypeScript project build completed with no errors |
| `npm test` | Passed: 22 tests in 6 files |
| `npm run build` | Passed: Vite transformed 30 modules; generated 0.62 kB HTML, 11.50 kB CSS and 253.18 kB JavaScript before gzip |
| `.venv/bin/python -m pytest -q` | Passed: 131 tests |
| Vite-to-container HTTP integration | Passed: frontend 200; proxied health 200; readiness 503; one-event preview 200 with all 29 features; scoring 503 with no score field |

## Manual/contract review checklist

- The interface labels the records as Solana DEX swap events and does not imply NFT-sale evidence.
- The synthetic example is visibly and structurally synthetic.
- Health and model readiness are reported separately.
- A readiness/scoring 503 is represented as expected unavailability.
- There is no fake score, probability, prediction, label, threshold, or performance metric.
- All 29 fields come from the API response and follow the registered order.
- The browser does not persist events or contact an external provider.
- Local runtime configuration contains no secret.
- Layout, focus states, semantic labels, live messages, null display, and chart alternatives have dedicated implementation or test coverage.

## Remaining validation boundary

The tests establish frontend behavior and contract compatibility, not the authenticity or completeness of user-supplied events and not the correctness of any fraud claim. Browser/device usability beyond the tested responsive CSS and jsdom interaction suite remains a manual review activity. No hosted Firebase or Cloud Run environment was created or tested.

The temporary Vite server, Docker container, and Compose network used for the real HTTP check were stopped and removed after validation. The local image cache was not pushed or published.

## Phase 7B authentication revalidation

Phase 7B expands the suite to 35 tests in 8 files. New coverage includes missing production Firebase Web configuration, malformed project/domain configuration, auth-state sign-in/sign-out transitions, safe accessible popup errors, no-token local rejection, Bearer-header attachment only on protected requests, 401/403/authentication-503 handling, and signed-out control states. TypeScript checking and the production build pass with the pinned Firebase Web SDK; the resulting bundle contains 0.62 kB HTML, 12.16 kB CSS, and 355.25 kB JavaScript before gzip. The static bundle validator passes with public Firebase configuration and rejects service-account credential signatures. `npm audit --omit=dev` reports zero production vulnerabilities.

No live Google popup or Firebase project was used. Browser SDK integration is established by deterministic gateway tests; real authorized-domain, popup, token refresh, and hosted-device behavior remain Phase 7C/manual prerequisites.
