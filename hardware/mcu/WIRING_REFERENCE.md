# NodeMCU Amica - Hardware Wiring Reference

**Current contract for the ESP8266 controller and its MQTT topic map.**

---

## Pin Summary

| Component | Pin Label | GPIO # | Type | Mode | Voltage | Notes |
|-----------|-----------|--------|------|------|---------|-------|
| **Gas Sensor (DO)** | D4 | GPIO2 | Digital | INPUT | 3.3V | HIGH = gas detected |
| **Water/Flood Sensor (AO)** | A0 | ADC | Analog | INPUT | 0-1023 | Threshold: >300 = flood detected |
| **Door Servo (SG90)** | D5 | GPIO14 | Digital | OUTPUT | 3.3V | 0° = locked, 90° = open |
| **Fan Output** | D0 | GPIO16 | Digital | OUTPUT | 3.3V | HIGH = fan ON |
| **Lights PWM** | D1 | GPIO5 | PWM | OUTPUT | 3.3V | 0 = off, 400 = dim, 1023 = bright |
| **Water Valve Output** | D2 | GPIO4 | Digital | OUTPUT | 3.3V | LOW = open, HIGH = closed |
| **Gas Valve Output** | D6 | GPIO12 | Digital | OUTPUT | 3.3V | LOW = open, HIGH = closed |
| **Door Indicator** | D7 | GPIO13 | Digital | OUTPUT | 3.3V | Mirrors servo position |
| **Mode Indicator** | D8 | GPIO15 | Digital | OUTPUT | 3.3V | Blink pattern for mode |

---

## MQTT Contract

### NodeMCU subscribes to

- `home/commands`

### NodeMCU publishes to

- `home/sensors/gas` - `"1"` or `"0"` every 2 seconds.
- `home/sensors/water` - raw analog reading as a string every 2 seconds.
- `home/sensors/flood` - `"1"` or `"0"` every 2 seconds.
- `home/state/fan` - `"on"` or `"off"` on every change.
- `home/state/lights` - `"off"`, `"dim"`, or `"bright"` on every change.
- `home/state/door` - `"open"` or `"locked"` on every change.
- `home/state/mode` - current mode on every change.
- `home/state/gas_valve` - `"open"` or `"closed"` on every change.
- `home/state/water_valve` - `"open"` or `"closed"` on every change.
- `home/alerts/gas` - `"ALERT"` on first detection, `"CLEAR"` when the alert is cleared.
- `home/alerts/flood` - `"ALERT"` on first detection, `"CLEAR"` when the alert is cleared.

### Command tokens accepted on `home/commands`

- `fan_on`, `fan_off`
- `lights_on`, `lights_off`, `lights_dim`, `lights_bright`
- `door_open`, `door_close`
- `alert_cancel`
- `emergency_activate`, `emergency_cancel`
- `mode_home`, `mode_away`, `mode_sleep`, `mode_guest`
- `status_query`
- `windows_open_all`, `windows_close_all`, `window_open_1`, `window_close_1`, `window_open_2`, `window_close_2`

Window commands remain virtual-only on the dispatcher side; the MCU accepts them for compatibility but does not move hardware.

---

## Detailed Wiring

---

## Detailed Wiring

### 1. DOOR SERVO (GPIO Output)

#### SG90 Door Servo
```
NodeMCU D5 (GPIO14)
    ├─→ Servo signal (orange/yellow wire)
    ├─→ Servo VCC (red wire) → external 5V supply
    └─→ Servo GND (brown/black wire) → common GND
```

**Servo Behavior:**
- MCU D5 drives the SG90 position.
- `DOOR_SERVO_CLOSED_ANGLE` = 0°.
- `DOOR_SERVO_OPEN_ANGLE` = 90°.
- D7 mirrors the servo state: LOW when locked, HIGH when open.

**Power Isolation:**
- MCU D5 → Servo signal only
- Separate regulated 5V PSU → Servo VCC
- Common GND between MCU and servo PSU

---

### 2. FAN OUTPUT
```
NodeMCU D0 (GPIO16)
    └─→ Fan driver / relay input
```

**Fan Behavior:**
- MCU D0 LOW = fan OFF.
- MCU D0 HIGH = fan ON.
- The current firmware drives the output directly rather than through a separate command topic.

**Power Isolation:**
- Keep the fan driver circuit isolated from the MCU.
- If you are using a relay module, wire the module input to D0 and keep the high-voltage load side separate.

---

### 3. LIGHTS, VALVES, AND INDICATORS (GPIO Outputs)

All LEDs use **active HIGH** (LED anode → pin, cathode → GND via 220Ω resistor).

#### Lights PWM
```
NodeMCU D1 (GPIO5)
    ├─→ PWM driver / LED dimmer input
        └─→ Room lights state output
```
**Behavior:**
- `0` = lights off.
- `400` = lights dim.
- `1023` = lights bright / full on.
- `lights_on` defaults to bright in the current firmware.

#### Water Valve Output
```
NodeMCU D2 (GPIO4)
    └─→ Water valve driver input
```
**Behavior:**
- LOW = valve open.
- HIGH = valve closed.
- Flood detection closes the valve once per event; it stays closed until `alert_cancel`.

