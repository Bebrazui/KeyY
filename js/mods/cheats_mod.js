/**
 * Cheats Mod for KeyY.
 * God Mode (invulnerability, no damage taken) & score multiplier.
 * Toggle hotkey: '['
 */

export class CheatsMod {
    constructor() {
        this.id = 'cheats';
        this.name = 'Читы';
        this.version = '1.0';
        this.desc = 'Бессмертие и множитель очков';
        this.enabled = false;
    }

    onKeyPress(e, state, engine) {
        if (e.code === 'BracketLeft' || e.key === '[') {
            this.enabled = !this.enabled;
            if (engine.modSystem) engine.modSystem.saveState();
            return true;
        }
        return false;
    }

    onDamage(amount, state) {
        if (!this.enabled) return amount;
        // God mode: Cancel all damage
        return 0;
    }

    onHit(note, judgment, state) {
        if (!this.enabled) return;
        state.score += 50;
    }

    onDrawUI(ctx, state, w, h) {
        if (!this.enabled) return;
        ctx.save();
        ctx.fillStyle = '#ffaa78';
        ctx.font = 'bold 14px sans-serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'top';
        ctx.fillText('🛡️ GOD MODE ([)', w - 20, 60);
        ctx.restore();
    }
}
