#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <Servo.h>
#include "config.h"

#if MQTT_USE_TLS
#include <WiFiClientSecure.h>
#endif

// Include modular components
#include "src/logic/SystemState.h"
#include "src/mqtt/MqttHandlers.h"

// Global system state instance
SystemState sysState;

#if MQTT_USE_TLS
WiFiClientSecure wifiClient;
#else
WiFiClient wifiClient;
#endif
PubSubClient mqttClient(wifiClient);

unsigned long lastHeartbeatMs = 0;

void onWifiStationDisconnected(const WiFiEventStationModeDisconnected& event) {
  logLine(String("[WIFI] station disconnected reason=") + String(event.reason) +
          " ssid=" + String(event.ssid));
  sysState.setWifiConnected(false);
}

void onWifiStationGotIp(const WiFiEventStationModeGotIP& event) {
  logLine(String("[WIFI] got ip=") + event.ip.toString() +
          " gw=" + event.gw.toString() +
          " mask=" + event.mask.toString());
}

// ============================================================================
// Logging Helpers
// ============================================================================
void logPrefix() {
  Serial.print("[");
  Serial.print(millis());
  Serial.print(" ms] ");
}

void logLine(const String& message) {
  logPrefix();
  Serial.println(message);
}

const char* wifiStatusToText(wl_status_t status) {
  switch (status) {
    case WL_IDLE_STATUS: return "IDLE";
    case WL_NO_SSID_AVAIL: return "NO_SSID_AVAIL";
    case WL_SCAN_COMPLETED: return "SCAN_COMPLETED";
    case WL_CONNECTED: return "CONNECTED";
    case WL_CONNECT_FAILED: return "CONNECT_FAILED";
    case WL_CONNECTION_LOST: return "CONNECTION_LOST";
    case WL_DISCONNECTED: return "DISCONNECTED";
    default: return "UNKNOWN";
  }
}

const char* mqttStateToText(int8_t state) {
  switch (state) {
    case MQTT_CONNECTION_TIMEOUT: return "CONNECTION_TIMEOUT";
    case MQTT_CONNECTION_LOST: return "CONNECTION_LOST";
    case MQTT_CONNECT_FAILED: return "CONNECT_FAILED";
    case MQTT_DISCONNECTED: return "DISCONNECTED";
    case MQTT_CONNECTED: return "CONNECTED";
    case MQTT_CONNECT_BAD_PROTOCOL: return "BAD_PROTOCOL";
    case MQTT_CONNECT_BAD_CLIENT_ID: return "BAD_CLIENT_ID";
    case MQTT_CONNECT_UNAVAILABLE: return "SERVER_UNAVAILABLE";
    case MQTT_CONNECT_BAD_CREDENTIALS: return "BAD_CREDENTIALS";
    case MQTT_CONNECT_UNAUTHORIZED: return "UNAUTHORIZED";
    default: return "UNKNOWN";
  }
}

void subscribeTopic(const char* topic) {
  bool ok = mqttClient.subscribe(topic);
  if (ok) {
    logLine(String("[MQTT] subscribed -> ") + topic);
  } else {
    logLine(String("[MQTT] subscribe FAILED -> ") + topic);
  }
}

