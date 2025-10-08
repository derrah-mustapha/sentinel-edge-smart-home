Voice Publisher
===============

This module listens to a microphone, performs offline speech recognition with Vosk, normalizes recognized phrases to canonical tokens, and publishes tokens to the dispatcher topic `home/voice/command`.

Quick start
-----------

1. Download a Vosk model (recommended `vosk-model-small-en-us-0.15`) from https://alphacephei.com/vosk/models and unzip it into `hardware/raspberry-pi/edge-ai/voice_control/models/` or set `VOSK_MODEL_PATH`.
2. Activate the project venv and install requirements (already in `requirements.txt`).
3. Run:

```bash
python hardware/raspberry-pi/edge-ai/voice_control/voice_publisher.py --verbose
```

Configuration
-------------
- `VOSK_MODEL_PATH` — path to vosk model folder.
- `VOICE_SAMPLE_RATE` — microphone sample rate (default 16000).
- `VOICE_INPUT_DEVICE` — optional sounddevice device id or name.
- `VOICE_VERBOSE` — show transcripts and unmapped phrases.

Notes
-----
- The module maps many natural phrases into canonical tokens used by the `ActionRouter` (see project README). Keep new tokens consistent between voice and gesture modules.
