#!/usr/bin/env bash
# RDP launcher — danglingtree.htb
# UWAGA: noah.b NIE jest w "Remote Desktop Users" → pełna sesja RDP pada (post_connect).
# Działa pod kątem auth test / gdy user ma RDP (np. jake.h w DevOps_PKI).
set -euo pipefail

IP="${1:-10.129.6.118}"
USER="${RDP_USER:-noah.b}"
PASS="${RDP_PASS:-RiverDragon#Storm25}"
DOMAIN="${RDP_DOMAIN:-DANGLINGTREE}"

if command -v xfreerdp3 >/dev/null 2>&1; then
  RDP=xfreerdp3
elif command -v xfreerdp >/dev/null 2>&1; then
  RDP=xfreerdp
else
  echo "[-] brak xfreerdp3" >&2
  exit 1
fi

if ! ip -br a 2>/dev/null | grep -q tun; then
  echo "[!] brak tun0 — włącz VPN HTB"
fi

# soft clock hint (box jest zwykle ~UTC+7h względem "zepsutego" lokalnego)
echo "[i] Jeśli padnie Kerberos/NLA: zsynchronizuj czas z DC (rdp-ntlm-info System_Time)"
echo "[*] $RDP  ${DOMAIN}\\${USER}@${IP}"
echo "[i] force NTLM (bez KDC). Grupa RDP Users: tylko jake (DevOps_PKI / Helpdesk_Cert_Support)"

# reszta args z CLI idzie dalej
shift || true

exec "$RDP" \
  "/v:${IP}" \
  "/u:${USER}" \
  "/d:${DOMAIN}" \
  "/p:${PASS}" \
  /cert:ignore \
  /sec:nla \
  '/auth-pkg-list:ntlm,!kerberos' \
  /network:auto \
  /bpp:16 \
  /gdi:sw \
  +clipboard \
  /log-level:INFO \
  "$@"
