import os
import sys
import time
from pathlib import Path

import cv2
import mediapipe as mp

# Allow running this file directly from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.mqtt_client import MQTTClient
from shared.mqtt_topics import TOPICS


CAMERA_INDEX = int(os.getenv("GESTURE_CAMERA_INDEX", "0"))
FRAME_WIDTH = int(os.getenv("GESTURE_FRAME_WIDTH", "640"))
FRAME_HEIGHT = int(os.getenv("GESTURE_FRAME_HEIGHT", "480"))
HOLD_FRAMES = int(os.getenv("GESTURE_HOLD_FRAMES", "8"))
COOLDOWN_SECONDS = float(os.getenv("GESTURE_COOLDOWN_S", "2.0"))
SHOW_PREVIEW = os.getenv("GESTURE_SHOW_PREVIEW", "1") not in ("0", "false", "False")
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.6

# Gesture path emits the 16 active control tokens only; doc-only extras
# such as the window/status/emergency-cancel variants are intentionally left out.

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
INDEX_MCP = 5
MIDDLE_TIP = 12
MIDDLE_MCP = 9
RING_TIP = 16
RING_MCP = 13
PINKY_TIP = 20
PINKY_MCP = 17


def _tip_above_mcp(lm, tip: int, mcp: int) -> bool:
    return lm[tip].y < lm[mcp].y


def _finger_states(lm) -> list[bool]:
    return [
        _tip_above_mcp(lm, INDEX_TIP, INDEX_MCP),
        _tip_above_mcp(lm, MIDDLE_TIP, MIDDLE_MCP),
        _tip_above_mcp(lm, RING_TIP, RING_MCP),
        _tip_above_mcp(lm, PINKY_TIP, PINKY_MCP),
    ]


def _thumb_extended(lm) -> bool:
    return abs(lm[THUMB_TIP].x - lm[WRIST].x) > 0.15


def _thumb_index_close(lm) -> bool:
    """Check if thumb and index finger are close (rock/horns gesture)"""
    dx = lm[THUMB_TIP].x - lm[INDEX_TIP].x
    dy = lm[THUMB_TIP].y - lm[INDEX_TIP].y
    return (dx**2 + dy**2) ** 0.5 < 0.1


def _pinch_active(lm) -> bool:
    """Pinch: thumb + index very close (< 0.07)"""
    dx = lm[THUMB_TIP].x - lm[INDEX_TIP].x
    dy = lm[THUMB_TIP].y - lm[INDEX_TIP].y
    return (dx**2 + dy**2) ** 0.5 < 0.07


def _pinky_extended(lm) -> bool:
    """Pinky isolated: only pinky up, all others down"""
    index_up, middle_up, ring_up, pinky_up = _finger_states(lm)
    return pinky_up and not index_up and not middle_up and not ring_up


def _palm_up(lm) -> bool:
    """Check if palm is facing up (approximately): middle_tip.y < wrist.y"""
    return lm[MIDDLE_TIP].y < lm[WRIST].y


def _palm_down(lm) -> bool:
    """Check if palm is facing down: middle_tip.y > wrist.y"""
    return lm[MIDDLE_TIP].y > lm[WRIST].y


def classify_gesture(hand_landmarks) -> str | None:
    """
    Single-hand gesture classification.
    Maps hand shapes to control commands (21 possible commands total).
    """
    lm = hand_landmarks.landmark
    index_up, middle_up, ring_up, pinky_up = _finger_states(lm)
    any_finger_up = any([index_up, middle_up, ring_up, pinky_up])
    all_fingers_up = index_up and middle_up and ring_up and pinky_up

    # ╔════════════════════════════════════════════════════════════════╗
    # ║  SINGLE FINGER CONTROLS                                        ║
    # ╚════════════════════════════════════════════════════════════════╝

    # Point (index only): alert CANCEL
    if index_up and not any([middle_up, ring_up, pinky_up, _thumb_extended(lm)]):
        return "alert_cancel"

    # Middle only: lights ON
    if middle_up and not any([index_up, ring_up, pinky_up, _thumb_extended(lm)]):
        return "lights_on"

    # Ring only: lights OFF
    if ring_up and not any([index_up, middle_up, pinky_up, _thumb_extended(lm)]):
        return "lights_off"

    # Pinky only: lights DIM
    if _pinky_extended(lm):
        return "lights_dim"

    # ╔════════════════════════════════════════════════════════════════╗
    # ║  TWO FINGER CONTROLS                                           ║
    # ╚════════════════════════════════════════════════════════════════╝

    # Victory/Peace (index+middle): lights BRIGHT
    if index_up and middle_up and not ring_up and not pinky_up and not _thumb_extended(lm):
        return "lights_bright"

    # Rock sign (index+pinky): open door
    if _thumb_index_close(lm) or (index_up and pinky_up and not middle_up and not ring_up):
        return "door_open"

    # ╔════════════════════════════════════════════════════════════════╗
    # ║  THREE & FOUR FINGER CONTROLS                                  ║
    # ╚════════════════════════════════════════════════════════════════╝

    # All 4 fingers up (no thumb): HOME mode
    if all_fingers_up and not _thumb_extended(lm):
        return "mode_home"

    # Index + Middle + Ring (ring shows but not pinky): windows OPEN all
    if index_up and middle_up and ring_up and not pinky_up and not _thumb_extended(lm):
        return "windows_open_all"

    # ╔════════════════════════════════════════════════════════════════╗
    # ║  FIST & MODIFIER CONTROLS                                      ║
    # ╚════════════════════════════════════════════════════════════════╝

    # Fist (no fingers, no thumb): AWAY mode
    if not any_finger_up and not _thumb_extended(lm):
        return "mode_away"

    # Thumbs up: turn fan ON
    if _thumb_extended(lm) and not any_finger_up:
        return "fan_on"

    # Index + Middle (index+middle visible): GUEST mode
    if index_up and middle_up and not ring_up and not pinky_up:
        return "mode_guest"

    # Pinch (thumb+index very close): fan OFF
    if _pinch_active(lm):
        return "fan_off"

    return None


