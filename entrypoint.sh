#!/usr/bin/env sh
set -e

# Crea carpeta de estado si la usas (para preguntas.json, fichas, etc.)
mkdir -p "${APP_STATE_DIR:-/state}"

# Permite cambiar el módulo vía env (por si no es www.app:app)
APP_MODULE="${APP_MODULE:-www.app:app}"

exec gunicorn "$APP_MODULE" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --worker-class "${WORKER_CLASS:-gthread}" \
  --threads "${THREADS:-8}" \
  --bind "0.0.0.0:${PORT:-5000}" \
  --timeout "${TIMEOUT:-120}" \
  --graceful-timeout "${GRACEFUL_TIMEOUT:-120}" \
  --keep-alive "${KEEP_ALIVE:-5}" \
  --max-requests "${MAX_REQUESTS:-1000}" \
  --max-requests-jitter "${MAX_REQUESTS_JITTER:-100}" \
  --access-logfile "-" \
  --error-logfile "-" \
  --log-level "${LOG_LEVEL:-info}"
# 👆 sin --preload
