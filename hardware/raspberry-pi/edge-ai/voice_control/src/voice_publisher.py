import argparse
import json
import os
import queue
import sys
import re
from difflib import SequenceMatcher
from pathlib import Path

import sounddevice as sd
from vosk import KaldiRecognizer, Model

# Allow running this file directly from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[5]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.mqtt_client import MQTTClient
from shared.mqtt_topics import TOPICS


DEFAULT_MODEL_PATH = str(
    PROJECT_ROOT
    / "hardware"
    / "raspberry-pi"
    / "edge-ai"
    / "voice_control"
    / "models"
    / "vosk-model-small-en-us-0.15"
)

NORMALIZED_COMMANDS: dict[str, str] = {
    "open front door": "door_open",
    "open door": "door_open",
    "unlock front door": "door_open",
    "unlock door": "door_open",
    "close front door": "door_close",
    "close door": "door_close",
    "lock front door": "door_close",
    "lock door": "door_close",
    "open all windows": "windows_open_all",
    "open windows": "windows_open_all",
    "close all windows": "windows_close_all",
    "close windows": "windows_close_all",
    "open window one": "window_open_1",
    "open window 1": "window_open_1",
    "close window one": "window_close_1",
    "close window 1": "window_close_1",
    "open window two": "window_open_2",
    "open window 2": "window_open_2",
    "close window two": "window_close_2",
    "close window 2": "window_close_2",
    "turn fan on": "fan_on",
    "fan on": "fan_on",
    "start fan": "fan_on",
    "turn fan off": "fan_off",
    "fan off": "fan_off",
    "stop fan": "fan_off",
    "lights on": "lights_on",
    "turn lights on": "lights_on",
    "turn on lights": "lights_on",
    "lights off": "lights_off",
    "turn lights off": "lights_off",
    "turn off lights": "lights_off",
    "dim lights": "lights_dim",
    "lights dim": "lights_dim",
    "bright lights": "lights_bright",
    "lights bright": "lights_bright",
    "home mode": "mode_home",
    "i am home": "mode_home",
    "i'm home": "mode_home",
    "activate home mode": "mode_home",
    "away mode": "mode_away",
    "i am leaving": "mode_away",
    "i'm leaving": "mode_away",
    "leaving home": "mode_away",
    "activate away mode": "mode_away",
    "goodbye": "mode_away",
    "sleep mode": "mode_sleep",
    "good night": "mode_sleep",
    "goodnight": "mode_sleep",
    "activate sleep mode": "mode_sleep",
    "going to sleep": "mode_sleep",
    "guest mode": "mode_guest",
    "activate guest mode": "mode_guest",
    "let my guest in": "mode_guest",
    "enable guest mode": "mode_guest",
    "emergency": "emergency_activate",
    "activate emergency": "emergency_activate",
    "emergency mode": "emergency_activate",
    "evacuate": "emergency_activate",
    "cancel emergency": "emergency_cancel",
    "cancel alert": "alert_cancel",
    "all clear": "alert_cancel",
    "disable alarm": "alert_cancel",
    "false alarm": "alert_cancel",
    "system status": "status_query",
    "what is the mode": "status_query",
    "what mode": "status_query",
    "report status": "status_query",
}

AUDIO_QUEUE: queue.Queue[bytes] = queue.Queue()


def _best_fuzzy_match(cleaned: str) -> str | None:
    best = None
    best_score = 0.0
    for phrase, token in NORMALIZED_COMMANDS.items():
        score = SequenceMatcher(None, cleaned, phrase).ratio()
        if score > best_score:
            best_score = score
            best = token
    return best if best_score >= 0.65 else None


def normalize_command(text: str) -> str | None:
    cleaned = " ".join(text.lower().strip().split())
    # exact match
    if cleaned in NORMALIZED_COMMANDS:
        return NORMALIZED_COMMANDS[cleaned]

    # remove articles and retry
    cleaned_no_articles = re.sub(r"\b(the|a|an)\b", "", cleaned).strip()
    cleaned_no_articles = " ".join(cleaned_no_articles.split())
    if cleaned_no_articles in NORMALIZED_COMMANDS:
        return NORMALIZED_COMMANDS[cleaned_no_articles]

    # simple singular->plural heuristic
    alt = cleaned.replace(" light", " lights")
    if alt in NORMALIZED_COMMANDS:
        return NORMALIZED_COMMANDS[alt]

    # fuzzy fallback
    fuzzy = _best_fuzzy_match(cleaned)
    if fuzzy:
        return fuzzy

    return None


def _audio_callback(indata, frames, time_info, status):
    del frames, time_info
    if status:
        print(f"[VOICE] Audio stream status: {status}")
    AUDIO_QUEUE.put(bytes(indata))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline Vosk voice command publisher for Sentinel Edge Smart Home"
    )
    parser.add_argument(
        "--model-path",
        default=os.getenv("VOSK_MODEL_PATH", DEFAULT_MODEL_PATH),
        help="Path to Vosk model directory",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=int(os.getenv("VOICE_SAMPLE_RATE", "16000")),
        help="Microphone sample rate (Hz)",
    )
    parser.add_argument(
        "--device",
        default=os.getenv("VOICE_INPUT_DEVICE"),
        help="Optional sounddevice input device name or index",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=os.getenv("VOICE_VERBOSE", "").lower() in ("1", "true"),
        help="Print all transcripts, including unrecognized ones",
    )
    return parser.parse_args()


def run() -> None:
    args = parse_args()
    model_path = Path(args.model_path)

    if not model_path.exists():
        print(f"[VOICE] Vosk model not found at: {model_path}")
        print("[VOICE] Download: https://alphacephei.com/vosk/models")
        print("[VOICE] Set --model-path or VOSK_MODEL_PATH after download")
        raise SystemExit(1)

    print(f"[VOICE] Loading Vosk model from: {model_path}")
    model = Model(str(model_path))
    recognizer = KaldiRecognizer(model, args.sample_rate)
    recognizer.SetWords(False)

    print(f"[VOICE] Connecting MQTT topic='{TOPICS.VOICE_CMD}'")
    mqtt = MQTTClient("voice-pub")
    mqtt.connect(start_loop=True)

    print("[VOICE] Listening... (Ctrl-C to stop)")
    try:
        with sd.RawInputStream(
            samplerate=args.sample_rate,
            blocksize=8000,
            device=args.device,
            dtype="int16",
            channels=1,
            callback=_audio_callback,
        ):
            while True:
                data = AUDIO_QUEUE.get()
                if not recognizer.AcceptWaveform(data):
                    continue

                result = json.loads(recognizer.Result())
                text = result.get("text", "").strip()
                if not text:
                    continue

                if args.verbose:
                    print(f"[VOICE] Transcript: '{text}'")

                token = normalize_command(text)
                if not token:
                    if args.verbose:
                        print(f"[VOICE] Unmapped phrase: '{text}'")
                    continue

                print(f"[VOICE] '{text}' -> {token}")
                mqtt.publish(TOPICS.VOICE_CMD, token)
    except KeyboardInterrupt:
        print("\n[VOICE] Exit requested")


if __name__ == "__main__":
    run()
