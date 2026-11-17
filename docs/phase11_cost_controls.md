# Phase 11 cost-control assessment

## Observed state

Billing is disabled for `solana-wallet-risk`, so the image was not pushed and no Cloud Run, Artifact Registry, build or new logging resource was created. Phase 11 therefore incurred no observed cloud deployment usage. Local Docker work is outside Google Cloud billing.

No billing account was available to query for budgets, alerts or spend-cap eligibility. Their absence must not be interpreted as configured protection.

## Planned conservative limits

| Control | Planned value |
|---|---|
| Region | `africa-south1` |
| Minimum instances | 0 |
| Maximum instances | 1 |
| CPU | 1 |
| Memory | 512 MiB |
| Concurrency | 20 |
| Request timeout | 30 seconds |
| GPU | None |
| Artifact retention | Existing policy: delete versions older than 30 days while keeping 3 recent versions |

Scale-to-zero avoids instance charges while no instance is running under the applicable Cloud Run billing model, although requests, networking, logs, builds and stored images can still incur charges. See [Cloud Run pricing](https://cloud.google.com/run/pricing).

## Budget safeguards still required

1. Assign an accountable billing owner before attaching billing.
2. Configure a low project budget with multiple alert thresholds and tested recipients.
3. Check current spend-cap eligibility separately. Google states that ordinary alert-only budgets do not automatically cap spending ([Cloud Billing budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets)).
4. Review the separate spend-cap feature and its customer/service eligibility; do not assume it covers Firebase Hosting, Artifact Registry, Logging or every project service ([spend-cap budgets](https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps)).
5. Apply the Artifact Registry cleanup policy first in dry-run mode and review matches before enforcement ([Artifact Registry cleanup policies](https://docs.cloud.google.com/artifact-registry/docs/repositories/cleanup-policy)).
6. Monitor Cloud Run request count, instance count, latency, errors, image storage, build minutes and log ingestion after the first synthetic test.

Maximum instances bounds concurrency-driven scale but is not a monetary hard cap. Billing disablement is the present deployment blocker, not a recommended operating control.
