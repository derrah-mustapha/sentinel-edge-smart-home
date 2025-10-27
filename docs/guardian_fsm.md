# Guardian FSM (Dispatcher)

This document explains the Guardian finite-state machine implemented in the dispatcher `ActionRouter`.

## Modes

- `HOME` — Normal/default mode.
- `AWAY` — System is armed for absence.
- `SLEEP` — Night mode.
- `GUEST` — Guest access enabled.
- `ALERT` — Sensor reported a hazard (gas/flood). Auto-response active.
- `EMERGENCY` — Full escalation (evacuation/critical response).

## Alert behaviour

- When a sensor alarm is detected from the MCU publishes on `home/sensors/gas` or `home/sensors/flood`, the router enters `ALERT` mode and updates its virtual state.
- The router republishes the token to `home/commands` for the MCU, while also keeping its in-memory snapshot aligned for dashboards.
- Window tokens remain virtual-only and do not move hardware.

Immediate dispatcher state on alert:

- `mode = alert`
- `fan = on`
- `gas_valve = closed` for gas alerts
- `water_valve = closed` for flood alerts
- `gas_alert = ALERT` or `flood_alert = ALERT`
- `home/state/*` topics are republished when `status_query` is requested or when the dispatcher updates its snapshot.

- A background countdown starts when entering `ALERT` (configurable by `ALERT_ESCALATION_SECONDS`, default `30`).
  - If the mode remains `ALERT` when the timer expires, the router escalates to `EMERGENCY` and issues evacuation actions.
  - If a user sends `alert_cancel` (token published to `home/voice/command` or `home/gesture/raw`), the router republishes the token on `home/commands`, clears the virtual alert snapshot, and the countdown aborts.

## Emergency behaviour

- On escalation to `EMERGENCY`, the router sets its virtual state to open/critical and republishes `emergency_activate` to `home/commands`.
- The MCU then performs the hardware-side response: flash outputs, close both valves, turn the fan on, open the door, and publish the resulting state topics.
- The exact flash timing is hardware-sensitive and should be bench-checked after flashing.

## Environment variables / tuning

- `ALERT_ESCALATION_SECONDS` — seconds to wait in `ALERT` before auto-escalating to `EMERGENCY` (default `30`).
- `GESTURE_HOLD_FRAMES`, `GESTURE_COOLDOWN_S` — tune gesture sensitivity in the gesture publisher.

## Testing

- A simple E2E test has been added: `tests/e2e_alert_cancel.py`.
  - It publishes an alert to `home/sensors/gas`, waits, sends `alert_cancel`, and asserts the dispatcher clears the alert state without escalating to `EMERGENCY`.

## Notes

- The router currently uses a simple thread-based countdown; for high-reliability deployments consider using a persistent scheduler or external watchdog that survives process restarts.
- The remaining runtime risk on the MCU is the exact mode-indicator timing and the emergency flash routine.
