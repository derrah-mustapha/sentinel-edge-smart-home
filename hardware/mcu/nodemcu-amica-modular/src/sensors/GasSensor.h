#ifndef GAS_SENSOR_H
#define GAS_SENSOR_H

#include "../../config.h"

// Gas sensor sample configuration
#define GAS_SENSOR_PIN A0            // Analog pin for gas sensor
#define GAS_SENSOR_THRESHOLD 400     // ADC threshold: >400 = gas detected
#define GAS_READ_INTERVAL_MS 5000    // Read every 5 seconds

class GasSensor {
private:
  uint16_t lastReading = 0;
  bool lastDetected = false;
  unsigned long lastReadMs = 0;
  
public:
  GasSensor() {}
  
  // Initialize sensor
  void begin() {
    pinMode(GAS_SENSOR_PIN, INPUT);
  }
  
  // Read sensor if interval has passed
  // Returns true if new reading taken
  bool update() {
    unsigned long now = millis();
    if (now - lastReadMs < GAS_READ_INTERVAL_MS) {
      return false;  // Not time to read yet
    }
    
    lastReadMs = now;
    lastReading = analogRead(GAS_SENSOR_PIN);
    bool detected = (lastReading > GAS_SENSOR_THRESHOLD);
    
    // Only return true if state changed (edge detect)
    if (detected != lastDetected) {
      lastDetected = detected;
      return true;  // Change detected
    }
    
    return false;   // No change
  }
  
  uint16_t getReading() const {
    return lastReading;
  }
  
  bool isDetected() const {
    return lastDetected;
  }
  
  const char* getStatusStr() const {
    return lastDetected ? "DETECTED" : "NORMAL";
  }
};

#endif
