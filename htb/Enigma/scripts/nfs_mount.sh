#!/usr/bin/env bash
set -euo pipefail
IP="${1:-}"
MNT="${2:-$HOME/mnt/enigma_nfs}"
if [[ -z "$IP" ]]; then
  echo "Usage: $0 <target_ip> [mount_point]" >&2
  exit 1
fi
showmount -e "$IP"
mkdir -p "$MNT"
sudo mount -t nfs "${IP}:/srv/nfs/onboarding" "$MNT" -o ro,nfsvers=3
ls -la "$MNT"
echo "[*] PDF: mutool draw -F txt $MNT/New_Employee_Access.pdf"