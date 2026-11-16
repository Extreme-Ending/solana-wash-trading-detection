# Secure deployment architecture

## Current decision

**NO-GO for live deployment.** Phase 8E proposes an architecture but creates no resource, changes no IAM policy, publishes no frontend and enables no model. The existing production fail-closed behaviour remains mandatory.

The unresolved conflict is architectural: a Firebase-hosted static browser can present a Firebase user ID token, but it cannot mint the Google-signed service identity token required by an IAM-private Cloud Run service. Firebase application authentication and Cloud Run Invoker IAM solve different layers.

## Options assessed

| Option | Advantages | Risks/limitations | Assessment |
|---|---|---|---|
| Public Cloud Run platform endpoint; FastAPI verifies Firebase token and UID | Lowest component count; normal SPA calls | Invalid traffic reaches the service; per-instance limiter is not distributed; public core boundary increases abuse/cost exposure | Not recommended without explicit risk acceptance and stronger edge controls |
| Public authentication BFF; IAM-private core API | Browser uses Firebase ID token; core remains private; BFF service account receives only core Invoker | Additional service, cost, logging and failure modes; public BFF still needs abuse controls | **Recommended hosted design** if a browser deployment is required |
| External HTTPS load balancer with IAP/Cloud Armor | Central edge policy and mature abuse controls | Cost/complexity; IAP identity may duplicate or alter the Firebase identity model | Consider only if institutional access/traffic requirements justify it |
| IAM-private core with operator proxy/two-token smoke test | Smallest public attack surface; preserves current private plan | Not a normal end-user browser experience | **Recommended first private pilot posture** |

Google documents that service-to-service Cloud Run calls use a Google-signed ID token and the caller needs `roles/run.invoker`. When both identity planes are needed, `X-Serverless-Authorization` can carry the platform token while `Authorization` carries the application token ([Cloud Run service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service)). Making a service public disables or grants around the Invoker check and is a separate security decision ([Cloud Run public access](https://docs.cloud.google.com/run/docs/authenticating/public)).

## Recommended hosted request path

```text
Firebase Hosting SPA
  -> Google sign-in / Firebase ID token
  -> public authentication BFF (+ Firebase App Check if accepted)
       - verifies signature, issuer, audience, expiry, email/provider,
         revocation/disabled state and approved UID
       - applies request limits and emits privacy-minimised audit events
       - uses its workload service account to mint a core audience token
  -> IAM-private FastAPI core
       X-Serverless-Authorization: <Google service identity token>
       Authorization: Bearer <Firebase user ID token>
       - repeats application identity and UID checks (defence in depth)
       - preserves schema, size, UTC, feature and model gates
```

The current API may remain the private core. A later authorized phase would implement and test the BFF separately; Phase 8E does not do so.

## Identity, revocation and authorization

- The browser receives only Firebase's public web configuration and short-lived user tokens; it never receives a service-account credential.
- Google Application Default Credentials supply runtime identities. No downloaded service-account key is stored.
- The BFF runtime identity receives only `roles/run.invoker` on the core service.
- The core runtime identity needs only the Firebase user-read capability actually required by revoked/disabled-user verification. Google lists `firebaseauth.users.get` in `roles/firebaseauth.viewer`; a reviewed narrower custom role is preferable if operational testing proves it sufficient ([Firebase Authentication IAM](https://docs.cloud.google.com/iam/docs/roles-permissions/firebaseauth)).
- Approved UIDs remain server-side configuration. Verified email/provider checks and revocation checks remain fail-closed. Firebase documents that revocation validation must be explicitly checked ([session management](https://firebase.google.com/docs/auth/admin/manage-sessions)).
- Deployment identities and runtime identities remain separate. Runtime identities receive no Editor, Owner, Artifact Registry administrator or IAM administrator role.

## Network, CORS and routing

- Keep the core Cloud Run service IAM-private and restrict ingress to the selected service path.
- Permit the exact Firebase Hosting custom origin at the BFF; do not use wildcard CORS with credentials.
- The core accepts calls only from the BFF/operator identity. Browser CORS is unnecessary there.
- Preserve request-body limits, strict content types, UTC scoring rules, feature registry checks and production experimental-model refusal.
- Firebase Hosting rewrites preserve the request path. Any future `/api/**` rewrite must be matched by the BFF/router or explicitly strip the prefix; the existing `/v1/**` core routes must not be assumed to match automatically ([Hosting configuration](https://firebase.google.com/docs/hosting/full-config)).

## Secrets, privacy and auditability

- Treat Firebase web configuration as public configuration, not a secret. Keep server allowlists and environment-specific identifiers outside the built frontend.
- Use Secret Manager only for a genuine server secret introduced later, with accessor permission scoped to the consuming runtime identity.
- Never log bearer tokens, raw event payloads or full wallet histories. Record request ID, endpoint, decision code, model/config fingerprint, bounded latency and a pseudonymised or truncated principal only where justified.
- Set retention and access policies before live traffic. Audit IAM, deploys, configuration revisions and authorized/denied requests without claiming blockchain identity attribution.

## Abuse and cost controls

The existing in-process rate limit is useful locally but is neither distributed nor able to reject traffic before instance work. A public BFF needs a shared quota/rate-control strategy and bounded payload/concurrency/max-instance settings. Firebase App Check can provide app-attestation defence and the Admin SDK supports replay-protected consumption, but it is not user authorization or a universal cost cap ([App Check custom backend](https://firebase.google.com/docs/app-check/custom-resource-backend)). Roll it out in observe mode before enforcement and grant its verifier permission only if consumption is enabled.

Use billing alerts for the whole project and separately evaluate the current Cloud Run spend-cap feature. Google documents eligible-service limitations, project/service scope and delayed enforcement; it does not cap Firebase Hosting, Artifact Registry, Logging and every other service as one universal control ([Cloud Run spend caps](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps)). Retain max instances, request-based billing, log controls and a documented shutdown owner.

## Private pilot acceptance gate

Before any separately authorized mutation:

1. verify project/site ownership, billing state, region support and required APIs without creating them;
2. review named deployer, BFF and core service accounts and exact bindings;
3. tag images with full Git SHA and verify source/artifact/manifest hashes;
4. deploy the core privately with the Invoker check intact and experimental scoring disabled;
5. use a synthetic payload and separate short-lived platform/application tokens for health, 401, 403 and model-gate checks;
6. inspect logs for credential/payload leakage and confirm rollback to a named prior revision;
7. stop before public routing; and
8. require a separate architecture, cost and data-use decision before BFF/Hosting publication.

No item above is claimed complete from local tests.
