from shared.mqtt_topics import TOPICS


def publish_face_event(mqtt_client, identity: str, allowed: bool) -> None:
    payload = f"{identity}:{'allow' if allowed else 'deny'}"
    mqtt_client.publish(TOPICS.FACE_ACCESS, payload)
