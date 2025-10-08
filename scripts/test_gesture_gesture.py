#!/usr/bin/env python3
"""
Quick test script to verify gesture→command→device flow.
Publishes fake gesture commands to MQTT to test dispatcher routing.
"""
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.mqtt_client import MQTTClient
from shared.mqtt_topics import TOPICS

TEST_GESTURES = [
    "fan_on",
    "fan_off",
    "mode_home",
    "mode_away",
    "mode_guest",
    "alert_cancel",
    "door_open",
    "door_close",
    "emergency_activate",
]


def test_gesture_publishing():
    """Test publishing gesture commands without camera."""
    print("[TEST] Connecting to MQTT...")
    mqtt = MQTTClient("gesture-test-pub")
    mqtt.connect(start_loop=True)
    
    print(f"[TEST] Testing with TOPIC: {TOPICS.GESTURE_RAW}\n")
    
    for gesture in TEST_GESTURES:
        print(f"[TEST] Publishing gesture: {gesture}")
        mqtt.publish(TOPICS.GESTURE_RAW, gesture)
        time.sleep(1.5)
    
    print("\n[TEST] All test gestures published!")
    print("[TEST] Check dispatcher logs to verify commands routed correctly")


if __name__ == "__main__":
    try:
        test_gesture_publishing()
    except KeyboardInterrupt:
        print("\n[TEST] Interrupted")
