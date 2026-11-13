# Firebase Hosting configuration

## Prepared static site

`firebase.json` publishes `frontend/dist`, which is Vite's actual production output. It provides a catch-all rewrite to `/index.html` for client-side SPA routes and does not configure Cloud Run rewrites, Functions, Firestore, or automatic deployment. Phase 7B adds the official Firebase Web SDK in source for Authentication, but creates or enables no Firebase resource.

Caching is split by mutability:

- `/index.html`: `no-cache, no-store, must-revalidate`, so a client rechecks the entry point after a release;
- `/assets/**`: one-year immutable caching, appropriate for Vite's content-hashed filenames; and
- all paths: `nosniff`, clickjacking denial, strict referrer handling, a restrictive permissions policy, and same-origin opener isolation.

The repository contains `.firebaserc.example` with only `YOUR_GCP_PROJECT_ID`. A real `.firebaserc` is ignored. The Firebase configuration contains no data files, credentials, project ID, deployment trigger or backend secret. Firebase documents the available [headers, redirects and rewrites](https://firebase.google.com/docs/hosting/full-config) and [cache-control behavior](https://firebase.google.com/docs/hosting/manage-cache).

## Production build

The browser-visible API origin and Firebase Web values are configuration, never Admin credentials. `VITE_API_BASE_URL` must be the exact HTTPS Cloud Run origin without a path. The Web API key identifies the Firebase project and should have appropriate API restrictions, but it cannot authorize protected API access; the signed ID token and backend allowlist do that.

```bash
cp frontend/.env.production.example frontend/.env.production.local
# Replace the placeholder locally; never add credentials.
cd frontend
npm ci
VITE_API_BASE_URL=https://YOUR_CLOUD_RUN_SERVICE_HOST npm run typecheck
VITE_API_BASE_URL=https://YOUR_CLOUD_RUN_SERVICE_HOST npm test -- --run
VITE_API_BASE_URL=https://YOUR_CLOUD_RUN_SERVICE_HOST npm run build
cd ..
python3 scripts/validate_deployment_bundle.py frontend/dist
```

The student-operated equivalent, after exporting the reviewed deployment variables, is:

```bash
./scripts/deployment.sh build-frontend --execute
```

It requires interactive confirmation even though it only builds locally. The validator rejects raw CSV, model artifacts, private instructions, private-key signatures and common credential signatures. The generated directory is Git-ignored.

## Future Firebase setup and deployment

These commands are examples for later student execution; none ran in Phase 7A:

```bash
npm install --global firebase-tools
firebase login
firebase projects:list
firebase use --add YOUR_GCP_PROJECT_ID
firebase hosting:sites:list --project YOUR_GCP_PROJECT_ID
./scripts/deployment.sh deploy-firebase --execute
```

The project must already have a Firebase Hosting site and Web app with Google sign-in configured. Verify its actual site ID and authorized authentication domains before building. If the site ID differs from the project ID, set `FIREBASE_ORIGINS` to that site's matching `https://SITE_ID.web.app,https://SITE_ID.firebaseapp.com` origins before backend deployment. Add only reviewed Google-account UIDs to the backend allowlist. The deployment action validates `frontend/dist`, displays the project/region/effect, and runs `firebase deploy --only hosting --project PROJECT_ID` only after the exact confirmation. The deployer needs the predefined Firebase Hosting Admin role only for the deployment task; do not grant it to the Cloud Run runtime identity.

## Routing and access limitation

Direct API-origin routing preserves the existing paths and avoids a duplicate `/api`. The local proxy still converts local `/api/*` calls to the loopback API. In production, the build uses the bare API origin and the client calls the native paths directly.

A Firebase ID token authenticates the end user to FastAPI but does not grant `roles/run.invoker` or satisfy Cloud Run's platform IAM check. A successful static deployment would therefore show sign-in controls, but protected API calls would still be blocked at private Cloud Run before reaching FastAPI. This remains an explicit deployment blocker, not an error to bypass with anonymous invocation without a separately approved access design.

## Hosting cleanup

After confirming the intended project, the student can disable Hosting in a later cleanup window:

```bash
firebase hosting:disable --project YOUR_GCP_PROJECT_ID
```

This is included in the guarded `cleanup` action. Hosting usage and quotas must be reviewed before deployment; the [Firebase Hosting usage page](https://firebase.google.com/docs/hosting/usage-quotas-pricing) describes current no-cost allowances and paid-plan behavior. No zero-cost outcome is guaranteed.
