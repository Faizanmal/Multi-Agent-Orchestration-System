#!/usr/bin/env bash
# Run ON the GCP Compute Engine VM (from the repo root).
# Installs Docker, creates .env.gcp if missing, starts backend stack.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "${REPO_ROOT}"

ENV_FILE="${ENV_FILE:-.env.gcp}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.gce.yml}"

echo "==> Installing Docker (if needed)"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" || true
  sudo systemctl enable --now docker
fi

# Prefer docker compose plugin
if ! docker compose version >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y docker-compose-plugin || true
fi

EXTERNAL_IP="$(curl -s -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip 2>/dev/null || true)"
INTERNAL_IP="$(curl -s -H 'Metadata-Flavor: Google' \
  http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/ip 2>/dev/null || true)"
HOST_FOR_APP="${EXTERNAL_IP:-${INTERNAL_IP:-localhost}}"

if [ ! -f "${ENV_FILE}" ]; then
  echo "==> Creating ${ENV_FILE} from template"
  cp deploy/gcp/.env.gcp.example "${ENV_FILE}"
  # Generate secrets
  SECRET_KEY="$(openssl rand -base64 48 | tr -d '\n')"
  JWT_SECRET="$(openssl rand -base64 32 | tr -d '\n')"
  POSTGRES_PASSWORD="$(openssl rand -base64 24 | tr -d '\n=/+')"
  REDIS_PASSWORD="$(openssl rand -base64 24 | tr -d '\n=/+')"

  # Portable in-place edits
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" "${ENV_FILE}"
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET}|" "${ENV_FILE}"
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|" "${ENV_FILE}"
  sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=${REDIS_PASSWORD}|" "${ENV_FILE}"
  sed -i "s|^DEBUG=.*|DEBUG=False|" "${ENV_FILE}"
  sed -i "s|^ALLOWED_HOSTS=.*|ALLOWED_HOSTS=${HOST_FOR_APP},localhost,127.0.0.1|" "${ENV_FILE}"
  sed -i "s|^BACKEND_URL=.*|BACKEND_URL=http://${HOST_FOR_APP}:8000|" "${ENV_FILE}"
  sed -i "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=http://${HOST_FOR_APP}:8000|" "${ENV_FILE}"
  echo "Generated secrets in ${ENV_FILE}. Edit API keys (GROQ_API_KEY, etc.) before production use."
fi

# Ensure ALLOWED_HOSTS includes current IP when env already exists
if ! grep -q "${HOST_FOR_APP}" "${ENV_FILE}" 2>/dev/null; then
  echo "NOTE: Add ${HOST_FOR_APP} to ALLOWED_HOSTS in ${ENV_FILE} if health checks fail with DisallowedHost."
fi

echo "==> Building and starting stack (${COMPOSE_FILE})"
sudo docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --build

echo "==> Waiting for health"
for i in $(seq 1 36); do
  if curl -fsS "http://127.0.0.1:8000/health/live/" >/dev/null 2>&1; then
    echo "Healthy."
    break
  fi
  sleep 5
  if [ "$i" -eq 36 ]; then
    echo "Health check timed out. Logs:"
    sudo docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" logs --tail=80 backend
    exit 1
  fi
done

echo ""
echo "API:  http://${HOST_FOR_APP}:8000"
echo "Live: http://${HOST_FOR_APP}:8000/health/live/"
echo "Logs: sudo docker compose -f ${COMPOSE_FILE} --env-file ${ENV_FILE} logs -f backend"
