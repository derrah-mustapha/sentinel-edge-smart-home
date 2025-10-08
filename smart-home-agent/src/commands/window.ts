import { publishMessage } from '../mqtt/client';

const WINDOW_TOPIC = 'home/window/set';

export async function openWindow(): Promise<void> {
    await publishMessage(WINDOW_TOPIC, { command: 'open' });
}

export async function closeWindow(): Promise<void> {
    await publishMessage(WINDOW_TOPIC, { command: 'close' });
}
