#!/usr/bin/env bash
# stop.sh — Boiler Steam Generation

set -euo pipefail

if ! ss -tlnp | grep -q ':507 '; then
    echo "Boiler is not running"
    exit 0
fi

echo "Stopping Boiler Steam Generation..."
sudo pkill -f "python3 main.py" 2>/dev/null || true

for i in $(seq 1 10); do
    if ! ss -tlnp | grep -q ':507 '; then
        echo "Stopped cleanly"
        exit 0
    fi
    sleep 1
done

echo "Force killing..."
sudo pkill -9 -f "python3 main.py" 2>/dev/null || true
echo "Force stopped"
