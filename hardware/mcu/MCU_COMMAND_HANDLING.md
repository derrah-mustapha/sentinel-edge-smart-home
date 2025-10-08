# MCU Command Handling Guide

**NodeMCU Amica Modular Firmware**  
**Last Updated**: May 26, 2026

---

## Overview

The MCU firmware receives commands from the Raspberry Pi dispatcher via MQTT and executes them on connected hardware (door servo, fan relay, sensors).

**Current Status**:
- ✅ **Door control**: Fully implemented (servo + relay)
- ✅ **Fan control**: Fully implemented (relay)
- 🔧 **Windows**: Subscribed but no hardware yet
- 🔧 **Lights**: Subscribed but no hardware yet
- 🔧 **Valves**: Subscribed but no hardware yet
- 🔧 **Alarm/Sensors**: Gas sensor implemented, flood sensor placeholder

---

## Command Flow Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Dispatcher (Raspberry Pi)                                    │
│ - Routes voice/gesture commands to MQTT topics               │
│ - Example: "fan_on" → publish home/fan/command = "ON"       │
└────────────────────┬─────────────────────────────────────────┘
                     │ MQTT
                     ▼
┌──────────────────────────────────────────────────────────────┐
│ MCU (NodeMCU Amica)                                          │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ MQTT Client                                              │ │
│ │ - Subscribes to command topics                           │ │
│ │ - Receives "ON", "OFF", "OPEN", "CLOSE", etc.          │ │
│ └────────────────┬─────────────────────────────────────────┘ │
│                  │                                            │
│ ┌────────────────▼─────────────────────────────────────────┐ │
│ │ MqttHandlers.h::handleMqttCommand()                       │ │
│ │ - Parses topic and payload                               │ │
│ │ - Routes to appropriate handler                          │ │
│ │ - Queues command in SystemState                          │ │
│ └────────────────┬─────────────────────────────────────────┘ │
│                  │                                            │
│ ┌────────────────▼─────────────────────────────────────────┐ │
│ │ SystemState.h::update()                                  │ │
│ │ - Executes pending commands                              │ │
│ │ - Manages actuators (door, fan)                          │ │
│ │ - Reads sensors (gas)                                    │ │
│ └────────────────┬─────────────────────────────────────────┘ │
│                  │                                            │
│ ┌────────────────▼─────────────────────────────────────────┐ │
│ │ Hardware Layer                                           │ │
│ │ - Servo: GPIO D5 → Door unlock/lock                     │ │
│ │ - Relay: GPIO D1 → Fan ON/OFF                           │ │
│ │ - LEDs: D2, D3, D4 → Status indicators                  │ │
│ │ - Gas Sensor: ADC → Detects gas                         │ │
│ └────────────────┬─────────────────────────────────────────┘ │
│                  │                                            │
│ ┌────────────────▼─────────────────────────────────────────┐ │
│ │ Physical Devices                                         │ │
│ │ - SG90 servo (door)                                      │ │
│ │ - Relay board (fan motor)                                │ │
│ │ - Status LEDs (WiFi, MQTT, OK)                          │ │
│ │ - MQ-2 gas sensor                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## MQTT Topics Subscribed

### Fully Implemented ✅

| Topic | Payload | Action | Hardware |
|-------|---------|--------|----------|
| `home/door/front/command` | `OPEN`, `UNLOCK` | Unlock door | Servo D5 |
| | `CLOSE`, `LOCK` | Lock door | Servo D5 |
| `home/fan/command` | `ON` | Turn fan on | Relay D1 |
| | `OFF` | Turn fan off | Relay D1 |

**Example Flow**:
```
Dispatcher publishes: home/fan/command = "ON"
       ↓
MCU receives in handleMqttCommand()
       ↓
Matches: if (String(topic) == TOPIC_FAN_CMD)
       ↓
Calls: sysState.onFanCommand("ON")
       ↓
SystemState.update() executes: fanRelay.on()
       ↓
GPIO D1 energizes
       ↓  
Fan motor runs
```

### Partially Implemented 🔧

| Topic | Status | Missing |
|-------|--------|---------|
| `home/window/+/command` | Subscribed ✅ | No hardware (need 2x servo) |
| `home/light/+/command` | Subscribed ✅ | No hardware (need relay) |
| `home/valve/gas/indicator` | Subscribed ✅ | No hardware (need solenoid driver) |
| `home/valve/water/indicator` | Subscribed ✅ | No hardware (need solenoid driver) |
| `home/alarm/gas` | Subscribed ✅ | Handler exists (sensor reads work) |
| `home/alarm/flood` | Subscribed ✅ | Handler missing (not yet wired) |

