#!/usr/bin/env bash
# SwarmOps — build, push, and deploy to Cloud Run (gcloud alternative to Terraform).
# Usage: PROJECT_ID=my-project REGION=us-central1 ./infrastructure/deploy.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-us-central1}"
REPO="swarmops"
REG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"

echo "==> Enabling APIs"
gcloud services enable run.googleapis.com firestore.googleapis.com pubsub.googleapis.com \
  secretmanager.googleapis.com artifactregistry.googleapis.com cloudtrace.googleapis.com \
  aiplatform.googleapis.com --project "${PROJECT_ID}"

echo "==> Ensuring Artifact Registry repo"
gcloud artifacts repositories describe "${REPO}" --location "${REGION}" --project "${PROJECT_ID}" \
  >/dev/null 2>&1 || gcloud artifacts repositories create "${REPO}" \
  --repository-format=docker --location "${REGION}" --project "${PROJECT_ID}"

echo "==> Building + pushing images (Cloud Build)"
gcloud builds submit apps/api --tag "${REG}/api:latest" --project "${PROJECT_ID}"
gcloud builds submit apps/web --tag "${REG}/web:latest" --project "${PROJECT_ID}"

echo "==> Deploying API (Cloud Run, scale-to-zero)"
gcloud run deploy swarmops-api --image "${REG}/api:latest" --region "${REGION}" \
  --platform managed --allow-unauthenticated --min-instances 0 --max-instances 4 \
  --memory 512Mi --port 8080 --project "${PROJECT_ID}" \
  --set-env-vars "ENVIRONMENT=production,PERSISTENCE_BACKEND=firestore,EVENT_BUS=pubsub,GOOGLE_CLOUD_PROJECT=${PROJECT_ID},GOOGLE_GENAI_USE_VERTEXAI=true,GEMINI_MODEL=gemini-3.5-flash,OTEL_ENABLED=true"

API_URL="$(gcloud run services describe swarmops-api --region "${REGION}" --project "${PROJECT_ID}" --format 'value(status.url)')"
echo "    API_URL=${API_URL}"

echo "==> Deploying Web (Cloud Run)"
gcloud run deploy swarmops-web --image "${REG}/web:latest" --region "${REGION}" \
  --platform managed --allow-unauthenticated --min-instances 0 --max-instances 4 \
  --port 3000 --project "${PROJECT_ID}" \
  --set-env-vars "NEXT_PUBLIC_API_URL=${API_URL}"

echo "==> Done. Web:"
gcloud run services describe swarmops-web --region "${REGION}" --project "${PROJECT_ID}" --format 'value(status.url)'
