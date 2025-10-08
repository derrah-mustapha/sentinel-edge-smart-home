# Gesture Control Notes

This module publishes canonical gesture labels to MQTT topic `home/gesture/raw`.

## Vocabulary Contract (Phase 1)

- `OPEN_HAND` -> open front door
- `FIST` -> close front door
- `FAN_ON` -> turn fan on
- `FAN_OFF` -> turn fan off

Only these labels should be emitted by the gesture detector. Any unknown label must be ignored.

## Current Status

- MQTT publisher loop is connected and running.
- Vocabulary normalization is implemented.
- Duplicate publish protection is enabled (cooldown + dedupe).
- Detector is still placeholder (`detect_gesture` returns `NONE`) until classifier integration.

## Next Implementation Tasks

1. Integrate MediaPipe Hands for landmark extraction.
2. Add simple rule-based classifier for the 4 canonical gestures.
3. Add confidence score and threshold filtering.
4. Publish only stable detections across consecutive frames.
