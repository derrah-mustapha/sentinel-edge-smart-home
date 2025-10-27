Project: Sentinel — Edge Smart Home
=================================

**Overview**
- **Purpose**: Lightweight, secure edge-first smart home platform combining MCU-controlled actuators/sensors, a Raspberry Pi edge node for local AI (gesture + voice), and a backend + dashboard for monitoring and management.
- **Primary components**: MCU devices (ESP/Nodemcu family), Raspberry Pi (dispatcher, edge AI publishers), MQTT broker (local or cloud), Backend API, Dashboard UI.

**Architecture Summary**
- **Edge-first design**: Intelligence and quick responses are handled locally on the Raspberry Pi and MCUs; the backend is used for logging, management, and user interfaces.
- **Communication layer**: MQTT is the central message bus connecting MCUs, the Pi, AI publishers, and the backend/dashboard.
- **Deployment model**: Modular services (MCU firmware, Pi processes, backend API, web dashboard) that can be run locally, on a Pi, or containerized with docker-compose.

**Why this architecture is good**
- **Low-latency**: Local processing of gestures/voice reduces round-trip delays for control actions.
- **Resilience**: Disconnected operation when cloud is unavailable—MCUs and Pi can operate autonomously via MQTT/local rules.
- **Scalability & modularity**: MQTT topics decouple producers/consumers; components can be added/removed without code changes.
- **Security posture**: Supports TLS MQTT connections (see environment config), authentication for broker access, and local-only sensitive processing for camera/voice.

Repository structure (tree)
- **Top level**
  - [backend/](backend/)
  - [communication/](communication/)
  - [dashboard/](dashboard/)
  - [docker/](docker/)
  - [hardware/](hardware/)
  - [raspberry-pi/](raspberry-pi/)
  - [shared/](shared/)
  - [scripts/](scripts/)
  - [tests/](tests/)

- **Selected important files**
  - [docker/docker-compose.yml](docker/docker-compose.yml)
  - [backend/api/routes.py](backend/api/routes.py)
  - [raspberry-pi/dispatcher/action_router.py](raspberry-pi/dispatcher/action_router.py)
  - [raspberry-pi/edge-ai/gesture_control/src/gesture_model.py](raspberry-pi/edge-ai/gesture_control/src/gesture_model.py)
  - [raspberry-pi/edge-ai/voice_control/models/vosk-model-small-en-us-0.15](raspberry-pi/edge-ai/voice_control/models/vosk-model-small-en-us-0.15)
  - [hardware/mcu/nodemcu-amica-modular/src/actuators/Relay.h](hardware/mcu/nodemcu-amica-modular/src/actuators/Relay.h)
  - [hardware/mcu/nodemcu-amica-modular/src/mqtt/MqttHandlers.h](hardware/mcu/nodemcu-amica-modular/src/mqtt/MqttHandlers.h)
  - [.env.cloud](.env.cloud)

High-level component responsibilities
- **MCU (nodemcu-amica-modular)**: Runs the low-level actuator control (relays, servo, LEDs), subscribes to command topics, reports state on state topics, implements WiFi + MQTT reconnection and basic error handling.
- **Raspberry Pi (dispatcher & edge-AI)**: Hosts publishers for gesture and voice, runs action router / alarm handler for integrating sensor inputs, and forwards commands to MCUs or cloud. Runs lightweight ML inference where appropriate.
- **Backend API**: Aggregates events, persists logs, exposes REST endpoints used by the dashboard.
- **Dashboard**: Web UI for login, viewing system status and historical data, and sending manual commands.

