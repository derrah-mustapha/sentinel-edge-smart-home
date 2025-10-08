from dataclasses import asdict

from shared.mqtt_topics import TOPICS


def health() -> dict:
    return {"status": "ok"}


def mqtt_topics() -> dict:
    return asdict(TOPICS)
