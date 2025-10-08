import sys
from pathlib import Path

# Allow direct execution: `python3 scripts/test_subscriber.py`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.mqtt_client import MQTTClient
from shared.mqtt_topics import TOPICS


def on_message(client, userdata, msg):
    payload = msg.payload.decode(errors="ignore")
    print(f"[SUBSCRIBER] 📩 topic='{msg.topic}' payload='{payload}'")


OUTPUT_TOPICS = [
    TOPICS.DOOR_FRONT_CMD,
    TOPICS.FAN_CMD,
    TOPICS.VALVE_GAS_IND,
    TOPICS.VALVE_WATER_IND,
    TOPICS.ALARM_GAS,
    TOPICS.ALARM_FLOOD,
]

mqtt = MQTTClient("sub")

print("[SUBSCRIBER] Starting. output-only monitor mode")
mqtt.connect(start_loop=False)
for topic in OUTPUT_TOPICS:
    mqtt.subscribe(topic, on_message)

print("[SUBSCRIBER] Running...")

mqtt.loop_forever()