MQTT communication and topics
- **Broker config**: Cloud or local broker with TLS supported. Example values are in [.env.cloud](.env.cloud).
- **Key environment variables**: MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_USE_TLS, MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID_PREFIX.
- **Topics (selected)**
  - **home/gesture/raw**: Raw gesture predictions published by the gesture publisher.
  - **home/voice/command**: Voice-derived commands published by the voice publisher.
  - **home/door/front/command** and **home/door/front/state**: Door actuator control and state feedback.
  - **home/light/** and **home/window/** prefixes: Generic command/state channels for lights and windows.
  - **home/sensor/gas**, **home/alarm/gas** etc.: Sensor telemetry and alarms.

Detailed topics and retained semantics
- The project centralizes topic names in `shared/mqtt_topics.py` and MCU `config.h`. Core topics (defaults):
  - `home/commands` — single ingress for manual/automated command tokens (string payloads or Node-RED JSON envelope).
  - `home/gesture/raw` — gesture tokens (e.g., `fan_on`, `door_open`) published by the gesture publisher.
  - `home/voice/command` — canonical tokens emitted by voice ASR mapping.
  - `home/door/front/command`, `home/door/front/state` — per-door command/state channel.
  - `home/fan/command`, `home/fan/state` — fan control & state.
  - `home/light/<zone>/command`, `home/light/<zone>/state` — zone-specific light control (virtual/topic prefix).
  - `home/window/<id>/command`, `home/window/<id>/state` — window control (virtual-only in firmware).
  - `home/state/*` — snapshot state topics used by MCU for states (fan, lights, door, mode, valves).
  - `home/sensors/gas`, `home/sensors/water`, `home/sensors/flood` — sensor telemetry.
  - `home/alerts/gas`, `home/alerts/flood` — alert topics triggered on threshold crossing.
  - `home/valve/*/indicator` — valve indicator topics (gas/water).

- Retain rules (observed in code): sensor telemetry (`publishTelemetry`) is published with `retain=false` so updates are transient; state snapshot topics are published with `retain=true` by default so consumers can get current state on connect.

Command tokens and mappings
- The MCU firmware accepts plain token strings on `home/commands` (or device-specific command topics). Key accepted tokens (from `SystemState::handleCommand`):
  - Fan: `fan_on`, `fan_off`
  - Lights: `lights_on`, `lights_off`, `lights_dim`, `lights_bright`
  - Door: `door_open`, `door_close`
  - Modes: `mode_home`, `mode_away`, `mode_sleep`, `mode_guest`
  - Alerts/emergency: `alert_cancel`, `emergency_activate`, `emergency_cancel`
  - Status: `status_query`
  - Window virtual commands: `windows_open_all`, `windows_close_all`, `window_open_1`, `window_close_1`, `window_open_2`, `window_close_2`

- Gesture tokens map directly to these tokens — the gesture publisher emits the same canonical tokens (see `hardware/raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py`). Example mappings:
  - thumbs up → `fan_on`
  - pinch → `fan_off`
  - middle finger → `lights_on`
  - ring finger → `lights_off`
  - pinky → `lights_dim`
  - index+middle → `lights_bright`
  - rock sign / thumb+index close → `door_open`
  - index finger → `alert_cancel`
  - fist → `mode_away`
  - all fingers → `mode_home`
  - two-fist close (two-hand) → `emergency_activate`

- Voice publishes canonical tokens (or the Node-RED JSON envelope) to `home/voice/command` which are routed by the Pi `ActionRouter` to the `home/commands` topic or device topics as needed.

Message formats
- Two common message styles exist across the system:
  1. Plain token string payloads on a command topic, e.g. publish `fan_on` to `home/commands`.
  2. Structured Node-RED / serial JSON envelope (docs/NODE_RED_INTEGRATION.md) used by integrations and some dashboards:

```json
{"v":1,"type":"command","source":"dashboard","device":"fan","topic":"home/commands","value":"fan_off","status":"REQUESTED","ts":1716700000456}
```

MCU wiring and pin mapping (nodemcu-amica-modular)
- Pin/functional map is in `hardware/mcu/nodemcu-amica-modular/config.h`. Key mappings (NodeMCU Dn names):
  - `PIN_GAS_SENSOR = D4` (digital input, HIGH = gas detected)
  - `PIN_WATER_SENSOR = A0` (analog, flood threshold defined in config)
  - `PIN_DOOR_SERVO = D5` (servo output for door lock)
  - `PIN_FAN_RELAY = D0` (fan relay control)
  - `PIN_LIGHTS_OUTPUT = D1` (PWM lights output)
  - `PIN_WATER_VALVE_OUTPUT = D2`
  - `PIN_GAS_VALVE_OUTPUT = D6`
  - `PIN_DOOR_INDICATOR = D7` (status LED)
  - `PIN_MODE_INDICATOR = D8` (mode LED)

- LED wiring notes:
  - LEDs are driven active-high in firmware (`digitalWrite(HIGH)` -> LED on). Connect the LED anode (through a suitable resistor, e.g., 220Ω) to the NodeMCU pin and cathode to GND. If using 5V indicator LEDs or an external LED board, use a transistor or MOSFET driver.
  - On relay modules, VCC should match module spec (often 5V) and IN pin connects to the NodeMCU control pin; ensure common GND.
  - Servo `PIN_DOOR_SERVO` expects a 5V-powered SG90 with common ground; supply servo from a stable 5V source and avoid drawing servo current from the NodeMCU 3.3V regulator.

MCU loop, state machine and timings
- Main MCU loop pattern (see `ARCHITECTURE.md` and `SystemState`):
  - Non-blocking periodic polling: sensors polled every `SENSOR_POLL_INTERVAL_MS` (default 2000 ms).
  - Heartbeat loop interval `LOOP_HEARTBEAT_MS` (default 10000 ms) for status messages.
  - WiFi/MQTT reconnect delays: `WIFI_RETRY_DELAY_MS` (500 ms), `MQTT_RETRY_DELAY_MS` (2000 ms).
  - SystemState acts as central orchestrator: sensor updates → condition checks → actuator commands → MQTT state publishes.

Error handling and fail-safes (MCU)
- **Connectivity**: Reconnect loops with backoff; report connection status via system topics.
- **Watchdog-style recovery**: Firmware recommends a watchdog or reboot on repeated connection failures.
- **Safe defaults**: On critical errors or emergency commands, the system forces safe states (valves closed, lights on for visibility, door open for exit, etc.).

Where the code maps to these behaviors
- Topic definitions: `shared/mqtt_topics.py` and MCU `config.h`.
- Command token handling: `hardware/mcu/nodemcu-amica-modular/src/logic/SystemState.h` (`handleCommand`).
- Gesture → token generation: `hardware/raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py`.
- Node-RED/serial envelope examples: `docs/NODE_RED_INTEGRATION.md`.


AI models and inference
- **Gesture control**
  - **Where**: Raspberry Pi edge-ai gesture publisher (raspberry-pi/edge-ai/gesture_control).
  - **What**: A lightweight gesture model used for recognition; inference executed locally to produce classification/confidence values (thresholds controlled by GESTURE_CONFIDENCE_THRESHOLD in environment config).
  - **Output**: When gesture confidence exceeds threshold, gesture events are published to home/gesture/raw or higher-level command topics after optional post-processing.

- **Voice control**
  - **Where**: raspberry-pi/edge-ai/voice_control.
  - **Model**: Vosk small English model included under models/vosk-model-small-en-us-0.15 — local ASR for offline voice-to-text.
  - **Output**: Recognized commands are mapped to internal actions and published to home/voice/command.

- **Face recognition**
  - **Where**: backend models/services/face_recognition.py and Raspberry Pi camera integration.
  - **Role**: Access control or logging; configuration toggles whether face recognition is enabled.

Dispatcher, routing, and decision flow
- **Action Router**: The Pi's dispatcher action_router.py receives processed inputs (gesture, voice, sensor alarms) and applies rules/state machine logic to produce actuator commands.
- **Stateful decisions**: The router maintains local state (e.g., door closed/open, alarm armed/disarmed) to avoid unsafe repeated actions and to implement hysteresis and debounce for sensors.
- **Failover behavior**: If backend is unreachable, the Pi continues to process local AI events and uses MQTT to command devices.

MCU firmware notes (C/C++ for ESP)
- **Structure**: Modular headers for actuators, sensors, MQTT handlers, and system state. See hardware/mcu/nodemcu-amica-modular/src.
- **Main loop responsibilities**
  - **WiFi & MQTT connection management**: Connect on boot, reattempt on disconnect with backoff, and report status on system topics.
  - **MQTT subscriptions**: Subscribe to command topics for controlled actuators.
  - **Actuator update loop**: Poll for incoming commands, apply to actuators (relays/servo/LED), and publish new state.
  - **Sensor sampling**: Periodically sample sensors (gas, water) and publish telemetry or trigger alarms when thresholds are crossed.
  - **Auto-triggers & state machine**: Implement simple finite-state machines for e.g., door automation (open, closed, moving), fan control, or alarm conditions; transitions are event-driven.
- **Error handling**
  - **Connectivity**: Exponential backoff reconnects for WiFi and MQTT; optional local retry counters and watchdog resets on repeated failures.
  - **Actuator faults**: If actuator operation fails, publish an error indicator on a state topic and optionally retry with limits.
  - **Safe defaults**: On critical failures, MCUs can revert actuators to safe states (e.g., close valve) and report the condition.

Raspberry Pi code notes (Python)
- **Dispatcher/service layout**: The Pi contains dispatcher, action_router, alarm_handler, and edge-AI publishers under raspberry-pi/dispatcher and raspberry-pi/edge-ai.
- **Concurrency**: Publishers and subscribers are typically run as separate processes or threads; MQTT callbacks enqueue messages to the router.
- **Error handling & robustness**
  - **MQTT client**: Uses automatic reconnect logic; ensures QoS for critical messages where required.
  - **AI process isolation**: Gesture and voice publishers run independently so an inference crash doesn't bring down routing.
  - **Logging & monitoring**: Backend ingestion endpoints and local logs capture events for debugging.

Best practices used in the project
- **Separation of concerns**: Clear split between device firmware, edge processing, and backend/dashboard.
- **Decoupling via MQTT**: Publishers and consumers communicate through topics rather than direct RPC calls.
- **Config via environment**: .env files centralize deployment configuration for easy switching between cloud/local brokers and toggling features.
- **Local-first intelligence**: Real-time actions happen at the edge to reduce latency and improve privacy.
- **Idempotent commands & state reporting**: Devices publish state after actions so callers can reconcile and avoid race conditions.
- **Modular firmware design**: MCU code splits actuators, sensors, and mqtt handlers to ease testing and extension.

How to set up quickly (summary)
- **Prepare Python environment**: Create virtualenv and install backend/dashboard requirements from requirements.txt files.
- **MQTT broker**: For cloud use set .env.cloud values; for local testing use the included mosquitto config under communication/broker-config.
- **Run backend**: Start backend API (see backend README or routes.py) and ensure DB (dashboard/web/dashboard_data.sqlite3) is in place.
- **Run dashboard**: Start the dashboard server under dashboard/web/server.py for local UI.
- **Start Raspberry Pi services**: On Pi, run gesture publisher, voice publisher, and dispatcher scripts in raspberry-pi/edge-ai and raspberry-pi/dispatcher.
- **Flash MCUs**: Build and flash firmware from hardware/mcu/nodemcu-amica-modular with appropriate WiFi and MQTT credentials.

Quick commands (examples)
- Create Python venv and install:

  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt

- Run dashboard server (example):

  python3 dashboard/web/server.py

- Start local Mosquitto (example script available):

  bash scripts/manage_mqtt_broker.sh start

Notes, caveats, and next steps
- **Model tuning**: Gesture confidence threshold is controlled by GESTURE_CONFIDENCE_THRESHOLD; tune per environment.
- **Security**: Rotate MQTT credentials, enforce TLS, and minimize camera model access rights for privacy.
- **Testing**: Add integration tests for MQTT flows and CI checks for backend endpoints.
- **Observability**: Consider adding metrics (Prometheus) and structured logs for production deployments.

Where to look in the code (entry points)
- For routing and decision logic: [raspberry-pi/dispatcher/action_router.py](raspberry-pi/dispatcher/action_router.py)
- For gesture publisher: raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py and gesture_model.py
- For voice publisher: raspberry-pi/edge-ai/voice_control/voice_publisher.py and models/vosk-model-small-en-us-0.15
- For MCU handlers: hardware/mcu/nodemcu-amica-modular/src/mqtt/MqttHandlers.h and actuators/*
- For backend API: [backend/api/routes.py](backend/api/routes.py)

Presentation / jury questions and good answers
- **What type of architecture is this?**
  - It is an edge-first, event-driven, MQTT-based distributed architecture. The Pi and MCU make local decisions; MQTT decouples all actors; the dashboard/backend observe and manage, but do not block real-time control.

- **Why is it a strong architecture for a smart home?**
  - Fast reactions at the edge, lower bandwidth usage, better privacy, and easier failure isolation. If the cloud or UI fails, the house can still react to sensors and local commands.

- **What are the main use cases?**
  - Gesture control for fan, lights, and door actions; voice control for natural commands; automatic safety responses for gas/flood events; state monitoring and manual overrides via dashboard.

- **How do MCU and Raspberry Pi communicate?**
  - Through MQTT topics. The Pi publishes canonical tokens to `home/commands` or direct topics, and the MCU subscribes to command topics, applies actions, then republishes state on `home/state/*` or device state topics.

- **What happens in the MCU main loop?**
  - The main sketch (`nodemcu-amica-modular.ino`) keeps WiFi alive, reconnects MQTT, calls `mqttClient.loop()`, and then calls `sysState.update(mqttClient)`. That update function is where sensor polling, actuator updates, state publishing, and automatic safety transitions happen.

- **Which functions should you know in the MCU code?**
  - `setup()` initializes serial, WiFi, TLS if enabled, MQTT, and the system state.
  - `loop()` maintains WiFi/MQTT and runs the control cycle.
  - `ensureWifi()` reconnects WiFi with retry logging.
  - `ensureMqtt()` reconnects the broker, subscribes to `home/commands`, and publishes a state snapshot.
  - `handleMqttCommand()` receives command payloads and forwards them to `SystemState::handleCommand()`.
  - `SystemState::begin()` configures pins, servo, and safe defaults.
  - `SystemState::update()` polls sensors and publishes telemetry/state.
  - `SystemState::handleCommand()` maps command strings to actions.
  - `pollSensors()` triggers gas/flood safety behavior and publishes alerts.

- **What are the important state machine concepts in the MCU?**
  - The MCU keeps a `Mode` state with `HOME`, `AWAY`, `SLEEP`, `GUEST`, `ALERT`, and `EMERGENCY`. This is the core intelligence layer. Sensor events and commands transition between states, and the current mode controls outputs like lights, door, valves, and indicators.

- **How do the LEDs and indicators work?**
  - `PIN_DOOR_INDICATOR` and `PIN_MODE_INDICATOR` are driven as output LEDs. The mode LED is not just on/off: it uses timing-based patterns to show different states. `HOME` is steady on, `AWAY` and `SLEEP` blink at different speeds, `GUEST` uses a pulse pattern, and `ALERT/EMERGENCY` stay fully on.

- **How are `millis()` and timing used?**
  - Timing is non-blocking for regular behavior. `millis()` powers sensor polling intervals, mode blink patterns, retry delays, and the heartbeat log. This avoids freezing the MCU with long blocking waits during normal operation.

- **How do you explain the `millis()` style to the jury?**
  - It is a standard embedded pattern for cooperative multitasking. Instead of sleeping or blocking, the firmware checks elapsed time and only acts when the interval is reached. That keeps WiFi, MQTT, sensors, and outputs responsive.

- **What happens on gas or flood detection?**
  - The MCU reads sensors in `pollSensors()`. If gas is detected, it closes the gas valve, sets mode to `ALERT`, publishes `home/alerts/gas`, and updates `home/state/mode` and `home/state/gas_valve`. Flood detection does the same for the water valve and flood alert. If the alert clears, the alert topic is reset.

- **What is the emergency behavior?**
  - `emergency_activate` flashes outputs, turns fan and lights on, opens the door, closes both valves, and sets mode to `EMERGENCY`. `emergency_cancel` restores the default home state. This is a strong safety-answer for juries because it shows explicit fail-safe design.

- **How does the Raspberry Pi dispatcher work?**
  - `hardware/raspberry-pi/dispatcher/main.py` creates a publisher and subscriber MQTT client, instantiates `ActionRouter`, and subscribes to gesture, voice, and sensor topics. `ActionRouter` maps canonical tokens into state changes and publishes the matching command/state topics.

- **What is special about `ActionRouter`?**
  - It is the policy layer. It keeps a virtual state of fan, lights, door, mode, valves, and windows. It also implements alert escalation: if gas/flood stays active for too long, it escalates from `ALERT` to `EMERGENCY` automatically.

- **Why is the dispatcher useful if the MCU already exists?**
  - Because it adds higher-level intelligence, combines multiple inputs, and normalizes behavior. The MCU does the physical control; the dispatcher handles orchestration, automation, and cross-device rules.

- **What do the gesture and voice modules do?**
  - The gesture module classifies hand poses into control tokens like `fan_on`, `door_open`, or `mode_sleep`. The voice module converts speech into canonical command tokens. Both publish to MQTT, so the rest of the system stays independent from the AI implementation.

- **What are the AI models used?**
  - Gesture recognition is local vision-based hand classification with MediaPipe landmarks and rule-based gesture mapping. Voice recognition uses the bundled Vosk small English model for offline speech-to-text. Face recognition is available as an optional feature, disabled by default in the cloud config.

- **What should you say if asked about robustness?**
  - The design handles WiFi and MQTT reconnects, separates publishers from the dispatcher, uses retained state topics, and keeps safety behaviors local to the MCU. That means a failure in one layer does not collapse the entire house automation flow.

- **What is the strongest technical point of the project?**
  - The project combines edge AI, embedded control, MQTT decoupling, and a clear state machine. That gives it low latency, modularity, safety, and a presentation-friendly architecture that is easy to explain and defend.

Python functions and architectural approach
- **MQTT abstraction layer**: `backend/services/mqtt_client.py` wraps Paho MQTT in a small reusable client. The important methods are:
  - `MQTTClient.__init__()` sets the client ID, applies username/password, and enables TLS when required.
  - `connect()` opens the broker connection and optionally starts the background network loop.
  - `publish()` sends a payload and waits until the broker confirms the publish, which is useful for commands that must not be dropped silently.
  - `subscribe()` registers the callback and subscribes to a topic.
  - `loop_forever()` is used by long-lived subscribers like the dispatcher.

- **Gesture module functions**: `hardware/raspberry-pi/edge-ai/gesture_control/src/gesture_publisher.py`
  - `_tip_above_mcp()`, `_finger_states()`, `_thumb_extended()`, `_thumb_index_close()`, `_pinch_active()`, `_pinky_extended()`, `_palm_up()`, `_palm_down()` are small geometry helpers built on MediaPipe landmarks.
  - `classify_gesture()` turns a single hand into canonical tokens such as `fan_on`, `lights_bright`, `door_open`, `mode_home`, `mode_away`, `mode_guest`, `alert_cancel`, and `fan_off`.
  - `classify_two_hand_gesture()` handles compound gestures like `emergency_activate`, `mode_sleep`, `windows_close_all`, and `door_close`.
  - `GesturePublisher.update()` is the anti-noise layer: it requires the same token to hold for several frames before publishing, and it enforces a cooldown so the same gesture does not spam commands.
  - `run()` ties everything together: camera capture, MediaPipe inference, token classification, preview display, and MQTT publishing.

- **Voice module functions**: `hardware/raspberry-pi/edge-ai/voice_control/src/voice_publisher.py`
  - `NORMALIZED_COMMANDS` is the command dictionary that maps natural language phrases to canonical tokens.
  - `_best_fuzzy_match()` gives a fallback when speech recognition is close but not exact.
  - `normalize_command()` is the command parser; it cleans the transcript, tries exact matching, tries article removal, tries a singular/plural heuristic, then falls back to fuzzy matching.
  - `_audio_callback()` is the real-time microphone callback that pushes raw PCM bytes into a queue.
  - `parse_args()` controls runtime configuration such as Vosk model path, sample rate, input device, and verbose logging.
  - `run()` loads the Vosk model, starts the microphone stream, runs recognition, normalizes transcripts, and publishes tokens over MQTT.

- **Dispatcher functions**: `hardware/raspberry-pi/dispatcher/action_router.py`
  - `ActionRouter.__init__()` defines the routing policy, initial mode, virtual device state, and alert escalation timeout.
  - `on_voice_command()`, `on_gesture_command()`, and `on_sensor_alarm()` are the input adapters.
  - `_dispatch()` is the main policy engine that maps a token to fan/lights/door/window/mode/safety actions.
  - `_publish_command()` forwards canonical tokens into the shared command topic.
  - `_publish_full_state()` republishes the virtual system snapshot so dashboards and other services always know the current state.
  - `_set_mode_home()`, `_set_mode_away()`, `_set_mode_sleep()`, `_set_mode_guest()`, `_set_mode_alert()`, and `_set_mode_emergency()` implement the high-level state machine.
  - `_start_alert_countdown()` adds delayed escalation from `ALERT` to `EMERGENCY` if the hazard persists.
  - `build_mqtt_callback()` binds MQTT topics to the router so voice, gesture, gas, and flood topics each reach the correct handler.

- **Python architectural style**
  - The Python side is layered and event-driven: AI publishers produce tokens, the dispatcher converts tokens into policy decisions, and MQTT acts as the decoupled transport.
  - It is also intentionally modular: each process can be run independently, which helps debugging, deployment, and demonstrations.
  - The code favors small pure helpers for normalization/classification and larger orchestration functions for routing and state control.

MCU architecture and approach
- **Layered firmware design**: the MCU uses a modular C++ structure with a boot sketch, a `SystemState` orchestrator, and dedicated headers for MQTT, sensors, actuators, and configuration.
- **Central state object**: `SystemState` stores mode, actuator states, alerts, sensor readings, and connection flags. This makes the firmware easy to reason about because all important behavior flows through one object.
- **Finite-state machine**: `Mode` drives behavior across `HOME`, `AWAY`, `SLEEP`, `GUEST`, `ALERT`, and `EMERGENCY`.
- **Non-blocking control**: normal operation is timed with `millis()` checks instead of long blocking delays. That keeps the device responsive to WiFi, MQTT, sensors, and commands.
- **Event-driven reactions**: commands and sensor changes trigger transitions, state publishes, and actuator updates.
- **Safe-by-default design**: if gas or flood is detected, the corresponding valve is closed, alert topics are published, and the mode shifts to `ALERT`.
- **Presentation-friendly status outputs**: LEDs and servo positions are used as visible state indicators, which makes debugging and demonstrations easier.

MCU functions worth mentioning in a defense
- `setup()` bootstraps serial logging, WiFi event hooks, the system state, TLS configuration, MQTT server settings, and the command callback.
- `loop()` continuously keeps WiFi and MQTT alive, processes MQTT traffic, calls `sysState.update(mqttClient)`, and emits a heartbeat.
- `ensureWifi()` retries WiFi connection and updates connection state.
- `ensureMqtt()` reconnects to the broker, subscribes to `home/commands`, and publishes a fresh state snapshot after reconnect.
- `handleMqttCommand()` receives command payloads and forwards them into `SystemState::handleCommand()`.
- `SystemState::begin()` configures the pins, servo, safe defaults, and initial mode.
- `SystemState::update()` handles periodic polling and state synchronization.
- `SystemState::handleCommand()` maps incoming tokens to real actions.
- `pollSensors()` is the automatic safety layer for gas and flood detection.

Final words
- This single-file summary is designed to be converted into slides or a PDF. If you want, I can: (1) generate a formatted README with embedded diagrams, (2) produce a slide deck skeleton, or (3) run quick repository scans to extract exact function/class references to enrich this doc.
