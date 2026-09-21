/**
 * Autopilot Mod for KeyY.
 * Automatically hits arriving notes with Perfect precision, manages holds and slides.
 * Toggle hotkey: ']'
 */

export class AutopilotMod {
    constructor() {
        this.id = 'autopilot';
        this.name = 'Автопилот';
        this.version = '1.0';
        this.desc = 'Автоматическое идеальное нажатие нот';
        this.enabled = false;
        this.reactionMs = 30;
    }

    onKeyPress(e, state, engine) {
        if (e.code === 'BracketRight' || e.key === ']') {
            this.enabled = !this.enabled;
            if (engine.modSystem) engine.modSystem.saveState();
            return true;
        }
        return false;
    }

    onGameUpdate(state, dt, nowMs, engine) {
        if (!this.enabled || !state || !engine) return;

        for (let i = 0; i < state.activeNotes.length; i++) {
            const an = state.activeNotes[i];
            if (an.hit || an.missed) continue;

            const arrive = an.arrive_time_ms;
            const diff = arrive - nowMs;

            // Trigger hit within Perfect window
            if (Math.abs(diff) <= this.reactionMs || (diff < 0 && !an.hold_started)) {
                if (an.is_hold) {
                    if (!an.hold_started) {
                        engine.processHit(an.note.side, nowMs);
                    } else if (nowMs >= an.end_time_ms - 20) {
                        engine.processRelease(an.note.side, nowMs);
                    }
                } else {
                    engine.processHit(an.note.side, nowMs);
                }
            }
        }
    }

    onDrawUI(ctx, state, w, h) {
        if (!this.enabled) return;
        ctx.save();
        ctx.fillStyle = '#78ffa0';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'top';
        ctx.fillText('🤖 AUTOPILOT (])', w - 20, 40);
        ctx.restore();
    }
}
