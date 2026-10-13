#!/usr/bin/env bash
# Push env values into GCP Secret Manager for Cloud Run.
#
#   export GOOGLE_CLOUD_PROJECT=your-project
#   set -a && source deploy/gcp/.env.cloudrun && set +a
#   bash deploy/gcp/setup-secrets.sh
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
gcloud config set project "${PROJECT_ID}"

create_or_update() {
  local name="$1"
  local value="${2:-}"
  if [ -z "${value}" ]; then
    value="unset"
  fi
  if gcloud secrets describe "${name}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo -n "${value}" | gcloud secrets versions add "${name}" --data-file=-
    echo "Updated ${name}"
  else
    echo -n "${value}" | gcloud secrets create "${name}" --data-file=- --replication-policy=automatic
    echo "Created ${name}"
  fi
}

create_or_update "django-secret-key" "${SECRET_KEY:-}"
create_or_update "database-url" "${DATABASE_URL:-}"
create_or_update "redis-url" "${REDIS_URL:-}"
create_or_update "celery-broker-url" "${CELERY_BROKER_URL:-${REDIS_URL:-}}"
create_or_update "celery-result-backend" "${CELERY_RESULT_BACKEND:-${CELERY_BROKER_URL:-${REDIS_URL:-}}}"
create_or_update "allowed-hosts" "${ALLOWED_HOSTS:-.run.app}"
create_or_update "cors-allowed-origins" "${CORS_ALLOWED_ORIGINS:-}"
create_or_update "csrf-trusted-origins" "${CSRF_TRUSTED_ORIGINS:-}"
create_or_update "frontend-url" "${FRONTEND_URL:-}"
create_or_update "groq-api-key" "${GROQ_API_KEY:-}"
create_or_update "openai-api-key" "${OPENAI_API_KEY:-}"
create_or_update "jwt-secret" "${JWT_SECRET:-${SECRET_KEY:-}}"

echo "Secrets synced."
