#!/usr/bin/env bash
# Kerberos / PKINIT on danglingtree requires clock ≈ DC (skew often ~+7h on Kali).
# Usage: ./sync_time_to_dc.sh [DC_IP]
set -euo pipefail
DC="${1:-${DC_IP:-10.129.6.118}}"
ROOT_PASS="${ROOT_PASS:-wasd}"

echo "[*] DC=$DC"
# Prefer ctf sudo if present, else su root
if id ctf &>/dev/null; then
  echo "$ROOT_PASS" | su - ctf -c "sudo timedatectl set-ntp false 2>/dev/null; sudo systemctl stop systemd-timesyncd 2>/dev/null; sudo ntpdate -u '$DC'"
else
  echo "$ROOT_PASS" | su -c "timedatectl set-ntp false 2>/dev/null; systemctl stop systemd-timesyncd 2>/dev/null; ntpdate -u '$DC'"
fi
date
echo "[+] clock synced to $DC"
