import TelegramBot from 'node-telegram-bot-api';
import { config } from '../config/env';
import { getState } from '../state/deviceState';
import { setBotInstance } from '../alerts/alertHandler';
import { fanOn, fanOff } from '../commands/fan';
import { openWindow, closeWindow } from '../commands/window';
import { lightOn, lightOff } from '../commands/light';

type CommandHandler = (msg: TelegramBot.Message) => Promise<void>;

export class SmartHomeBot {
    private bot: TelegramBot;
    private authorizedChatId: string;

    constructor() {
        this.authorizedChatId = config.telegram.authorizedChatId;
        this.bot = new TelegramBot(config.telegram.botToken, { polling: true });
        setBotInstance(this.bot);
        this.registerCommands();
        console.log('[Bot] Telegram bot started and polling for messages.');
    }

    private isAuthorized(msg: TelegramBot.Message): boolean {
        return String(msg.chat.id) === this.authorizedChatId;
    }

    private guard(handler: CommandHandler): CommandHandler {
        return async (msg: TelegramBot.Message) => {
            if (!this.isAuthorized(msg)) {
                console.warn(`[Bot] Unauthorized access attempt from chat ID: ${msg.chat.id}`);
                await this.reply(msg, '🚫 Unauthorized. You are not allowed to control this system.');
                return;
            }
            try {
                await handler(msg);
            } catch (err) {
                console.error('[Bot] Command error:', err);
                await this.reply(msg, '❌ An error occurred while processing your command.');
            }
        };
    }

    private async reply(msg: TelegramBot.Message, text: string): Promise<void> {
        await this.bot.sendMessage(msg.chat.id, text, { parse_mode: 'Markdown' });
    }

    private registerCommands(): void {
        this.bot.onText(/\/start/, this.guard(async (msg) => {
            const name = msg.from?.first_name ?? 'there';
            await this.reply(
                msg,
                `👋 Hello, *${name}*! Welcome to your Smart Home Controller.\n\n` +
                `Available commands:\n` +
                `🌀 /fan\\_on — Turn fan on\n` +
                `🌀 /fan\\_off — Turn fan off\n` +
                `🪟 /open\\_window — Open window\n` +
                `🪟 /close\\_window — Close window\n` +
                `💡 /light\\_on — Turn light on\n` +
                `💡 /light\\_off — Turn light off\n` +
                `📊 /status — Show current device status`,
            );
        }));

        this.bot.onText(/\/status/, this.guard(async (msg) => {
            const s = getState();
            const temp = s.temperature !== null ? `${s.temperature}°C` : 'N/A';
            const hum = s.humidity !== null ? `${s.humidity}%` : 'N/A';
            await this.reply(
                msg,
                `🏠 *Smart Home Status*\n\n` +
                `🌀 Fan: *${s.fan.toUpperCase()}*\n` +
                `🪟 Window: *${s.window.toUpperCase()}*\n` +
                `💡 Light: *${s.light.toUpperCase()}*\n` +
                `🌡️ Temperature: *${temp}*\n` +
                `💧 Humidity: *${hum}*`,
            );
        }));

        this.bot.onText(/\/fan_on/, this.guard(async (msg) => {
            await fanOn();
            await this.reply(msg, '✅ Fan turned *ON*.');
        }));

        this.bot.onText(/\/fan_off/, this.guard(async (msg) => {
            await fanOff();
            await this.reply(msg, '✅ Fan turned *OFF*.');
        }));

        this.bot.onText(/\/open_window/, this.guard(async (msg) => {
            await openWindow();
            await this.reply(msg, '✅ Window *OPENED*.');
        }));

        this.bot.onText(/\/close_window/, this.guard(async (msg) => {
            await closeWindow();
            await this.reply(msg, '✅ Window *CLOSED*.');
        }));

        this.bot.onText(/\/light_on/, this.guard(async (msg) => {
            await lightOn();
            await this.reply(msg, '✅ Light turned *ON*.');
        }));

        this.bot.onText(/\/light_off/, this.guard(async (msg) => {
            await lightOff();
            await this.reply(msg, '✅ Light turned *OFF*.');
        }));

        this.bot.on('polling_error', (err) => {
            console.error('[Bot] Polling error:', err.message);
        });
    }
}
