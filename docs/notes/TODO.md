# Sentinel Smart Home — Project TODO

## Dashboard & Frontend
- [ ] **Decide deployment target** (in-progress)
  - Options: Run on Raspi 4 (lightweight Flask + static React) vs. laptop (Next.js/React with SSR)
  - Decision pending for presentation setup
- [ ] **Choose frontend stack**
  - React SPA (Vite) recommended for best UX without overloading Pi
  - Next.js only if running on laptop/cloud
- [ ] **Prototype UI**
  - Real-time room visualization
  - Interactive controls (doors, lights, fans, windows, sensors)
  - Alert/alarm indicators
  - System status dashboard

## Backend & Integration
- [ ] **Plan backend changes**
  - Flask API for MQTT/REST bridge
  - Option to serve static React assets
- [ ] **Decide Node-RED/Blynk**
  - Node-RED: Recommended—excellent for MQTT flows, integrations, and dashboards
  - Blynk: Mobile app option if needed
- [ ] **Integrate Telegram bot for alerts/commands**
  - Real-time alerts (gas, flood, motion)
  - Command triggers (lock/unlock doors, turn lights, etc.)

## Voice & AI
- [ ] **Evaluate voice support**
  - Current: Vosk (English)
  - Goal: Arabic & Algerian Darija support
  - Test: Whisper vs. Vosk Arabic model for accuracy
  - Note: Darija may require custom fine-tuning or Whisper fallback

## Future Enhancements
- Face recognition (currently disabled)
- Gesture control improvements
- Additional language support
