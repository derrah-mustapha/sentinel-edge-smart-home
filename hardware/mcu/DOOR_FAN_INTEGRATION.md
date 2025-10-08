# Door & Fan Integration Guide

## Overview

The door and fan relays are now fully integrated into the modular MCU firmware. When the dispatcher publishes commands, the MCU receives them, executes the action, and publishes state feedback back.

## Architecture

### 1. **SystemState.h** - Logic Orchestrator

Added:
- `Relay doorRelay` - GPIO control for door relay (pin D0)
- `Relay fanRelay` - GPIO control for fan relay (pin D1)
- `DoorActuator doorActuator` - Door-specific wrapper with safety logic
- `onDoorCommand(command)` - Queue door commands from MQTT
- `onFanCommand(command)` - Queue fan commands from MQTT
- `getDoorState()` - Get door state string ("LOCKED" or "UNLOCKED")
- `getFanState()` - Get fan state string ("ON" or "OFF")

**Command Processing** (in `update()`):
```cpp
// When dispatcher publishes "OPEN" or "UNLOCK"
if (doorCommand == "OPEN" || doorCommand == "UNLOCK") {
  doorActuator.unlock();  // Energize relay for 5 seconds
}

// When dispatcher publishes "CLOSE" or "LOCK"
if (doorCommand == "CLOSE" || doorCommand == "LOCK") {
  doorActuator.lock();    // De-energize relay
}

// Fan accepts "ON" or "OFF"
if (fanCommand == "ON") {
  fanRelay.on();          // Energize continuously
}
```

**Auto-Gas Response**:
```cpp
if (gasSensor.isDetected()) {
  fanRelay.on();  // Auto-start fan when gas detected
}
```

---

### 2. **Relay.h** - Generic GPIO Relay Class

Generic relay control for any GPIO-driven actuator.

**Methods:**
- `begin()` - Set pin to OUTPUT, default LOW
- `on(maxDurationMs)` - Turn relay on, optionally with auto-off timer
- `off()` - Turn relay off
- `toggle()` - Toggle state
- `update()` - Call periodically to enforce max duration
- `getState()` - Returns bool
- `getStateStr()` - Returns "ON" or "OFF"

**Key Feature: Auto-Off Timer**
```cpp
relay.on(5000);  // Relay turns off automatically after 5 seconds
```

---

### 3. **DoorActuator.h** - Door-Specific Safety Wrapper

Provides door-specific logic built on top of Relay with safety constraints.

**Methods:**
- `begin()` - Initialize relay
- `unlock()` - Energize relay with 5-second auto-lock timeout
- `lock()` - De-energize relay
- `update()` - Enforce auto-off logic
- `getStateStr()` - Returns "LOCKED" or "UNLOCKED"

**Safety Constraints:**
1. **Debounce (500ms)**: Protects against rapid toggling from glitchy commands
2. **Auto-Lock (5s)**: Even if command stuck, door re-locks automatically
3. **Min Action Interval**: Methods return false if called too soon

**Behavior:**
```
Dispatcher publishes "OPEN" 
  ↓
MCU receives via MQTT
  ↓
SystemState.update() processes command
  ↓
doorActuator.unlock() called
  ↓
Relay energizes pin D0 for 5000ms (5 seconds)
  ↓
After 5s, relay auto-de-energizes
  ↓
MCU publishes state: "UNLOCKED" → "LOCKED"
```

---

### 4. **MqttHandlers.h** - Command Routing & Publishing

**Updated `handleMqttCommand()`:**
```cpp
// Route door commands to SystemState
if (String(topic) == TOPIC_DOOR_FRONT_CMD) {
  if (message == "OPEN" || message == "UNLOCK") {
    sysState.onDoorCommand("UNLOCK");
  } else if (message == "CLOSE" || message == "LOCK") {
    sysState.onDoorCommand("LOCK");
  }
}

// Route fan commands to SystemState
if (String(topic) == TOPIC_FAN_CMD) {
  if (message == "ON") {
    sysState.onFanCommand("ON");
  } else if (message == "OFF") {
    sysState.onFanCommand("OFF");
  }
}
```

**Updated `publishSensorData()`:**
Now publishes state feedback:
```cpp
// Actuator state feedback
mqttClient.publish("home/door/front/state", sysState.getDoorState());
mqttClient.publish("home/fan/state", sysState.getFanState());

// Plus existing gas sensor data
mqttClient.publish("home/alarm/gas/value", gasValue);
mqttClient.publish("home/alarm/gas/status", gasStatus);
```

---

### 5. **config.h** - Updated Topic Definitions

Added state topics for feedback:
```cpp
#define TOPIC_DOOR_FRONT_CMD "home/door/front/command"
#define TOPIC_DOOR_FRONT_STATE "home/door/front/state"
#define TOPIC_FAN_CMD "home/fan/command"
#define TOPIC_FAN_STATE "home/fan/state"
```

---

## End-to-End Flow

### Door Control Example

**1. Dispatcher sends unlock command:**
```
Topic: home/door/front/command
Payload: OPEN
```

**2. MCU Serial output:**
```
[MQTT RX] topic=home/door/front/command payload=OPEN
[ACTION] Door unlock command received
```

