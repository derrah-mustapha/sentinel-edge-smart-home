# MCU Modular Architecture Guide

## Overview

The refactored MCU firmware uses a **modular, hierarchical architecture** to scale from simple to complex logic without becoming unmaintainable:

```
┌─────────────────────────────────────────────────────┐
│         Main Sketch (nodemcu-amica-modular.ino)     │
│    - WiFi/MQTT lifecycle management                 │
│    - Main loop coordination                          │
│    - Heartbeat logging                              │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┬─────────────┐
        │                     │             │
   ┌────▼─────┐        ┌─────▼──────┐  ┌──▼──────────┐
   │ Sensors  │        │ Actuators  │  │ Logic Layer │
   └──────────┘        └────────────┘  └─────────────┘
       │                    │                  │
    GasSensor          LED class           SystemState
    MotionSensor       Relay class         (orchestrator)
    TempSensor         Buzzer class             │
       │                    │                  │
       └────────────────────┼──────────────────┘
                            │
                  ┌─────────▼────────────┐
                  │ MQTT Handlers Layer  │
                  │ - Publish data       │
                  │ - Handle commands    │
                  └──────────────────────┘
```

---

## File Structure

```
nodemcu-amica/
├── config.h                          # WiFi, broker, pin definitions, topic names
├── nodemcu-amica-modular.ino         # Main sketch (simple & clean)
└── src/
    ├── sensors/
    │   ├── GasSensor.h              # Gas analog sensor
    │   ├── MotionSensor.h           # PIR motion (add later)
    │   └── TemperatureSensor.h      # DHT/BMP (add later)
    ├── actuators/
    │   ├── LED.h                    # GPIO LED control with blink
    │   ├── Relay.h                  # GPIO relay/solenoid (add later)
    │   └── Buzzer.h                 # PWM buzzer (add later)
    ├── logic/
    │   └── SystemState.h            # Central state machine & logic
    └── mqtt/
        └── MqttHandlers.h           # Publish/subscribe handlers
```

---

## Key Principles

### 1. **Separation of Concerns**
- **Sensors** (`src/sensors/`) - Only read, filter, edge-detect
- **Actuators** (`src/actuators/`) - Only write/control state
- **Logic** (`src/logic/`) - Coordinate sensor inputs → actuator outputs
- **MQTT** (`src/mqtt/`) - Publish sensor data, handle commands

### 2. **State Over Events**
Instead of interrupt callbacks (hard to debug on resource-constrained devices), we use **periodic polling with edge detection**:
```cpp
// GasSensor only returns true if state changed
if (gasSensor.update()) {  // Returns true only on gas detect/clear
  publishSensorData();     // Publish the change
}
```

### 3. **Non-Blocking Design**
All update functions check if enough time has passed before acting:
```cpp
bool update() {
  if (now - lastReadMs < INTERVAL_MS) {
    return false;  // Not time yet, don't block
  }
  // Do work here...
  return true;
}
```

### 4. **Centralized Logic (SystemState)**
All sensor→actuator logic lives in one place. Easy to debug cause-effect:
```cpp
void SystemState::update() {
  gasSensor.update();
  
  // Gas detected → activate alert
  if (gasSensor.isDetected()) {
    ledAlert.blink(5000, 200);
    // TODO: triggerFan();  // Add later
  }
}
```

---

## How to Add a New Sensor

### Example: Add motion sensor

**1. Create `src/sensors/MotionSensor.h`:**
```cpp
#ifndef MOTION_SENSOR_H
#define MOTION_SENSOR_H

#define MOTION_SENSOR_PIN D5
#define MOTION_READ_INTERVAL_MS 2000

class MotionSensor {
private:
  bool lastDetected = false;
  unsigned long lastReadMs = 0;
  
public:
  void begin() {
    pinMode(MOTION_SENSOR_PIN, INPUT);
  }
  
  bool update() {
    unsigned long now = millis();
    if (now - lastReadMs < MOTION_READ_INTERVAL_MS) {
      return false;
    }
    lastReadMs = now;
    
    bool detected = (digitalRead(MOTION_SENSOR_PIN) == HIGH);
    if (detected != lastDetected) {
      lastDetected = detected;
      return true;  // Change detected
    }
    return false;
  }
  
  bool isDetected() const { return lastDetected; }
};

#endif
```

