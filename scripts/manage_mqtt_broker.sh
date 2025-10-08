#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"
COMPOSE_DIR="$ROOT_DIR/docker"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.yml"
DEFAULT_PORT=1883
HOST_SERVICE_NAME="${HOST_BROKER_SERVICE:-mosquitto}"
HOST_LAN_CONF_PATH="/etc/mosquitto/conf.d/local-lan.conf"

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

local_iface="$(ip route show default 2>/dev/null | awk 'NR==1 {print $5}')"
local_ip=""
if [[ -n "$local_iface" ]]; then
  local_ip="$(ip -4 addr show dev "$local_iface" 2>/dev/null | awk '/inet / {print $2; exit}')"
  local_ip="${local_ip%%/*}"
fi

broker_host="$(read_env_value MQTT_BROKER_HOST)"
broker_port="$(read_env_value MQTT_BROKER_PORT)"
env_name="$(read_env_value ENV)"

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

can_connect() {
  local host="$1"
  local port="$2"

  if has_cmd nc; then
    nc -z -w 2 "$host" "$port" >/dev/null 2>&1
    return $?
  fi

  timeout 2 bash -c ">/dev/tcp/${host}/${port}" >/dev/null 2>&1
}

host_service_active() {
  if has_cmd systemctl; then
    systemctl is-active --quiet "$HOST_SERVICE_NAME"
    return $?
  fi

  if has_cmd service; then
    service "$HOST_SERVICE_NAME" status >/dev/null 2>&1
    return $?
  fi

  return 1
}

docker_broker_running() {
  if ! has_cmd docker; then
    return 1
  fi

  local container_id
  container_id="$(cd "$COMPOSE_DIR" && docker compose ps -q broker 2>/dev/null || true)"
  [[ -n "$container_id" ]] || return 1
  [[ "$(docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null || echo false)" == "true" ]]
}

print_listeners() {
  local port="$1"
  echo "Listeners on port ${port}:"
  ss -ltn | awk -v p=":${port}" '$4 ~ p {print}' || true
}

host_broker_state() {
  if host_service_active; then
    echo "up"
  else
    echo "down"
  fi
}

docker_broker_state() {
  if docker_broker_running; then
    echo "up"
  else
    echo "down"
  fi
}

detect_listener_owner() {
  local listener_lines
  listener_lines="$(ss -ltn | awk -v port=":${broker_port}" '$4 ~ port {print}')"

  if [[ -z "$listener_lines" ]]; then
    echo "none"
    return
  fi

  if printf '%s\n' "$listener_lines" | grep -q '127.0.0.1:'; then
    echo "host"
    return
  fi

  if printf '%s\n' "$listener_lines" | grep -q '0.0.0.0:'; then
    if docker_broker_running; then
      echo "docker"
    else
      echo "host"
    fi
    return
  fi

  echo "unknown"
}

print_host_lan_enable_commands() {
  echo "Host broker LAN enable commands"
  echo "  1) Create listener config:"
  echo "     sudo tee ${HOST_LAN_CONF_PATH} >/dev/null <<'EOF'"
  echo "     listener ${broker_port} 0.0.0.0"
  echo "     protocol mqtt"
  echo "     allow_anonymous true"
  echo "     EOF"
  echo
  echo "  2) Restart host broker:"
  echo "     sudo systemctl restart ${HOST_SERVICE_NAME}"
  echo
  echo "  3) Verify listener and LAN reachability:"
  echo "     ss -ltn | grep ':${broker_port}'"
  if [[ -n "$local_ip" ]]; then
    echo "     nc -vz -w 2 ${local_ip} ${broker_port}"
  fi
}

apply_host_lan_config() {
  echo "Applying host Mosquitto LAN config to ${HOST_LAN_CONF_PATH}..."

  local backup_path
  backup_path="${HOST_LAN_CONF_PATH}.bak.$(date +%Y%m%d_%H%M%S)"

  if sudo test -f "$HOST_LAN_CONF_PATH"; then
    echo "Creating backup: ${backup_path}"
    sudo cp "$HOST_LAN_CONF_PATH" "$backup_path"
  fi

  sudo tee "$HOST_LAN_CONF_PATH" >/dev/null <<EOF
listener ${broker_port} 0.0.0.0
protocol mqtt
allow_anonymous true
EOF

  echo "Restarting host broker (${HOST_SERVICE_NAME})..."
  if has_cmd systemctl; then
    sudo systemctl restart "$HOST_SERVICE_NAME"
  elif has_cmd service; then
    sudo service "$HOST_SERVICE_NAME" restart
  else
    echo "No supported host service manager found." >&2
    return 1
  fi

  echo "Host LAN config applied."
}

