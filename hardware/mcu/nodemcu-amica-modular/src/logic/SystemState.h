#ifndef SYSTEM_STATE_H
#define SYSTEM_STATE_H

#include <Arduino.h>
#include <PubSubClient.h>
#include <Servo.h>

#include "../../config.h"

class SystemState {
public:
  enum class Mode {
    HOME,
    AWAY,
    SLEEP,
    GUEST,
    ALERT,
    EMERGENCY,
  };

  void begin() {
    analogWriteFreq(1000);
    analogWriteRange(1023);

    pinMode(PIN_GAS_SENSOR, INPUT);
    pinMode(PIN_FAN_RELAY, OUTPUT);
    pinMode(PIN_LIGHTS_OUTPUT, OUTPUT);
    pinMode(PIN_WATER_VALVE_OUTPUT, OUTPUT);
    pinMode(PIN_GAS_VALVE_OUTPUT, OUTPUT);
    pinMode(PIN_DOOR_INDICATOR, OUTPUT);
    pinMode(PIN_MODE_INDICATOR, OUTPUT);

    doorServo.attach(PIN_DOOR_SERVO);

    setFan(false);
    setLightsLevel(0);
    setDoorLocked();
    setWaterValveOpen(true);
    setGasValveOpen(true);
    setMode(Mode::HOME, true);

    gasDetected = false;
    floodDetected = false;
    gasAlertActive = false;
    floodAlertActive = false;
    lastSensorPollMs = millis();
    publishBootSnapshot = true;
  }

  void update(PubSubClient& mqttClient) {
    updateModeIndicator();

    unsigned long now = millis();
    if (publishBootSnapshot) {
      publishBootSnapshot = false;
      publishAllStates(mqttClient);
    }

    if (now - lastSensorPollMs < SENSOR_POLL_INTERVAL_MS) {
      return;
    }

    lastSensorPollMs = now;
    pollSensors(mqttClient);
  }

  void setWifiConnected(bool connected) {
    wifiConnected = connected;
  }

  void setMqttConnected(bool connected) {
    mqttConnected = connected;
  }

  void handleCommand(const String& token, PubSubClient& mqttClient) {
    Serial.print("[CMD] received = ");
    Serial.println(token);

    if (token == "fan_on") {
      setFan(true);
      publishFanState(mqttClient);
      return;
    }

    if (token == "fan_off") {
      setFan(false);
      publishFanState(mqttClient);
      return;
    }

    if (token == "lights_on") {
      setLightsLevel(mode == Mode::SLEEP ? 400 : 1023);
      publishLightsState(mqttClient);
      return;
    }

    if (token == "lights_off") {
      setLightsLevel(0);
      publishLightsState(mqttClient);
      return;
    }

    if (token == "lights_dim") {
      setLightsLevel(400);
      publishLightsState(mqttClient);
      return;
    }

    if (token == "lights_bright") {
      setLightsLevel(1023);
      publishLightsState(mqttClient);
      return;
    }

    if (token == "door_open") {
      setDoorOpen();
      publishDoorState(mqttClient);
      return;
    }

    if (token == "door_close") {
      setDoorLocked();
      publishDoorState(mqttClient);
      return;
    }

    if (token == "mode_home") {
      setMode(Mode::HOME);
      publishModeState(mqttClient);
      return;
    }

    if (token == "mode_away") {
      setMode(Mode::AWAY);
      publishModeState(mqttClient);
      return;
    }

    if (token == "mode_sleep") {
      setMode(Mode::SLEEP);
      publishModeState(mqttClient);
      return;
    }

    if (token == "mode_guest") {
      setMode(Mode::GUEST);
      publishModeState(mqttClient);
      return;
    }

    if (token == "alert_cancel") {
      gasAlertActive = false;
      floodAlertActive = false;
      setGasValveOpen(true);
      setWaterValveOpen(true);
      publishGasValveState(mqttClient);
      publishWaterValveState(mqttClient);
      publishGasAlertState(mqttClient);
      publishFloodAlertState(mqttClient);
      return;
    }

    if (token == "emergency_activate") {
      flashEmergencyOutputs();
      setFan(true);
      setLightsLevel(1023);
      setDoorOpen();
      setGasValveOpen(false);
      setWaterValveOpen(false);
      setMode(Mode::EMERGENCY, true);
      publishAllStates(mqttClient);
      return;
    }

    if (token == "emergency_cancel") {
      restoreHomeDefaults();
      publishAllStates(mqttClient);
      return;
    }

    if (token == "status_query") {
      publishAllStates(mqttClient);
      return;
    }

    if (token == "windows_open_all" || token == "windows_close_all" ||
        token == "window_open_1" || token == "window_close_1" ||
        token == "window_open_2" || token == "window_close_2") {
      Serial.println("[TODO] Window token accepted as virtual-only state");
      return;
    }

    Serial.println("[CMD] unknown token ignored");
  }

