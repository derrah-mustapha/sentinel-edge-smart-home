#ifndef DOOR_ACTUATOR_H
#define DOOR_ACTUATOR_H

#include "../../config.h"
#include "Relay.h"

// Door-specific logic wrapper
// Handles door lock/unlock with safety constraints
class DoorActuator {
private:
  Relay* relay;
  bool isLocked = false;  // Track actual state
  unsigned long lastActionMs = 0;
  const unsigned long MIN_ACTION_INTERVAL = 500;  // Prevent rapid toggling
  const unsigned long UNLOCK_MAX_DURATION = 5000; // Auto-lock after 5s
  
public:
  DoorActuator(Relay& doorRelay) : relay(&doorRelay) {}
  
  void begin() {
    relay->begin();
  }
  
  // Unlock door (energize solenoid)
  bool unlock() {
    unsigned long now = millis();
    if (now - lastActionMs < MIN_ACTION_INTERVAL) {
      return false;  // Action too soon, ignore
    }
    
    relay->on(UNLOCK_MAX_DURATION);  // Auto-lock after 5 seconds
    isLocked = false;
    lastActionMs = now;
    return true;
  }
  
  // Lock door (de-energize solenoid)
  bool lock() {
    unsigned long now = millis();
    if (now - lastActionMs < MIN_ACTION_INTERVAL) {
      return false;  // Action too soon, ignore
    }
    
    relay->off();
    isLocked = true;
    lastActionMs = now;
    return true;
  }
  
  // Call periodically for auto-off logic
  void update() {
    relay->update();
  }
  
  bool getIsLocked() const {
    return isLocked;
  }
  
  const char* getStateStr() const {
    return isLocked ? "LOCKED" : "UNLOCKED";
  }
};

#endif
