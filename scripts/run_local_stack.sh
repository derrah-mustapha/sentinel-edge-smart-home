#!/usr/bin/env bash
set -euo pipefail

# Run all local services for testing: dispatcher, gesture, voice
# Usage: scripts/run_local_stack.sh

cd "$(dirname "$0")/.."

# activate virtualenv if present
if [ -f venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

# Ensure model path exists (adjust if you keep models elsewhere)
export VOSK_MODEL_PATH="$PWD/hardware/raspberry-pi/edge-ai/voice_control/models/vosk-model-small-en-us-0.15"
export GESTURE_CAMERA_INDEX=${GESTURE_CAMERA_INDEX:-0}

mkdir -p logs

# Start dispatcher
nohup python3 hardware/raspberry-pi/dispatcher/main.py > logs/dispatcher.log 2>&1 &
echo $! > logs/dispatcher.pid

# Start gesture (camera) publisher
nohup python3 hardware/raspberry-pi/edge-ai/gesture_control/gesture_publisher.py > logs/gesture.log 2>&1 &
echo $! > logs/gesture.pid

# Start voice (mic) publisher
nohup python3 hardware/raspberry-pi/edge-ai/voice_control/voice_publisher.py --verbose > logs/voice.log 2>&1 &
echo $! > logs/voice.pid

echo "Started dispatcher, gesture, voice. Logs are in ./logs/"
