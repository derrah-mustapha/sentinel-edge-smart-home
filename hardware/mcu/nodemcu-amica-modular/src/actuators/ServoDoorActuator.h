#ifndef SERVO_DOOR_ACTUATOR_H
#define SERVO_DOOR_ACTUATOR_H

#include <Servo.h>

#include "../../config.h"

// SG90-based door actuator.
// Keeps the existing lock/unlock semantics used by the MQTT command flow.
class ServoDoorActuator {
private:
  Servo servo;
  uint8_t pin;
  bool isLocked = true;
  unsigned long lastActionMs = 0;
  const unsigned long MIN_ACTION_INTERVAL = 500;

  void moveToAngle(int angle) {
    servo.write(angle);
  }

public:
  explicit ServoDoorActuator(uint8_t servoPin) : pin(servoPin) {}

  void begin() {
    servo.attach(pin);
    moveToAngle(DOOR_SERVO_CLOSED_ANGLE);
    isLocked = true;
  }

  // Unlock door = move servo to the open position.
  bool unlock() {
    unsigned long now = millis();
    if (now - lastActionMs < MIN_ACTION_INTERVAL) {
      return false;
    }

    moveToAngle(DOOR_SERVO_OPEN_ANGLE);
    isLocked = false;
    lastActionMs = now;
    return true;
  }

  // Lock door = move servo back to the closed position.
  bool lock() {
    unsigned long now = millis();
    if (now - lastActionMs < MIN_ACTION_INTERVAL) {
      return false;
    }

    moveToAngle(DOOR_SERVO_CLOSED_ANGLE);
    isLocked = true;
    lastActionMs = now;
    return true;
  }

  void update() {
    // SG90 holds position via servo library; no periodic work required.
  }

  bool getIsLocked() const {
    return isLocked;
  }

  const char* getStateStr() const {
    return isLocked ? "LOCKED" : "UNLOCKED";
  }
};

#endif
