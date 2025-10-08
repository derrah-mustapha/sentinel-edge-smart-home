import paho.mqtt.client as mqtt
import os
import ssl
import uuid
from shared.mqtt_topics import MQTTConfig


class MQTTClient:
    def __init__(self, client_type="pub", client_id: str | None = None):
        base_client_id = (
            MQTTConfig.CLIENT_ID_PUB
            if client_type == "pub"
            else MQTTConfig.CLIENT_ID_SUB
        )
        # Ensure simultaneous local processes do not kick each other out.
        resolved_client_id = client_id or f"{base_client_id}_{os.getpid()}_{uuid.uuid4().hex[:6]}"

        self.client = mqtt.Client(client_id=resolved_client_id)
        self.client_type = client_type
        self.client_id = resolved_client_id

        if MQTTConfig.USERNAME and MQTTConfig.PASSWORD:
            self.client.username_pw_set(
                MQTTConfig.USERNAME.strip(),
                MQTTConfig.PASSWORD.strip()
            )

        if MQTTConfig.USE_TLS:
            self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)

    def connect(self, start_loop: bool = False):
        print(
            f"[MQTT:{self.client_type}] Connecting client_id='{self.client_id}' "
            f"to {MQTTConfig.BROKER}:{MQTTConfig.PORT} tls={MQTTConfig.USE_TLS}"
        )
        self.client.connect(MQTTConfig.BROKER, MQTTConfig.PORT)
        if start_loop:
            self.client.loop_start()
            print(f"[MQTT:{self.client_type}] Network loop started in background")

    def publish(self, topic, message):
        print(f"[MQTT:{self.client_type}] Publishing topic='{topic}' payload='{message}'")
        result = self.client.publish(topic, message)
        result.wait_for_publish()
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[MQTT:{self.client_type}] Publish OK topic='{topic}'")
        else:
            print(f"[MQTT:{self.client_type}] Publish failed rc={result.rc} topic='{topic}'")
        return result

    def subscribe(self, topic, on_message):
        print(f"[MQTT:{self.client_type}] Subscribing topic='{topic}'")
        self.client.on_message = on_message
        self.client.subscribe(topic)

    def loop_forever(self):
        print(f"[MQTT:{self.client_type}] Entering blocking loop_forever()")
        self.client.loop_forever()