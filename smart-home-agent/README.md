# 🏠 Smart Home Agent

A production-ready **Node.js + TypeScript** Telegram bot that controls smart home devices (fan, window, light) over **MQTT**, monitors sensor data, and sends alerts — all from your Telegram chat.

---

## 🚀 Quick Start

### 1. Clone / Navigate to the project

```bash
cd smart-home-agent
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `AUTHORIZED_CHAT_ID` | Your Telegram chat ID (only this ID can send commands) |
| `MQTT_URL` | MQTT broker URL, e.g. `mqtt://localhost:1883` |
| `MQTT_USERNAME` | *(optional)* MQTT broker username |
| `MQTT_PASSWORD` | *(optional)* MQTT broker password |

> **Tip:** To find your chat ID, send a message to [@userinfobot](https://t.me/userinfobot) on Telegram.

### 4. Run in development mode

```bash
npm run dev
```

### 5. Build & run for production

```bash
npm run build
npm start
```

---

## 📁 Project Structure

```
src/
├── app.ts                  # Entry point
├── config/
│   └── env.ts              # Environment variable validation
├── types/
│   └── mqtt.ts             # TypeScript interfaces for MQTT payloads
├── state/
│   └── deviceState.ts      # In-memory device state store
├── mqtt/
│   └── client.ts           # MQTT connection, subscriptions & publishing
├── alerts/
│   └── alertHandler.ts     # Routes incoming MQTT messages to state/alerts
├── commands/
│   ├── fan.ts              # Fan MQTT publish helpers
│   ├── window.ts           # Window MQTT publish helpers
│   └── light.ts            # Light MQTT publish helpers
└── bot/
    └── telegram.ts         # SmartHomeBot class — all command handlers
```

---

## 🤖 Telegram Commands

| Command | Action | MQTT Topic | Payload |
|---|---|---|---|
| `/start` | Welcome message + command list | — | — |
| `/status` | Show all device states | — | — |
| `/fan_on` | Turn fan on | `home/fan/set` | `{"command":"on"}` |
| `/fan_off` | Turn fan off | `home/fan/set` | `{"command":"off"}` |
| `/open_window` | Open window | `home/window/set` | `{"command":"open"}` |
| `/close_window` | Close window | `home/window/set` | `{"command":"close"}` |
| `/light_on` | Turn light on | `home/light/set` | `{"command":"on"}` |
| `/light_off` | Turn light off | `home/light/set` | `{"command":"off"}` |

---

## 📡 MQTT Topics

### Subscriptions (inbound)

| Topic | Description |
|---|---|
| `home/status/fan` | `{"status": "on"\|"off"}` |
| `home/status/window` | `{"status": "open"\|"closed"}` |
| `home/status/light` | `{"status": "on"\|"off"}` |
| `home/status/temperature` | `{"value": 28}` |
| `home/status/humidity` | `{"value": 65}` |
| `home/alerts/temperature` | `{"value": 45}` → sends Telegram alert |
| `home/alerts/humidity` | `{"value": 90}` → sends Telegram alert |

### Publications (outbound)

| Topic | Payload |
|---|---|
| `home/fan/set` | `{"command": "on"\|"off"}` |
| `home/window/set` | `{"command": "open"\|"close"}` |
| `home/light/set` | `{"command": "on"\|"off"}` |

---

## 🏗️ Architecture

```
Telegram User
     │  (commands)
     ▼
SmartHomeBot (telegram.ts)
     │  publishes
     ▼
MQTT Client (client.ts) ──► MQTT Broker ──► IoT Devices
     │  subscribes
     ▼
Alert Handler (alertHandler.ts)
     ├── updates ──► Device State (deviceState.ts)
     └── notifies ──► Telegram User
```

---

## 🔒 Security

- Only messages from `AUTHORIZED_CHAT_ID` are processed.
- All other users receive an "Unauthorized" response.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `mqtt` | MQTT client |
| `node-telegram-bot-api` | Telegram Bot API |
| `dotenv` | Environment variable loading |
| `ts-node-dev` | Dev server with hot-reload |
| `typescript` | TypeScript compiler |
