# Complete System Integration Matrix

**Sentinel Edge Smart Home - End-to-End Command Flow**  
**Status**: May 31, 2026  

---

## Quick Reference: All 24 Commands

| # | Command | Voice | Gesture | Dispatcher | MCU | Hardware | Status |
|---|---------|-------|---------|------------|-----|----------|--------|
| 1 | `door_open` | ✅ | ✅ | ✅ | ✅ | ✅ Servo D5 | 🟢 Ready |
| 2 | `door_close` | ✅ | ✅ | ✅ | ✅ | ✅ Servo D5 | 🟢 Ready |
| 3 | `fan_on` | ✅ | ✅ | ✅ | ✅ | ✅ D0 output | 🟢 Ready |
| 4 | `fan_off` | ✅ | ✅ | ✅ | ✅ | ✅ D0 output | 🟢 Ready |
| 5 | `lights_on` | ✅ | ✅ | ✅ | ✅ | ✅ D1 PWM | 🟢 Ready |
| 6 | `lights_off` | ✅ | ✅ | ✅ | ✅ | ✅ D1 PWM | 🟢 Ready |
| 7 | `lights_dim` | ✅ | ✅ | ✅ | ✅ | ✅ D1 PWM | 🟢 Ready |
| 8 | `lights_bright` | ✅ | ✅ | ✅ | ✅ | ✅ D1 PWM | 🟢 Ready |
| 9 | `mode_home` | ✅ | ✅ | ✅ | ✅ | ✅ D8 indicator | 🟢 Ready |
| 10 | `mode_away` | ✅ | ✅ | ✅ | ✅ | ✅ D8 indicator | 🟢 Ready |
| 11 | `mode_sleep` | ✅ | ✅ | ✅ | ✅ | ✅ D8 indicator | 🟢 Ready |
| 12 | `mode_guest` | ✅ | ✅ | ✅ | ✅ | ✅ D8 indicator | 🟢 Ready |
| 13 | `emergency_activate` | ✅ | ✅ | ✅ | ✅ | ✅ outputs | 🟡 Runtime risk |
| 14 | `emergency_cancel` | ✅ | ❌ | ✅ | ✅ | ✅ outputs | 🟢 Ready |
| 15 | `alert_cancel` | ✅ | ✅ | ✅ | ✅ | ✅ outputs | 🟢 Ready |
| 16 | `status_query` | ✅ | ❌ | ✅ | ✅ | MQTT only | 🟢 Ready |
| 17 | `windows_open_all` | ✅ | ✅ | ✅ | ✅ | virtual-only | 🟡 Virtual |
| 18 | `windows_close_all` | ✅ | ✅ | ✅ | ✅ | virtual-only | 🟡 Virtual |
| 19 | `window_open_1` | ✅ | ❌ | ✅ | ✅ | virtual-only | 🟡 Virtual |
| 20 | `window_close_1` | ✅ | ❌ | ✅ | ✅ | virtual-only | 🟡 Virtual |
| 21 | `window_open_2` | ✅ | ❌ | ✅ | ✅ | virtual-only | 🟡 Virtual |
| 22 | `window_close_2` | ✅ | ❌ | ✅ | ✅ | virtual-only | 🟡 Virtual |
| 23 | `fan_on` duplicate? | - | - | - | - | - | - |
| 24 | `fan_off` duplicate? | - | - | - | - | - | - |

**Legend**:
- ✅ = Implemented and working
- ⚠️ = Partial (MCU receives individual commands that make up the mode)
- ⚠️* = Modes work as expected (MCU executes the door/fan parts)
- ❌ = Not implemented / no hardware
- 🟢 = Ready to use
- 🟡 = Partially working (some hardware implemented)
- 🔴 = Not ready / needs hardware

---

## Detailed Command Mappings

### Group 1: Door Control (2 commands) ✅

| Command | Voice | Gesture | MQTT Topic | Payload | GPIO | Hardware | Status |
|---------|-------|---------|-----------|---------|------|----------|--------|
| `door_open` | "open door" | 🤘 Rock | `home/commands` | door_open | D5 | SG90 Servo | ✅ Ready |
| `door_close` | "close door" | 👊 Crossed | `home/commands` | door_close | D5 | SG90 Servo | ✅ Ready |

