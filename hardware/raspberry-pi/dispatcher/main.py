import sys
from pathlib import Path

# Allow running this file directly: `python hardware/raspberry-pi/dispatcher/main.py`
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.mqtt_client import MQTTClient
from action_router import ActionRouter, build_mqtt_callback
from shared.mqtt_topics import TOPICS


SUBSCRIBER = MQTTClient("dispatcher-sub")
PUBLISHER = MQTTClient("dispatcher-pub")


if __name__ == "__main__":
    print("[DISPATCHER] Starting dispatcher...")
    PUBLISHER.connect(start_loop=True)
    SUBSCRIBER.connect(start_loop=False)

    router = ActionRouter(PUBLISHER)
    callback = build_mqtt_callback(router)

    for topic in [
        TOPICS.GESTURE_RAW,
        TOPICS.VOICE_CMD,
        TOPICS.ALARM_GAS,
        TOPICS.ALARM_FLOOD,
        TOPICS.SENSOR_GAS,
        TOPICS.SENSOR_WATER,
    ]:
        SUBSCRIBER.subscribe(topic, callback)

    print("[DISPATCHER] Ready. Waiting for gesture/voice/sensor events...")

    SUBSCRIBER.loop_forever()
