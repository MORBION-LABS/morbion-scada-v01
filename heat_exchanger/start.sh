#!/usr/bin/env bash
# start.sh — Pipeline Pump Station

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/opt/ot_scripts/logs"
PID_FILE="/tmp/heat_exchager.pid"
LOG_FILE="$LOG_DIR/heat_exchanger_$(date +%Y%m%d).log"

mkdir -p "$LOG_DIR"

if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Heat Exhnager already running (PID $PID)"
        echo "Attaching to log — Ctrl+C to detach"
        echo "─────────────────────────────────────"
        trap 'echo ""; echo "Detached. Process still running (PID $PID)"; exit 0' INT
        tail -f "$LOG_FILE"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

echo "Starting Heat Exchanger Station — KenGen Olkaria"
cd "$SCRIPT_DIR"

sudo setsid python3 main.py >> "$LOG_FILE" 2>&1 &
BGPID=$!
echo $BGPID > "$PID_FILE"

echo "Started (PID $BGPID)"
echo "Log: $LOG_FILE"
echo "Press Ctrl+C to detach — process keeps running in background"
echo "─────────────────────────────────────────────────────────────"

trap 'echo ""; echo "Detached. Process still running (PID $BGPID)"; exit 0' INT

tail -f "$LOG_FILE"
