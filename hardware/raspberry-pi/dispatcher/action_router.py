import logging
import os
import threading
import time
from enum import Enum, auto
from dataclasses import dataclass, field

from shared.mqtt_topics import TOPICS


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [ROUTER] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


class Mode(Enum):
    HOME = auto()
    AWAY = auto()
    SLEEP = auto()
    GUEST = auto()
    ALERT = auto()
    EMERGENCY = auto()


@dataclass
class VirtualState:
    fan: str = "off"
    lights: str = "off"
    door: str = "locked"
    mode: str = "home"
    gas_valve: str = "open"
    water_valve: str = "open"
    windows: dict[str, str] = field(default_factory=lambda: {"1": "closed", "2": "closed"})
    gas_alert: str = "CLEAR"
    flood_alert: str = "CLEAR"


class ActionRouter:
    """
    Receives canonical tokens from voice/gesture publishers and sensor alarms,
    translates them into MQTT actuator commands, and manages alert escalation.
    """

    def __init__(self, mqtt):
        self.mqtt = mqtt
        self._mode = Mode.HOME
        self._virtual_state = VirtualState()
        # Alert escalation config
        self._alert_escalation_seconds = int(os.getenv("ALERT_ESCALATION_SECONDS", "30"))
        self._alert_thread: threading.Thread | None = None
        self._alert_lock = threading.Lock()
        log.info("ActionRouter ready. Initial mode: HOME")

    def on_voice_command(self, token: str) -> None:
        log.info(f"VOICE token='{token}'")
        self._dispatch(token, source="voice")

    def on_gesture_command(self, token: str) -> None:
        log.info(f"GESTURE token='{token}'")
        self._dispatch(token, source="gesture")

    def on_sensor_alarm(self, alarm_type: str, payload: str) -> None:
        normalized = payload.strip().upper()
        is_alert = normalized in {"DETECTED", "ALERT", "1", "TRUE", "ON", "DANGER"}
        if not is_alert:
            return
        log.warning(f"SENSOR ALARM type='{alarm_type}' payload='{payload}'")
        if alarm_type == "gas":
            self._set_mode_alert(reason="gas")
        elif alarm_type == "flood":
            self._set_mode_alert(reason="flood")

    def _dispatch(self, token: str, source: str) -> None:
        if not token.startswith("_"):
            self._publish_command(token)

        if token.startswith("window_"):
            self._update_window_state(token)

        # DOOR
        if token == "door_open":
            self._virtual_state.door = "open"

        elif token == "door_close":
            self._virtual_state.door = "locked"

        # WINDOWS
        elif token == "windows_open_all":
            self._virtual_state.windows["1"] = "open"
            self._virtual_state.windows["2"] = "open"

        elif token == "windows_close_all":
            self._virtual_state.windows["1"] = "closed"
            self._virtual_state.windows["2"] = "closed"

        elif token == "window_open_1":
            self._virtual_state.windows["1"] = "open"

        elif token == "window_close_1":
            self._virtual_state.windows["1"] = "closed"

        elif token == "window_open_2":
            self._virtual_state.windows["2"] = "open"

        elif token == "window_close_2":
            self._virtual_state.windows["2"] = "closed"

        # FAN
        elif token == "fan_on":
            self._virtual_state.fan = "on"

        elif token == "fan_off":
            self._virtual_state.fan = "off"

        # LIGHTS
        elif token == "lights_on":
            self._virtual_state.lights = "bright"

        elif token == "lights_off":
            self._virtual_state.lights = "off"

        elif token == "lights_dim":
            self._virtual_state.lights = "dim"

        elif token == "lights_bright":
            self._virtual_state.lights = "bright"

        # SYSTEM MODES
        elif token == "mode_home":
            self._set_mode_home()

        elif token == "mode_away":
            self._set_mode_away()

        elif token == "mode_sleep":
            self._set_mode_sleep()

        elif token == "mode_guest":
            self._set_mode_guest()

        # EMERGENCY / SAFETY
        elif token == "emergency_activate":
            self._set_mode_emergency()

        elif token == "emergency_cancel":
            if self._mode == Mode.EMERGENCY:
                log.info("Emergency cancelled by user.")
                self._set_mode_home()
            else:
                log.info("emergency_cancel ignored — not in EMERGENCY mode")

        elif token == "alert_cancel":
            if self._mode in (Mode.ALERT, Mode.EMERGENCY):
                log.info("Alert cancelled by user.")
                self._virtual_state.gas_valve = "open"
                self._virtual_state.water_valve = "open"
                self._virtual_state.gas_alert = "CLEAR"
                self._virtual_state.flood_alert = "CLEAR"
                with self._alert_lock:
                    if self._alert_thread and self._alert_thread.is_alive():
                        log.info("Notifying alert countdown to abort")
                        self._alert_thread = None
                self._publish_full_state()
            else:
                log.info("alert_cancel ignored — not in ALERT/EMERGENCY mode")

        # SENSOR-TRIGGERED
        # STATUS
        elif token == "status_query":
            log.info(f"Status query — current mode: {self._mode.name}")
            self._publish_full_state()

        else:
            log.warning(f"Unknown token '{token}' from {source} — ignored")

    def _publish_command(self, token: str) -> None:
        self._pub(TOPICS.COMMANDS, token)

    def _update_window_state(self, token: str) -> None:
        if token == "window_open_1":
            self._virtual_state.windows["1"] = "open"
        elif token == "window_close_1":
            self._virtual_state.windows["1"] = "closed"
        elif token == "window_open_2":
            self._virtual_state.windows["2"] = "open"
        elif token == "window_close_2":
            self._virtual_state.windows["2"] = "closed"

    def _publish_full_state(self) -> None:
        self._pub(TOPICS.FAN_STATE_TOPIC, self._virtual_state.fan)
        self._pub(TOPICS.LIGHTS_STATE_TOPIC, self._virtual_state.lights)
        self._pub(TOPICS.WINDOWS_STATE_TOPIC, self._format_window_state())
        self._pub(TOPICS.DOOR_STATE_TOPIC, self._virtual_state.door)
        self._pub(TOPICS.MODE_STATE_TOPIC, self._virtual_state.mode)
        self._pub(TOPICS.device_status("dispatcher"), self._virtual_state.mode.upper())
        self._pub(TOPICS.GAS_VALVE_STATE_TOPIC, self._virtual_state.gas_valve)
        self._pub(TOPICS.WATER_VALVE_STATE_TOPIC, self._virtual_state.water_valve)
        self._pub(TOPICS.ALERT_GAS_TOPIC, self._virtual_state.gas_alert)
        self._pub(TOPICS.ALERT_FLOOD_TOPIC, self._virtual_state.flood_alert)

    def _format_window_state(self) -> str:
        return f"1:{self._virtual_state.windows['1']},2:{self._virtual_state.windows['2']}"

    # mode transitions
    def _set_mode_home(self) -> None:
        self._mode = Mode.HOME
        self._virtual_state.mode = "home"
        log.info("→ Mode: HOME")
        self._virtual_state.door = "locked"
        self._virtual_state.fan = "off"
        self._virtual_state.windows["1"] = "closed"
        self._virtual_state.windows["2"] = "closed"
        self._virtual_state.lights = "bright"
        self._virtual_state.gas_valve = "open"
        self._virtual_state.water_valve = "open"
        self._virtual_state.gas_alert = "CLEAR"
        self._virtual_state.flood_alert = "CLEAR"
        self._pub(TOPICS.device_status("dispatcher"), "HOME")
        self._publish_full_state()

    def _set_mode_away(self) -> None:
        self._mode = Mode.AWAY
        self._virtual_state.mode = "away"
        log.info("→ Mode: AWAY")
        self._virtual_state.door = "locked"
        self._virtual_state.fan = "off"
        self._virtual_state.windows["1"] = "closed"
        self._virtual_state.windows["2"] = "closed"
        self._virtual_state.lights = "off"
        self._virtual_state.gas_alert = "CLEAR"
        self._virtual_state.flood_alert = "CLEAR"
        self._pub(TOPICS.device_status("dispatcher"), "AWAY")
        self._publish_full_state()

    def _set_mode_sleep(self) -> None:
        self._mode = Mode.SLEEP
        self._virtual_state.mode = "sleep"
        log.info("→ Mode: SLEEP")
        self._virtual_state.door = "locked"
        self._virtual_state.fan = "off"
        self._virtual_state.windows["1"] = "closed"
        self._virtual_state.windows["2"] = "closed"
        self._virtual_state.lights = "off"
        self._virtual_state.gas_alert = "CLEAR"
        self._virtual_state.flood_alert = "CLEAR"
        self._pub(TOPICS.device_status("dispatcher"), "SLEEP")
        self._publish_full_state()

    def _set_mode_guest(self) -> None:
        self._mode = Mode.GUEST
        self._virtual_state.mode = "guest"
        log.info("→ Mode: GUEST")
        self._virtual_state.door = "open"
        self._virtual_state.lights = "bright"
        self._virtual_state.gas_alert = "CLEAR"
        self._virtual_state.flood_alert = "CLEAR"
        self._pub(TOPICS.device_status("dispatcher"), "GUEST")
        self._publish_full_state()

    def _set_mode_alert(self, reason: str = "unknown") -> None:
        self._mode = Mode.ALERT
        self._virtual_state.mode = "alert"
        log.warning(f"→ Mode: ALERT (reason={reason})")
        self._virtual_state.fan = "on"
        self._virtual_state.windows["1"] = "open"
        self._virtual_state.windows["2"] = "open"
        if reason == "gas":
            self._virtual_state.gas_valve = "closed"
            self._virtual_state.gas_alert = "ALERT"
        elif reason == "flood":
            self._virtual_state.water_valve = "closed"
            self._virtual_state.flood_alert = "ALERT"
        self._pub(TOPICS.device_status("dispatcher"), f"ALERT_{reason.upper()}")
        self._publish_full_state()
        # start escalation countdown
        self._start_alert_countdown(reason)

    def _set_mode_emergency(self) -> None:
        self._mode = Mode.EMERGENCY
        self._virtual_state.mode = "emergency"
        log.critical("→ Mode: EMERGENCY")
        self._virtual_state.door = "open"
        self._virtual_state.fan = "on"
        self._virtual_state.windows["1"] = "open"
        self._virtual_state.windows["2"] = "open"
        self._virtual_state.gas_valve = "closed"
        self._virtual_state.water_valve = "closed"
        self._pub(TOPICS.device_status("dispatcher"), "EMERGENCY")
        self._publish_full_state()

    def _pub(self, topic: str, payload: str) -> None:
        log.info(f"PUB {topic} -> {payload}")
        self.mqtt.publish(topic, payload)

    def _start_alert_countdown(self, reason: str) -> None:
        with self._alert_lock:
            if self._alert_thread and self._alert_thread.is_alive():
                log.info("Alert countdown already running")
                return

            def _countdown():
                log.info(f"Alert countdown started ({self._alert_escalation_seconds}s)")
                start = time.monotonic()
                while True:
                    time.sleep(1)
                    elapsed = time.monotonic() - start
                    if self._mode != Mode.ALERT:
                        log.info("Alert countdown aborted (mode changed)")
                        return
                    if elapsed >= self._alert_escalation_seconds:
                        log.warning("Alert countdown expired — escalating to EMERGENCY")
                        self._set_mode_emergency()
                        return

            t = threading.Thread(target=_countdown, daemon=True)
            self._alert_thread = t
            t.start()


def build_mqtt_callback(router: ActionRouter):
    def on_message(client, userdata, msg):
        del client, userdata
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="replace").strip()

        if topic == TOPICS.VOICE_CMD:
            router.on_voice_command(payload)
        elif topic == TOPICS.GESTURE_RAW:
            router.on_gesture_command(payload)
        elif topic in (TOPICS.ALARM_GAS, TOPICS.SENSOR_GAS):
            router.on_sensor_alarm("gas", payload)
        elif topic in (TOPICS.ALARM_FLOOD, TOPICS.SENSOR_WATER):
            router.on_sensor_alarm("flood", payload)
        else:
            log.debug(f"Unhandled topic '{topic}' payload='{payload}'")

    return on_message
