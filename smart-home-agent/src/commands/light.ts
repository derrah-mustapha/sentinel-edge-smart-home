import { publishMessage } from '../mqtt/client';

const LIGHT_TOPIC = 'home/light/set';

export async function lightOn(): Promise<void> {
    await publishMessage(LIGHT_TOPIC, { command: 'on' });
}

export async function lightOff(): Promise<void> {
    await publishMessage(LIGHT_TOPIC, { command: 'off' });
}