**2. Add to `SystemState.h`:**
```cpp
#include "../sensors/MotionSensor.h"

class SystemState {
private:
  GasSensor gasSensor;
  MotionSensor motionSensor;  // ADD THIS
  // ...
  
public:
  void begin() {
    gasSensor.begin();
    motionSensor.begin();    // ADD THIS
    // ...
  }
  
  void update() {
    gasSensor.update();
    motionSensor.update();   // ADD THIS
    
    // UPDATE: Motion-triggered actions
    if (motionSensor.isDetected()) {
      ledStatus.on();  // Turn on status LED
    }
  }
};
```

**3. Publish motion data in `MqttHandlers.h`:**
```cpp
void publishSensorData(PubSubClient& mqttClient) {
  // Existing gas publish...
  
  // ADD THIS:
  mqttClient.publish("home/motion/status", 
    sysState.getMotionDetected() ? "DETECTED" : "NORMAL");
}
```

**Done!** No changes needed to the main sketch.

---

## How to Add New Logic

All business logic lives in `SystemState::update()`. Add conditions there:

```cpp
void SystemState::update() {
  gasSensor.update();
  motionSensor.update();
  
  // Gas detected → turn on fan + alert
  if (gasSensor.isDetected()) {
    ledAlert.blink(5000, 200);
    fanRelay.on();  // Will add Relay class
  } else {
    fanRelay.off();
  }
  
  // Motion detected + night mode → turn on hallway light
  if (motionSensor.isDetected() && isNightMode) {
    hallwayLight.on();
  }
  
  // Temperature too high → activate cooling
  if (tempSensor.getTemp() > 28) {
    coolingFan.on();
  }
}
```

---

## How to Add a New Actuator

### Example: Add relay for door lock

**1. Create `src/actuators/Relay.h`:**
```cpp
#ifndef RELAY_H
#define RELAY_H

class Relay {
private:
  uint8_t pin;
  bool isOn = false;
  
public:
  Relay(uint8_t relayPin) : pin(relayPin) {}
  
  void begin() {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);  // Default off
  }
  
  void on() {
    digitalWrite(pin, HIGH);
    isOn = true;
  }
  
  void off() {
    digitalWrite(pin, LOW);
    isOn = false;
  }
  
  bool getState() const { return isOn; }
};

#endif
```

**2. Add to `SystemState.h` and use in logic.**

---

## MQTT Integration

### Publishing sensor data from `MqttHandlers.h`:
```cpp
void publishSensorData(PubSubClient& mqttClient) {
  // Called every 30 seconds (see main sketch)
  mqttClient.publish("home/gas/value", gasReading);
  mqttClient.publish("home/gas/status", gasStatus);
  mqttClient.publish("home/motion/status", motionStatus);
  mqttClient.publish("home/temp/value", tempReading);
}
```

### Handling incoming MQTT commands:
```cpp
void handleMqttCommand(const char* topic, const byte* payload, unsigned int length) {
  // Called when dispatcher publishes commands
  if (String(topic) == "home/door/front/command") {
    if (message == "OPEN") {
      sysState.doorRelay.on();
    }
  }
}
```

---

## Benefits of This Architecture

✅ **Easy to debug** - All logic in one place (SystemState::update)  
✅ **Easy to test** - Each sensor/actuator is independent  
✅ **Easy to extend** - Add new sensors without touching main loop  
✅ **Memory efficient** - No interrupts or callbacks (simpler stack)  
✅ **Deterministic timing** - No race conditions  
✅ **Future-proof** - Ready for motion sensor, temp sensor, speaker, relays, etc.

---

## Next Steps (Priority Order)

1. ✅ Gas sensor + LED indicator
2. Add door relay (copy Relay.h pattern)
3. Add fan relay (same pattern)
4. Add motion sensor
5. Add temperature sensor (DHT11/BMP280)
6. Add state feedback topic publishing
7. Add speaker/buzzer for alerts
8. Create gas-node and motion-node firmwares (same architecture, different sensors)