**When unsupported command received**:
```
[MQTT RX] topic=home/window/1/command payload=OPEN
[TODO] Window command received - hardware not yet wired
       Window servos need GPIO pins and hardware integration
       See: hardware/mcu/ARCHITECTURE.md -> Phase 3
```

---

## Command Processing Pipeline

### 1. MQTT Receives Message

```cpp
// In PubSubClient callback:
mqttClient.setCallback([](char* topic, byte* payload, unsigned int length) {
  handleMqttCommand(topic, payload, length);
});
```

### 2. Parse Command

```cpp
void handleMqttCommand(const char* topic, const byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();
  
  Serial.print("[MQTT RX] topic=");
  Serial.print(topic);
  Serial.print(" payload=");
  Serial.println(message);
  
  // Now route based on topic...
}
```

### 3. Route to Handler

```cpp
// Door handler
if (String(topic) == TOPIC_DOOR_FRONT_CMD) {
  if (message == "OPEN" || message == "UNLOCK") {
    sysState.onDoorCommand("UNLOCK");
  } else if (message == "CLOSE" || message == "LOCK") {
    sysState.onDoorCommand("LOCK");
  }
  return;  // ← Important: prevents falling through to "unknown topic"
}

// Fan handler  
if (String(topic) == TOPIC_FAN_CMD) {
  if (message == "ON") {
    sysState.onFanCommand("ON");
  } else if (message == "OFF") {
    sysState.onFanCommand("OFF");
  }
  return;
}

// Future: Windows, Lights, etc.
```

### 4. Queue in SystemState

```cpp
void onDoorCommand(const String& command) {
  doorCommand = command;        // Store the command
  doorCommandPending = true;    // Mark as pending
}
```

### 5. Execute in Main Loop

In `SystemState::update()` (called every 1 second):

```cpp
if (doorCommandPending) {
  doorCommandPending = false;
  if (doorCommand == "OPEN" || doorCommand == "UNLOCK") {
    doorActuator.unlock();  // Servo moves, 5s auto-lock
  } else if (doorCommand == "CLOSE" || doorCommand == "LOCK") {
    doorActuator.lock();    // Servo moves to locked position
  }
}

if (fanCommandPending) {
  fanCommandPending = false;
  if (fanCommand == "ON") {
    fanRelay.on();   // GPIO D1 HIGH → relay energizes
  } else if (fanCommand == "OFF") {
    fanRelay.off();  // GPIO D1 LOW → relay de-energizes
  }
}
```

### 6. Publish State Feedback

Periodically (every 30s), MCU publishes states back:

```cpp
void publishSensorData(PubSubClient& mqttClient) {
  // Door state
  String doorState = sysState.getDoorState();  // "LOCKED" or "UNLOCKED"
  mqttClient.publish("home/door/front/state", doorState.c_str());
  
  // Fan state
  String fanState = sysState.getFanState();    // "ON" or "OFF"
  mqttClient.publish("home/fan/state", fanState.c_str());
  
  // Gas sensor
  uint16_t gasReading = sysState.getGasReading();
  mqttClient.publish("home/alarm/gas/value", String(gasReading).c_str());
}
```

---

## Command-to-Hardware Mapping

### Door Control

**Command Sequence**: `door_open` (voice) → `UNLOCK` (MCU payload)

```
Topic: home/door/front/command
Payload: OPEN / UNLOCK / CLOSE / LOCK

GPIO:  D5 (GPIO14)
├─ SG90 servo power: 5V (USB power)
├─ Servo GND: GND
└─ Servo signal: D5

Behavior:
├─ OPEN: Servo to 90° (unlocked)
├─ UNLOCK: Same as OPEN
├─ CLOSE: Servo to 0° (locked)
├─ LOCK: Same as CLOSE
└─ Auto-lock: After 5s, servo returns to 0°
```

**Code Flow**:
```cpp
class ServoDoorActuator {
  void unlock() {
    servo.write(DOOR_SERVO_OPEN_ANGLE);    // 90°
    relayActivatedAt = millis();           // Record time
  }
  
  void lock() {
    servo.write(DOOR_SERVO_CLOSED_ANGLE);  // 0°
  }
  
  void update() {
    // Auto-lock after 5 seconds
    if (servo.read() != DOOR_SERVO_CLOSED_ANGLE) {
      if (millis() - relayActivatedAt >= 5000) {
        lock();
      }
    }
  }
}
```

### Fan Control  

**Command Sequence**: `fan_on` (voice/gesture) → `ON` (MCU payload)

