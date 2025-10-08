import sys
from pathlib import Path

# Allow running this file directly from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.mqtt_client import MQTTClient
from shared.mqtt_topics import MQTTConfig

mqtt_client = MQTTClient("pub")
mqtt_client.connect()

def publish_command(cmd):
    mqtt_client.publish(MQTTConfig.PUB_TOPIC, cmd)