import 'dotenv/config';
import { connectMqtt } from './mqtt/client';
import { SmartHomeBot } from './bot/telegram';

async function main(): Promise<void> {
    console.log('=== Smart Home Agent Starting ===');

    try {
        // 1. Connect to MQTT broker first
        await connectMqtt();
    } catch (err) {
        console.error('[App] Failed to connect to MQTT broker:', err);
        process.exit(1);
    }

    // 2. Start the Telegram bot
    new SmartHomeBot();

    console.log('=== Smart Home Agent Running ===');
}

process.on('uncaughtException', (err) => {
    console.error('[App] Uncaught Exception:', err);
    process.exit(1);
});

process.on('unhandledRejection', (reason) => {
    console.error('[App] Unhandled Rejection:', reason);
    process.exit(1);
});

main();
