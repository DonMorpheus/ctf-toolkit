#!/usr/bin/env bash
# Stealth port + WWW probe — 10.129.46.7 / connected.htb
IP="${1:-10.129.46.7}"
BASE="$(cd "$(dirname "$0")/.." && pwd)"
echo "[*] SYN stealth (nmap -sS -T2 -f, top 1000) → $BASE/nmap/stealth-syn"
echo 'wasd' | su - ctf -c "sudo nmap -Pn -sS -T2 -f --scan-delay 50ms --top-ports 1000 --open -oA $BASE/nmap/stealth-syn $IP"
echo "[*] naabu SYN rate 80"
naabu -host "$IP" -scan-type s -rate 80 -top-ports 1000 -silent | tee "$BASE/loot/naabu-stealth.txt"
echo "[*] stealth browser (headless)"
cd "$BASE" && DISPLAY= python3 scripts/stealth_web_probe.py "$IP" || true