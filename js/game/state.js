/**
 * Game state representations for active gameplay.
 */

export class ActiveNote {
    constructor(note, approachMs) {
        this.note = note;
        this.approach_ms = approachMs;
        this.arrive_time_ms = note.time_ms;
        this.spawn_time_ms = note.time_ms - approachMs;
        this.end_time_ms = note.time_ms + (note.duration_ms || 0);

        this.hit = false;
        this.missed = false;

        this.is_hold = (note.duration_ms || 0) >= 50;
        this.hold_started = false;
        this.hold_completed = false;
        this.hold_side = null;
        this.hold_progress = 0; // 0.0 to 1.0
    }

    progress(nowMs) {
        return Math.max(0, Math.min(1, (nowMs - this.spawn_time_ms) / this.approach_ms));
    }
}

export class GameState {
    constructor(level) {
        this.level = level;
        this.activeNotes = [];
        this.nextNoteIdx = 0;

        this.score = 0;
        this.combo = 0;
        this.bestCombo = 0;
        this.hp = 100;
        this.maxHp = 100;

        this.totalNotes = level.notes.length;
        this.hits = 0;

        // Statistics
        this.stats = {
            perfect: 0,
            great: 0,
            good: 0,
            bad: 0,
            miss: 0,
            fakeHit: 0
        };

        // Active floating judgements [{ text: 'PERFECT', color: '#...', time: nowMs, life: 0.8 }]
        this.judgements = [];

        // Slide mechanic state
        this.pendingSlideTarget = null;
        this.pendingSlideExpireMs = 0;

        // Visual juice timers
        this.shakeTimer = 0;
        this.shakeIntensity = 0;
        this.pulseTimer = 0;
        this.flashTimer = 0;
        this.flashColor = 'rgba(255, 0, 0, 0.3)';

        // Track glow for pressed directions
        this.trackGlow = {
            left: 0,
            top: 0,
            right: 0,
            bottom: 0,
            top_left: 0,
            top_right: 0,
            bottom_left: 0,
            bottom_right: 0
        };
        this.heldTouchSides = new Set();

        this.beatGlowIntensity = 0;

        // Visual effects from level
        this.activeEffects = new Set(level.effects || []);
        this.nextEventIdx = 0;

        // Pre-game countdown (3 - 2 - 1 - GO!)
        this.countdown = 3.0;
        this.countdownDone = false;

        // Game Over state & note fragments
        this.gameOverTimer = 0;
        this.fragments = [];

        this.finished = false;
        this.failed = false;

        // Last note end time
        this.lastNoteEndTimeMs = 0;
        for (const n of level.notes) {
            const end = n.time_ms + (n.duration_ms || 0);
            if (end > this.lastNoteEndTimeMs) {
                this.lastNoteEndTimeMs = end;
            }
        }
    }

    reset() {
        this.activeNotes.length = 0;
        this.nextNoteIdx = 0;
        this.score = 0;
        this.combo = 0;
        this.bestCombo = 0;
        this.hp = 100;
        this.hits = 0;
        this.stats = { perfect: 0, great: 0, good: 0, bad: 0, miss: 0, fakeHit: 0 };
        this.judgements.length = 0;
        this.pendingSlideTarget = null;
        this.pendingSlideExpireMs = 0;
        this.shakeTimer = 0;
        this.shakeIntensity = 0;
        this.pulseTimer = 0;
        this.flashTimer = 0;
        this.finished = false;
        this.failed = false;
        this.gameOverTimer = 0;
        this.fragments = [];
        this.countdown = 3.0;
        this.countdownDone = false;
        this.activeEffects = new Set(this.level.effects || []);
        this.nextEventIdx = 0;
        this.trackGlow = { left: 0, top: 0, right: 0, bottom: 0 };
        this.beatGlowIntensity = 0;
    }

    applyDamage(amount) {
        this.hp = Math.max(0, this.hp - amount);
        if (this.hp <= 0 && !this.failed) {
            this.failed = true;
            this.gameOverTimer = 0;
            this.shakeTimer = 0.5;
            this.shakeIntensity = 15;
            this.flashTimer = 0.5;
            this.flashColor = 'rgba(255, 0, 0, 0.5)';
            this.spawnGameOverFragments();
        }
    }

    spawnGameOverFragments() {
        this.fragments.length = 0;
        const count = Math.min(16, this.activeNotes.length + 10);
        for (let i = 0; i < count; i++) {
            const angle = Math.random() * Math.PI * 2;
            const speed = 150 + Math.random() * 300;
            this.fragments.push({
                x: 450 + (Math.random() * 40 - 20),
                y: 450 + (Math.random() * 40 - 20),
                vx: Math.cos(angle) * speed,
                vy: Math.sin(angle) * speed,
                size: 8 + Math.random() * 8,
                life: 1.0,
                color: ['#78c8ff', '#78ffa0', '#ffaa78', '#ff78c8'][i % 4]
            });
        }
    }

    addJudgement(text, color) {
        this.judgements.push({
            text,
            color,
            life: 0.7,
            maxLife: 0.7
        });
        if (this.judgements.length > 5) {
            this.judgements.shift();
        }
    }
}
