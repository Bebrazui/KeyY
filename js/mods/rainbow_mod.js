/**
 * Rainbow Mod for KeyY.
 * Dynamically shifts note colors, target glow, and beam colors across the HSL spectrum.
 */

export class RainbowMod {
    constructor() {
        this.id = 'rainbow';
        this.name = 'Радужные ноты';
        this.version = '1.0';
        this.desc = 'Переливание цветов дорожек';
        this.enabled = true; // Enabled by default
    }

    getColor(side, nowMs) {
        if (!this.enabled) return null;
        const offsets = { left: 0, top: 90, right: 180, bottom: 270 };
        const baseHue = (nowMs * 0.12) % 360;
        const hue = (baseHue + (offsets[side] || 0)) % 360;
        return `hsl(${hue}, 95%, 65%)`;
    }

    getDimColor(side, nowMs) {
        if (!this.enabled) return null;
        const offsets = { left: 0, top: 90, right: 180, bottom: 270 };
        const baseHue = (nowMs * 0.12) % 360;
        const hue = (baseHue + (offsets[side] || 0)) % 360;
        return `hsla(${hue}, 95%, 65%, 0.3)`;
    }
}
