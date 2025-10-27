# Original delivery roadmap (kept for reference)

Written during the project; several items were completed later, so see the main README for the current status.

### Phase 1: Voice AI + Gesture Recognition

- [ ] Build production voice command listener (offline, low-latency on Raspberry Pi).
- [ ] Define and lock gesture vocabulary (gesture-to-intent contract).
- [ ] Implement gesture classifier pipeline and MQTT publisher.
- [ ] Unify command normalization so voice and gesture emit the same intent set.
- [ ] Add confidence threshold + unknown-command handling.

### Phase 2: Sensors + Guardian FSM

- [ ] Add PIR motion sensor module and MQTT events.
- [ ] Add temperature sensor module (DHT11/22) and MQTT telemetry.
- [ ] Implement Guardian FSM modes:
	- [ ] HOME
	- [ ] AWAY
	- [ ] NIGHT
	- [ ] ALARM
- [ ] Connect sensor events to FSM transitions and actuator policies.
- [ ] Add watchdog/error-safe fallback behavior.

### Phase 3: End-to-End Verification

- [ ] Create full-loop test flow:
	- [ ] Voice -> dispatcher -> MCU -> actuator action -> state feedback
	- [ ] Gesture -> dispatcher -> MCU -> actuator action -> state feedback
- [ ] Add pass/fail script for MQTT topic-level verification.
- [ ] Add regression checks for command routing and alarm paths.

### Phase 4: Dashboard + Demo Preparation

- [ ] Build operator dashboard for live device states and alarms.
- [ ] Add Node-RED serial bridge for JSON event intake, automation rules, and demo dashboards.
- [ ] Add manual override controls for door/fan/alarm actions.
- [ ] Add timeline/log panel for command and event traceability.
- [ ] Prepare demo scenario scripts and final integration checklist.

## Immediate Sprint Start (Now)

This sprint begins with the first high-impact item:

- [ ] Replace manual voice input with offline speech recognition (Vosk) and publish normalized MQTT voice commands.


