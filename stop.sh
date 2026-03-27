#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.running_pids"

echo "Fermando i processi..."
sudo pkill -f "temperature_logger.py" 2>/dev/null && echo "  ✓ logger fermato"     || echo "  (logger non trovato)"
sudo pkill -f "interface.py"          2>/dev/null && echo "  ✓ interfaccia fermata" || echo "  (interfaccia non trovata)"

if [ -f "$PID_FILE" ]; then
    while read -r pid; do
        kill "$pid" 2>/dev/null
    done < "$PID_FILE"
    rm -f "$PID_FILE"
fi
echo "Fatto."
