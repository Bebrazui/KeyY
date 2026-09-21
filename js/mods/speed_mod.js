/**
 * Speed Mod for KeyY.
 * Dynamically modulates music playback speed and note pace (0.5x - 3.0x).
 * Hotkeys: '+' / '=' (Speed up), '-' / '_' (Slow down), '0' (Reset).
 */

export class SpeedMod {
    constructor() {
        this.id = 'speed';
        this.name = 'Скорость BPM';
        this.version = '1.0';
        this.desc = 'Регулировка темпа игры';
        this.enabled = false;
        this.speedMultiplier = 1.0;
    }

    onInit(engine) {
        this.speedMultiplier = 1.0;
        if (engine && engine.audio) {
            engine.audio.setPlaybackRate(1.0);
        }
    }

    onKeyPress(e, state, engine) {
        if (!this.enabled) return false;

        if (e.key === '=' || e.key === '+') {
            this.speedMultiplier = Math.min(3.0, Math.round((this.speedMultiplier + 0.1) * 10) / 10);
            engine.audio.setPlaybackRate(this.speedMultiplier);
            return true;
        } else if (e.key === '-' || e.key === '_') {
            this.speedMultiplier = Math.max(0.5, Math.round((this.speedMultiplier - 0.1) * 10) / 10);
            engine.audio.setPlaybackRate(this.speedMultiplier);
            return true;
        } else if (e.key === '0') {
            this.speedMultiplier = 1.0;
            engine.audio.setPlaybackRate(1.0);
            return true;
        }
        return false;
    }

    onDrawUI(ctx, state, w, h) {
        if (!this.enabled) return;
        ctx.save();
        ctx.fillStyle = this.speedMultiplier > 1.0 ? '#ffff64' : (this.speedMultiplier < 1.0 ? '#78c8ff' : '#e6e6e6');
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'top';
        ctx.fillText(`⚡ Speed: ${this.speedMultiplier.toFixed(1)}x (+/-)`, w - 20, 80);
        ctx.restore();
    }
}
