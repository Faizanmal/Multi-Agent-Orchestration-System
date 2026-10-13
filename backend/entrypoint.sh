#!/bin/sh
set -e

PORT="${PORT:-8000}"
WORKERS="${GUNICORN_WORKERS:-2}"
TIMEOUT="${GUNICORN_TIMEOUT:-120}"
ROLE="${SERVICE_ROLE:-web}"

echo "Starting backend (role=${ROLE}, port=${PORT})"

if [ "${RUN_MIGRATIONS:-true}" = "true" ] && [ "${ROLE}" = "web" ]; then
  echo "Running database migrations..."
  python manage.py migrate --noinput
fi

if [ "${COLLECT_STATIC:-false}" = "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

# Cloud Run requires a process listening on $PORT. Celery does not, so start a tiny probe.
start_cloud_run_probe() {
  # Background process must stay alive (do not use a daemon thread).
  python - <<'PY' &
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

port = int(os.environ.get("PORT", "8000"))

class Probe(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *_args):
        return

print(f"Cloud Run probe listening on :{port}", flush=True)
ThreadingHTTPServer(("0.0.0.0", port), Probe).serve_forever()
PY
}

case "${ROLE}" in
  web)
    exec gunicorn backend.asgi:application \
      --bind "0.0.0.0:${PORT}" \
      --workers "${WORKERS}" \
      --worker-class uvicorn.workers.UvicornWorker \
      --timeout "${TIMEOUT}" \
      --access-logfile - \
      --error-logfile -
    ;;
  worker)
    start_cloud_run_probe
    exec celery -A backend worker -l info --concurrency="${CELERY_WORKERS:-2}"
    ;;
  beat)
    start_cloud_run_probe
    exec celery -A backend beat -l info
    ;;
  *)
    echo "Unknown SERVICE_ROLE=${ROLE} (expected: web|worker|beat)"
    exit 1
    ;;
esac
