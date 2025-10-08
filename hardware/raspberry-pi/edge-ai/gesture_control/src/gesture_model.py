from typing import Optional

# Canonical gesture labels expected by dispatcher/action router.
SUPPORTED_GESTURES = {
    "OPEN_HAND",   # Open front door
    "FIST",        # Close front door
    "FAN_ON",      # Turn fan on
    "FAN_OFF",     # Turn fan off
}


def normalize_gesture_label(raw_label: str) -> Optional[str]:
    candidate = raw_label.strip().upper().replace(" ", "_")
    if candidate in SUPPORTED_GESTURES:
        return candidate
    return None


def detect_gesture(frame) -> str:
    """Return canonical gesture label or 'NONE'.

    This is a placeholder detector until the MediaPipe/classifier pipeline is wired.
    Keep return values constrained to SUPPORTED_GESTURES to avoid invalid MQTT actions.
    """
    del frame
    return "NONE"