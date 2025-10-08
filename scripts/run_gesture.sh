#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python hardware/raspberry-pi/edge-ai/gesture_control/src/main.py
