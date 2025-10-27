# Gesture Control Complete Reference

## Summary

The Sentinel Edge gesture control system supports **16 active control commands** mapped to **15 distinct hand gestures** (single & two-hand). The gesture publisher intentionally emits only the active set; window-only and status-only tokens are kept out of the live path.

## Single-Hand Gesture Mapping

### Finger-Based Commands (Lights & Fan)

**Isolated Single Finger Patterns:**
- **Thumbs Up (Thumb extended, all fingers down)**: `fan_on` — Turn fan ON
- **Middle only**: `lights_on` — Turn lights ON  
- **Ring only**: `lights_off` — Turn lights OFF
- **Pinky only**: `lights_dim` — Dim lights

**Multi-Finger Patterns:**
- **Victory/Peace (Index + Middle)**: `lights_bright` — Brighten lights
- **Rock sign (Index + Pinky)**: `door_open` — Open front door

### Fist & Hand Shapes

- **Open Hand (All 4 fingers extended, no thumb)**: `mode_home` — HOME mode
- **Fist (All fingers + thumb fully closed)**: `mode_away` — AWAY mode
- **Index + Middle only (other fingers down)**: `mode_guest` — GUEST mode

### Special Gestures

- **Pinch (Thumb + Index very close)**: `fan_off` — Turn fan OFF
- **Point (Index only)**: `alert_cancel` — Cancel alerts/emergency

### Complex Patterns

- **Three Fingers (Index + Middle + Ring)**: `windows_open_all` — Open all windows (virtual-only in dispatcher)

## Two-Hand Gesture Mapping

| Gesture | Pattern | Command | Action |
|---------|---------|---------|--------|
| **Both Fists Crossed** | Two closed fists, wrists very close | `emergency_activate` | EMERGENCY mode (evacuate) |
| **Both Hands Open** | All fingers up on both hands | `mode_sleep` | SLEEP mode |
| **Both Palms Down** | Both hands open, palms facing down/away | `windows_close_all` | Close all windows |
| **Hands Crossed (Fists)** | Both fists, hands overlapping horizontally | `door_close` | Close front door |

## Complete Command List (16 Active Commands)

### Control Commands

| Category | Command | Method | Details |
|----------|---------|--------|---------|
| **Lights** | `lights_on` | Middle finger only | Turn lights ON |
| | `lights_off` | Ring finger only | Turn lights OFF |
| | `lights_dim` | Pinky only | Dim lights |
| | `lights_bright` | Victory sign (index+middle) | Brighten lights |
| **Fan** | `fan_on` | Thumbs up | Turn fan ON |
| | `fan_off` | Pinch (thumb+index) | Turn fan OFF |
| **Door** | `door_open` | Rock sign (index+pinky) | Open front door |
| | `door_close` | Two fists crossed (horizontal) | Close front door |
| **Windows** | `windows_open_all` | Three fingers (index+middle+ring) | Virtual state only |
| | `windows_close_all` | Two palms down facing out | Virtual state only |
| **Modes** | `mode_home` | Open hand (all 4 fingers) | HOME: door closed, lights on, fan off |
| | `mode_away` | Fist (closed hand) | AWAY: everything closed/off |
| | `mode_sleep` | Both hands open | SLEEP: everything off, lights off |
| | `mode_guest` | Index + Middle only | GUEST: door open, lights on |
| **Safety** | `alert_cancel` | Point (index only) | Cancel alert/emergency |
| | `emergency_activate` | Both fists crossed | EMERGENCY: door open, lights on, fan on, valves closed |

## Intentionally Omitted Tokens

The live gesture publisher does not emit some doc-only tokens that are kept for dispatcher compatibility and future expansion. The currently omitted tokens are:

- `emergency_cancel`
- `status_query`
- `window_open_1`
- `window_close_1`
- `window_open_2`
- `window_close_2`

## Gesture Detection Details

### How Gestures Are Detected

