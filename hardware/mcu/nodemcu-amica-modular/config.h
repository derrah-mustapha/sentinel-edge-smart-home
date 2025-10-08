#ifndef CONFIG_H
#define CONFIG_H

// ============================================================================
// Broker Profile Selection
// ============================================================================
// Set to 1 for LOCAL (your laptop/network broker)
// Set to 2 for CLOUD (HiveMQ or external broker with credentials)
#define BROKER_PROFILE 2

// ============================================================================
// WiFi Configuration (Required for both profiles)
// ============================================================================
#define WIFI_SSID "YOUR_WIFI_SSID"
#define WIFI_PASSWORD "YOUR_WIFI_PASSWORD"

// ============================================================================
// Profile 1: LOCAL BROKER (development on your laptop)
// ============================================================================
#if BROKER_PROFILE == 1
  #define MQTT_BROKER "10.54.92.8"
  #define MQTT_PORT 1883
  #define MQTT_CLIENT_ID "nodemcu-amica"
  #define MQTT_USERNAME ""          // Leave empty for anonymous
  #define MQTT_PASSWORD ""          // Leave empty for anonymous
  #define MQTT_USE_TLS false

// ============================================================================
// Profile 2: CLOUD BROKER (e.g., HiveMQ cloud with credentials)
// ============================================================================
#elif BROKER_PROFILE == 2
  #define MQTT_BROKER "YOUR_CLUSTER.s1.eu.hivemq.cloud"
  #define MQTT_PORT 8883
  #define MQTT_CLIENT_ID "nodemcu-amica-cloud"
  #define MQTT_USERNAME "YOUR_MQTT_USER"
  #define MQTT_PASSWORD "YOUR_MQTT_PASSWORD"
  #define MQTT_USE_TLS true

#else
  #error "Invalid BROKER_PROFILE. Set to 1 (LOCAL) or 2 (CLOUD)"
#endif

// ============================================================================
// MQTT Topic Subscriptions
// ============================================================================
#define TOPIC_COMMANDS "home/commands"

#define TOPIC_SENSOR_GAS "home/sensors/gas"
#define TOPIC_SENSOR_WATER "home/sensors/water"
#define TOPIC_SENSOR_FLOOD "home/sensors/flood"

#define TOPIC_STATE_FAN "home/state/fan"
#define TOPIC_STATE_LIGHTS "home/state/lights"
#define TOPIC_STATE_DOOR "home/state/door"
#define TOPIC_STATE_MODE "home/state/mode"
#define TOPIC_STATE_GAS_VALVE "home/state/gas_valve"
#define TOPIC_STATE_WATER_VALVE "home/state/water_valve"

#define TOPIC_ALERT_GAS "home/alerts/gas"
#define TOPIC_ALERT_FLOOD "home/alerts/flood"

#define TOPIC_DOOR_FRONT_CMD "home/door/front/command"
#define TOPIC_DOOR_FRONT_STATE "home/door/front/state"
#define TOPIC_FAN_CMD "home/fan/command"
#define TOPIC_FAN_STATE "home/fan/state"

// Window control topics (future implementation)
#define TOPIC_WINDOW_CMD_PREFIX "home/window"
#define TOPIC_WINDOW_STATE_PREFIX "home/window"

// Light control topics (future implementation)
#define TOPIC_LIGHT_CMD_PREFIX "home/light"
#define TOPIC_LIGHT_STATE_PREFIX "home/light"

// Valve indicator topics (future implementation)
#define TOPIC_VALVE_GAS_IND "home/valve/gas/indicator"
#define TOPIC_VALVE_WATER_IND "home/valve/water/indicator"

// Alarm & sensor topics
#define TOPIC_ALARM_GAS "home/alarm/gas"
#define TOPIC_ALARM_FLOOD "home/alarm/flood"

// ============================================================================
// Timing Configuration
// ============================================================================
#define WIFI_RETRY_DELAY_MS 500
#define MQTT_RETRY_DELAY_MS 2000
#define LOOP_HEARTBEAT_MS 10000

// ============================================================================
// GPIO Pin Mapping (for future GPIO control)
// ============================================================================
// Requested NodeMCU pin map
#define PIN_GAS_SENSOR D4          // Digital input: HIGH = gas detected
#define PIN_WATER_SENSOR A0        // Analog input: >300 = flood detected

// Door servo
#define PIN_DOOR_SERVO D5         // GPIO14

// SG90 servo door positions
// Adjust these if the servo travel does not match your linkage.
#define DOOR_SERVO_CLOSED_ANGLE 0
#define DOOR_SERVO_OPEN_ANGLE 90

// Fan relay
#define PIN_FAN_RELAY D0          // Fan state output

// Lights PWM output
#define PIN_LIGHTS_OUTPUT D1      // Room lights state output

// Water and gas valve outputs
#define PIN_WATER_VALVE_OUTPUT D2
#define PIN_GAS_VALVE_OUTPUT D6

// Door and mode indicators
#define PIN_DOOR_INDICATOR D7
#define PIN_MODE_INDICATOR D8

// Keep the relay logic active-high for the fan relay board.
#define RELAY_ACTIVE_LOW false

// Sensor thresholds and update intervals
#define WATER_FLOOD_THRESHOLD 300
#define SENSOR_POLL_INTERVAL_MS 2000
#define MODE_BLINK_SLOW_MS 1000
#define MODE_BLINK_FAST_MS 200
#define MODE_GUEST_PULSE_MS 120
#define EMERGENCY_FLASH_MS 80

// Legacy status LED pins from the old prototype are intentionally not used in
// the current hardware map. The new firmware drives D2/D6/D7/D8 for valves,
// door indicator, and mode indicator instead.

#endif
