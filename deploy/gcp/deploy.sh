#!/usr/bin/env bash
# One-shot GCP bootstrap + deploy for the backend (frontend excluded).
#
# Prerequisites: gcloud CLI authenticated, billing enabled.
#
# Usage:
#   export GOOGLE_CLOUD_PROJECT=your-project
#   export GCP_REGION=us-central1
#   # optionally: set SECRET_KEY, POSTGRES_PASSWORD, REDIS password, API keys
#   bash deploy/gcp/deploy.sh
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
REGION="${GCP_REGION:-us-central1}"
REPO="${ARTIFACT_REGISTRY_REPO:-multi-agent}"
SQL_INSTANCE="${CLOUD_SQL_INSTANCE:-multi-agent-pg}"
SERVICE="${CLOUD_RUN_SERVICE:-multi-agent-api}"
WORKER_SERVICE="${CLOUD_RUN_WORKER_SERVICE:-multi-agent-worker}"
DB_NAME="${POSTGRES_DB:-multi_agent_db}"
DB_USER="${POSTGRES_USER:-multi_agent_user}"
DB_PASS="${POSTGRES_PASSWORD:-$(openssl rand -base64 24)}"
SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 48)}"
JWT_SECRET="${JWT_SECRET:-$(openssl rand -base64 32)}"

echo "==> Project=${PROJECT_ID} region=${REGION}"

gcloud config set project "${PROJECT_ID}"

echo "==> Enabling APIs"
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  vpcaccess.googleapis.com \
  redis.googleapis.com \
  --quiet

echo "==> Artifact Registry"
if ! gcloud artifacts repositories describe "${REPO}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Multi-agent backend images"
fi

echo "==> Cloud SQL (PostgreSQL 15)"
if ! gcloud sql instances describe "${SQL_INSTANCE}" >/dev/null 2>&1; then
  gcloud sql instances create "${SQL_INSTANCE}" \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region="${REGION}" \
    --storage-size=20GB \
    --storage-auto-increase \
    --availability-type=ZONAL \
    --quiet
  gcloud sql databases create "${DB_NAME}" --instance="${SQL_INSTANCE}" || true
  gcloud sql users create "${DB_USER}" --instance="${SQL_INSTANCE}" --password="${DB_PASS}" || \
    gcloud sql users set-password "${DB_USER}" --instance="${SQL_INSTANCE}" --password="${DB_PASS}"
else
  echo "Cloud SQL instance already exists; not rotating password automatically."
fi

CONNECTION_NAME="${PROJECT_ID}:${REGION}:${SQL_INSTANCE}"
DATABASE_URL="${DATABASE_URL:-postgresql://${DB_USER}:${DB_PASS}@/${DB_NAME}}"

echo "==> IAM for Cloud Run runtime (Secret Manager + Cloud SQL)"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
RUNTIME_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/secretmanager.secretAccessor" \
  --quiet >/dev/null || true
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/cloudsql.client" \
  --quiet >/dev/null || true

echo "==> Writing secrets to Secret Manager"
export SECRET_KEY DATABASE_URL JWT_SECRET
export ALLOWED_HOSTS="${ALLOWED_HOSTS:-.run.app}"
export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-}"
export CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-}"
export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
export CELERY_BROKER_URL="${CELERY_BROKER_URL:-${REDIS_URL}}"
export CELERY_RESULT_BACKEND="${CELERY_RESULT_BACKEND:-${CELERY_BROKER_URL}}"
export GROQ_API_KEY="${GROQ_API_KEY:-}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-}"
bash "$(dirname "$0")/setup-secrets.sh"

echo "==> Cloud Build + Cloud Run deploy"
gcloud builds submit \
  --config=deploy/gcp/cloudbuild.yaml \
  --substitutions=_REGION="${REGION}",_REPO="${REPO}",_SERVICE="${SERVICE}",_WORKER_SERVICE="${WORKER_SERVICE}",_SQL_INSTANCE="${SQL_INSTANCE}"

API_URL="$(gcloud run services describe "${SERVICE}" --region="${REGION}" --format='value(status.url)')"
echo ""
echo "Backend API deployed: ${API_URL}"
echo "Health: ${API_URL}/health/live/"
echo ""
echo "IMPORTANT:"
echo "  1. Point REDIS_URL at Memorystore (or a Redis VM) and re-run setup-secrets.sh + redeploy."
echo "  2. Update ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS with the Cloud Run hostname:"
echo "       ${API_URL#https://}"
echo "  3. Frontend is not deployed by this script."
echo "  4. Save DB password if generated this run: (shown only if you set POSTGRES_PASSWORD yourself)"
