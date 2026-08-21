# infrastructure/

Deployment and cloud infrastructure for SwarmOps on Google Cloud (P12).

- `terraform/` — Terraform for enabled APIs, Artifact Registry, Firestore (native),
  Pub/Sub topics (one per domain event), a least-privilege service account + IAM,
  a Secret Manager secret, and two Cloud Run services (API + Web).
- `deploy.sh` — a gcloud-only alternative that builds, pushes, and deploys both services.

See [`docs/deployment/google-cloud.md`](../docs/deployment/google-cloud.md) for the full
walkthrough (build, secrets, env vars, Firestore emulator, and verification).

No credentials are committed here. Secrets live in Secret Manager and are referenced by
Cloud Run at deploy time.
