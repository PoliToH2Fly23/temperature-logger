#!/bin/bash
# ============================================================
#  start.sh  —  avvia logger + interfaccia in terminali separati
#               e crea stop.sh per fermarli facilmente
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python3"
PIP="$SCRIPT_DIR/venv/bin/pip"
PID_FILE="$SCRIPT_DIR/.running_pids"

# Controlla che il venv esista
if [ ! -f "$PYTHON" ]; then
    echo "❌  Virtualenv non trovato in $SCRIPT_DIR/venv"
    echo "   Crea il venv con:  python3 -m venv venv && venv/bin/pip install -r requirements.txt"
    exit 1
fi

# ── Verifica e installa dipendenze mancanti nel venv ─────────
# NOTA: usiamo sudo PIP con path assoluto così i pacchetti finiscono
# nel venv anche quando il processo gira come root.
echo "  Verifica dipendenze nel venv..."
MISSING=()
for pkg in matplotlib w1thermsensor; do
    if ! "$PYTHON" -c "import $pkg" &>/dev/null; then
        MISSING+=("$pkg")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  Installazione pacchetti mancanti: ${MISSING[*]}"
    sudo "$PIP" install "${MISSING[@]}"
    if [ $? -ne 0 ]; then
        echo "❌  Installazione fallita. Prova manualmente:"
        echo "   sudo $PIP install ${MISSING[*]}"
        exit 1
    fi
    echo "  ✓ Dipendenze installate"
else
    echo "  ✓ Tutte le dipendenze presenti"
fi

# Pulisce eventuali PID vecchi
rm -f "$PID_FILE"

# ── Funzione: apre un terminale con titolo e comando ─────────
open_terminal() {
    local title="$1"
    local cmd="$2"

    if command -v lxterminal &>/dev/null; then
        lxterminal --title="$title" -e bash -c "$cmd; echo; echo '[ Premi Invio per chiudere ]'; read" &
    elif command -v xterm &>/dev/null; then
        xterm -title "$title" -e bash -c "$cmd; echo; echo '[ Premi Invio per chiudere ]'; read" &
    elif command -v gnome-terminal &>/dev/null; then
        gnome-terminal --title="$title" -- bash -c "$cmd; echo; echo '[ Premi Invio per chiudere ]'; read" &
    elif command -v konsole &>/dev/null; then
        konsole --title "$title" -e bash -c "$cmd; echo; echo '[ Premi Invio per chiudere ]'; read" &
    else
        echo "⚠  Nessun terminale grafico trovato — avvio $title in background"
        eval "sudo $cmd" &
        echo $! >> "$PID_FILE"
        return
    fi
    echo $! >> "$PID_FILE"
}

echo "============================================================"
echo "  Temperature Monitor — avvio"
echo "============================================================"

# ── 1. Logger ────────────────────────────────────────────────
echo "  Avvio logger..."
open_terminal \
    "Temperature Logger" \
    "cd '$SCRIPT_DIR' && sudo '$PYTHON' temperature_logger.py"

# ── 2. Aspetta che il CSV venga creato ───────────────────────
echo "  Attendo creazione del log CSV..."
POINTER="$SCRIPT_DIR/logged_data/.current_log"
TIMEOUT=30
ELAPSED=0
while [ ! -f "$POINTER" ]; do
    sleep 0.5
    ELAPSED=$((ELAPSED + 1))
    if [ $ELAPSED -ge $((TIMEOUT * 2)) ]; then
        echo "⚠  Timeout: il logger non ha creato il file log entro ${TIMEOUT}s"
        echo "   Avvio interfaccia comunque."
        break
    fi
done

if [ -f "$POINTER" ]; then
    CSV_PATH=$(cat "$POINTER")
    echo "  Log trovato: $CSV_PATH"
fi

# ── 3. Interfaccia ───────────────────────────────────────────
echo "  Avvio interfaccia grafica..."
open_terminal \
    "Temperature Interface" \
    "cd '$SCRIPT_DIR' && sudo '$PYTHON' interface.py"

# ── 4. Genera stop.sh ────────────────────────────────────────
cat > "$SCRIPT_DIR/stop.sh" << 'STOP'
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
STOP

chmod +x "$SCRIPT_DIR/stop.sh"

echo ""
echo "============================================================"
echo "  Avviato! I processi girano in finestre separate."
echo "  Per fermare tutto:   ./stop.sh"
echo "============================================================"
