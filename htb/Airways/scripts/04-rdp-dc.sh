#!/usr/bin/env bash
# Isabel has SeRemoteInteractiveLogonRight on DC01. Logon applies the user GPO.
set -euo pipefail
: "${ISABEL_PASS:?}"
SOCKS="${SOCKS:-127.0.0.1:1080}"
DC_IP="${DC_IP:-192.168.100.1}"
USER="${ISABEL_USER:-Isabel.O}"
DOMAIN="${DOMAIN:-AIRWAYS}"
exec xfreerdp3 \
  /v:"$DC_IP" \
  /u:"$USER" \
  /d:"$DOMAIN" \
  /p:"$ISABEL_PASS" \
  /proxy:socks5://"$SOCKS" \
  /cert:ignore \
  /sec:nla \
  /t:HTB-DC01-Isabel \
  /bpp:16 \
  +clipboard
