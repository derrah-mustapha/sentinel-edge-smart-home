#!/usr/bin/env bash

set -euo pipefail

command -v ip >/dev/null 2>&1 || {
  echo "Error: 'ip' command not found." >&2
  exit 1
}

command -v ss >/dev/null 2>&1 || {
  echo "Error: 'ss' command not found." >&2
  exit 1
}

LOCAL_IFACE="$(ip route show default 2>/dev/null | awk 'NR==1 {print $5}')"
LOCAL_IP=""
if [[ -n "$LOCAL_IFACE" ]]; then
  LOCAL_IP="$(ip -4 addr show dev "$LOCAL_IFACE" 2>/dev/null | awk '/inet / {print $2; exit}')"
  LOCAL_IP="${LOCAL_IP%%/*}"
fi

if [[ -z "$LOCAL_IFACE" || -z "$LOCAL_IP" ]]; then
  echo "Could not detect active Wi-Fi interface/IP." >&2
  exit 1
fi

BROKER_PORT="${1:-1883}"

printf 'Wi-Fi interface : %s\n' "$LOCAL_IFACE"
printf 'Wi-Fi IP        : %s\n' "$LOCAL_IP"
printf 'MQTT port       : %s\n' "$BROKER_PORT"

echo
if command -v nc >/dev/null 2>&1; then
  if nc -vz -w 2 "$LOCAL_IP" "$BROKER_PORT" >/dev/null 2>&1; then
    echo "LAN test        : broker reachable on $LOCAL_IP:$BROKER_PORT"
  else
    echo "LAN test        : broker NOT reachable on $LOCAL_IP:$BROKER_PORT"
  fi
else
  echo "LAN test        : nc not installed, skipping direct connection test"
fi

echo
LISTEN_LINES="$(ss -ltn | awk -v port=":$BROKER_PORT" '$4 ~ port {print}')"
if [[ -z "$LISTEN_LINES" ]]; then
  echo "Listen check    : nothing is listening on port $BROKER_PORT"
  exit 0
fi

echo "Listen check    :"
printf '%s\n' "$LISTEN_LINES"

echo
if printf '%s\n' "$LISTEN_LINES" | grep -q '127.0.0.1:'; then
  echo "Diagnosis       : broker is bound to localhost only. The NodeMCU cannot reach it over Wi-Fi."
  echo "Fix             : reconfigure Mosquitto to listen on 0.0.0.0, or stop the host broker and run the Docker broker instead."
else
  echo "Diagnosis       : broker appears to be listening on a non-loopback interface."
fi