  void publishTelemetry(PubSubClient& mqttClient) {
    publishState(mqttClient, TOPIC_SENSOR_GAS, gasDetected ? "1" : "0", false);
    publishState(mqttClient, TOPIC_SENSOR_WATER, String(waterReading), false);
    publishState(mqttClient, TOPIC_SENSOR_FLOOD, floodDetected ? "1" : "0", false);
  }

  void publishAllStates(PubSubClient& mqttClient) {
    publishTelemetry(mqttClient);
    publishFanState(mqttClient);
    publishLightsState(mqttClient);
    publishDoorState(mqttClient);
    publishModeState(mqttClient);
    publishGasValveState(mqttClient);
    publishWaterValveState(mqttClient);
    publishGasAlertState(mqttClient);
    publishFloodAlertState(mqttClient);
  }

  uint16_t getGasReading() const { return gasDetected ? 1 : 0; }
  bool getGasDetected() const { return gasDetected; }
  const char* getGasStatus() const { return gasDetected ? "DETECTED" : "NORMAL"; }

private:
  Servo doorServo;

  Mode mode = Mode::HOME;

  bool fanOn = false;
  uint16_t lightsLevel = 0;
  bool doorOpen = false;
  bool gasValveOpen = true;
  bool waterValveOpen = true;

  bool wifiConnected = false;
  bool mqttConnected = false;

  bool gasDetected = false;
  bool floodDetected = false;
  bool gasAlertActive = false;
  bool floodAlertActive = false;

  uint16_t waterReading = 0;
  unsigned long lastSensorPollMs = 0;
  bool publishBootSnapshot = false;

  unsigned long lastModePatternMs = 0;
  unsigned long modePatternPhaseMs = 0;
  bool modePatternOutput = true;

  const char* modeToString() const {
    switch (mode) {
      case Mode::HOME: return "home";
      case Mode::AWAY: return "away";
      case Mode::SLEEP: return "sleep";
      case Mode::GUEST: return "guest";
      case Mode::ALERT: return "alert";
      case Mode::EMERGENCY: return "emergency";
    }
    return "home";
  }

  void publishState(PubSubClient& mqttClient, const char* topic, const String& payload, bool retain = true) {
    mqttClient.publish(topic, payload.c_str(), retain);
    Serial.print("[MQTT TX] ");
    Serial.print(topic);
    Serial.print(" = ");
    Serial.println(payload);
  }

  void publishFanState(PubSubClient& mqttClient) { publishState(mqttClient, TOPIC_STATE_FAN, fanOn ? "on" : "off"); }
  void publishLightsState(PubSubClient& mqttClient) {
    if (lightsLevel <= 0) {
      publishState(mqttClient, TOPIC_STATE_LIGHTS, "off");
    } else if (lightsLevel < 800) {
      publishState(mqttClient, TOPIC_STATE_LIGHTS, "dim");
    } else {
      publishState(mqttClient, TOPIC_STATE_LIGHTS, "bright");
    }
  }
  void publishDoorState(PubSubClient& mqttClient) { publishState(mqttClient, TOPIC_STATE_DOOR, doorOpen ? "open" : "locked"); }
  void publishModeState(PubSubClient& mqttClient) { publishState(mqttClient, TOPIC_STATE_MODE, modeToString()); }
  void publishGasValveState(PubSubClient& mqttClient) { publishState(mqttClient, TOPIC_STATE_GAS_VALVE, gasValveOpen ? "open" : "closed"); }
  void publishWaterValveState(PubSubClient& mqttClient) { publishState(mqttClient, TOPIC_STATE_WATER_VALVE, waterValveOpen ? "open" : "closed"); }
  void publishGasAlertState(PubSubClient& mqttClient) { publishState(mqttClient, TOPIC_ALERT_GAS, gasAlertActive ? "ALERT" : "CLEAR"); }
  void publishFloodAlertState(PubSubClient& mqttClient) { publishState(mqttClient, TOPIC_ALERT_FLOOD, floodAlertActive ? "ALERT" : "CLEAR"); }

  void setFan(bool on) {
    fanOn = on;
    digitalWrite(PIN_FAN_RELAY, on ? HIGH : LOW);
  }

  void setLightsLevel(uint16_t level) {
    lightsLevel = level;
    analogWrite(PIN_LIGHTS_OUTPUT, level);
  }

  void setDoorOpen() {
    doorOpen = true;
    doorServo.write(DOOR_SERVO_OPEN_ANGLE);
    digitalWrite(PIN_DOOR_INDICATOR, HIGH);
  }

  void setDoorLocked() {
    doorOpen = false;
    doorServo.write(DOOR_SERVO_CLOSED_ANGLE);
    digitalWrite(PIN_DOOR_INDICATOR, LOW);
  }

  void setGasValveOpen(bool open) {
    gasValveOpen = open;
    digitalWrite(PIN_GAS_VALVE_OUTPUT, open ? LOW : HIGH);
  }

