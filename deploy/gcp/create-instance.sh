#!/usr/bin/env bash
# Create a GCP Compute Engine VM and deploy the backend (no frontend).
#
# Usage (from your laptop with gcloud configured):
#   export GOOGLE_CLOUD_PROJECT=your-project-id
#   export GCP_ZONE=us-central1-a
#   # optional: export INSTANCE_NAME=multi-agent-api
#   # optional: path to a local .env.gcp to scp after create
#   bash deploy/gcp/create-instance.sh
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT}"
ZONE="${GCP_ZONE:-us-central1-a}"
REGION="${GCP_REGION:-${ZONE%-*}}"
INSTANCE="${INSTANCE_NAME:-multi-agent-api}"
MACHINE="${MACHINE_TYPE:-e2-standard-4}"
DISK_SIZE="${DISK_SIZE_GB:-50}"
IMAGE_FAMILY="${IMAGE_FAMILY:-ubuntu-2204-lts}"
IMAGE_PROJECT="${IMAGE_PROJECT:-ubuntu-os-cloud}"
REPO_URL="${REPO_URL:-}"          # e.g. https://github.com/you/multi-agent-orch-system.git
REPO_BRANCH="${REPO_BRANCH:-master}"
FIREWALL_RULE="${FIREWALL_RULE:-allow-multi-agent-api}"

gcloud config set project "${PROJECT_ID}"

echo "==> Enabling Compute API"
gcloud services enable compute.googleapis.com --quiet

echo "==> Firewall: TCP 8000 (API)"
if ! gcloud compute firewall-rules describe "${FIREWALL_RULE}" >/dev/null 2>&1; then
  gcloud compute firewall-rules create "${FIREWALL_RULE}" \
    --allow=tcp:8000 \
    --target-tags=multi-agent-api \
    --description="Multi-agent backend API" \
    --direction=INGRESS \
    --priority=1000
fi

STARTUP_SCRIPT="$(dirname "$0")/vm-startup.sh"

echo "==> Creating instance ${INSTANCE} (${MACHINE}) in ${ZONE}"
if gcloud compute instances describe "${INSTANCE}" --zone="${ZONE}" >/dev/null 2>&1; then
  echo "Instance already exists; skipping create."
else
  gcloud compute instances create "${INSTANCE}" \
    --zone="${ZONE}" \
    --machine-type="${MACHINE}" \
    --image-family="${IMAGE_FAMILY}" \
    --image-project="${IMAGE_PROJECT}" \
    --boot-disk-size="${DISK_SIZE}GB" \
    --boot-disk-type=pd-balanced \
    --tags=multi-agent-api \
    --scopes=cloud-platform \
    --metadata=repo-url="${REPO_URL}",repo-branch="${REPO_BRANCH}" \
    --metadata-from-file=startup-script="${STARTUP_SCRIPT}"
fi

echo "==> Waiting for RUNNING"
gcloud compute instances wait-until-running "${INSTANCE}" --zone="${ZONE}" 2>/dev/null \
  || sleep 15

EXTERNAL_IP="$(gcloud compute instances describe "${INSTANCE}" --zone="${ZONE}" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')"

echo ""
echo "Instance: ${INSTANCE}"
echo "External IP: ${EXTERNAL_IP}"
echo ""
echo "Next steps:"
echo "  1) SSH:"
echo "       gcloud compute ssh ${INSTANCE} --zone=${ZONE}"
echo "  2) If startup did not clone the repo, copy it:"
echo "       gcloud compute scp --recurse --zone=${ZONE} . ${INSTANCE}:~/multi-agent-orch-system"
echo "  3) On the VM:"
echo "       cd ~/multi-agent-orch-system"
echo "       bash deploy/gcp/vm-setup.sh"
echo "  4) Open:"
echo "       http://${EXTERNAL_IP}:8000/health/live/"
echo ""
echo "Tip: put API keys in .env.gcp on the VM before or after vm-setup.sh."
