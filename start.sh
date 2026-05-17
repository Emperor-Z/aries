#!/usr/bin/env bash
# Ares startup — brings up all services and drops into the REPL.
set -euo pipefail

ARES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DIR="$(dirname "$ARES_DIR")/ares-core"
PYTHON="$CORE_DIR/.venv/bin/python"

export PYTHONPATH="$CORE_DIR/src:$CORE_DIR/.venv/lib/python3.13/site-packages:$ARES_DIR"

# Langfuse keys should be provided by the local shell/environment.
# Do not commit real keys to this repository.
: "${LANGFUSE_PUBLIC_KEY:=}"
: "${LANGFUSE_SECRET_KEY:=}"

# ── colours ──────────────────────────────────────────────────────────────────
G='\033[0;32m'; Y='\033[0;33m'; R='\033[0;31m'; N='\033[0m'
ok()   { echo -e "${G}[ok]${N}  $*"; }
warn() { echo -e "${Y}[warn]${N} $*"; }
err()  { echo -e "${R}[err]${N} $*"; }

echo -e "\n${G}Ares — starting up${N}\n"

if [ -z "$LANGFUSE_PUBLIC_KEY" ] || [ -z "$LANGFUSE_SECRET_KEY" ]; then
    warn "Langfuse keys are not set; observability may be disabled or unauthenticated"
fi

# ── 1. Ollama ─────────────────────────────────────────────────────────────────
if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    ok "Ollama already running"
else
    warn "Ollama not detected — starting..."
    ollama serve &>/dev/null &
    sleep 3
    curl -sf http://localhost:11434/api/tags &>/dev/null && ok "Ollama started" || { err "Ollama failed to start"; exit 1; }
fi

# ── 2. Langfuse (Docker) ──────────────────────────────────────────────────────
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q ares_langfuse; then
    ok "Langfuse already running (http://localhost:3000)"
else
    warn "Langfuse not running — starting Docker stack..."
    docker compose -f "$ARES_DIR/docker/langfuse/docker-compose.yml" up -d &>/dev/null
    until curl -sf http://localhost:3000/api/public/health &>/dev/null; do sleep 2; done
    ok "Langfuse started (http://localhost:3000)"
fi

# ── 3. A2A agent servers ──────────────────────────────────────────────────────
a2a_up() {
    curl -sf "http://127.0.0.1:$1/health" &>/dev/null
}

declare -A A2A_PORTS=([orchestrator]=8100 [coder]=8101 [thinker]=8102 [runner]=8103 [serena]=8104)
all_up=true
for agent in orchestrator coder thinker runner serena; do
    port="${A2A_PORTS[$agent]}"
    if a2a_up "$port"; then
        ok "A2A $agent already on :$port"
    else
        all_up=false
    fi
done

if [ "$all_up" = false ]; then
    warn "Starting A2A agent servers..."
    "$PYTHON" -c "
import sys
sys.path.insert(0, '$CORE_DIR/src')
sys.path.insert(0, '$CORE_DIR/.venv/lib/python3.13/site-packages')
sys.path.insert(0, '$ARES_DIR')
from ares.a2a_server import launch_all
procs = launch_all(background=True)
import time; time.sleep(8)   # give servers time to init models
" &

    # Wait up to 120s for all A2A servers to come up
    timeout=120
    elapsed=0
    while [ $elapsed -lt $timeout ]; do
        all_ready=true
        for agent in orchestrator coder thinker runner serena; do
            port="${A2A_PORTS[$agent]}"
            a2a_up "$port" || all_ready=false
        done
        [ "$all_ready" = true ] && break
        sleep 3; elapsed=$((elapsed + 3))
        echo -n "."
    done
    echo

    for agent in orchestrator coder thinker runner serena; do
        port="${A2A_PORTS[$agent]}"
        if a2a_up "$port"; then
            ok "A2A $agent :$port"
        else
            warn "A2A $agent :$port did not come up in time (continuing anyway)"
        fi
    done
fi

# ── 4. Drop into REPL ────────────────────────────────────────────────────────
echo
echo -e "${G}All services ready.${N}"
echo -e "  Langfuse UI  : http://localhost:3000"
echo -e "  A2A agents   : :8100 (orch) :8101 (coder) :8102 (thinker) :8103 (runner) :8104 (serena)"
echo
exec "$PYTHON" "$ARES_DIR/main.py"
