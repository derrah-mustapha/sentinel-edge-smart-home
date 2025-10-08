import mqtt, { MqttClient, IClientOptions } from 'mqtt';
import { config } from '../config/env';
import { handleAlertMessage } from '../alerts/alertHandler';

const SUBSCRIBED_TOPICS = ['home/alerts/#', 'home/status/#'];

let client: MqttClient | null = null;

export function getMqttClient(): MqttClient {
    if (!client) {
        throw new Error('MQTT client has not been initialized yet.');
    }
    return client;
}

export function connectMqtt(): Promise<MqttClient> {
    return new Promise((resolve, reject) => {
        const options: IClientOptions = {
            clientId: `smart-home-agent-${Math.random().toString(16).slice(2, 8)}`,
            clean: true,
            reconnectPeriod: 5000,
        };

        if (config.mqtt.username) options.username = config.mqtt.username;
        if (config.mqtt.password) options.password = config.mqtt.password;

        console.log(`[MQTT] Connecting to ${config.mqtt.url} ...`);
        client = mqtt.connect(config.mqtt.url, options);

        client.once('connect', () => {
            console.log('[MQTT] Connected successfully.');

            SUBSCRIBED_TOPICS.forEach((topic) => {
                client!.subscribe(topic, (err) => {
                    if (err) {
                        console.error(`[MQTT] Failed to subscribe to "${topic}":`, err);
                    } else {
                        console.log(`[MQTT] Subscribed to "${topic}"`);
                    }
                });
            });

            resolve(client!);
        });

        client.on('error', (err) => {
            console.error('[MQTT] Connection error:', err);
            reject(err);
        });

        client.on('reconnect', () => {
            console.log('[MQTT] Reconnecting...');
        });

        client.on('offline', () => {
            console.warn('[MQTT] Client went offline.');
        });

        client.on('message', (topic: string, payload: Buffer) => {
            const raw = payload.toString();
            console.log(`[MQTT] Message received | Topic: ${topic} | Payload: ${raw}`);
            handleAlertMessage(topic, raw);
        });
    });
}

export async function publishMessage(topic: string, payload: object): Promise<void> {
    const mqttClient = getMqttClient();
    const message = JSON.stringify(payload);

    return new Promise((resolve, reject) => {
        mqttClient.publish(topic, message, { qos: 1 }, (err) => {
            if (err) {
                console.error(`[MQTT] Failed to publish to "${topic}":`, err);
                reject(err);
            } else {
                console.log(`[MQTT] Published | Topic: ${topic} | Payload: ${message}`);
                resolve();
            }
        });
    });
}
