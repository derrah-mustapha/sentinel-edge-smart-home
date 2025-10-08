import os
from dataclasses import dataclass

from backend.config.env_loader import load_environment


@dataclass(frozen=True)
class Config:
    broker: str
    port: int
    use_tls: bool
    username: str | None
    password: str | None
    client_id_sub: str
    client_id_pub: str


def load_config() -> Config:
    load_environment()
    client_prefix = os.getenv("MQTT_CLIENT_ID_PREFIX", "sentinel")
    return Config(
        broker=os.getenv("MQTT_BROKER_HOST", os.getenv("BROKER", "localhost")),
        port=int(os.getenv("MQTT_BROKER_PORT", os.getenv("PORT", 1883))),
        use_tls=os.getenv("MQTT_USE_TLS", os.getenv("USE_TLS", "false")).lower() == "true",
        username=os.getenv("MQTT_USERNAME"),
        password=os.getenv("MQTT_PASSWORD", os.getenv("PASSWORD")),
        client_id_sub=os.getenv("CLIENT_ID_SUB", f"{client_prefix}_sub"),
        client_id_pub=os.getenv("CLIENT_ID_PUB", f"{client_prefix}_pub"),
    )


CONFIG = load_config()
