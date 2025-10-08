#ifndef RELAY_H
#define RELAY_H

#include "../../config.h"

// Relay control class for GPIO-driven actuators (door, fan, solenoids, etc.)
class Relay {
private:
  uint8_t pin;
  bool isOn = false;
  unsigned long onStartMs = 0;
  unsigned long maxOnDurationMs = 0;  // 0 = no limit, otherwise auto-off

  void writeRelay(bool on) {
    bool driveHigh = RELAY_ACTIVE_LOW ? !on : on;
    digitalWrite(pin, driveHigh ? HIGH : LOW);
  }
  
public:
  Relay(uint8_t relayPin) : pin(relayPin) {}
  
  void begin() {
    pinMode(pin, OUTPUT);
    writeRelay(false);  // Default off
  }
  
  // Turn relay on
  // If maxDurationMs > 0, relay will auto-off after that many milliseconds
  void on(unsigned long maxDurationMs = 0) {
    writeRelay(true);
    isOn = true;
    onStartMs = millis();
    maxOnDurationMs = maxDurationMs;
  }
  
  // Turn relay off
  void off() {
    writeRelay(false);
    isOn = false;
    maxOnDurationMs = 0;
  }
  
  // Toggle relay state
  void toggle() {
    if (isOn) {
      off();
    } else {
      on();
    }
  }
  
  // Call periodically to enforce max duration
  void update() {
    if (!isOn || maxOnDurationMs == 0) {
      return;  // Not on, or no time limit
    }
    
    unsigned long elapsed = millis() - onStartMs;
    if (elapsed >= maxOnDurationMs) {
      off();  // Time limit reached, auto-off
    }
  }
  
  bool getState() const {
    return isOn;
  }
  
  const char* getStateStr() const {
    return isOn ? "ON" : "OFF";
  }
};

#endif
