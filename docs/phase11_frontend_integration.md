# Phase 11 frontend integration assessment

## Status

**Blocked; no frontend cloud configuration or hosting release was made.** There is no Cloud Run service URL, and the planned initial service is IAM-private.

## Existing implementation

The React application uses the official Firebase Web SDK for Google sign-in and obtains the signed-in user's Firebase ID token. The API client sends that application token as `Authorization: Bearer ...`. The frontend handles authentication loading, sign-in/sign-out, and 401, 403 and 503 responses. Production configuration is environment-based and contains public Firebase Web identifiers only.

The local Firebase project ID and selected CLI project both resolve to `solana-wallet-risk`. The production bundle validator passed. No private service-account key, server UID allowlist or bearer token was added to the bundle.

## Why direct browser integration remains blocked

Cloud Run IAM and Firebase application authentication are separate identity layers. An IAM-private Cloud Run service requires a Google-signed invoker ID token. The browser currently has a Firebase user ID token for FastAPI, not a Cloud Run invoker token. Replacing the application token with a platform token would also remove the Firebase identity FastAPI is required to verify.

Cloud Run supports carrying the platform token in `X-Serverless-Authorization` while leaving `Authorization` for application authentication, but a static public SPA must not receive service-account credentials to mint the platform token. See [Cloud Run service-to-service authentication](https://docs.cloud.google.com/run/docs/authenticating/service-to-service).

## Secure integration paths

1. Keep the core IAM-private and add a separately reviewed authentication backend-for-frontend. The browser sends its Firebase token to the BFF; the BFF uses a workload identity to invoke the private core.
2. Separately approve a browser-reachable Cloud Run endpoint while retaining mandatory Firebase verification, server allowlisting, exact CORS, request/rate controls, monitoring and a shutdown plan.

Phase 11 did not implement either architectural change. It did not make Cloud Run public, deploy Firebase Hosting, alter Firebase domains, or weaken authentication.

## Acceptance still required

- actual service URL and exact CORS origin;
- real Google sign-in from the hosted origin;
- Firebase token forwarding and refresh/expiry handling;
- 401, 403, 429 and 503 browser behavior;
- authorized preview and disabled scoring;
- session expiry and sign-out;
- bundle rescan; and
- browser and server logs checked for token/payload leakage.
