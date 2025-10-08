# MCU Firmware - NodeMCU Amica Modular

**Status**: 60% Complete (May 2026)  
**Folder**: `nodemcu-amica-modular/`  
**Main Sketch**: `nodemcu-amica-modular.ino`

## Overview

The NodeMCU Amica firmware:
- ✅ Connects to Wi-Fi and MQTT broker
- ✅ Subscribes to all dispatch command topics (16 topics)
- ✅ Executes door and fan commands with hardware
- ✅ Reads gas sensor and publishes alerts
- ✅ Publishes state feedback for all devices
- ⚠️ Logs unimplemented commands (windows, lights, valves) as "[TODO]"
- ❌ Window, light, and valve hardware not yet wired

## Current Implementation (Working Now ✅)

### Devices Fully Implemented

| Device | Command | GPIO | Hardware | Status |
|--------|---------|------|----------|--------|
| **Door** | OPEN/CLOSE/LOCK/UNLOCK | D5 | SG90 Servo + 5V | ✅ Working |
| **Fan** | ON/OFF | D1 | Relay board | ✅ Working |
| **Gas Sensor** | Reads + alerts | A0 | MQ-2 + ADC | ✅ Working |
| **LEDs** | Status indicators | D2,D3,D4 | RGB (or 3× mono) | ✅ Working |

### Devices Subscribed (Awaiting Hardware)

| Device | Topics | Status |
|--------|--------|--------|
| Windows | `home/window/1/command`, `home/window/2/command` | ⚠️ Subscribed, no handler |
| Lights | `home/light/main/command` | ⚠️ Subscribed, no handler |
| Valves | `home/valve/gas/indicator`, `home/valve/water/indicator` | ⚠️ Subscribed, no handler |

When an unimplemented command is received:
```
[MQTT RX] topic=home/window/1/command payload=OPEN
[TODO] Window command received - hardware not yet wired
```

## Architecture

```
Modular Design:
├─ nodemcu-amica-modular.ino    (Main sketch, setup/loop)
├─ config.h                      (WiFi, MQTT, GPIO pins, topics)
│
└─ src/
   ├─ mqtt/
   │  └─ MqttHandlers.h          (Topic routing, handlers)
   │
   ├─ logic/
   │  └─ SystemState.h           (Business logic, queuing)
   │
   ├─ actuators/
   │  ├─ LED.h                   (LED blink/on/off)
   │  ├─ Relay.h                 (Generic GPIO relay)
   │  └─ ServoDoorActuator.h     (Door-specific servo logic)
   │
   └─ sensors/
      └─ GasSensor.h             (MQ-2 gas sensor ADC)
```

## Command Flow

**Example: "turn fan on" (voice)**

```
Voice input: "turn fan on"
  ↓
Voice Publisher: emit token "fan_on"
  ↓
Dispatcher: route "fan_on" → publish home/fan/command = "ON"
  ↓
MCU receives MQTT message
  ↓
MqttHandlers.h::handleMqttCommand()
  ├─ Parse: topic="home/fan/command", payload="ON"
  ├─ Match: if (topic == TOPIC_FAN_CMD)
  └─ Queue: sysState.onFanCommand("ON")
  ↓
SystemState::update() (called every 1s from main loop)
  ├─ Check: if (fanCommandPending)
  ├─ Execute: fanRelay.on()
  └─ GPIO: digitalWrite(D1, HIGH)
  ↓
GPIO D1 → 3.3V → Relay energizes → Motor runs
  ↓
MCU publishes feedback: home/fan/state = "ON"
```

## GPIO Pins (Current)

```
D0   - UNUSED (alternative for door relay)
D1   - FAN RELAY (active-high, energized = ON)
D2   - LED WiFi status
D3   - LED MQTT status
D4   - LED Overall status
D5   - DOOR SERVO (PWM, 0° = locked, 90° = unlocked)
A0   - GAS SENSOR (ADC, analog input)
```

## Features

### 1. **Door Control** (Implemented)
- Servo-based electronic lock
- 5-second auto-lock for safety
- State feedback (LOCKED/UNLOCKED)
- Debounce protection (500ms)

### 2. **Fan Control** (Implemented)
- Simple relay on/off
- No PWM (full speed only)
- State feedback (ON/OFF)
- Auto-on when gas detected

### 3. **Gas Sensor** (Implemented)
- MQ-2 analog sensor
- Threshold-based alert
- Auto-fan response
- LED indicator blink when alert

### 4. **Status LEDs** (Implemented)
- WiFi LED: ON when connected, blink when connecting
- MQTT LED: ON when connected, blink when connecting
- Status LED: ON when all OK, OFF if any issue

### 5. **Auto-Responses**
- Gas detected → Auto-turn on fan (safety feature)
- WiFi issue → Retry connection (exponential backoff)
- MQTT issue → Retry connection (exponential backoff)

## Tests & Verification

### Hardware Check
```bash
# From laptop/Raspberry Pi:
# Test door
mosquitto_pub -h broker -u user -P pass \
  -t home/door/front/command -m OPEN

# Expected MCU serial output:
# [MQTT RX] topic=home/door/front/command payload=OPEN
# [ACTION] Door unlock command received
# Servo moves to 90°, auto-locks after 5s
```

