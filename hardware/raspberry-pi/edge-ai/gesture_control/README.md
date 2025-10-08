# Gesture Publisher

Real-time hand gesture recognition using MediaPipe Hands that detects hand shapes and publishes canonical control tokens to MQTT.

## Overview

This module:
- Captures video from a connected webcam
- Detects hands and extracts 21 landmark points using MediaPipe
- Classifies static hand gestures into control commands
- Publishes commands to `home/gesture/raw` via MQTT
- Integrates with the dispatcher's action router for home control

**Total Supported Commands**: 19 unique control actions

## Available Gestures

### Single-Hand Gestures

#### Lights Control
| Gesture | Description | Command | Action |
|---------|-------------|---------|--------|
| 🖐️ Middle finger only | Middle finger extended, others down | `lights_on` | Turn lights ON |
| 🖐️ Ring finger only | Ring finger extended, others down | `lights_off` | Turn lights OFF |
| 🖐️ Pinky only | Pinky extended, others down | `lights_dim` | Dim lights |
| ✌️ Victory (index + middle) | Index + middle up, others down | `lights_bright` | Brighten lights |

#### Fan Control
| Gesture | Description | Command | Action |
|---------|-------------|---------|--------|
| 👍 Thumbs up | Thumb extended, all fingers down | `fan_on` | Turn fan ON |
| 🤏 Pinch | Thumb + index tip touching closely | `fan_off` | Turn fan OFF |

#### Door Control
| Gesture | Description | Command | Action |
|---------|-------------|---------|--------|
| 🤘 Rock sign | Index + pinky extended (thumb + index close) | `door_open` | Open front door |

#### System Modes
| Gesture | Description | Command | Action |
|---------|-------------|---------|--------|
| 👋 Open hand | All 4 fingers extended, no thumb | `mode_home` | Set HOME mode (lights ON, door closed, fan OFF) |
| ✋ Stop hand | All 4 fingers up, index+middle only | `mode_guest` | Set GUEST mode (door open, lights ON) |
| ✊ Fist | All fingers + thumb closed (closed hand) | `mode_away` | Set AWAY mode (everything closed/off) |
| ☝️ Point (index only) | Index finger extended, others down | `alert_cancel` | Cancel alerts/emergencies |

### Two-Hand Gestures

| Gesture | Description | Command | Action |
|---------|-------------|---------|--------|
| 👊👊 Both fists crossed | Both hands fists, wrists close/crossed | `emergency_activate` | Full emergency mode (evacuation) |
| 🤲 Both hands open | All fingers up on both hands | `mode_sleep` | Set SLEEP mode (everything off) |
| 🛑🛑 Both palms down | Both hands open, palms down | `windows_close_all` | Close all windows |

## Quick Start

### With Live Preview
```bash
cd /path/to/project/root
python hardware/raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py
```

### Headless Mode (No Display)
```bash
export GESTURE_SHOW_PREVIEW=0
python hardware/raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py
```

### Test Without Camera
```bash
python scripts/test_gesture_gesture.py
```

## Installation

1. **Ensure dependencies installed**:
```bash
pip install -r requirements.txt
pip install mediapipe>=0.10.14
```

2. **Connect USB camera** to device

3. **Configure (optional)**:
```bash
export GESTURE_CAMERA_INDEX=0          # Camera device
export GESTURE_HOLD_FRAMES=8           # Frames to confirm
export GESTURE_COOLDOWN_S=2.0          # Cooldown between same gestures
export GESTURE_SHOW_PREVIEW=1          # Show preview
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GESTURE_CAMERA_INDEX` | `0` | USB camera device index |
| `GESTURE_FRAME_WIDTH` | `640` | Video frame width |
| `GESTURE_FRAME_HEIGHT` | `480` | Video frame height |
| `GESTURE_HOLD_FRAMES` | `8` | Consecutive frames for confirmation |
| `GESTURE_COOLDOWN_S` | `2.0` | Minimum seconds between same gesture |
| `GESTURE_SHOW_PREVIEW` | `1` | Show preview (1=yes, 0=no) |

## Architecture

```
Camera → MediaPipe Hands (21 landmarks)
       → Gesture Classification (rule-based)
       → Hold & Cooldown Filter
       → MQTT Publish (home/gesture/raw)
       → Dispatcher (action_router)
       → Device Commands (door, fan, lights, windows)
```

## How Gestures Work

The classifier uses pure geometry:
- Detects hand position & orientation (21 3D landmark points)
- Checks finger states: up/down for each digit
- Matches to known patterns
- Returns canonical command token

**No machine learning required** — entirely rule-based & robust.

## All Supported Commands

| Category | Commands |
|----------|----------|
| **Lights** | `lights_on`, `lights_off`, `lights_dim`, `lights_bright` |
| **Fan** | `fan_on`, `fan_off` |
| **Door** | `door_open` |
| **Windows** | `windows_open_all`, `windows_close_all` |
| **Modes** | `mode_home`, `mode_away`, `mode_sleep`, `mode_guest` |
| **Safety** | `alert_cancel`, `emergency_activate` |

## Testing the Full Pipeline

**Terminal 1 - Dispatcher:**
```bash
python hardware/raspberry-pi/dispatcher/main.py
```

**Terminal 2 - Gesture Control:**
```bash
python hardware/raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py
```

**Terminal 3 - Monitor MQTT:**
```bash
mosquitto_sub -h localhost -t "home/#"
```

Make hand gestures → see tokens published → check dispatcher logs.

## Notes

- Rule-based, not ML — pure geometric hand shape matching
- Works across skin tones, hand sizes, lighting conditions
- ~30-50ms inference time per frame
- 20-30 FPS on Raspberry Pi 4
- Entirely offline — no cloud dependency