**Behavior**:
```
OPEN/UNLOCK → Servo angle 90° → Door unlocks → Auto-lock after 5s
CLOSE/LOCK → Servo angle 0° → Door locks
```

---

### Group 2: Fan Control (2 commands) ✅

| Command | Voice | Gesture | MQTT Topic | Payload | GPIO | Hardware | Status |
|---------|-------|---------|-----------|---------|------|----------|--------|
| `fan_on` | "turn fan on" | ☝️ Point | `home/commands` | fan_on | D0 | Output | ✅ Ready |
| `fan_off` | "turn fan off" | 🤏 Pinch | `home/commands` | fan_off | D0 | Output | ✅ Ready |

**Behavior**:
```
ON → GPIO D1 HIGH → Relay closes → Motor runs
OFF → GPIO D1 LOW → Relay opens → Motor stops

Auto-response: Gas detected → Auto ON
```

---

### Group 3: Window Control (6 commands) 🔴

| Command | Dispatcher → Topic | Status | Missing |
|---------|-------------------|--------|---------|
| `window_open_1` | virtual state only | ✅ tracked | dashboard only |
| `window_close_1` | virtual state only | ✅ tracked | dashboard only |
| `window_open_2` | virtual state only | ✅ tracked | dashboard only |
| `window_close_2` | virtual state only | ✅ tracked | dashboard only |
| `windows_open_all` | virtual state only | ✅ tracked | dashboard only |
| `windows_close_all` | virtual state only | ✅ tracked | dashboard only |

**Future Implementation**:
```
1. Allocate GPIO pins (suggest D7, D8 for window 1&2)
2. Create WindowActuator.h class
3. Add handlers in MqttHandlers.h (replace TODO)
4. Wire servo motors & test
```

---

### Group 4: Lighting Control (4 commands) 🔴

| Command | Dispatcher → Topic | Status | Missing |
|---------|-------------------|--------|---------|
| `lights_on` | `home/commands` = lights_on | ✅ Subscribed | D1 PWM |
| `lights_off` | `home/commands` = lights_off | ✅ Subscribed | D1 PWM |
| `lights_dim` | `home/commands` = lights_dim | ✅ Subscribed | D1 PWM |
| `lights_bright` | `home/commands` = lights_bright | ✅ Subscribed | D1 PWM |

**Future Implementation**:
```
1. Allocate GPIO pin (suggest D6 with PWM)
2. Create LightController.h class
3. Implement DIM/BRIGHT as PWM duty cycle
4. Add handlers in MqttHandlers.h
5. Wire relay/dimmable circuit & test
```

---

### Group 5: System Modes (5 commands) 🟡

**How Modes Work**:

Modes are orchestrated by the dispatcher. When a mode command is sent, the dispatcher publishes individual device commands:

```
mode_home (from voice/gesture)
  → Dispatcher receives
  → Publishes:
    home/commands = mode_home          ✅ MCU executes
    home/state/door = locked           ✅ state snapshot
    home/state/fan = off               ✅ state snapshot
    home/state/lights = bright         ✅ state snapshot
```

**Current Behavior** (May 2026):
- ✅ Door closes (MCU handles)
- ✅ Fan turns off (MCU handles)
- ⚠️ Window commands received but logged as TODO
- ⚠️ Light commands received but logged as TODO

**When Complete**:
- ✅ All devices respond to mode
- ✅ Entire system state synchronized

| Mode | Dispatcher Sequence | Current MCU | When Complete |
|------|-------------------|-------------|---|
| **mode_home** | door locked, fan off, lights bright, windows virtual closed | ✅ All relevant states |
| **mode_away** | door locked, fan off, lights off, windows virtual closed | ✅ All relevant states |
| **mode_sleep** | door locked, fan off, lights off, windows virtual closed | ✅ All relevant states |
| **mode_guest** | door open, lights bright | ✅ All relevant states |

---

### Group 6: Safety & Emergency (5 commands) 🟡

| Command | Dispatcher Action | MCU Today | Notes |
|---------|------------------|-----------|-------|
| `emergency_activate` | flash outputs, close valves, open door | 🟡 Runtime risk | Exact flash timing needs bench check |
| `emergency_cancel` | return to home defaults | ✅ | Restores boot defaults |
| `alert_cancel` | reopen valves, clear alerts | ✅ | Safety reset only |

