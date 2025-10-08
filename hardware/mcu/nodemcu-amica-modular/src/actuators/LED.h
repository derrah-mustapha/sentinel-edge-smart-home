#ifndef LED_H
#define LED_H

#include "../../config.h"

class LED {
private:
  uint8_t pin;
  bool isOn = false;
  unsigned long blinkStartMs = 0;
  unsigned long blinkDurationMs = 0;
  unsigned long blinkIntervalMs = 0;
  
public:
  LED(uint8_t ledPin) : pin(ledPin) {}
  
  void begin() {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, LOW);  // Assuming active-high
  }
  
  // Turn LED on
  void on() {
    digitalWrite(pin, HIGH);
    isOn = true;
    blinkDurationMs = 0;  // Cancel blink mode
  }
  
  // Turn LED off
  void off() {
    digitalWrite(pin, LOW);
    isOn = false;
    blinkDurationMs = 0;  // Cancel blink mode
  }
  
  // Blink LED for a duration
  // Example: blink(500, 100) = 500ms total, 100ms on/off cycles
  void blink(unsigned long durationMs, unsigned long intervalMs) {
    blinkStartMs = millis();
    blinkDurationMs = durationMs;
    blinkIntervalMs = intervalMs;
  }
  
  // Call periodically to update blink state
  void update() {
    if (blinkDurationMs == 0) {
      return;  // Not blinking
    }
    
    unsigned long elapsed = millis() - blinkStartMs;
    if (elapsed > blinkDurationMs) {
      blinkDurationMs = 0;  // Stop blinking
      off();
      return;
    }
    
    // Toggle at interval
    unsigned long cycle = elapsed % (2 * blinkIntervalMs);
    if (cycle < blinkIntervalMs) {
      digitalWrite(pin, HIGH);
    } else {
      digitalWrite(pin, LOW);
    }
  }
  
  bool isBlinking() const {
    return blinkDurationMs > 0;
  }
};

#endif