#### Gas Valve Output
```
NodeMCU D6 (GPIO12)
    └─→ Gas valve driver input
```
**Behavior:**
- LOW = valve open.
- HIGH = valve closed.
- Gas detection closes the valve once per event; it stays closed until `alert_cancel`.

#### Door Indicator
```
NodeMCU D7 (GPIO13)
    └─→ Door state indicator LED
```
**Behavior:**
- LOW = locked.
- HIGH = open.
- Always mirrors the servo position.

#### Mode Indicator
```
NodeMCU D8 (GPIO15)
    └─→ Mode indicator LED
```
**Behavior:**
- `home` = solid ON.
- `away` = slow blink, about 1 second on / 1 second off.
- `sleep` = fast blink, about 200ms on / 200ms off.
- `guest` = double pulse pattern.
- `emergency` and `alert` stay solid ON.

---

### 4. SENSORS

#### Gas Sensor (Digital Input)
```
NodeMCU D4 (GPIO2)
    └─→ Gas sensor DO pin
```

**Behavior:**
- HIGH = gas detected.
- LOW = safe.
- The firmware latches the alert and only publishes the first `ALERT` transition.

#### Water/Flood Sensor (Analog Input)
```
NodeMCU A0 (ADC)
    └─→ Water/flood sensor analog output
```

**Behavior:**
- Read every 2 seconds.
- Values above 300 = flood detected.
- Values below 300 = safe/dry.

**Note:** The raw reading is published to `home/sensors/water` as a string, and the flood state is published separately to `home/sensors/flood`.

---

## Complete Wiring Diagram (Text)

---

## Complete Wiring Diagram (Text)

```
┌─────────────────────────────────────────────────────────────────┐
│                      NodeMCU Amica Board                         │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  [USB/GND]                    [VIN] [GND] [3.3V]         │   │
│  │                                                            │   │
│  │  D0────────→ [Fan Output]                                │   │
│  │  D1────────→ [Lights PWM]                                │   │
│  │  D2────────→ [Water Valve Output]                        │   │
│  │  D3────────→ (unused)                                    │   │
│  │  D4────────→ [Gas Sensor Digital Input]                  │   │
│  │  D5────────→ [Door Servo Signal]                         │   │
│  │  D6────────→ [Gas Valve Output]                          │   │
│  │  D7────────→ [Door Indicator]                            │   │
│  │  D8────────→ [Mode Indicator]                            │   │
│  │  A0        ← [Water/Flood Sensor Analog Input]           │   │
│  │  GND───────→ [Common ground to all modules]              │   │
│  │  3.3V──────→ [MCU power]                                 │   │
│  │  VIN───────→ [FTDI 5V input, 500mA USB]                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  EXTERNAL CONNECTIONS:                                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 5V PSU (Relay Coil Power)                               │   │
│  │   +5V ─────→ Relay module JVcc, Door relay coil        │   │
│  │   GND ─────→ Relay module GND (shared with MCU GND)    │   │
│  │                                                          │   │
│  │ Door Solenoid Lock (12V)                                │   │
│  │   +12V ─────→ Relay NO contact                         │   │
│  │   GND ─────→ Relay COM contact                         │   │
│  │                                                          │   │
│  │ 230V AC Fan Motor                                       │   │
│  │   L(230V) ─→ Fan relay NO contact                      │   │
│  │   N(GND) ─→ Fan relay COM contact                      │   │
│  │                                                          │   │
│  │ Gas sensor module                                     │   │
│  │   DO ──────→ NodeMCU D4                                │   │
│  │                                                          │   │
│  │ Water/flood sensor module                               │   │
│  │   AO ──────→ NodeMCU A0                                │   │
│  │                                                          │   │
│  │ Indicators / outputs                                    │   │
│  │   Fan output:      D0                                  │   │
│  │   Lights PWM:      D1                                  │   │
│  │   Water valve:     D2                                  │   │
│  │   Gas valve:       D6                                  │   │
│  │   Door indicator:  D7                                  │   │
│  │   Mode indicator:  D8                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Power Budget

| Component | Voltage | Current | Power | Notes |
|-----------|---------|---------|-------|-------|
| NodeMCU Board | 5V | ~100mA | 0.5W | FTDI USB, WiFi radio |
| Door Relay Module | 5V | ~50mA | 0.25W | Control circuit only |
| Door Solenoid | 12V | ~500mA | 6W | External PSU (seperate) |
| Fan Relay Module | 5V | ~50mA | 0.25W | Control circuit only |
| Fan Motor | 230V AC | ~0.5A | ~115W | External AC PSU (separate) |
| Gas Sensor Module | 3.3V/5V | depends on module | varies | Use a D4-compatible output level |
| Water/Flood Sensor | 3.3V/5V | depends on module | varies | Feed the analog output to A0 |
| Outputs / indicators | 3.3V | varies | varies | Fan, lights, valves, door, mode |
| **TOTAL (MCU circuit)** | 5V | varies | varies | Size power for the attached drivers |

**Power Isolation:**
- Keep the MCU side isolated from any relay or load side.
- Use a common ground between the NodeMCU and the low-voltage driver circuits.
- Keep the servo on a separate, stable 5V supply if the current draw is noisy.

---

## Runtime Notes

- The current firmware publishes all sensor and state updates over MQTT without requiring extra router-side pin logic.
- `alert_cancel` reopens both valves and clears alert flags, but it does not auto-reopen based on sensor recovery.
- The mode indicator timing and the emergency flash routine are the main runtime risks because they depend on hardware PWM, delay timing, and the exact LED/load wiring.
- No hardware flash or bench validation was performed for this documentation update.

---

## Relay Module Specifications

Assuming standard 2-channel relay module (5V logic):

| Pin | Connection |
|-----|-----------|
| JVcc | +5V (powers relay coils) |
| GND | Ground (return) |
| IN1 | Door relay control input (from D0) |
| IN2 | Fan relay control input (from D1) |
| COM1 | Common terminal for relay 1 (solenoid) |
| NO1 | Normally open for relay 1 (solenoid +12V) |
| NC1 | Normally closed for relay 1 (unused) |
| COM2 | Common terminal for relay 2 (fan) |
| NO2 | Normally open for relay 2 (fan L phase) |
| NC2 | Normally closed for relay 2 (unused) |

---

## Troubleshooting Checklist

**LEDs not lighting:**
- [ ] Check LED polarity (anode to pin, cathode to GND)
- [ ] Verify resistor value (220Ω min for 3.3V)
- [ ] Test with multimeter: D0-D4 should show 3.3V when on

**Relays not activating:**
- [ ] Check relay module power (5V at JVcc)
- [ ] Verify relay module GND connected to MCU GND
- [ ] Check relay coil continuity (should beep between COM and NO)
- [ ] Test MCU pin output with multimeter (should see voltage change)

**Gas sensor not reading:**
- [ ] Check sensor VCC (should be 5V)
- [ ] Check sensor GND (connected to MCU GND)
- [ ] Check A0 connection (should see 0-3.3V as gas changes)
- [ ] Check ADC reading in Serial Monitor (should print every 5 seconds)

**Door/Fan not responding to commands:**
- [ ] Verify MQTT topic spelling matches: `home/door/front/command`, `home/fan/command`
- [ ] Check relay control pin voltage (should pulse when command received)
- [ ] Check solenoid/motor power connections (12V or 230V)
- [ ] Verify relay coil polarity (if using DC solenoid)

---

## Configuration Defaults (from config.h)

```cpp
// Gas sensor threshold
#define GAS_SENSOR_THRESHOLD 400     // ADC value >400 = gas detected