status_report() {
  local lan_ok="unknown"
  local loopback_ok="unknown"

  echo "Active config"
  echo "  ENV               : ${env_name}"
  echo "  MQTT_BROKER_HOST  : ${broker_host}"
  echo "  MQTT_BROKER_PORT  : ${broker_port}"
  if [[ -n "$local_ip" ]]; then
    echo "  Wi-Fi IP          : ${local_ip}"
  fi
  echo

  echo "Broker states"
  echo "  Host service      : $(host_broker_state) ($HOST_SERVICE_NAME)"
  echo "  Docker broker     : $(docker_broker_state)"
  echo "  Listener owner    : $(detect_listener_owner)"
  echo

  print_listeners "$broker_port"
  echo

  if [[ -n "$local_ip" ]]; then
    if can_connect "$local_ip" "$broker_port"; then
      echo "LAN reachability   : $local_ip:$broker_port reachable"
      lan_ok="yes"
    else
      echo "LAN reachability   : $local_ip:$broker_port not reachable"
      lan_ok="no"
    fi
  fi

  if can_connect 127.0.0.1 "$broker_port"; then
    echo "Loopback reachability : 127.0.0.1:$broker_port reachable"
    loopback_ok="yes"
  else
    echo "Loopback reachability : 127.0.0.1:$broker_port not reachable"
    loopback_ok="no"
  fi

  if [[ "$(host_broker_state)" == "up" && "$loopback_ok" == "yes" && "$lan_ok" == "no" ]]; then
    echo
    echo "Hint: host broker looks localhost-only. Run this to open LAN access:"
    echo "  ./scripts/manage_mqtt_broker.sh --print-host-lan-commands"
  fi
}

start_host_broker() {
  echo "Starting host broker ($HOST_SERVICE_NAME)..."
  if has_cmd systemctl; then
    sudo systemctl start "$HOST_SERVICE_NAME"
    return $?
  fi

  if has_cmd service; then
    sudo service "$HOST_SERVICE_NAME" start
    return $?
  fi

  echo "No supported host service manager found." >&2
  return 1
}

stop_host_broker() {
  echo "Stopping host broker ($HOST_SERVICE_NAME)..."
  if has_cmd systemctl; then
    sudo systemctl stop "$HOST_SERVICE_NAME"
    return $?
  fi

  if has_cmd service; then
    sudo service "$HOST_SERVICE_NAME" stop
    return $?
  fi

  echo "No supported host service manager found." >&2
  return 1
}

start_docker_broker() {
  if ! has_cmd docker; then
    echo "Docker is not installed, cannot start the container broker." >&2
    return 1
  fi

  echo "Starting Docker broker..."
  (cd "$COMPOSE_DIR" && docker compose up -d broker)
}

stop_docker_broker() {
  if ! has_cmd docker; then
    echo "Docker is not installed, cannot stop the container broker." >&2
    return 1
  fi

  echo "Stopping Docker broker..."
  (cd "$COMPOSE_DIR" && docker compose stop broker)
}

switch_to_host() {
  stop_docker_broker || true
  start_host_broker
}

switch_to_docker() {
  stop_host_broker || true
  start_docker_broker
}

show_menu() {
  echo
  echo "Choose an action:"
  echo "  1) Refresh status"
  echo "  2) Start host broker"
  echo "  3) Stop host broker"
  echo "  4) Start Docker broker"
  echo "  5) Stop Docker broker"
  echo "  6) Switch to host broker"
  echo "  7) Switch to Docker broker"
  echo "  8) Show host LAN enable commands"
  echo "  9) Apply host LAN config now (sudo)"
  echo " 10) Exit"
  echo
  read -r -p "Select [1-10]: " choice

  case "$choice" in
    1) clear; status_report ;;
    2) start_host_broker ;;
    3) stop_host_broker ;;
    4) start_docker_broker ;;
    5) stop_docker_broker ;;
    6) switch_to_host ;;
    7) switch_to_docker ;;
    8) print_host_lan_enable_commands ;;
    9) apply_host_lan_config ;;
    10) exit 0 ;;
    *) echo "Invalid option." ;;
  esac
}

case "${1:-}" in
  --status)
    status_report
    exit 0
    ;;
  --host)
    start_host_broker
    exit 0
    ;;
  --docker)
    start_docker_broker
    exit 0
    ;;
  --switch-host)
    switch_to_host
    exit 0
    ;;
  --switch-docker)
    switch_to_docker
    exit 0
    ;;
  --print-host-lan-commands)
    print_host_lan_enable_commands
    exit 0
    ;;
  --apply-host-lan)
    apply_host_lan_config
    status_report
    exit 0
    ;;
esac

while true; do
  clear
  status_report
  show_menu
done