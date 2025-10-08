# Raspberry Pi setup — Sentinel Edge

This file documents the system packages, Python packages and extra commands used when developing and testing the services on a Raspberry Pi (camera, voice, dispatcher). Follow these steps after cloning the repository.

Requirements
- Raspberry Pi OS (Bullseye or newer), Python 3.8+
- Git

1) System packages

Run as root or prefix with `sudo`:

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip build-essential git \
  libatlas-base-dev libportaudio2 portaudio19-dev libasound2-dev ffmpeg \
  libjpeg-dev libv4l-dev unzip
```

Notes:
- `libportaudio2` / `portaudio19-dev` are required for `sounddevice`.
- If `opencv-python` wheel fails on your Pi, install the OS package `python3-opencv` instead.

2) Create and activate virtualenv

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
```

3) Install Python requirements

The repository contains a `requirements.txt` for core dependencies. Install it, then install optional heavy packages used during local testing:

```bash
pip install -r requirements.txt
# extras commonly used during development/testing
pip install opencv-python vosk sounddevice mediapipe
```

If `opencv-python` fails, use the OS package instead:

```bash
sudo apt install -y python3-opencv
```

4) Vosk ASR model (required for offline voice)

Download and extract the model into the voice_control `models` folder:

```bash
mkdir -p hardware/raspberry-pi/edge-ai/voice_control/models
cd hardware/raspberry-pi/edge-ai/voice_control/models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -O vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
cd -
```

5) Make helper scripts runnable and prepare logs

```bash
chmod +x scripts/run_local_stack.sh
mkdir -p logs
```

6) Running the services

- Run all three services in background (convenience script):

```bash
./scripts/run_local_stack.sh
```

- Run individual services during development:

Dispatcher
```bash
source venv/bin/activate
python hardware/raspberry-pi/dispatcher/main.py
```

Gesture publisher (camera)
```bash
export GESTURE_CAMERA_INDEX=0    # or 1 if you use a different camera index
python hardware/raspberry-pi/edge-ai/gesture_control/gesture_publisher.py
```

Voice publisher
```bash
source venv/bin/activate
python hardware/raspberry-pi/edge-ai/voice_control/voice_publisher.py --verbose
```

7) Audio & camera permissions

- If you have audio permission issues, install dev packages and add your user to the `audio` group:

```bash
sudo apt install -y libasound2-dev
sudo usermod -aG audio $USER
```

- For camera support on Raspberry Pi OS, enable camera interface in `raspi-config` or use `libcamera` depending on your Pi OS version.

8) Hardware notes (servo)

- The SG90 servo used by the MCU requires a stable 5V supply. Power the servo from an external 5V regulator and share ground with the NodeMCU.
- Typical wiring: servo VCC -> external 5V, GND -> common GND, signal -> D5 (GPIO14) as configured in `hardware/mcu/nodemcu-amica-modular/config.h`.

9) Troubleshooting

- If `sounddevice` cannot open the audio device, run `arecord -l` and confirm the device exists.
- If `opencv` import fails, prefer the OS package (`python3-opencv`).
- If the Vosk model is large for your SD card, download a smaller model or expand storage.

10) Quick checklist after clone

```bash
# 1. Update OS & install system deps
sudo apt update && sudo apt install -y python3-venv python3-pip build-essential libasound2-dev portaudio19-dev libportaudio2 ffmpeg libjpeg-dev libv4l-dev unzip

# 2. Create venv and install Python deps
python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install opencv-python vosk sounddevice mediapipe || true

# 3. Get model
mkdir -p hardware/raspberry-pi/edge-ai/voice_control/models && cd hardware/raspberry-pi/edge-ai/voice_control/models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip -O model.zip && unzip model.zip && rm model.zip
cd -

# 4. Make run script executable and start
chmod +x scripts/run_local_stack.sh && mkdir -p logs && ./scripts/run_local_stack.sh
```

If you want, I can also add a small `requirements-raspi.txt` with the extra packages pinned for Raspberry Pi APs. Want that created?