Each hand captures 21 3D landmark points (MediaPipe Hands):
- **0**: Wrist
- **1-4**: Thumb (CMC, MCP, IP, TIP)
- **5-8**: Index (MCP, PIP, DIP, TIP)
- **9-12**: Middle (MCP, PIP, DIP, TIP)
- **13-16**: Ring (MCP, PIP, DIP, TIP)
- **17-20**: Pinky (MCP, PIP, DIP, TIP)

**Classification checks:**
1. Which fingers are **up** (tip above MCP joint)?
2. Is thumb **extended** (horizontally away from wrist)?
3. Are nearby fingers **close** (pinch)?
4. What is **palm orientation** (facing up/down)?

### Filter Stages

```
Raw Gesture Detection
    ↓
Hold Filter (8 frames = ~300-400ms)
    ↓
Cooldown Filter (2 seconds between same gesture)
    ↓
MQTT Publish (confirmed gesture only)
```

This prevents:
- False positives from brief hand movements
- Rapid repeated triggers
- Accidental double-commands

## Performance Metrics

- **Detection latency**: ~30-50ms (CPU, Raspberry Pi 4)
- **Frame rate**: 20-30 FPS at 640x480
- **Total latency gesture→MQTT**: 200-500ms (includes hold time)
- **CPU usage**: 25-35% (gesture detection only)
- **Memory**: ~150-200MB (MediaPipe model + Python runtime)

## Configuration Tuning

### For Slow Recognition
```bash
export GESTURE_HOLD_FRAMES=5          # Reduce from 8
export GESTURE_COOLDOWN_S=1.0         # Reduce from 2.0
export GESTURE_MIN_DETECTION_CONFIDENCE=0.6  # Reduce from 0.7
```

### For Stability (Avoid False Positives)
```bash
export GESTURE_HOLD_FRAMES=12         # Increase from 8
export GESTURE_COOLDOWN_S=3.0         # Increase from 2.0
export GESTURE_MIN_DETECTION_CONFIDENCE=0.8  # Increase from 0.7
```

### For Multiple Cameras
```bash
export GESTURE_CAMERA_INDEX=0         # First camera
# or
export GESTURE_CAMERA_INDEX=1         # Second camera
```

## Integration with Dispatcher

Gesture → MQTT (`home/gesture/raw`) → Dispatcher → `home/commands`

Example flow:
```
User makes "Thumbs Up" gesture
        ↓
Detector recognizes: fan_on
        ↓
Publishes to: home/gesture/raw = "fan_on"
        ↓
Dispatcher receives on TOPICS.GESTURE_RAW
        ↓
Routes: on_gesture_command("fan_on")
        ↓
Publishes: home/commands = "fan_on"
        ↓
MCU receives and turns on the fan output
```

## Gesture Combinations (Future)

These could be extended to:
- Individual window control if hardware is added later
- Emergency cancel as a dedicated gesture
- Status query as a dedicated gesture
- Device-specific commands (light zones, etc.)

## Voice vs Gesture

Both use the **same active command tokens**, so they're fully interchangeable:

| Command | Voice Example | Gesture |
|---------|---------------|---------|
| `fan_on` | "turn fan on" | Thumbs up |
| `door_open` | "open door" | Rock sign |
| `mode_home` | "home mode" | Open hand |
| `lights_bright` | "bright lights" | Victory sign |

## Testing Checklist

- [ ] Camera connected and detected (`ls /dev/video*`)
- [ ] MediaPipe installed (`pip list | grep mediapipe`)
- [ ] Can run with preview: `GESTURE_SHOW_PREVIEW=1`
- [ ] Gestures appear in terminal output
- [ ] MQTT topics received by dispatcher
- [ ] Device commands executed (lights on/off, fan, etc.)

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No gestures detected | Hand too far/small | Move closer to camera |
| Too many false positives | Low detection threshold | Increase `GESTURE_MIN_DETECTION_CONFIDENCE` |
| Slow response | High hold frames | Reduce `GESTURE_HOLD_FRAMES` |
| Repeated triggers | Low cooldown | Increase `GESTURE_COOLDOWN_S` |
| Black screen with preview | Camera index wrong | Try `GESTURE_CAMERA_INDEX=1` or `2` |
| MediaPipe errors | Incompatible version | Install `mediapipe==0.10.14` |
