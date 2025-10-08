import dotenv from 'dotenv';

dotenv.config();

function requireEnv(key: string): string {
    const value = process.env[key];
    if (!value) {
        throw new Error(`Missing required environment variable: ${key}`);
    }
    return value;
}

export const config = {
    telegram: {
        botToken: requireEnv('TELEGRAM_BOT_TOKEN'),
        authorizedChatId: requireEnv('AUTHORIZED_CHAT_ID'),
    },
    mqtt: {
        url: requireEnv('MQTT_URL'),
        username: process.env.MQTT_USERNAME,
        password: process.env.MQTT_PASSWORD,
    },
} as const;
