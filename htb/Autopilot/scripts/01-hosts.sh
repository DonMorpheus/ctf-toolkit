#!/bin/bash
# Print hosts line + TLS Date (clock skew breaks logon).
set -euo pipefail
. "$(dirname "$0")/00-env.sh"

echo "$HOSTS_LINE"
echo "# sudo: append / replace that line in /etc/hosts"
echo

HDR=$(curl -skI --max-time 8 "https://grommunio.autopilot.htb/" \
  | awk -F': ' 'tolower($1)=="date"{print $2}' | tr -d '\r')
echo "[*] TLS Date: ${HDR:-unknown}"
echo "[*] local : $(date -u)"
echo "[+] if skew > a few minutes: sudo date -u -s '\$HDR'"