**3. SystemState processes command:**
- `update()` calls `doorActuator.unlock()`
- Sets relay to HIGH with 5000ms max duration

**4. Relay energizes pin D0:**
- Solenoid lock is energized
- Door unlocks

**5. After 5 seconds, relay auto-de-energizes:**
- Solenoid de-energizes
- Door re-locks (mechanical fail-safe)

**6. MCU publishes state feedback:**
```
[MQTT TX] home/door/front/state = UNLOCKED
(After 5s)
[MQTT TX] home/door/front/state = LOCKED
```

**7. Dispatcher receives feedback:**
- Uses state changes to confirm action succeeded
- Logs to database/dashboard

---

### Fan Control Example

**1. Dispatcher sends fan command:**
```
Topic: home/fan/command
Payload: ON
```

**2. MCU processes and energizes:**
- Fan relay (pin D1) turns ON
- Fan runs continuously

**3. MCU publishes state:**
```
[MQTT TX] home/fan/state = ON
```

**4. Auto-off on gas alert:**
- If `gasSensor.isDetected()` is false, fan stays on
- If gas detected, fan is already on
- Dispatcher can send "OFF" to stop fan

---

## Error Handling

### Debounce Protection
If dispatcher sends rapid commands (< 500ms apart):
```
First command: UNLOCK → Success (relay on, door unlocks)
Second command (100ms later): LOCK → Ignored (debounce active)
```

### Auto-Lock Timeout
Even if MQTT connection lost and command stuck:
```
Relay energized at t=0
↓
After 5 seconds, Relay.update() checks elapsed time
↓
If > 5000ms, calls relay.off() automatically
↓
Door re-locks (fail-safe)
```

### Command Format Tolerance
Door accepts both variants:
- "OPEN" or "UNLOCK" → unlock()
- "CLOSE" or "LOCK" → lock()

Fan accepts:
- "ON" → on()
- "OFF" → off()

---

## Testing Checklist

Before deploying to MCU:

- [ ] **Compile**: Upload `nodemcu-amica-modular.ino` to ESP8266
  - Should compile without errors
  - Check Serial Monitor for boot messages

- [ ] **WiFi Connection**: MCU connects to SSID (configured in config.h)
  - Serial output shows: `[WIFI] connected ip=...`

- [ ] **MQTT Connection**: MCU connects to broker
  - Serial output shows: `[MQTT] connected successfully`
  - Shows subscription to topics

- [ ] **Direct Command**: From laptop, publish test command
  ```bash
  mosquitto_pub -h 10.54.92.8 -t home/door/front/command -m OPEN
  ```
  - MCU Serial shows: `[MQTT RX] ... payload=OPEN`
  - MCU Serial shows: `[ACTION] Door unlock command received`
  - Relay pin D0 goes HIGH (check with multimeter: 3.3V or GND)
  - After 5s, pin goes LOW
  - Serial shows state feedback published

- [ ] **Gas Alert Triggers Fan**: Hold MCU near odor/gas source (or test with code)
  - Gas sensor detects, gas alert LED blinks
  - Fan relay auto-turns on
  - Serial shows: `fanRelay.on()` and state published

- [ ] **Dispatcher Integration**: Run dispatcher, send voice/gesture command
  - Expect command to reach TOPIC_DOOR_FRONT_CMD
  - MCU receives and acts
  - Expect MCU publishes state to TOPIC_DOOR_FRONT_STATE
  - Dispatcher receives state change

---

## Files Modified/Created

| File | Change |
|------|--------|
| `config.h` | Added TOPIC_DOOR_FRONT_STATE, TOPIC_FAN_STATE |
| `src/actuators/Relay.h` | **NEW**: Generic relay control |
| `src/actuators/DoorActuator.h` | **NEW**: Door-specific safety wrapper |
| `src/logic/SystemState.h` | Added door/fan relays, command queuing, auto-gas response |
| `src/mqtt/MqttHandlers.h` | Wire commands to SystemState, publish state feedback |
| `nodemcu-amica-modular.ino` | No changes needed (already calls sysState.begin/update) |

---

## Next Steps

1. **Done**: Deploy to MCU and verify command flow in Serial Monitor
2. **Dispatcher State Subscriptions**: Subscribe and log `home/door/front/state` and `home/fan/state`
3. **Command Timeout Tracking**: Start a short timer after publish and warn/retry when expected state is not received
4. **Payload Normalization**: Normalize dispatcher payloads in one place (`open`/`Open` -> `OPEN`, etc.)
5. **Regression Test Script**: Add a small publish-and-wait script to validate command + state feedback quickly
6. **Physical Test (Deferred)**: Verify relay controls solenoid/fan during hardware wiring phase
7. **Motion Sensor (Optional)**: Add `MotionSensor.h` using the same modular pattern
8. **Node Variants**: Create specialized firmware for gas-node, motion-node, and others

---

## Architecture Benefits

✅ **Modular**: Each component is independent, easy to test
✅ **Safe**: Auto-timeouts prevent stuck relays
✅ **Responsive**: Commands processed every 1 second
✅ **Debuggable**: Detailed Serial logging for troubleshooting
✅ **Scalable**: Same pattern works for adding temp sensor, humidity sensor, etc.
✅ **Flexible**: Broker profile (LOCAL/CLOUD) configurable without recompile
