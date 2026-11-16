# Phase 9 validation results

## Result

All feasible local regression, reproducibility, integration, security, frontend and container checks passed. A real Firebase sign-in and protected browser request were not executed because that requires a student-operated approved account/ADC session; no credential was requested or bypassed.

## Automated suites

| Command | Observed result |
|---|---|
| `MPLCONFIGDIR=/tmp/mpl-phase9-tests .venv/bin/python -m pytest -q` | **205 passed** in 15.32 s |
| Final full Python rerun after SVG normalization | **205 passed** in 13.08 s |
| `npm test -- --run` | **10 files, 72 tests passed** |
| `npm run typecheck` | Passed |
| `VITE_API_BASE_URL=https://api.example.invalid npm run build` | Passed; 49 modules transformed |
| Focused feature/model/API/auth/deployment/container/figure pytest set | **146 passed** in 12.06 s |
| `bash -n scripts/deployment.sh commit.sh` | Passed; neither script was executed as a workflow |
| Python compilation of validation/figure scripts | Passed |

The three new figure tests establish byte-deterministic output, reject `labels_used=true`, and reject an evaluation whose artifact fingerprint differs from the model manifest.

## Pipeline reproducibility

Two independent temporary runs each executed audit, preprocessing, three-cutoff feature construction and anomaly training. Both observed:

- 10,800 input events;
- 10,798 retained and two quarantined;
- 5,996 wallet snapshots;
- no labels or confirmed outcomes; and
- the registered 29-feature contract.

Every paired output was byte-identical by `cmp`, and the regenerated snapshot/artifact/manifest matched the current local files:

| Output | SHA-256 |
|---|---|
| Audit JSON | `c32090b1df2bbaf36243b5031c2ae075ef0467daeae64a41d8350315e1739c36` |
| Cleaned events | `1889adf72a727544a8759203336ac257108d344e2ea71aaa118aa04f0aa50937` |
| Quarantine | `5cab1d4860e5ab2345979085cada6e3a583933f132875209309cb1fe84e9eb38` |
| Wallet snapshots | `779b446b15cce9cdc630353c60ffad2bfae039b086a1e0daa8dd66d05aff3a60` |
| Model artifact | `3e35561b0bf5db42c5b7146e7ff568e313be1beb1be724997356af45f5533035` |
| Model manifest | `1551d55f469ac3abd7a985d98055c69375968a2d9e28151e153aea2b61061ad0` |

## Research evidence package

The ignored evaluation report was regenerated against the current artifact, replacing its stale Phase 8B fingerprint. Its current SHA-256 is `d37426a7bc8ab478b165af7c84263283c91e46a2148bc82b146245b87383b145`.

`scripts/generate_phase9_figures.py` generated five SVG figures, three CSV tables and a manifest. A second independent output directory was byte-identical for every figure, table and manifest. The manifest states `labels_used=false`, records no confirmed outcomes and binds all four report/manifest inputs by SHA-256.

A headless Chrome render of the holdout-agreement SVG showed readable axes, color scale and the correct `0.049`, `0.866` and `-0.019` values. This was visual-format validation, not new experimental evidence.

## FastAPI and scoring contract

`PYTHONPATH=src .venv/bin/python scripts/audit_local_integration.py` passed with the current real artifact:

| Check | Status |
|---|---:|
| Health | 200 |
| Readiness | 503 |
| Missing/invalid/expired authentication | 401 |
| Feature preview | 200 |
| Batch scoring | 200 |
| Single scoring | 200 for each synthetic history |
| Production score | 503 |
| Feature order/count | Exact 29-field contract |
| Single/batch equivalence | Exact |

The verifier was injected only inside the audit process. Firebase was not contacted. The script returned synthetic scores `0.650997`, `0.559608` and `0.444146`; these prove wiring only.

The separate deterministic batch script passed with model version 4B.1, repeated identical output, exact single/batch equality and `is_probability=false`. Its different synthetic fixture produced `0.711229`, `0.524491` and `0.451791`; it is not a research validation cohort.

## Frontend and browser validation

The frontend suite covers authentication states, schema guards, feature preview, score gating, batch ranking, filters, sorts, details, reference comparisons, errors and scientific wording. The updated overview and evidence panel were included in the full tests and production build.

Vite was started on loopback and headless Chrome rendered a 1440×1800 local view. The timed render visibly contained:

- the corrected “Features and gated anomaly scores” / “Experimental local mode only” boundary;
- service and model capability gates;
- the new observation/model evidence panel; and
- no probability or confirmed-fraud wording.

An initial screenshot taken immediately after navigation captured only the background before React mounted. Repeating with a five-second virtual-time budget rendered correctly; this was capture timing, not a persistent UI failure. The session did not complete Google sign-in or a protected browser call.

## Deployment bundle and container

| Command/check | Observed result |
|---|---|
| `scripts/validate_deployment_bundle.py frontend/dist` | Passed; four files scanned |
| `docker compose config --quiet` | Passed |
| `docker build -t solana-wallet-risk-api:phase9 .` | Passed |
| Container smoke on loopback 18086/18087 | Passed |

The smoke test verified API import/image content, configured user `10001:10001`, runtime UID 10001, health 200, readiness 503, unauthenticated protected routes 401, configured internal port 9090 and graceful exit 0. The image is `sha256:93b9f66a96b31dc549595914620a824222566f2f36371267f318aafb5cc4248b`, 415,754,874 bytes. Experimental model artifacts and modelling dependencies remain outside the production image.

## Security conclusion

Authentication, authorization, request limits, UTC/cutoff validation, CORS validation, artifact pinning, feature parity and production fail-closed behavior remain effective under local automated checks. This does not establish distributed rate limiting, hosted Firebase acceptance, platform IAM routing, live logging/privacy behavior or production readiness.