// Door auto-lock timeout (safety)
// In DoorActuator: 5000 ms (5 seconds)

// Door action debounce
// In DoorActuator: 500 ms (prevents rapid toggling)

// LED blink intervals
// Gas alert: 200ms cycles for 5 seconds
// WiFi lost: 100ms cycles until WiFi recovers
// MQTT lost: 100ms cycles until MQTT recovers
```

---

## Files Using These Pins

| File | Usage |
|------|-------|
| [config.h](config.h) | Pin macro definitions |
| [src/actuators/Relay.h](src/actuators/Relay.h) | Door/Fan relay control (D0, D1) |
| [src/actuators/DoorActuator.h](src/actuators/DoorActuator.h) | Door-specific logic |
| [src/actuators/LED.h](src/actuators/LED.h) | Status LEDs (D2, D3, D4) |
| [src/sensors/GasSensor.h](src/sensors/GasSensor.h) | Gas sensor analog input (A0) |
| [src/logic/SystemState.h](src/logic/SystemState.h) | Orchestrates all components |

---

## Quick LED Truth Table

| WiFi | MQTT | Gas | Green | Blue | Yellow | Action |
|------|------|-----|-------|------|--------|--------|
| ✓ | ✓ | ✗ | ON | ON | ON | System OK |
| ✓ | ✓ | ✓ | OFF | BLINK | ON | Gas Alert! (Fan ON) |
| ✓ | ✗ | ✗ | OFF | ON | BLINK | MQTT searching |
| ✗ | -- | -- | OFF | BLINK | OFF | WiFi searching |
| ✗ | -- | -- | OFF | BLINK | BLINK | WiFi + MQTT lost |

---

## Connection Checklist Before Powering

- [ ] All GND connections secure (single point return)
- [ ] LED polarity correct (anode to pin, cathode to resistor to GND)
- [ ] Relay module receiving 5V
- [ ] Relay control inputs (IN1, IN2) connected to D0, D1 via small resistors
- [ ] Solenoid/motor connected via relay contacts (NOT directly to MCU)
- [ ] Gas sensor VCC at 5V, GND connected
- [ ] Gas sensor A0 connected to NodeMCU A0
- [ ] USB power not exceeded (check total current <500mA)
- [ ] No shorts between 3.3V, 5V, and GND

---

**Ready to wire!** Reference this file while connecting each component.
