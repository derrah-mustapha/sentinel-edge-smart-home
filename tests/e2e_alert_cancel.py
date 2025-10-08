"""
E2E test: alert -> cancel during countdown

Run this with the project's virtualenv active. It publishes a gas alert,
waits a configurable delay, then publishes `alert_cancel` and asserts the
dispatcher published `ALERT_CANCELLED` and did not escalate to `EMERGENCY`.

Usage:
    python tests/e2e_alert_cancel.py

Environment:
- Uses broker from `shared.mqtt_topics.MQTTConfig` (respect .env)
- Configurable delays via constants below
"""

import time
import queue
import sys
from shared.mqtt_topics import TOPICS, MQTTConfig
import paho.mqtt.client as mqtt

# Test parameters
ALERT_PUBLISH_DELAY = 0.5       # seconds before sending the initial alert
CANCEL_AFTER_SECONDS = 5       # send alert_cancel after this many seconds
TEST_TIMEOUT = 40              # overall timeout

msg_q: queue.Queue = queue.Queue()
received_status = []


def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode('utf-8', errors='replace').strip()
    print(f"[TEST RX] {topic} -> {payload}")
    msg_q.put((topic, payload))
    if topic == TOPICS.device_status("dispatcher"):
        received_status.append(payload)


def run_test():
    client_id = f"e2e-test-{int(time.time())}"
    client = mqtt.Client(client_id=client_id)
    if MQTTConfig.USERNAME and MQTTConfig.PASSWORD:
        client.username_pw_set(MQTTConfig.USERNAME, MQTTConfig.PASSWORD)

    client.on_message = on_message
    client.connect(MQTTConfig.BROKER, MQTTConfig.PORT)
    client.loop_start()

    # Subscribe to dispatcher status and alarm topics
    subs = [
        TOPICS.device_status("dispatcher"),
        TOPICS.ALARM_GAS,
        TOPICS.ALARM_FLOOD,
    ]
    for s in subs:
        client.subscribe(s)
        print(f"[TEST] Subscribed to {s}")

    time.sleep(ALERT_PUBLISH_DELAY)
    print(f"[TEST] Publishing ALERT to {TOPICS.SENSOR_GAS}")
    client.publish(TOPICS.SENSOR_GAS, "ALERT")

    start = time.time()
    canceled = False
    escalated = False
    saw_cancelled = False

    # After CANCEL_AFTER_SECONDS, publish alert_cancel
    cancel_time = start + CANCEL_AFTER_SECONDS

    while time.time() - start < TEST_TIMEOUT:
        now = time.time()
        if not canceled and now >= cancel_time:
            print(f"[TEST] Publishing alert_cancel to {TOPICS.VOICE_CMD}")
            client.publish(TOPICS.VOICE_CMD, "alert_cancel")
            canceled = True

        try:
            topic, payload = msg_q.get(timeout=1)
        except queue.Empty:
            continue

        # Watch for EMERGENCY
        if topic == TOPICS.device_status("dispatcher") and payload.upper() == "EMERGENCY":
            escalated = True
            break
        if topic == TOPICS.device_status("dispatcher") and payload.upper() == "ALERT_CANCELLED":
            saw_cancelled = True
            # Once cancelled and not escalated yet, test can finish early
            break

    client.loop_stop()
    client.disconnect()

    print("[TEST] Results:")
    print(f"  saw_cancelled={saw_cancelled}")
    print(f"  escalated={escalated}")

    if saw_cancelled and not escalated:
        print("[TEST] PASS: Alert was cancelled and no escalation occurred")
        return 0
    else:
        print("[TEST] FAIL: Unexpected outcome")
        return 2


if __name__ == '__main__':
    code = run_test()
    sys.exit(code)
