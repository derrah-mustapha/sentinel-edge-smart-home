#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env.cloud"
DEFAULT_URL="http://127.0.0.1:5000"

if [[ -f "${ROOT_DIR}/venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/venv/bin/activate"
fi

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a
  source "$ENV_FILE"
  set +a
fi

CF_TUNNEL_BIN="$(command -v cloudflared || true)"
if [[ -z "$CF_TUNNEL_BIN" && -x "$HOME/.local/bin/cloudflared" ]]; then
  CF_TUNNEL_BIN="$HOME/.local/bin/cloudflared"
fi

if [[ -z "$CF_TUNNEL_BIN" ]]; then
  echo "Error: cloudflared is not installed or not on PATH." >&2
  echo "Install it first, then rerun this script." >&2
  exit 1
fi

cd "$ROOT_DIR"

echo "Starting dashboard on ${DEFAULT_URL}..."
echo "Using MQTT broker: ${MQTT_BROKER_HOST:-localhost}:${MQTT_BROKER_PORT:-1883}"
echo
python3 dashboard/web/server.py > /tmp/sentinel-dashboard.log 2>&1 &
DASHBOARD_PID=$!

cleanup() {
  kill "$DASHBOARD_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "Waiting for the dashboard to be ready..."
for _ in $(seq 1 30); do
  if command -v curl >/dev/null 2>&1 && curl -fsS "$DEFAULT_URL" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Launching Cloudflare Tunnel..."
echo "Share the public URL printed below with the teacher."
echo
"$CF_TUNNEL_BIN" tunnel --url "$DEFAULT_URL"