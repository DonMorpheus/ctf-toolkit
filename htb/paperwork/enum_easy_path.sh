#!/bin/sh
# Paperwork Easy — szukaj prostego wektora (moduły, writable, prod server.py)
set -e
echo "=== LPDServer ==="
ls -la /opt/LPDServer/ 2>&1
echo "=== head server.py (prod) ==="
head -120 /opt/LPDServer/server.py 2>&1
echo "=== grep import/load in server ==="
grep -nE 'import|load|module|plugin|handler' /opt/LPDServer/server.py 2>&1 || true
echo "=== systemd lpd drop-ins ==="
ls -la /etc/systemd/system/lpdserver.service.d/ 2>&1 || true
systemctl cat lpdserver.service 2>&1 | head -40
echo "=== printer dir (lp readable?) ==="
ls -la /home/archivist/printer/ 2>&1
ls -la /home/archivist/printer/logs/ 2>&1
echo "=== corposite unit ==="
systemctl cat corposite.service 2>&1 | head -30
echo "=== curl 1337 extra paths ==="
for p in /download/archive /static /module /modules /plugin /plugins /api/v1 /admin/login /pin/verify /corpo /archive/upload; do
  code=$(curl -s -o /tmp/cbody -w '%{http_code}' "http://127.0.0.1:1337$p" 2>/dev/null || echo ERR)
  echo "$code $p $(head -c 80 /tmp/cbody 2>/dev/null | tr '\n' ' ')"
done
echo "=== VALID_QUEUE sanity ==="
python3 -c 'q="archive_intake"; print("x in q", "x" in q); print("archive in q", "archive" in q)'