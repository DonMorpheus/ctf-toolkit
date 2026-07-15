#!/usr/bin/env bash
# Install ForceCommand trap (requires root). Lab / authorized scope only.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
install -m 755 "$DIR/require_agent_forward.sh" /usr/local/bin/require_agent_forward.sh
echo "[+] Installed /usr/local/bin/require_agent_forward.sh"
echo "[+] Merge sshd_match_legacy.snippet into your sshd config, then restart sshd."
echo "[+] Full lab on Kali: ~/Desktop/htb/ttp-docker-ssh-lab/setup_kali_user.sh"