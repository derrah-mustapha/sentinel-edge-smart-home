#!/usr/bin/env bash

set -euo pipefail

RAW_OUTPUT=false
if [[ "${1:-}" == "--raw" ]]; then
  RAW_OUTPUT=true
fi

command -v ip >/dev/null 2>&1 || {
  echo "Error: 'ip' command not found." >&2
  exit 1
}

# Prefer the interface used for the default route (usually your active Wi-Fi interface).
DEFAULT_IFACE="$(ip route show default 2>/dev/null | awk 'NR==1 {print $5}')"

if [[ -z "$DEFAULT_IFACE" ]]; then
  echo "Could not detect active network interface from default route." >&2
  echo "Make sure you are connected to a network." >&2
  exit 1
fi

IP_CIDR="$(ip -4 addr show dev "$DEFAULT_IFACE" 2>/dev/null | awk '/inet / {print $2; exit}')"
IP_ADDR="${IP_CIDR%%/*}"

if [[ -z "$IP_ADDR" ]]; then
  echo "No IPv4 address found on interface '$DEFAULT_IFACE'." >&2
  echo "Try reconnecting to Wi-Fi and run again." >&2
  exit 1
fi

if [[ "$RAW_OUTPUT" == true ]]; then
  echo "$IP_ADDR"
  exit 0
fi

echo "Active interface : $DEFAULT_IFACE"
echo "Local IPv4       : $IP_ADDR"
echo "Use this in NodeMCU as MQTT_BROKER if your broker runs on this laptop."
