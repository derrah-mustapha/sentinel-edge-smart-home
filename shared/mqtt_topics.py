import os
from dataclasses import dataclass

from backend.config.env_loader import load_environment


# Load the selected .env file before reading broker/topic settings.
load_environment()


@dataclass(frozen=True)
class Topics:
    COMMANDS: str
    DOOR_FRONT_CMD: str
    DOOR_FRONT_STATE: str
    WINDOW_CMD_PREFIX: str
    WINDOW_STATE_PREFIX: str
    LIGHT_CMD_PREFIX: str
    LIGHT_STATE_PREFIX: str
    FAN_STATE_TOPIC: str
    LIGHTS_STATE_TOPIC: str
    WINDOWS_STATE_TOPIC: str
    DOOR_STATE_TOPIC: str
    MODE_STATE_TOPIC: str
    GAS_VALVE_STATE_TOPIC: str
    WATER_VALVE_STATE_TOPIC: str
    SENSOR_GAS_TOPIC: str
    SENSOR_WATER_TOPIC: str
    SENSOR_FLOOD_TOPIC: str
    ALERT_GAS_TOPIC: str
    ALERT_FLOOD_TOPIC: str
    VALVE_GAS_IND: str
    VALVE_WATER_IND: str
    FAN_CMD: str
    FAN_STATE: str
    SENSOR_GAS: str
    SENSOR_WATER: str
    ALARM_GAS: str
    ALARM_FLOOD: str
    GESTURE_RAW: str
    VOICE_CMD: str
    FACE_ACCESS: str
    SYSTEM_STATUS_PREFIX: str

    def window_cmd(self, window_id: str) -> str:
        return f"{self.WINDOW_CMD_PREFIX}/{window_id}/command"

    def window_state(self, window_id: str) -> str:
        return f"{self.WINDOW_STATE_PREFIX}/{window_id}/state"

    def light_cmd(self, zone: str) -> str:
        return f"{self.LIGHT_CMD_PREFIX}/{zone}/command"

    def light_state(self, zone: str) -> str:
        return f"{self.LIGHT_STATE_PREFIX}/{zone}/state"

    def device_status(self, device: str) -> str:
        return f"{self.SYSTEM_STATUS_PREFIX}/{device}/status"


