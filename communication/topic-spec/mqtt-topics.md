# MQTT Topics

These topics are defined in `shared/mqtt_topics.py` and can be overridden from `.env`.

## Fixed Topics

| Env key | Default topic |
|---|---|
| TOPIC_DOOR_FRONT_CMD | home/door/front/command |
| TOPIC_DOOR_FRONT_STATE | home/door/front/state |
| TOPIC_VALVE_GAS_IND | home/valve/gas/indicator |
| TOPIC_VALVE_WATER_IND | home/valve/water/indicator |
| TOPIC_FAN_CMD | home/fan/command |
| TOPIC_FAN_STATE | home/fan/state |
| TOPIC_SENSOR_GAS | home/sensor/gas |
| TOPIC_SENSOR_WATER | home/sensor/water |
| TOPIC_ALARM_GAS | home/alarm/gas |
| TOPIC_ALARM_FLOOD | home/alarm/flood |
| TOPIC_GESTURE_RAW | home/gesture/raw |
| TOPIC_VOICE_CMD | home/voice/command |
| TOPIC_FACE_ACCESS | home/access/face |

## Prefix Topics

| Env key | Default prefix | Built helpers |
|---|---|---|
| TOPIC_WINDOW_CMD_PREFIX | home/window | window_cmd(id) |
| TOPIC_WINDOW_STATE_PREFIX | home/window | window_state(id) |
| TOPIC_LIGHT_CMD_PREFIX | home/light | light_cmd(zone) |
| TOPIC_LIGHT_STATE_PREFIX | home/light | light_state(zone) |
| TOPIC_SYSTEM_STATUS_PREFIX | home/system | device_status(device) |

## Compatibility Keys

`TOPIC` and `PUB_TOPIC` are still available for legacy scripts and map to the subscriber wildcard and publish topic used by older code paths.
