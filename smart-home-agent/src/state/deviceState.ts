export interface DeviceState {
    fan: 'on' | 'off';
    window: 'open' | 'closed';
    light: 'on' | 'off';
    temperature: number | null;
    humidity: number | null;
}

const state: DeviceState = {
    fan: 'off',
    window: 'closed',
    light: 'off',
    temperature: null,
    humidity: null,
};

export function getState(): Readonly<DeviceState> {
    return state;
}

export function updateFan(status: 'on' | 'off'): void {
    state.fan = status;
}

export function updateWindow(status: 'open' | 'closed'): void {
    state.window = status;
}

export function updateLight(status: 'on' | 'off'): void {
    state.light = status;
}

export function updateTemperature(value: number): void {
    state.temperature = value;
}

export function updateHumidity(value: number): void {
    state.humidity = value;
}
