# Quick Gesture Reference Cheat Sheet

Print this or keep nearby when using gesture control!

## 🖐️ Single-Hand Gestures

### Finger Commands (Just show the finger!)

```
☝️  Point (index only)        → alert_cancel  (Cancel alerts/emergency)
🖐️  Middle only               → lights_on     (Turn lights ON)  
🖐️  Ring only                 → lights_off    (Turn lights OFF)
🖐️  Pinky only                → lights_dim    (Dim lights)
✌️  Victory (index+middle)    → lights_bright (Brighten lights)
🤘  Rock sign (index+pinky)   → door_open     (Open door)
```

### Hand Shapes

```
👋  Open hand (all 4 fingers) → mode_home     (HOME: on lights, close door, off fan)
✊  Fist (closed hand)         → mode_away     (AWAY: close all, off all)
✋  Index+Middle only          → mode_guest    (GUEST: open door, on lights)
👍  Thumbs up                  → fan_on        (Turn fan ON)
🤏  Pinch (thumb+index close)  → fan_off       (Turn fan OFF)
```

## 🙌 Two-Hand Gestures  

```
👊👊 Both fists crossed         → emergency_activate (EMERGENCY evacuate)
🤲  Both hands open (all up)   → mode_sleep         (SLEEP: all off)
🛑🛑 Both palms down facing out → windows_close_all  (Close all windows)
👊🤝 Both fists overlapped      → door_close         (Close door)
```

## All 16 Active Commands

| # | Command | Gesture | Device |
|---|---------|---------|--------|
| 1 | `fan_on` | 👍 Thumbs | Fan |
| 2 | `fan_off` | 🤏 Pinch | Fan |
| 3 | `lights_on` | 🖐️ Middle | Lights |
| 4 | `lights_off` | 🖐️ Ring | Lights |
| 5 | `lights_dim` | 🖐️ Pinky | Lights |
| 6 | `lights_bright` | ✌️ Victory | Lights |
| 7 | `door_open` | 🤘 Rock | Door |
| 8 | `door_close` | 👊🤝 Crossed | Door |
| 9 | `windows_open_all` | 🖐️ 3-fingers | Virtual |
| 10 | `windows_close_all` | 🛑🛑 Both Down | Virtual |
| 11 | `mode_home` | 👋 Open | Mode |
| 12 | `mode_away` | ✊ Fist | Mode |
| 13 | `mode_sleep` | 🤲 Both Open | Mode |
| 14 | `mode_guest` | ✋ Two up | Mode |
| 15 | `alert_cancel` | ☝️ Point | Safety |
| 16 | `emergency_activate` | 👊👊 Crossed | Safety |

## System Modes

### HOME (👋 Open hand)
- Door: CLOSE
- Fan: OFF  
- Lights: ON
- Windows: CLOSE

### AWAY (✊ Fist)
- Door: CLOSE
- Fan: OFF
- Lights: OFF
- Windows: CLOSE

### SLEEP (🤲 Both open)
- Door: CLOSE
- Fan: OFF
- Lights: OFF
- Windows: CLOSE

### GUEST (✋ Index+Middle)
- Door: OPEN
- Lights: ON

### EMERGENCY (👊👊 Crossed)
- Door: OPEN
- Fan: ON
- Lights: ON
- Windows: OPEN
- Valves: CLOSED (gas/water safety shutoff)

## Tips

✅ **DO:**
- Hold gesture for ~1 second (let it register)
- Keep hand fully in frame
- Good lighting helps
- Try different distances
- Move slowly & deliberately

❌ **DON'T:**
- Flash gestures too quickly
- Partially show hand
- Move erratically
- Repeat same gesture back-to-back (2s cooldown)
- Use very dim lighting

## Quick Test

Run test without camera:
```bash
python scripts/test_gesture_gesture.py
```

See if dispatcher receives commands!

## Environment Setup

```bash
# Show preview while testing
export GESTURE_SHOW_PREVIEW=1

# Faster response (trade stability)
export GESTURE_HOLD_FRAMES=5
export GESTURE_COOLDOWN_S=1.0

# More stable (trade speed)
export GESTURE_HOLD_FRAMES=12
export GESTURE_COOLDOWN_S=3.0

# Different camera
export GESTURE_CAMERA_INDEX=1

# Headless (server mode)
export GESTURE_SHOW_PREVIEW=0
```

Run:
```bash
python hardware/raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py
```

---

**Questions?** Check:
- docs/GESTURE_CONTROL_REFERENCE.md (detailed reference)
- hardware/raspberry-pi/edge-ai/gesture_control/README.md (full guide)
