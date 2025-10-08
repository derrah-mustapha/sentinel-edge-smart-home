#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

target="${1:-local}"

if [[ "$target" != "local" && "$target" != "cloud" && "$target" != "dev" ]]; then
  echo "Usage: scripts/switch_broker.sh [local|cloud|dev]"
  exit 1
fi

if [[ ! -f ".env.${target}" ]]; then
  echo "Missing .env.${target}"
  exit 1
fi

cp ".env.${target}" .env

echo "Switched broker config to ${target} (.env)"