  void setWaterValveOpen(bool open) {
    waterValveOpen = open;
    digitalWrite(PIN_WATER_VALVE_OUTPUT, open ? LOW : HIGH);
  }

  void restoreHomeDefaults() {
    setFan(false);
    setLightsLevel(1023);
    setDoorLocked();
    setGasValveOpen(true);
    setWaterValveOpen(true);
    gasAlertActive = false;
    floodAlertActive = false;
    setMode(Mode::HOME, true);
  }

  void setMode(Mode newMode, bool applyIndicator = true) {
    mode = newMode;
    lastModePatternMs = millis();
    modePatternPhaseMs = millis();
    modePatternOutput = true;

    if (applyIndicator) {
      applyModeIndicator(true);
    }
  }

  void applyModeIndicator(bool forceImmediate = false) {
    unsigned long now = millis();
    if (forceImmediate) {
      lastModePatternMs = now;
      modePatternPhaseMs = now;
      modePatternOutput = true;
    }

    switch (mode) {
      case Mode::HOME:
        digitalWrite(PIN_MODE_INDICATOR, HIGH);
        return;
      case Mode::AWAY:
        if (now - lastModePatternMs >= MODE_BLINK_SLOW_MS) {
          lastModePatternMs = now;
          modePatternOutput = !modePatternOutput;
        }
        digitalWrite(PIN_MODE_INDICATOR, modePatternOutput ? HIGH : LOW);
        return;
      case Mode::SLEEP:
        if (now - lastModePatternMs >= MODE_BLINK_FAST_MS) {
          lastModePatternMs = now;
          modePatternOutput = !modePatternOutput;
        }
        digitalWrite(PIN_MODE_INDICATOR, modePatternOutput ? HIGH : LOW);
        return;
      case Mode::GUEST: {
        unsigned long elapsed = now - modePatternPhaseMs;
        unsigned long cycle = elapsed % (MODE_GUEST_PULSE_MS * 3 + 1000);
        bool on = cycle < MODE_GUEST_PULSE_MS || (cycle >= (MODE_GUEST_PULSE_MS * 2) && cycle < (MODE_GUEST_PULSE_MS * 3));
        digitalWrite(PIN_MODE_INDICATOR, on ? HIGH : LOW);
        return;
      }
      case Mode::ALERT:
      case Mode::EMERGENCY:
        digitalWrite(PIN_MODE_INDICATOR, HIGH);
        return;
    }
  }

  void updateModeIndicator() {
    applyModeIndicator(false);
  }

  void flashEmergencyOutputs() {
    for (int i = 0; i < 3; i++) {
      digitalWrite(PIN_FAN_RELAY, HIGH);
      analogWrite(PIN_LIGHTS_OUTPUT, 1023);
      digitalWrite(PIN_WATER_VALVE_OUTPUT, HIGH);
      digitalWrite(PIN_GAS_VALVE_OUTPUT, HIGH);
      digitalWrite(PIN_DOOR_INDICATOR, HIGH);
      digitalWrite(PIN_MODE_INDICATOR, HIGH);
      delay(EMERGENCY_FLASH_MS);

      digitalWrite(PIN_FAN_RELAY, LOW);
      analogWrite(PIN_LIGHTS_OUTPUT, 0);
      digitalWrite(PIN_WATER_VALVE_OUTPUT, LOW);
      digitalWrite(PIN_GAS_VALVE_OUTPUT, LOW);
      digitalWrite(PIN_DOOR_INDICATOR, LOW);
      digitalWrite(PIN_MODE_INDICATOR, LOW);
      delay(EMERGENCY_FLASH_MS);
    }
  }

  void pollSensors(PubSubClient& mqttClient) {
    gasDetected = (digitalRead(PIN_GAS_SENSOR) == HIGH);
    waterReading = analogRead(PIN_WATER_SENSOR);
    floodDetected = (waterReading > WATER_FLOOD_THRESHOLD);

    publishTelemetry(mqttClient);

    if (gasDetected && !gasAlertActive) {
      gasAlertActive = true;
      setGasValveOpen(false);
      setMode(Mode::ALERT, true);
      publishGasAlertState(mqttClient);
      publishGasValveState(mqttClient);
      publishModeState(mqttClient);
    } else if (!gasDetected && gasAlertActive) {
      gasAlertActive = false;
      publishGasAlertState(mqttClient);
    }

    if (floodDetected && !floodAlertActive) {
      floodAlertActive = true;
      setWaterValveOpen(false);
      setMode(Mode::ALERT, true);
      publishFloodAlertState(mqttClient);
      publishWaterValveState(mqttClient);
      publishModeState(mqttClient);
    } else if (!floodDetected && floodAlertActive) {
      floodAlertActive = false;
      publishFloodAlertState(mqttClient);
    }
  }
};

#endif
