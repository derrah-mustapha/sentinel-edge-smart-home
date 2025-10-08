from shared.mqtt_topics import TOPICS


def handle_sensor_alert(source_topic: str, payload: str, mqtt_publisher) -> bool:
    normalized = payload.strip().lower()
    is_alert = normalized in {"1", "true", "alert", "danger", "on"}

    if not is_alert:
        return False

    if source_topic == TOPICS.SENSOR_GAS:
        mqtt_publisher.publish(TOPICS.ALARM_GAS, "ALERT")
        mqtt_publisher.publish(TOPICS.VALVE_GAS_IND, "CLOSE")
        mqtt_publisher.publish(TOPICS.FAN_CMD, "ON")
        return True

    if source_topic == TOPICS.SENSOR_WATER:
        mqtt_publisher.publish(TOPICS.ALARM_FLOOD, "ALERT")
        mqtt_publisher.publish(TOPICS.VALVE_WATER_IND, "CLOSE")
        return True

    return False
