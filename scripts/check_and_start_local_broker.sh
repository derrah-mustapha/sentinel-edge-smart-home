#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.yml"
DEFAULT_PORT=1883

command -v ss >/dev/null 2>&1 || {
  echo "Error: 'ss' command not found." >&2
  exit 1
}

read_env_value() {
  local key="$1"
  local value=""

  if [[ -f "$ENV_FILE" ]]; then
    value="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true)"
  fi

  if [[ -z "$value" ]]; then
    case "$key" in
      ENV) value="local" ;;
      MQTT_BROKER_HOST) value="localhost" ;;
      MQTT_BROKER_PORT) value="$DEFAULT_PORT" ;;
    esac
  fi

  printf '%s' "$value"
}

broker_host="$(read_env_value MQTT_BROKER_HOST)"
broker_port="$(read_env_value MQTT_BROKER_PORT)"
env_name="$(read_env_value ENV)"

echo "Active config"
echo "  ENV               : ${env_name}"
echo "  MQTT_BROKER_HOST  : ${broker_host}"
echo "  MQTT_BROKER_PORT  : ${broker_port}"
echo

is_reachable() {
  local host="$1"
  local port="$2"

  if command -v nc >/dev/null 2>&1; then
    nc -z -w 2 "$host" "$port" >/dev/null 2>&1
    return $?
  fi

  ss -ltn | awk -v p=":${port}" '$4 ~ p {found=1} END {exit found ? 0 : 1}'
}

print_listeners() {
  local port="$1"
  echo "Listeners on port ${port}:"
  ss -ltn | awk -v p=":${port}" '$4 ~ p {print}' || true
}

start_broker_with_compose() {
  if [[ ! -f "$COMPOSE_FILE" ]]; then
    echo "Compose file not found: $COMPOSE_FILE" >&2
    return 1
  fi

  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is not installed, so the broker cannot be started automatically." >&2
    return 1
  fi

  echo "Starting Mosquitto broker from Docker Compose..."
  (cd "$ROOT_DIR/docker" && docker compose up -d broker)
}

if is_reachable 127.0.0.1 "$broker_port"; then
  echo "Broker status    : up"
  print_listeners "$broker_port"
  exit 0
fi

echo "Broker status    : down"
print_listeners "$broker_port"
echo

if [[ "$broker_host" != "localhost" && "$broker_host" != "127.0.0.1" ]]; then
  echo "Note             : .env is not set to a local broker host, so this script will not start one for you."
  exit 1
fi

if start_broker_with_compose; then
  sleep 2
  if is_reachable 127.0.0.1 "$broker_port"; then
    echo "Broker status    : up after start"
    print_listeners "$broker_port"
    exit 0
  fi
fi

echo "Broker status    : still down"
echo "Tip              : check Docker logs with 'docker compose -f docker/docker-compose.yml logs -f broker'"
exit 1