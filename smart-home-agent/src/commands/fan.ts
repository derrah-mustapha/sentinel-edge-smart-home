import { publishMessage } from '../mqtt/client';

const FAN_TOPIC = 'home/fan/set';

export async function fanOn(): Promise<void> {
    await publishMessage(FAN_TOPIC, { command: 'on' });
}

export async function fanOff(): Promise<void> {
    await publishMessage(FAN_TOPIC, { command: 'off' });
}
