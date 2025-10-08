#ifndef MQTT_HANDLERS_H
#define MQTT_HANDLERS_H

#include <PubSubClient.h>
#include "../../config.h"
#include "../logic/SystemState.h"

// Forward declare the system state (will be set by main sketch)
extern SystemState sysState;
extern PubSubClient mqttClient;

// Publish sensor readings to MQTT
void publishSensorData(PubSubClient& mqttClient) {
  sysState.publishTelemetry(mqttClient);
}

// Handle incoming MQTT commands (dispatcher messages)
void handleMqttCommand(const char* topic, const byte* payload, unsigned int length) {
  String message;
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  message.trim();
  
  Serial.print("[MQTT RX] topic=");
  Serial.print(topic);
  Serial.print(" payload=");
  Serial.println(message);

  if (String(topic) == TOPIC_COMMANDS) {
    sysState.handleCommand(message, mqttClient);
    return;
  }

  Serial.print("[MQTT] ⚠️  Unknown/unhandled topic: ");
  Serial.println(topic);
}

#endif