```
Topic: home/fan/command
Payload: ON / OFF

GPIO: D1 (GPIO5)
├─ Relay VCC: 3.3V (MCU power)
├─ Relay IN: D1 (logic high → relay energized)
├─ Relay COM: Motor supply positive
├─ Relay NO: Motor positive (from MCU relay)
└─ Motor: COM + NO → Fan motor

Behavior:
├─ ON: GPIO D1 → HIGH (3.3V)
│  → Relay coil energized
│  → NO contact closes
│  → Current flows to motor
│  → Fan spins
└─ OFF: GPIO D1 → LOW (0V)
   → Relay coil de-energized
   → NO contact opens
   → Current stops
   → Fan stops

Auto-response:
└─ Gas sensor detects → fanRelay.on() automatically
```

**Code Flow**:
```cpp
class Relay {
  void on() {
    digitalWrite(pin, HIGH);  // D1 = 3.3V
    // Relay energizes, contact closes
  }
  
  void off() {
    digitalWrite(pin, LOW);   // D1 = 0V
    // Relay de-energizes, contact opens
  }
}
```

### Gas Sensor (Auto-Response)

```
Topic: home/alarm/gas (published by MCU when gas detected)

ADC: A0 (GPIO A0)
├─ MQ-2 sensor VCC: 5V
├─ Sensor GND: GND
├─ Sensor signal: A0 (0-1023)
└─ LED indicator: GPIO D4 (red blink)

Behavior:
├─ Normal: ADC < threshold → LED off
├─ Gas detected: ADC > threshold
│  ├─ LED D4: blink red (5s cycles)
│  ├─ Fan auto-on: fanRelay.on()
│  └─ Publish: home/alarm/gas/status = "ALERT"
└─ Gas cleared: ADC drops below threshold
   ├─ LED D4: off
   └─ Publish: home/alarm/gas/status = "NORMAL"
```

---

## Status LED Indicators

| LED | GPIO | Purpose | Behavior |
|-----|------|---------|----------|
| WiFi | D2 | Connection status | ON: connected, Blink: searching |
| MQTT | D3 | Broker status | ON: connected, Blink: searching |
| Status | D4 | Overall health | ON: all OK, OFF: issue detected |

**Logic**:
```cpp
// WiFi indicator
if (wifiConnected) {
  ledWifi.on();
} else {
  ledWifi.blink(1000, 100);  // 1s cycle, 100ms pulse
}

// Overall status
if (wifiConnected && mqttConnected && !gasSensor.isDetected()) {
  ledStatus.on();  // Green: everything OK
} else {
  ledStatus.off();  // Red: something wrong
}
```

---

## Actual Command Flow Test

### Test Case: "Turn Fan On" (Voice)

**Step 1 - Voice Publisher**:
```
User: "turn fan on"
Vosk: Recognizes speech
Publisher: Normalizes → "fan_on"
Publishes to: home/voice/command = "fan_on"
```

**Step 2 - Dispatcher**:
```
Receives: home/voice/command = "fan_on"
Router: on_voice_command("fan_on")
Dispatch: token == "fan_on"
  → _pub(TOPICS.FAN_CMD, "ON")
Publishes: home/fan/command = "ON"
```

**Step 3 - MCU**:
```
Receives: home/fan/command = "ON"
Handler: if (topic == TOPIC_FAN_CMD)
  if (message == "ON")
    sysState.onFanCommand("ON")

SystemState:
  fanCommand = "ON"
  fanCommandPending = true

update() called every 1s:
  if (fanCommandPending) {
    fanRelay.on()
    digitalWrite(D1, HIGH)
  }

GPIO D1 goes HIGH
```

**Step 4 - Hardware**:
```
GPIO D1 (3.3V) energizes relay
Relay contact closes (NO pin)
Current flows: 5V → Motor → GND
Fan motor spins
```

**Step 5 - Feedback**:
```
MCU update() calls publishSensorData()
sysState.getFanState() → "ON"  
Publishes: home/fan/state = "ON"
```

**Full Serial Output**:
```
[MQTT RX] topic=home/fan/command payload=ON
[ACTION] Fan ON command received
[CMD] queue fan command = ON
[CMD] execute fan command = ON
[MQTT TX] home/fan/state = ON
```

---

## Future Implementation (Not Yet Done)

### Adding Window Control

**When ready** (Phase 3):

1. **Wire hardware**: 2× servo motors (GPIO pins TBD)
2. **Create WindowActuator.h**: Similar to DoorActuator  
3. **Add to SystemState.h**: 
   ```cpp
   void onWindowCommand_1(const String& command);
   void onWindowCommand_2(const String& command);
   ```
