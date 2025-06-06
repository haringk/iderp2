#!/usr/bin/env bash
set -euo pipefail

SITE=${1:-sito.local}
STATUS=0

# Must be run inside ~/frappe-bench
if [ ! -f sites/common_site_config.json ]; then
    echo "Errore: esegui lo script nella directory ~/frappe-bench" >&2
    exit 1
fi

# Python version check
PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python $PY_VERSION"
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    echo "ATTENZIONE: Python 3.10+ consigliato" >&2
    STATUS=1
fi

# Node version check
NODE_VERSION=$(node --version 2>&1 || echo "")
if [ -z "$NODE_VERSION" ]; then
    echo "Node.js non trovato" >&2
    exit 1
fi
echo "Node.js $NODE_VERSION"
NODE_VERSION=${NODE_VERSION#v}
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 18 ]; then
    echo "ATTENZIONE: Node.js 18+ consigliato" >&2
    STATUS=1
fi

# bench presence
if ! bench --version >/dev/null 2>&1; then
    echo "Comando bench non trovato" >&2
    exit 1
fi

# List installed apps
APPS=$(bench --site "$SITE" list-apps 2>&1)
if [ $? -ne 0 ]; then
    echo "$APPS" >&2
    exit 1
fi
echo "$APPS"
for app in frappe erpnext iderp; do
    echo "$APPS" | grep -qx "$app" || { echo "App mancante: $app" >&2; STATUS=1; }
done

# Run check_installation
CHECK_RAW=$(bench --site "$SITE" execute iderp.__init__.check_installation 2>&1)
echo "$CHECK_RAW"
last_line=$(echo "$CHECK_RAW" | tail -n 1)
if ! echo "$last_line" | python3 - "$SITE" <<'PY'
import ast,sys,json
try:
    data=ast.literal_eval(sys.stdin.read())
    print(json.dumps(data, indent=2))
    sys.exit(0 if data.get('installed') else 1)
except Exception as e:
    print(f"Errore parsing output: {e}", file=sys.stderr)
    sys.exit(1)
PY
then
    STATUS=1
fi

exit $STATUS