```bash
# Test fan
mosquitto_pub -h broker -u user -P pass \
  -t home/fan/command -m ON

# Expected MCU serial output:
# [MQTT RX] topic=home/fan/command payload=ON
# [ACTION] Fan ON command received
# GPIO D1 goes HIGH, fan runs
```

### State Feedback
```bash
# Listen for state updates
mosquitto_sub -h broker -u user -P pass -t "home/+/state"

# Should see periodic updates:
# home/door/front/state LOCKED
# home/fan/state OFF
# home/alarm/gas/status NORMAL
```

## Where to Find Documentation

| Document | Purpose |
|----------|---------|
| [MCU_COMMAND_HANDLING.md](./MCU_COMMAND_HANDLING.md) | **Complete guide** to command processing, topic routing, handlers |
| [INTEGRATION_MATRIX.md](../docs/INTEGRATION_MATRIX.md) | **All 21 commands** mapped across voice, gesture, dispatcher, MCU |
| [COMMAND_FLOW_AUDIT.md](../docs/COMMAND_FLOW_AUDIT.md) | **Detailed audit** of what's implemented vs. what's missing |
| [DOOR_FAN_INTEGRATION.md](./DOOR_FAN_INTEGRATION.md) | Implementation details of door servo and fan relay |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | High-level design (to be updated) |
| [WIRING_REFERENCE.md](./WIRING_REFERENCE.md) | Current GPIO wiring (to be updated) |

**Start here**: Read [MCU_COMMAND_HANDLING.md](./MCU_COMMAND_HANDLING.md) for complete command flow overview.

## Workflow: Edit → Compile → Flash → Test

### 1. Edit Firmware
```bash
# Edit in VS Code:
# - nodemcu-amica-modular.ino
# - src/logic/SystemState.h
# - src/mqtt/MqttHandlers.h
# - config.h (WiFi, MQTT settings)
```

### 2. Compile & Upload (Arduino IDE)
```bash
# Open Arduino IDE:
# File → Open → nodemcu-amica-modular/nodemcu-amica-modular.ino
# Tools → Board → NodeMCU 1.0 (ESP8266)
# Tools → Upload Speed → 115200
# Sketch → Upload
```

### 3. Monitor Serial Output
```bash
# In Arduino IDE:
# Tools → Serial Monitor (115200 baud)
# Or from terminal:
screen /dev/ttyUSB0 115200
```

### 4. Send Test Commands
```bash
# From Raspberry Pi:
mosquitto_pub -t home/fan/command -m ON
```

### 5. Observe Feedback
```
MCU Serial Output:
[MQTT RX] topic=home/fan/command payload=ON
[ACTION] Fan ON command received
[CMD] queue fan command = ON
[CMD] execute fan command = ON
[MQTT TX] home/fan/state = ON
```

## Current Job

✅ **Phase 1** (Complete): Door & Fan + Gas sensor  
🔧 **Phase 2** (In Progress): Add unimplemented command logging (prevents silent failures)  
⏳ **Phase 3** (Next): Wire windows, lights, valves + implement handlers  

## Next Steps

**Phase 2** (Just completed):
- ✅ Subscribe to all command topics (windows, lights, valves)
- ✅ Log "[TODO]" when unimplemented commands received
- ✅ Makes it clear what's unfinished

**Phase 3** (To do next):
1. Allocate GPIO pins for new devices (windows, lights, valves)
2. Wire hardware (servos, relays, solenoid drivers)
3. Update config.h with new pins
4. Create WindowActuator.h, LightController.h
5. Add real handlers (replace [TODO] logs)
6. Test end-to-end

**Phase 4** (After hardware):
1. Test all 21 commands
2. Verify state feedback for all devices
3. Test system modes (home, away, sleep, guest)
4. Emergency activation & cancellation
5. Full end-to-end integration

## FAQ

**Q: Why do windows/lights show "[TODO]"?**  
A: Dispatcher publishes the commands correctly, MCU receives them, but no hardware is wired yet. The logs make it clear what's missing. When you add the hardware, replace the TODO with a real handler.

**Q: Can I test modes today?**  
A: Partially. When you say "home mode", the dispatcher sends individual commands (door close, fan off, lights on, windows close). MCU executes door and fan parts. Windows and lights get logged as TODO.

**Q: How do I add support for a new device?**  
A: See [MCU_COMMAND_HANDLING.md](./MCU_COMMAND_HANDLING.md) section "Adding Support for New Commands" for step-by-step guide.

**Q: Is the gas sensor automatic?**  
A: Yes. Gas detection triggers auto-fan, LED blink, and alert publish. User can cancel with voice/gesture "cancel alert".

## References

- [PubSubClient library](https://github.com/knolleary/pubsub_client) - MQTT
- [Servo library](https://www.arduino.cc/reference/en/libraries/servo/) - Door control
- [ESP8266 bootloader](https://github.com/esp8266/Arduino) - Flashing
- [NodeMCU Amica pinout](https://nodemcu.readthedocs.io/en/latest/api/) - GPIO mapping
