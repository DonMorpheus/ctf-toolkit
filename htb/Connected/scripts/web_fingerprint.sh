#!/usr/bin/env bash
# Fingerprint WWW — Connected @ Release Arena
set -euo pipefail
IP="${1:-10.129.46.7}"
OUT="${2:-$(dirname "$0")/../loot}"
mkdir -p "$OUT"
for h in "$IP" connected.htb pbxconnect; do
  echo "=== $h HTTP ===" | tee -a "$OUT/http-headers-live.txt"
  curl -sI --connect-timeout 6 -m 12 "http://$h/" 2>&1 | tee -a "$OUT/http-headers-live.txt" || true
  echo "=== $h HTTPS ===" | tee -a "$OUT/http-headers-live.txt"
  curl -skI --connect-timeout 6 -m 12 "https://$h/" 2>&1 | tee -a "$OUT/http-headers-live.txt" || true
done
whatweb -a 3 "http://connected.htb/" "https://connected.htb/" 2>&1 | tee "$OUT/whatweb.txt" || true
echo 'wasd' | su - ctf -c "sudo nmap -Pn -p 80,443 -sV --script http-server-header,http-title,http-methods -oN $OUT/nmap-http.txt $IP" || true