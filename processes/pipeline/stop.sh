#!/usr/bin/env bash
set -euo pipefail

# The process pattern to look for
PROC_PATTERN="python3 main.py"
PID_FILE="/tmp/pipeline.pid"

# 1. Try to find the process ID by name
PID=$(pgrep -f "$PROC_PATTERN" || echo "")

if [[ -z "$PID" ]]; then
    echo "Pipeline is not running"
    rm -f "$PID_FILE"
    exit 0
fi

echo "Stopping Pipeline ($PROC_PATTERN) PID: $PID..."

# 2. Ask it to stop nicely (SIGTERM)
pkill -f "$PROC_PATTERN"

# 3. Wait up to 10 seconds for it to exit
for i in $(seq 1 10); do
    if ! pgrep -f "$PROC_PATTERN" > /dev/null; then
        rm -f "$PID_FILE"
        echo "Stopped cleanly"
        exit 0
    fi
    sleep 1
done

# 4. If still running, force it (SIGKILL)
echo "Process didn't respond; force killing..."
pkill -9 -f "$PROC_PATTERN"
rm -f "$PID_FILE"
echo "Force stopped"
