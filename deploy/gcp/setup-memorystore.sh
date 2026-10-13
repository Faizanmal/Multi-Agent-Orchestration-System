#!/usr/bin/env bash
# Provision Memorystore Redis + Serverless VPC Access connector for Cloud Run.
# VM (Compute Engine) deploys do not need this — they use Docker Redis.
#
# Usage:
#   export GOOGLE_CLOUD_PROJECT=your-project
#   export GCP_REGION=us-central1
#   bash deploy/gcp/setup-memorystore.sh
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
REGION="${GCP_REGION:-us-central1}"
NETWORK="${VPC_NETWORK:-default}"
REDIS_NAME="${MEMORYSTORE_NAME:-multi-agent-redis}"
REDIS_SIZE_GB="${MEMORYSTORE_SIZE_GB:-1}"
REDIS_TIER="${MEMORYSTORE_TIER:-basic}"
CONNECTOR_NAME="${VPC_CONNECTOR_NAME:-multi-agent-connector}"
CONNECTOR_RANGE="${VPC_CONNECTOR_RANGE:-10.8.0.0/28}"
API_SERVICE="${CLOUD_RUN_SERVICE:-multi-agent-api}"
WORKER_SERVICE="${CLOUD_RUN_WORKER_SERVICE:-multi-agent-worker}"

gcloud config set project "${PROJECT_ID}"

echo "==> Enabling APIs"
gcloud services enable \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  compute.googleapis.com \
  --quiet

echo "==> Serverless VPC Access connector (${CONNECTOR_NAME})"
if ! gcloud compute networks vpc-access connectors describe "${CONNECTOR_NAME}" \
  --region="${REGION}" >/dev/null 2>&1; then
  gcloud compute networks vpc-access connectors create "${CONNECTOR_NAME}" \
    --region="${REGION}" \
    --network="${NETWORK}" \
    --range="${CONNECTOR_RANGE}" \
    --min-instances=2 \
    --max-instances=3 \
    --machine-type=e2-micro
else
  echo "Connector already exists."
fi

echo "==> Memorystore Redis (${REDIS_NAME})"
if ! gcloud redis instances describe "${REDIS_NAME}" --region="${REGION}" >/dev/null 2>&1; then
  gcloud redis instances create "${REDIS_NAME}" \
    --size="${REDIS_SIZE_GB}" \
    --region="${REGION}" \
    --redis-version=redis_7_0 \
    --tier="${REDIS_TIER}" \
    --network="projects/${PROJECT_ID}/global/networks/${NETWORK}" \
    --connect-mode=DIRECT_PEERING
else
  echo "Memorystore instance already exists."
fi

REDIS_HOST="$(gcloud redis instances describe "${REDIS_NAME}" --region="${REGION}" \
  --format='get(host)')"
REDIS_PORT="$(gcloud redis instances describe "${REDIS_NAME}" --region="${REGION}" \
  --format='get(port)')"
REDIS_URL="redis://${REDIS_HOST}:${REDIS_PORT}/0"
CELERY_URL="redis://${REDIS_HOST}:${REDIS_PORT}/1"

echo "==> Writing Redis secrets"
export REDIS_URL CELERY_BROKER_URL="${CELERY_URL}" CELERY_RESULT_BACKEND="${CELERY_URL}"
# Reuse setup-secrets helpers for redis keys only
bash "$(dirname "$0")/setup-secrets.sh"

echo "==> Attaching VPC connector to Cloud Run services (if they exist)"
for svc in "${API_SERVICE}" "${WORKER_SERVICE}"; do
  if gcloud run services describe "${svc}" --region="${REGION}" >/dev/null 2>&1; then
    gcloud run services update "${svc}" \
      --region="${REGION}" \
      --vpc-connector="${CONNECTOR_NAME}" \
      --vpc-egress=private-ranges-only \
      --update-env-vars="REDIS_URL=${REDIS_URL},CELERY_BROKER_URL=${CELERY_URL},CELERY_RESULT_BACKEND=${CELERY_URL}" \
      --quiet
    echo "Updated ${svc}"
  else
    echo "Skip ${svc} (not deployed yet)"
  fi
done

echo ""
echo "Memorystore host: ${REDIS_HOST}:${REDIS_PORT}"
echo "REDIS_URL=${REDIS_URL}"
echo "VPC connector: ${CONNECTOR_NAME}"
echo "Add these to .env.gcp / Secret Manager and redeploy Cloud Run if services were missing."