**Valve State Topics**:
```
home/state/gas_valve → open/closed
home/state/water_valve → open/closed
```

The hardware contract is already implemented on the MCU; the remaining risk is physical flash-and-bench validation on the ESP8266.

---

### Group 7: Status Query (1 command) 🔴

| Command | Dispatcher | MCU | Status |
|---------|------------|-----|--------|
| `status_query` | republishes `home/state/*` snapshot | ✅ | state refresh only |

**Future**:
- MCU should subscribe and log current mode
- Or respond with `home/system/mcu/status` with device states

---

## GPIO Pin Allocation

### Current (Implemented)

```
D0  - FAN OUTPUT
D1  - LIGHTS PWM
D2  - WATER VALVE OUTPUT
D4  - GAS SENSOR DO
D5  - DOOR SERVO
D6  - GAS VALVE OUTPUT
D7  - DOOR INDICATOR
D8  - MODE INDICATOR
A0  - WATER/FLOOD SENSOR AO
```

### Future (To Allocate)

```
D6  - LIGHT control (PWM for dim/bright)
D7  - WINDOW 1 servo (PWM)
D8  - WINDOW 2 servo (PWM)
D9  - GAS valve solenoid
D10 - WATER valve solenoid

Alternative if pins limited:
- Use I2C expander (PCF8574) for extra GPIO
- Or use shift register (74HC595)
```

---

## Hardware Compatibility

### Required Components (Currently Wired)

| Component | Model | GPIO | Purpose | Status |
|-----------|-------|------|---------|--------|
| Servo | SG90 | D5 | Door lock | ✅ Wired |
| Output driver | Generic | D0 | Fan state | ✅ Wired |
| PWM output | Generic | D1 | Lights dim/bright | ✅ Wired |
| Sensors | Generic | D4, A0 | Gas + flood detection | ✅ Wired |
| Valves/indicators | Generic | D2, D6, D7, D8 | Water/gas valves and mode/door state | ✅ Wired |

### Future Components (To Wire)

| Component | Purpose | GPIO | Notes |
|-----------|---------|------|-------|
| Servo×2 | Window control | D7, D8 | SG90 compatible |
| Relay | Light control | D6 | With PWM for dimming |
| Solenoid×2 | Gas/water valves | D9, D10 | Need drivers (transistors/MOSFETs) |

---

## Complete Data Flow Diagram

```text
Voice + Gesture
  ↓
Dispatcher / action_router
  ↓ publishes tokens to home/commands
NodeMCU firmware
  ↓ updates fan, lights, door, valves, mode indicator
  ↓ publishes home/state/*, home/sensors/*, home/alerts/*
Dashboard / Node-RED / other consumers
  ↓ read dispatcher virtual windows snapshot and MCU state topics
```

---

## Integration Testing Checklist

### ✅ Already Working in Code
- [x] Voice `fan_on` / `fan_off` map to the current `home/commands` ingress
- [x] Gesture `door_open` / `door_close` map to the current `home/commands` ingress
- [x] Lights commands map to PWM on D1
- [x] Mode commands update the mode indicator on D8
- [x] Gas and flood alerts publish state and alert topics
- [x] `status_query` republishes the known state snapshot

### 🟡 Virtual-only
- [x] Window commands stay valid in the dispatcher
- [x] Window commands update virtual state only
- [x] Dashboard can consume the virtual window snapshot later

### ⚠️ Runtime-sensitive
- [ ] Flash and verify on actual ESP8266 hardware
- [ ] Check the exact mode-indicator timing
- [ ] Check the emergency flash routine

---

## Current Completeness

| Layer | Coverage | Status |
|-------|----------|--------|
| Voice publisher | 100% | ✅ Complete |
| Gesture publisher | 100% of the active set | ✅ Complete |
| Dispatcher | 100% of routed tokens | ✅ Complete |
| MCU subscriber | 100% on `home/commands` | ✅ Complete |
| MCU handlers | 100% of the current hardware contract | ✅ Complete |
| Virtual windows | 100% in dispatcher state | ✅ Complete |

**Overall System Status**: functional in code, pending physical flash-and-bench validation.

**Known residual risk**: the exact mode-indicator timing and the emergency flash routine on the ESP8266 hardware.