4. **Update MqttHandlers.h**: Replace TODO stub with real handler
5. **Test**: Send `home/window/1/command = OPEN`

### Current Stub (MqttHandlers.h)

```cpp
String topicStr(topic);
if (topicStr.startsWith(TOPIC_WINDOW_CMD_PREFIX)) {
  Serial.println("[TODO] Window command received - hardware not yet wired");
  Serial.println("       Window servos need GPIO pins and hardware integration");
  Serial.println("       See: hardware/mcu/ARCHITECTURE.md -> Phase 3");
  return;
}
```

When a window command is sent today:
```
[MQTT RX] topic=home/window/1/command payload=OPEN
[TODO] Window command received - hardware not yet wired
```

This makes it clear to developers what's missing.

---

## Adding Support for New Commands

### Template for New Device

1. **Add topic to config.h**:
```cpp
#define TOPIC_NEWDEVICE_CMD "home/newdevice/command"
```

2. **Create actuator class** (optional, if complex):
```cpp
// src/actuators/NewDevice.h
class NewDevice {
  void begin();
  void on();
  void off();
};
```

3. **Add to SystemState.h**:
```cpp
NewDevice device;

void onNewDeviceCommand(const String& command) {
  // Parse command
}
```

4. **Add handler in MqttHandlers.h**:
```cpp
if (String(topic) == TOPIC_NEWDEVICE_CMD) {
  if (message == "ON") {
    sysState.onNewDeviceCommand("ON");
  }
  return;
}
```

5. **Subscribe in nodemcu sketch**:
```cpp
subscribeTopic(TOPIC_NEWDEVICE_CMD);
```

6. **Test**: Send command, check serial output for confirmation

---

## Debugging

### Check Subscriptions

**On MCU boot**, you should see:
```
[MQTT] subscribed -> home/door/front/command
[MQTT] subscribed -> home/fan/command  
[MQTT] subscribed -> home/window/+/command
[MQTT] subscribed -> home/light/+/command
[MQTT] subscribed -> home/valve/gas/indicator
[MQTT] subscribed -> home/valve/water/indicator
[MQTT] subscribed -> home/alarm/gas
[MQTT] subscribed -> home/alarm/flood
[MQTT] ready to receive commands
```

### Send Test Command

From Raspberry Pi:
```bash
mosquitto_pub -h broker.hivemq.com \
  -u YOUR_MQTT_USER -P YOUR_MQTT_PASSWORD \
  -t home/fan/command -m ON
```

Expected MCU output:
```
[MQTT RX] topic=home/fan/command payload=ON
[ACTION] Fan ON command received
[CMD] queue fan command = ON
[CMD] execute fan command = ON
```

### Check Device Feedback

```bash
mosquitto_sub -h broker.hivemq.com \
  -u YOUR_MQTT_USER -P YOUR_MQTT_PASSWORD \
  -t "home/+/state"
```

Should see state updates:
```
home/fan/state ON
home/door/front/state UNLOCKED
```

---

## Error Codes & States

| State | Meaning | Action |
|-------|---------|--------|
| **LOCKED** | Door fully locked | Normal state |
| **UNLOCKED** | Door unlocked (temporary) | Auto-returns to LOCKED after 5s |
| **ON** (fan) | Fan relay energized | Motor running |
| **OFF** (fan) | Fan relay de-energized | Motor stopped |
| **ALERT** (gas) | Gas detected above threshold | Fan auto-runs, LED blinks |
| **NORMAL** (gas) | Gas below threshold | Normal operation |

---

## Wiring Checklist

- [x] Door servo (D5) + 5V supply
- [x] Fan relay (D1) + motor wiring
- [x] Gas sensor (A0)
- [x] Status LEDs (D2, D3, D4)
- [ ] Window servo 1 (unassigned GPIO)
- [ ] Window servo 2 (unassigned GPIO)
- [ ] Light relay (unassigned GPIO)
- [ ] Gas valve solenoid (unassigned GPIO)
- [ ] Water valve solenoid (unassigned GPIO)

---

## References

- [config.h](../config.h) - Pin & topic definitions
- [SystemState.h](./src/logic/SystemState.h) - Business logic
- [MqttHandlers.h](./src/mqtt/MqttHandlers.h) - Command routing
- [Relay.h](./src/actuators/Relay.h) - Generic relay class
- [ServoDoorActuator.h](./src/actuators/ServoDoorActuator.h) - Door control
- [DOOR_FAN_INTEGRATION.md](../DOOR_FAN_INTEGRATION.md) - Implementation guide
- [ARCHITECTURE.md](../ARCHITECTURE.md) - High-level design
