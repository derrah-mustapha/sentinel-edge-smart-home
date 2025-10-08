# Node-RED Workflows

This folder contains the importable Node-RED flow export for Sentinel Edge Smart Home.

## What the flows do

- Normalize voice and gesture inputs into the canonical `home/commands` token stream.
- Mirror retained state topics into a single live snapshot for dashboards and logs.
- Provide manual inject shortcuts for the common system commands.

## Files

- [sentinel-edge-smart-home-flows.json](sentinel-edge-smart-home-flows.json) - importable Node-RED flow export.

## Import Steps

1. Open Node-RED.
2. Import the flow JSON from this folder.
3. Edit the MQTT broker config node if your broker is not `localhost:1883`.
4. Deploy the flows.

## Recommended Dashboard Hooks

If you install a dashboard package, wire widgets to the state snapshot output from the `state snapshot` function node.

For manual control, keep every button publishing one of the repo's existing command tokens to `home/commands`.

## Notes

- The flows intentionally avoid inventing new topics.
- The same token vocabulary should be used by voice, gesture, Node-RED, and any future web UI.