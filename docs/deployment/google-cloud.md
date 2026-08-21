# Deploying SwarmOps to Google Cloud

SwarmOps runs its backend and console on **Cloud Run**, persists state in **Firestore**,
publishes domain events to **Pub/Sub**, explains governance decisions with **Gemini via
Vertex AI**, and exports traces to **Cloud Trace**. Everything scales to zero, so a demo
deployment costs almost nothing when idle.

> Local development never needs any of this — the default backend is SQLite with an
> in-memory event bus. These steps are for a cloud deployment (proof for judging).

> **⚠️ Ingress note.** The hackathon demo deployment uses **public Cloud Run ingress**
> (`--allow-unauthenticated`) for judge accessibility. **Production deployments require
> authenticated ingress and role-based access control** — set
> `allow_unauthenticated = false` in Terraform (or omit `--allow-unauthenticated`) and
> front the services with IAP / an identity-aware proxy.

## Prerequisites

- `gcloud` CLI authenticated (`gcloud auth login`) and a billing-enabled project
- Docker (only if building locally instead of Cloud Build)
- A project id, e.g. `export PROJECT_ID=my-swarmops` and `export REGION=us-central1`

## Option A — one script (gcloud)

```bash
PROJECT_ID=$PROJECT_ID REGION=$REGION ./infrastructure/deploy.sh
```

This enables the APIs, creates the Artifact Registry repo, builds + pushes both images
with Cloud Build, and deploys `swarmops-api` and `swarmops-web` to Cloud Run
(scale-to-zero). It prints the public URLs at the end.

## Option B — Terraform

```bash
cd infrastructure/terraform
terraform init
terraform apply \
  -var project_id=$PROJECT_ID \
  -var region=$REGION \
  -var api_image=$REGION-docker.pkg.dev/$PROJECT_ID/swarmops/api:latest \
  -var web_image=$REGION-docker.pkg.dev/$PROJECT_ID/swarmops/web:latest
```

Build + push the images first (see below), then `terraform apply`. Terraform provisions
the APIs, Artifact Registry, Firestore (native), the seven Pub/Sub topics, a
least-privilege service account + IAM, a Secret Manager secret, and both Cloud Run
services. Outputs include `api_url` and `web_url`.

### Build + push images manually

```bash
REG=$REGION-docker.pkg.dev/$PROJECT_ID/swarmops
gcloud builds submit apps/api --tag $REG/api:latest
gcloud builds submit apps/web --tag $REG/web:latest
```

## Secrets

Never commit secrets. Create them in Secret Manager and reference them from Cloud Run:

```bash
printf '%s' "$(openssl rand -hex 32)" | \
  gcloud secrets create swarmops-jwt-secret --data-file=- --project $PROJECT_ID

# Then attach at deploy time:
gcloud run services update swarmops-api --region $REGION \
  --set-secrets JWT_SECRET=swarmops-jwt-secret:latest
```

For a Gemini Developer API key (instead of Vertex AI) store `swarmops-gemini-key`
similarly and set `--set-secrets GEMINI_API_KEY=swarmops-gemini-key:latest` plus
`GOOGLE_GENAI_USE_VERTEXAI=false`.

## Environment variables (Cloud Run)

| Variable | Value in cloud |
|----------|----------------|
| `PERSISTENCE_BACKEND` | `firestore` |
| `EVENT_BUS` | `pubsub` |
| `GOOGLE_CLOUD_PROJECT` | your project id |
| `GOOGLE_GENAI_USE_VERTEXAI` | `true` (or `false` + `GEMINI_API_KEY`) |
| `GEMINI_MODEL` | `gemini-3.5-flash` |
| `OTEL_ENABLED` | `true` |
| `MODEL_ARMOR_ENABLED` | `true` to use Model Armor (needs the client + access) |
| `NEXT_PUBLIC_API_URL` (web) | the API's Cloud Run URL |

## Firestore emulator (local testing of the adapter)

```bash
gcloud emulators firestore start --host-port=localhost:8081
export FIRESTORE_EMULATOR_HOST=localhost:8081
export PERSISTENCE_BACKEND=firestore GOOGLE_CLOUD_PROJECT=demo
pip install -e "apps/api[gcp]"
uvicorn app.main:app --port 8080   # seeds the emulator on first run
```

## Verifying it runs on Google Cloud

- Cloud Run: `gcloud run services list` → `swarmops-api`, `swarmops-web` with `.run.app` URLs
- Firestore: the collections (`agents`, `executions`, `audit_events`, …) appear in the console
- Pub/Sub: `gcloud pubsub topics list` shows the seven `swarmops-*` topics
- Cloud Trace: execution traces appear when `OTEL_ENABLED=true`
- Vertex AI: Gemini invocations show in the Vertex AI logs

## Cost control

- Both services use `min-instances 0` (scale to zero).
- Firestore + Pub/Sub have generous free tiers.
- Tear down with `terraform destroy` or `gcloud run services delete swarmops-api swarmops-web`.
