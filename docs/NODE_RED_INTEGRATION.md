# Node-RED Integration Plan

This repo already has the MQTT contract needed for automation. Node-RED should sit on top of that contract as a bridge, manual test console, and optional dashboard layer.

## Role Split

- Raspberry Pi edge services keep producing command tokens and sensor/state topics.
- Node-RED subscribes to those topics, normalizes inputs, and publishes only canonical tokens back to `home/commands`.
- Node-RED builds dashboards and notifications from retained MQTT state topics instead of inventing a second source of truth.
- Serial is optional and only needed if a future device cannot speak MQTT directly.

## Ready-to-Import Flow

An importable flow export is available at [communication/node-red/sentinel-edge-smart-home-flows.json](../communication/node-red/sentinel-edge-smart-home-flows.json).

It includes:

- a command bridge for voice, gesture, and manual test inputs;
- a retained-state monitor that merges the latest MQTT state into one snapshot;
- inject-based control shortcuts for the common canonical tokens already used by the repo.

## Topic Contract

The Node-RED flows are aligned with these existing topics:

- `home/commands` - single ingress for canonical control tokens.
- `home/voice/command` - voice command output.
- `home/gesture/raw` - gesture command output.
- `home/state/fan`, `home/state/lights`, `home/state/door`, `home/state/mode`.
- `home/state/windows`, `home/state/gas_valve`, `home/state/water_valve`.
- `home/sensors/gas`, `home/sensors/water`, `home/sensors/flood`.
- `home/alerts/gas`, `home/alerts/flood`.
- Legacy compatibility topics such as `home/fan/state`, `home/door/front/state`, and `home/alarm/*` can also be monitored if you still have older consumers.

## Workflow 1: Command Bridge

1. Receive a string token or a JSON envelope.
2. Extract the canonical token from `value`, `command`, `token`, `text`, or raw string payload.
3. Publish the normalized token to `home/commands`.
4. Keep the original topic in `msg.original_topic` for tracing and debugging.

This keeps Node-RED compatible with the repo's existing token vocabulary:

- `fan_on`, `fan_off`
- `lights_on`, `lights_off`, `lights_dim`, `lights_bright`
- `door_open`, `door_close`
- `windows_open_all`, `windows_close_all`, `window_open_1`, `window_close_1`, `window_open_2`, `window_close_2`
- `mode_home`, `mode_away`, `mode_sleep`, `mode_guest`
- `alert_cancel`, `emergency_activate`, `emergency_cancel`
- `status_query`

## Workflow 2: State Monitor

1. Subscribe to retained state and alarm topics.
2. Cache the latest values in flow context.
3. Emit a merged snapshot object whenever any monitored topic changes.
4. Feed that snapshot into dashboards, logs, or Telegram notifications.

This is the safest pattern for the system because it uses MQTT as the shared bus and avoids duplicate automation rules.

## Workflow 3: Manual Control Console

The included inject nodes are meant for fast demo and debugging work. They publish the same canonical commands used by voice and gesture input, so every path exercises the same router.

## Optional Serial Variant

If you later add a serial-only MCU or peripheral, use newline-delimited JSON with one object per line. Keep the structure flat and include a schema version and timestamp.

```json
{"v":1,"type":"sensor","source":"mcu","device":"gas_sensor","topic":"home/sensors/gas","value":312,"status":"OK","ts":1716700000000}
```

If the serial bridge is enabled, the same normalization rule still applies: turn the inbound object into a canonical token or a retained state update, then publish through the existing MQTT topics.

## Practical Notes

- If the broker is local, point the Node-RED MQTT broker config at `localhost:1883`.
- If you want a dashboard, install `node-red-dashboard` or FlowFuse Dashboard and connect widgets to the state snapshot output.
- Do not introduce a new command vocabulary in Node-RED unless you also add the same token to the dispatcher and edge publishers.
