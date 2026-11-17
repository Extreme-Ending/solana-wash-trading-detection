# Phase 11 cloud security assessment

## Result

The local security controls passed, but cloud security is **not accepted** because no runtime service, IAM policy or live endpoint exists. The deployment remained private-by-design and no public invoker binding was added.

## Controls verified locally

- non-root runtime UID/GID `10001:10001`;
- pinned production base-image digest;
- raw data, model artifacts, reports, tests, local environments and private instructions excluded from the image context;
- exact CORS configuration with wildcard rejection;
- request-byte and event-count limits;
- strict UTC and registered-feature validation;
- Firebase issuer, audience, signature, expiry, verified-email and project checks in the application test suite;
- server-side approved UID enforcement and revocation checks configured fail-closed for production;
- production API documentation disabled;
- missing, malformed and expired credentials rejected;
- scoring remains unavailable with `MODEL_NOT_APPROVED`; and
- no credential or service-account key in source or frontend output.

## Planned identity boundary

The deployer identity, Cloud Run runtime identity and end-user Firebase identity must remain separate. The planned runtime account is `solana-wallet-risk-runtime@solana-wallet-risk.iam.gserviceaccount.com`; it does not yet exist. It should receive only the user-read capability required for Firebase revoked/disabled-user validation, not Owner, Editor, Cloud Run Admin or Artifact Registry Admin.

The private service's invoker IAM check must remain enabled. Operator smoke tests should carry the short-lived Google platform token in `X-Serverless-Authorization` and the approved user's Firebase token in `Authorization`. No long-lived service-account key is needed. Google recommends service identity/Application Default Credentials rather than setting `GOOGLE_APPLICATION_CREDENTIALS` on Cloud Run ([Cloud Run service identity](https://docs.cloud.google.com/run/docs/securing/service-identity)).

## Security checks not completed

- exact deployer permissions and ability to act as the runtime account;
- runtime Firebase user-read permission;
- live 401/403 negative cases and approved-user request;
- live CORS preflight from the hosted origin;
- platform IAM rejection without an invoker token;
- Cloud Audit/Run log review and retention;
- revision environment inspection;
- image registry vulnerability/provenance review; and
- rollback authorization.

No cloud logs existed to inspect, so no claim is made about live credential or payload leakage.

## Claim boundary

Anomaly scores are not calibrated fraud probabilities, verified wash-trading labels or legal findings. The absent independent labels and counterparty evidence remain unchanged by deployment work.
