#!/bin/sh
set -e

CRONTAB_FILE="/tmp/crontab"

log() {
    echo "[$(date -Iseconds)] [ENTRYPOINT] $1"
}

log "Schedule: ${KOMETA_TIME}"
echo "${KOMETA_TIME} python3 /app/generate_poster.py" > "$CRONTAB_FILE"

log "Running initial update..."
python3 /app/generate_poster.py || log "Initial update failed, will retry on first scheduled run"

log "Starting supercronic..."
exec supercronic "$CRONTAB_FILE"
