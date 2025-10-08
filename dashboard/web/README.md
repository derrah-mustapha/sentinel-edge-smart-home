Sentinel Edge - Web Dashboard

Quick start (from repo root):

1. Create a virtualenv and install dependencies

```bash
python3 -m venv venv-dashboard
source venv-dashboard/bin/activate
pip install -r dashboard/web/requirements.txt
```

2. Run the dashboard (by default it connects to localhost MQTT broker)

```bash
export MQTT_BROKER=localhost
export MQTT_PORT=1883
python dashboard/web/server.py
```

Optional persistence settings:

```bash
# Default DB path: dashboard/web/dashboard_data.sqlite3
export DASHBOARD_DB_PATH=dashboard/web/dashboard_data.sqlite3
```

3. Open http://localhost:5000 in your browser.

Demo from school without port forwarding:

```bash
./scripts/run_dashboard_tunnel.sh
```

This starts the Flask dashboard locally and exposes it through a free Cloudflare Tunnel URL.
If `cloudflared` is not installed, install it first and rerun the script.

Features:
- Live MQTT message stream
- Real-time state snapshot from `home/state/*`, sensors, and alerts
- Manual command execution for all canonical tokens via `home/commands`
- Gesture/voice token simulation
- Raw MQTT publish and dynamic subscribe/unsubscribe
- SQLite persistence for MQTT logs, latest states, and audit trail
- Command history backed by `command_events` (`/api/commands`)

Suggested next features:
- Role-based access control
- Command-level authorization policy
- Device health cards and derived uptime metrics
- Advanced filtering for persisted logs/audit
