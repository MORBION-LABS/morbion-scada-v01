#!/usr/bin/env bash
# start.sh — Boiler Steam Generation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/opt/ot_scripts/logs"
LOG_FILE="$LOG_DIR/boiler_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

# Check if already running by port
if ss -tlnp | grep -q ':507 '; then
    echo "Boiler already running on port 507"
    echo "Attaching to log — Ctrl+C to detach"
    echo "─────────────────────────────────────"
    trap 'echo ""; echo "Detached. Process still running."; exit 0' INT
    tail -f "$LOG_FILE"
    exit 0
fi

echo "Starting Boiler Steam Generation — EABL/Bidco"
cd "$SCRIPT_DIR"

sudo setsid python3 main.py >> "$LOG_FILE" 2>&1 &
disown

echo "Started"
echo "Log: $LOG_FILE"
echo "Press Ctrl+C to detach — process keeps running in background"
echo "─────────────────────────────────────────────────────────────"

trap 'echo ""; echo "Detached. Process still running."; exit 0' INT

tail -f "$LOG_FILE"
