#!/usr/bin/env bash
# Deploy API + Celery worker to Cloud Run.
# Postgres = Neon/Supabase, Redis = Upstash, Frontend = Vercel (separate).
#
# Prerequisites:
#   - gcloud auth login && billing enabled
#   - Neon/Supabase DATABASE_URL (pooled, sslmode=require)
#   - Upstash REDIS_URL (rediss://...)
#   - deploy/gcp/.env.cloudrun filled in (from .env.cloudrun.example)
#
# Usage:
#   bash deploy/gcp/deploy-cloudrun.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT/deploy/gcp/.env.cloudrun}"

if [ -f "${ENV_FILE}" ]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
  echo "==> Loaded ${ENV_FILE}"
else
  echo "Missing ${ENV_FILE}"
  echo "Copy deploy/gcp/.env.cloudrun.example → deploy/gcp/.env.cloudrun and fill values."
  exit 1
fi

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT in .env.cloudrun}"
REGION="${GCP_REGION:-us-central1}"
REPO="${ARTIFACT_REGISTRY_REPO:-multi-agent}"
SERVICE="${CLOUD_RUN_SERVICE:-multi-agent-api}"
WORKER_SERVICE="${CLOUD_RUN_WORKER_SERVICE:-multi-agent-worker}"

: "${SECRET_KEY:?Set SECRET_KEY}"
: "${DATABASE_URL:?Set DATABASE_URL (Neon/Supabase pooled URL)}"
: "${REDIS_URL:?Set REDIS_URL (Upstash rediss:// URL)}"

# Upstash: default Celery to same Redis URL
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-$REDIS_URL}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-$CELERY_BROKER_URL}"
export JWT_SECRET="${JWT_SECRET:-$SECRET_KEY}"
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-.run.app}"

echo "==> Project=${PROJECT_ID} region=${REGION}"
gcloud config set project "${PROJECT_ID}"

echo "==> Enabling APIs"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  --quiet

echo "==> Artifact Registry (${REPO})"
if ! gcloud artifacts repositories describe "${REPO}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Multi-agent backend images"
fi

echo "==> IAM (Secret Manager accessor for Cloud Run runtime SA)"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet >/dev/null || true

echo "==> Syncing secrets"
bash "$(dirname "$0")/setup-secrets.sh"

echo "==> Building & deploying (API + worker)"
cd "${ROOT}"
gcloud builds submit \
  --config=deploy/gcp/cloudbuild.yaml \
  --substitutions=_REGION="${REGION}",_REPO="${REPO}",_SERVICE="${SERVICE}",_WORKER_SERVICE="${WORKER_SERVICE}",_MIN_INSTANCES=0,_MAX_INSTANCES=1,_WORKER_MIN_INSTANCES=0,_WORKER_MAX_INSTANCES=1

API_URL="$(gcloud run services describe "${SERVICE}" --region="${REGION}" --format='value(status.url)')"
API_HOST="${API_URL#https://}"

echo ""
echo "=============================================="
echo " API:     ${API_URL}"
echo " Health:  ${API_URL}/health/live/"
echo " Worker:  ${WORKER_SERVICE} (Celery)"
echo "=============================================="
echo ""
echo "NEXT STEPS"
echo "1) Update secrets with the real Cloud Run host, then redeploy once:"
echo "     ALLOWED_HOSTS=${API_HOST},.run.app"
echo "     CSRF_TRUSTED_ORIGINS=${API_URL}"
echo "     # edit deploy/gcp/.env.cloudrun then:"
echo "     bash deploy/gcp/setup-secrets.sh"
echo "     gcloud builds submit --config=deploy/gcp/cloudbuild.yaml --substitutions=_REGION=${REGION},_REPO=${REPO},_SERVICE=${SERVICE},_WORKER_SERVICE=${WORKER_SERVICE}"
echo ""
echo "2) Vercel env vars:"
echo "     NEXT_PUBLIC_API_URL=${API_URL}"
echo "     NEXT_PUBLIC_WS_URL=wss://${API_HOST}"
echo ""
echo "3) Ensure FRONTEND_URL / CORS_ALLOWED_ORIGINS = your Vercel URL in .env.cloudrun"
echo ""