def load_topics() -> Topics:
    return Topics(
        COMMANDS=os.getenv("TOPIC_COMMANDS", "home/commands"),
        DOOR_FRONT_CMD=os.getenv("TOPIC_DOOR_FRONT_CMD", "home/door/front/command"),
        DOOR_FRONT_STATE=os.getenv("TOPIC_DOOR_FRONT_STATE", "home/door/front/state"),
        WINDOW_CMD_PREFIX=os.getenv("TOPIC_WINDOW_CMD_PREFIX", os.getenv("TOPIC_WINDOW_PREFIX", "home/window")),
        WINDOW_STATE_PREFIX=os.getenv("TOPIC_WINDOW_STATE_PREFIX", os.getenv("TOPIC_WINDOW_PREFIX", "home/window")),
        LIGHT_CMD_PREFIX=os.getenv("TOPIC_LIGHT_CMD_PREFIX", os.getenv("TOPIC_LIGHT_PREFIX", "home/light")),
        LIGHT_STATE_PREFIX=os.getenv("TOPIC_LIGHT_STATE_PREFIX", os.getenv("TOPIC_LIGHT_PREFIX", "home/light")),
        FAN_STATE_TOPIC=os.getenv("TOPIC_FAN_STATE_TOPIC", "home/state/fan"),
        LIGHTS_STATE_TOPIC=os.getenv("TOPIC_LIGHTS_STATE_TOPIC", "home/state/lights"),
        WINDOWS_STATE_TOPIC=os.getenv("TOPIC_WINDOWS_STATE_TOPIC", "home/state/windows"),
        DOOR_STATE_TOPIC=os.getenv("TOPIC_DOOR_STATE_TOPIC", "home/state/door"),
        MODE_STATE_TOPIC=os.getenv("TOPIC_MODE_STATE_TOPIC", "home/state/mode"),
        GAS_VALVE_STATE_TOPIC=os.getenv("TOPIC_GAS_VALVE_STATE_TOPIC", "home/state/gas_valve"),
        WATER_VALVE_STATE_TOPIC=os.getenv("TOPIC_WATER_VALVE_STATE_TOPIC", "home/state/water_valve"),
        SENSOR_GAS_TOPIC=os.getenv("TOPIC_SENSOR_GAS_TOPIC", "home/sensors/gas"),
        SENSOR_WATER_TOPIC=os.getenv("TOPIC_SENSOR_WATER_TOPIC", "home/sensors/water"),
        SENSOR_FLOOD_TOPIC=os.getenv("TOPIC_SENSOR_FLOOD_TOPIC", "home/sensors/flood"),
        ALERT_GAS_TOPIC=os.getenv("TOPIC_ALERT_GAS_TOPIC", "home/alerts/gas"),
        ALERT_FLOOD_TOPIC=os.getenv("TOPIC_ALERT_FLOOD_TOPIC", "home/alerts/flood"),
        VALVE_GAS_IND=os.getenv("TOPIC_VALVE_GAS_IND", "home/valve/gas/indicator"),
        VALVE_WATER_IND=os.getenv("TOPIC_VALVE_WATER_IND", "home/valve/water/indicator"),
        FAN_CMD=os.getenv("TOPIC_FAN_CMD", "home/fan/command"),
        FAN_STATE=os.getenv("TOPIC_FAN_STATE", "home/fan/state"),
        SENSOR_GAS=os.getenv("TOPIC_SENSOR_GAS", "home/sensor/gas"),
        SENSOR_WATER=os.getenv("TOPIC_SENSOR_WATER", "home/sensor/water"),
        ALARM_GAS=os.getenv("TOPIC_ALARM_GAS", "home/alarm/gas"),
        ALARM_FLOOD=os.getenv("TOPIC_ALARM_FLOOD", "home/alarm/flood"),
        GESTURE_RAW=os.getenv("TOPIC_GESTURE_RAW", "home/gesture/raw"),
        VOICE_CMD=os.getenv("TOPIC_VOICE_CMD", "home/voice/command"),
        FACE_ACCESS=os.getenv("TOPIC_FACE_ACCESS", "home/access/face"),
        SYSTEM_STATUS_PREFIX=os.getenv("TOPIC_SYSTEM_STATUS_PREFIX", os.getenv("TOPIC_SYSTEM_PREFIX", "home/system")),
    )


TOPICS = load_topics()


class MQTTConfig:
    BROKER = os.getenv("MQTT_BROKER_HOST", os.getenv("BROKER", "localhost"))
    PORT = int(os.getenv("MQTT_BROKER_PORT", os.getenv("PORT", 1883)))
    USE_TLS = os.getenv("MQTT_USE_TLS", os.getenv("USE_TLS", "false")).lower() == "true"
    USERNAME = os.getenv("MQTT_USERNAME")
    PASSWORD = os.getenv("MQTT_PASSWORD", os.getenv("PASSWORD"))
    _CLIENT_PREFIX = os.getenv("MQTT_CLIENT_ID_PREFIX", "sentinel")
    CLIENT_ID_SUB = os.getenv("CLIENT_ID_SUB", f"{_CLIENT_PREFIX}_sub")
    CLIENT_ID_PUB = os.getenv("CLIENT_ID_PUB", f"{_CLIENT_PREFIX}_pub")
    GESTURE_ENABLED = os.getenv("GESTURE_ENABLED", "true").lower() == "true"
    VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true").lower() == "true"
    FACE_RECOG_ENABLED = os.getenv("FACE_RECOG_ENABLED", "false").lower() == "true"
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
    GESTURE_CONFIDENCE_THRESHOLD = float(os.getenv("GESTURE_CONFIDENCE_THRESHOLD", 0.75))

    # Backward-compatible aliases for existing scripts.
    TOPIC = os.getenv("TOPIC", "home/#")
    PUB_TOPIC = os.getenv("PUB_TOPIC", TOPICS.GESTURE_RAW)
