#!/bin/bash
# GCE metadata startup-script: install Docker; optionally clone repo and start stack.
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y ca-certificates curl git openssl

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

# Compose plugin
apt-get install -y docker-compose-plugin || true

REPO_URL="$(curl -sf -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/repo-url || true)"
REPO_BRANCH="$(curl -sf -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/attributes/repo-branch || true)"
REPO_BRANCH="${REPO_BRANCH:-master}"
APP_DIR=/opt/multi-agent-orch-system

if [ -n "${REPO_URL}" ] && [ "${REPO_URL}" != "None" ]; then
  if [ ! -d "${APP_DIR}/.git" ]; then
    git clone --branch "${REPO_BRANCH}" "${REPO_URL}" "${APP_DIR}"
  else
    cd "${APP_DIR}"
    git fetch origin "${REPO_BRANCH}"
    git reset --hard "origin/${REPO_BRANCH}"
  fi
  cd "${APP_DIR}"
  bash deploy/gcp/vm-setup.sh || true
fi

# Mark startup done for debugging
date > /var/log/multi-agent-startup.done