def classify_two_hand_gesture(results) -> str | None:
    """
    Two-hand gesture classification.
    More complex gestures requiring both hands.
    """
    if len(results.multi_hand_landmarks) < 2:
        return None

    lm0 = results.multi_hand_landmarks[0].landmark
    lm1 = results.multi_hand_landmarks[1].landmark

    # Both fists (all closed)
    both_fists = (
        not any(_finger_states(lm0))
        and not _thumb_extended(lm0)
        and not any(_finger_states(lm1))
        and not _thumb_extended(lm1)
    )
    
    wrists_close = abs(lm0[WRIST].x - lm1[WRIST].x) < 0.25

    # ╔════════════════════════════════════════════════════════════════╗
    # ║  TWO-HAND GESTURES                                             ║
    # ╚════════════════════════════════════════════════════════════════╝

    # Both fists crossed or very close: EMERGENCY activate
    if both_fists and wrists_close:
        return "emergency_activate"

    # Both hands open (all fingers up) and palms facing each other: SLEEP mode
    hand0_open = all(_finger_states(lm0)) and not _thumb_extended(lm0)
    hand1_open = all(_finger_states(lm1)) and not _thumb_extended(lm1)
    if hand0_open and hand1_open and wrists_close:
        return "mode_sleep"

    # Hands in "stop" position (palms facing forward): WINDOWS CLOSE all
    # This is a more complex geometric check; approximate with palm orientation
    if wrists_close and _palm_down(lm0) and _palm_down(lm1):
        return "windows_close_all"

    # Hands rotated/wrists crossed: DOOR CLOSE
    hands_crossed = abs(lm0[WRIST].x - lm1[WRIST].x) < 0.15
    if hands_crossed and both_fists:
        return "door_close"

    return None


class GesturePublisher:
    def __init__(self, mqtt: MQTTClient):
        self.mqtt = mqtt
        self._hold_counts: dict[str, int] = {}
        self._last_fired_at: dict[str, float] = {}

    def update(self, token: str | None) -> None:
        if token is None:
            self._hold_counts.clear()
            return

        count = self._hold_counts.get(token, 0) + 1
        self._hold_counts = {token: count}

        now = time.monotonic()
        last = self._last_fired_at.get(token, 0.0)
        if count >= HOLD_FRAMES and (now - last) >= COOLDOWN_SECONDS:
            self._last_fired_at[token] = now
            self._hold_counts.clear()
            print(f"[GESTURE] Fired token: {token}")
            self.mqtt.publish(TOPICS.GESTURE_RAW, token)


def run() -> None:
    print("[GESTURE] Connecting MQTT")
    mqtt = MQTTClient("gesture-pub")
    mqtt.connect(start_loop=True)
    publisher = GesturePublisher(mqtt)

    print(f"[GESTURE] Opening camera index={CAMERA_INDEX}")
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

    if not cap.isOpened():
        print("[GESTURE] ERROR: camera unavailable")
        raise SystemExit(1)

    with mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
    ) as hands:
        while True:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.1)
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)
            rgb.flags.writeable = True

            token: str | None = None
            if results.multi_hand_landmarks:
                token = classify_two_hand_gesture(results)
                if token is None:
                    token = classify_gesture(results.multi_hand_landmarks[0])
                if SHOW_PREVIEW:
                    for hand_lm in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(frame, hand_lm, mp_hands.HAND_CONNECTIONS)

            publisher.update(token)

            if SHOW_PREVIEW:
                shown = token or "none"
                cv2.putText(
                    frame,
                    f"Gesture: {shown}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("Gesture Control", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    cap.release()
    if SHOW_PREVIEW:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n[GESTURE] Exit requested")
