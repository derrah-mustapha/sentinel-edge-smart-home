import TelegramBot from 'node-telegram-bot-api';
import { StatusPayload, ValuePayload } from '../types/mqtt';
import {
    updateFan,
    updateWindow,
    updateLight,
    updateTemperature,
    updateHumidity,
} from '../state/deviceState';

let botInstance: TelegramBot | null = null;

export function setBotInstance(bot: TelegramBot): void {
    botInstance = bot;
}

export function handleAlertMessage(topic: string, raw: string): void {
    let payload: Record<string, unknown>;

    try {
        payload = JSON.parse(raw);
    } catch {
        console.error(`[AlertHandler] Failed to parse payload on topic "${topic}": ${raw}`);
        return;
    }

    const device = topic.split('/').pop() ?? 'unknown';

    if (topic.startsWith('home/alerts/')) {
        handleAlert(device, payload);
    } else if (topic.startsWith('home/status/')) {
        handleStatus(device, payload);
    }
}

function handleAlert(device: string, payload: Record<string, unknown>): void {
    const value = (payload as Partial<ValuePayload>).value;
    let message = '';

    switch (device) {
        case 'temperature':
            if (typeof value === 'number') {
                updateTemperature(value);
                message = `⚠️ *Temperature Alert*\n\nCurrent temperature: *${value}°C*`;
            }
            break;
        case 'humidity':
            if (typeof value === 'number') {
                updateHumidity(value);
                message = `⚠️ *Humidity Alert*\n\nCurrent humidity: *${value}%*`;
            }
            break;
        default:
            message = `⚠️ *Alert: ${device}*\n\n${JSON.stringify(payload, null, 2)}`;
    }

    if (message && botInstance) {
        broadcastAlert(message);
    }
}

function handleStatus(device: string, payload: Record<string, unknown>): void {
    const status = (payload as Partial<StatusPayload>).status;
    const value = (payload as Partial<ValuePayload>).value;

    switch (device) {
        case 'fan':
            if (status === 'on' || status === 'off') {
                updateFan(status);
                console.log(`[AlertHandler] Fan state updated: ${status}`);
            }
            break;
        case 'window':
            if (status === 'open' || status === 'closed') {
                updateWindow(status);
                console.log(`[AlertHandler] Window state updated: ${status}`);
            }
            break;
        case 'light':
            if (status === 'on' || status === 'off') {
                updateLight(status);
                console.log(`[AlertHandler] Light state updated: ${status}`);
            }
            break;
        case 'temperature':
            if (typeof value === 'number') {
                updateTemperature(value);
                console.log(`[AlertHandler] Temperature updated: ${value}°C`);
            }
            break;
        case 'humidity':
            if (typeof value === 'number') {
                updateHumidity(value);
                console.log(`[AlertHandler] Humidity updated: ${value}%`);
            }
            break;
        default:
            console.warn(`[AlertHandler] Unknown status device: ${device}`);
    }
}

function broadcastAlert(message: string): void {
    if (!botInstance) return;

    const authorizedChatId = process.env.AUTHORIZED_CHAT_ID;
    if (!authorizedChatId) return;

    botInstance
        .sendMessage(authorizedChatId, message, { parse_mode: 'Markdown' })
        .catch((err) => console.error('[AlertHandler] Failed to send alert:', err));
}
