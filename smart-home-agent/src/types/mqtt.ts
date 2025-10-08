export interface CommandPayload {
    command: string;
}

export interface StatusPayload {
    status: string;
}

export interface ValuePayload {
    value: number;
}

// Union type for incoming MQTT messages
export type MqttPayload = CommandPayload | StatusPayload | ValuePayload;
