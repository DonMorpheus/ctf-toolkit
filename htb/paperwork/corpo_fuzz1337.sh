#!/bin/sh
for p in / /download/archive /admin /login /pin /verify /api /api/admin /console /internal /mgmt /staff /upload /debug /config /health /status /root /superuser /paperwork /archive/admin /download/../etc/passwd; do
  c=$(curl -s -o /tmp/b -w '%{http_code}' "http://127.0.0.1:1337$p")
  n=$(wc -c </tmp/b)
  echo "$c $n $p"
done