// ============================================================================
// WiFi Management
// ============================================================================
void ensureWifi() {
  bool connected = (WiFi.status() == WL_CONNECTED);
  sysState.setWifiConnected(connected);

  if (connected) {
    return;
  }

  logLine(String("[WIFI] starting connect to SSID=") + WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  unsigned int attempt = 0;
  while (WiFi.status() != WL_CONNECTED && attempt < 20) {
    delay(WIFI_RETRY_DELAY_MS);
    attempt++;
    wl_status_t currentStatus = WiFi.status();
    logLine(String("[WIFI] attempt #") + attempt + " status=" + wifiStatusToText(currentStatus));
  }

  if (WiFi.status() == WL_CONNECTED) {
    logLine(String("[WIFI] connected ip=") + WiFi.localIP().toString() + " rssi=" + String(WiFi.RSSI()) + " dBm");
    sysState.setWifiConnected(true);
  } else {
    wl_status_t finalStatus = WiFi.status();
    logLine(String("[WIFI] connect failed final status=") + wifiStatusToText(finalStatus));
    sysState.setWifiConnected(false);
  }
}

// ============================================================================
// MQTT Management
// ============================================================================
void ensureMqtt() {
  if (WiFi.status() != WL_CONNECTED) {
    if (mqttClient.connected()) {
      logLine("[MQTT] wifi lost, disconnecting client");
      mqttClient.disconnect();
    }
    sysState.setMqttConnected(false);
    return;
  }

  if (mqttClient.connected()) {
    sysState.setMqttConnected(true);
    return;
  }

  unsigned int attempt = 0;
  while (!mqttClient.connected()) {
    attempt++;
    logLine(String("[MQTT] connect attempt #") + attempt + " broker=" + MQTT_BROKER + ":" + String(MQTT_PORT));

    bool connected = false;
    if (strlen(MQTT_USERNAME) > 0 && strlen(MQTT_PASSWORD) > 0) {
      connected = mqttClient.connect(MQTT_CLIENT_ID, MQTT_USERNAME, MQTT_PASSWORD);
    } else {
      connected = mqttClient.connect(MQTT_CLIENT_ID);
    }

    if (connected) {
      logLine("[MQTT] connected successfully");
      
      // Single command channel from the dispatcher
      subscribeTopic(TOPIC_COMMANDS);
      
      logLine("[MQTT] ready to receive commands");
      sysState.setMqttConnected(true);
      sysState.publishAllStates(mqttClient);
      return;
    }

    int8_t state = mqttClient.state();
    logLine(String("[MQTT] connect failed state=") + mqttStateToText(state) + " retrying...");
    delay(MQTT_RETRY_DELAY_MS);
    
    if (attempt >= 5) {
      logLine("[MQTT] giving up after 5 attempts");
      sysState.setMqttConnected(false);
      return;
    }
  }
}

// ============================================================================
// Setup
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println();
  Serial.println("=====================================================");
  Serial.println("[BOOT] NodeMCU Amica - Sentinel Edge Smart Home");
  Serial.println("     Modular Architecture");
  Serial.println("=====================================================");
  logLine(String("[BOOT] firmware build date=") + __DATE__ + " " + __TIME__);
  logLine(String("[BOOT] chipId=") + String(ESP.getChipId(), HEX));
  logLine(String("[BOOT] cpuFreqMHz=") + ESP.getCpuFreqMHz());
  logLine(String("[BOOT] freeHeapBytes=") + ESP.getFreeHeap());
  logLine(String("[BOOT] wifi SSID=") + WIFI_SSID);
  logLine(String("[BOOT] mqtt broker=") + MQTT_BROKER + ":" + String(MQTT_PORT));
  logLine(String("[BOOT] mqtt profile=") + (BROKER_PROFILE == 1 ? "LOCAL" : BROKER_PROFILE == 2 ? "CLOUD" : "UNKNOWN"));

  WiFi.persistent(false);
  WiFi.setAutoReconnect(true);
  WiFi.onStationModeDisconnected(onWifiStationDisconnected);
  WiFi.onStationModeGotIP(onWifiStationGotIp);

  // Initialize all system sensors and actuators
  logLine("[BOOT] Initializing system state and peripherals...");
  sysState.begin();

  // Connect to WiFi
  ensureWifi();

  // Configure TLS only when the cloud profile is selected
#if MQTT_USE_TLS
  logLine("[BOOT] Setting up TLS for MQTT...");
  wifiClient.setInsecure();
#endif

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(handleMqttCommand);
  logLine("[BOOT] MQTT client configured");
  logLine("[BOOT] System ready");
}

// ============================================================================
// Main Loop
// ============================================================================
void loop() {
  // Maintain WiFi connection
  ensureWifi();

  // Maintain MQTT connection
  ensureMqtt();
  
  if (mqttClient.connected()) {
    mqttClient.loop();
  }

  // Update system logic (sensors, actuators, business logic)
  sysState.update(mqttClient);

  unsigned long now = millis();

  // Heartbeat status report
  if (now - lastHeartbeatMs >= LOOP_HEARTBEAT_MS) {
    lastHeartbeatMs = now;
    logLine(
      String("[HEARTBEAT] wifi=") + wifiStatusToText(WiFi.status()) +
      " mqtt=" + (mqttClient.connected() ? "CONNECTED" : "DISCONNECTED") +
      " gas=" + sysState.getGasStatus() +
      " gasValue=" + String(sysState.getGasReading())
    );
  }

  // Small delay to prevent watchdog reset
  delay(10);
}
