#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python hardware/raspberry-pi/dispatcher/main.py
