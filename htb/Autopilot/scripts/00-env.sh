#!/bin/bash
# Shared env. Copy ../secrets.example.env → ../secrets.env first.
set -euo pipefail

export SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export WORK="$(cd "$SCRIPTS/.." && pwd)"
export LOOT="${LOOT:-$WORK/loot}"
mkdir -p "$LOOT" "$SCRIPTS/lib"

SECRETS="$WORK/secrets.env"
if [[ ! -f "$SECRETS" ]]; then
  echo "[-] missing $SECRETS — cp secrets.example.env secrets.env and fill it" >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
. "$SECRETS"
set +a

export BOX_IP="${BOX_IP:?set BOX_IP in secrets.env}"
export DOMAIN="${DOMAIN:-autopilot.htb}"
export HOSTS_LINE="$BOX_IP grommunio.autopilot.htb autodiscover.autopilot.htb mail.autopilot.htb files.autopilot.htb autopilot.htb"

export DEB_USER="${DEB_USER:-deborah.hernandez}"
export DEB_PASS="${DEB_PASS:?set DEB_PASS}"
export MYSQL_USER="${MYSQL_USER:-grommunio}"
export MYSQL_PASS="${MYSQL_PASS:?set MYSQL_PASS}"
export ADMIN_PASS="${ADMIN_PASS:?set ADMIN_PASS}"
export SA_USER="${SA_USER:-sa-joshua.harris}"
export SA_PASS="${SA_PASS:-}"
export DA_USER="${DA_USER:-da-stephanie.lewis}"
export DA_PASSWORD="${DA_PASSWORD:-}"

export DC01="${DC01:-172.16.20.1}"
export MAIL_INT="${MAIL_INT:-172.16.20.10}"
export WS02="${WS02:-172.16.20.15}"

export WEBDIR="/var/lib/grommunio-files/data/${DEB_USER}/files"
export WS="https://grommunio.autopilot.htb/files/data/${DEB_USER}/files/s.php"
export DAV="https://grommunio.autopilot.htb/files/remote.php/dav/files/${DEB_USER}"
export API_PHP="https://grommunio.autopilot.htb/files/data/${DEB_USER}/files/api.php"

export SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
export PUBKEY="$(cat "${SSH_KEY}.pub" 2>/dev/null || true)"
export KALI_IP="${KALI_IP:-$(ip -4 -br a show tun0 2>/dev/null | awk '{print $3}' | cut -d/ -f1)}"
