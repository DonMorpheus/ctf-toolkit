#!/usr/bin/env bash
# Usage: RDP_USER=jake.h RDP_PASS='...' ./rdp-user.sh
# same as rdp-noah but no hardcoded noah password
set -euo pipefail
IP="${1:-10.129.6.118}"
: "${RDP_USER:?ustaw RDP_USER}"
: "${RDP_PASS:?ustaw RDP_PASS}"
export RDP_DOMAIN="${RDP_DOMAIN:-DANGLINGTREE}"
exec "$(dirname "$0")/rdp-noah.sh" "$IP"
