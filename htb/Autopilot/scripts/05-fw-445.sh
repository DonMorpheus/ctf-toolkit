#!/bin/bash
# firewalld public zone REJECT 445 until this runs as root on mail.
set -euo pipefail
. "$(dirname "$0")/00-env.sh"

ssh -p 2222 -i "$SSH_KEY" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  root@127.0.0.1 '
firewall-cmd --add-port=445/tcp
firewall-cmd --add-port=139/tcp
firewall-cmd --list-ports
ss -lntp | grep :445 || true
'
echo "[+] inbound 445/139 open (runtime). Re-run after reboot/reset."
