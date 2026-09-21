/**
 * Ultra-high-performance 2D Canvas renderer for KeyY.
 * Designed for 144Hz+ displays with smooth animations, post-processing shaders,
 * 3-2-1 countdown, track glow, rainbow mod support, and Canvas Game Over screen.
 */

import { modSystem } from '../mods/mod_system.js';

export const VIRTUAL_SIZE = 900;
export const CENTER = 450;
export const CENTER_RADIUS = 60;
export const NOTE_SIZE = 64;
export const SPAWN_PADDING = 40;

export const COLORS = {
    bg: '#10121c',
    grid: '#1a1e2a',
    center: '#f0f0ff',
    centerFill: 'rgba(30, 35, 55, 0.7)',
    text: '#e6e6e6',
    subtext: '#8c96a5',
    hpBg: '#3c2828',
    hp: '#dc4646',
    progressBg: '#282c38',
    progress: '#78c8ff',
    note: {
        left: '#78c8ff',
        top: '#78ffa0',
        right: '#ffaa78',
        bottom: '#ff78c8',
        top_left: '#a0a0ff',
        top_right: '#a0ffff',
        bottom_left: '#ffa0ff',
        bottom_right: '#ffffa0'
    },
    noteDim: {
        left: 'rgba(120, 200, 255, 0.3)',
        top: 'rgba(120, 255, 160, 0.3)',
        right: 'rgba(255, 170, 120, 0.3)',
        bottom: 'rgba(255, 120, 200, 0.3)',
        top_left: 'rgba(160, 160, 255, 0.3)',
        top_right: 'rgba(160, 255, 255, 0.3)',
        bottom_left: 'rgba(255, 160, 255, 0.3)',
        bottom_right: 'rgba(255, 255, 160, 0.3)'
    },
    judgement: {
        'PERFECT': '#78ffa0',
        'GREAT': '#78c8ff',
        'GOOD': '#ffaa78',
        'BAD': '#ff4664',
        'MISS': '#dc3246',
        'FAKE': '#ff2222',
        'HOLD START': '#c878ff',
        'HOLD OK': '#78ffa0',
        'SLIDE': '#ffff78'
    }
};

export const SPAWN_POINTS = {
    left: { x: SPAWN_PADDING, y: CENTER },
    top: { x: CENTER, y: SPAWN_PADDING },
    right: { x: VIRTUAL_SIZE - SPAWN_PADDING, y: CENTER },
    bottom: { x: CENTER, y: VIRTUAL_SIZE - SPAWN_PADDING },
    top_left: { x: SPAWN_PADDING, y: SPAWN_PADDING },
    top_right: { x: VIRTUAL_SIZE - SPAWN_PADDING, y: SPAWN_PADDING },
    bottom_left: { x: SPAWN_PADDING, y: VIRTUAL_SIZE - SPAWN_PADDING },
    bottom_right: { x: VIRTUAL_SIZE - SPAWN_PADDING, y: VIRTUAL_SIZE - SPAWN_PADDING }
};

export function colorWithAlpha(color, alpha) {
    if (!color) return `rgba(255, 255, 255, ${alpha})`;
    if (color.startsWith('#')) {
        let hex = color.slice(1);
        if (hex.length === 3) hex = hex.split('').map(c => c + c).join('');
        const num = parseInt(hex, 16);
        const r = (num >> 16) & 255;
        const g = (num >> 8) & 255;
        const b = num & 255;
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
    if (color.startsWith('rgb')) {
        return color.replace(/rgba?\(([^)]+)\)/, (m, val) => {
            const parts = val.split(',').map(s => s.trim());
            return `rgba(${parts[0]}, ${parts[1]}, ${parts[2]}, ${alpha})`;
        });
    }
    if (color.startsWith('hsl')) {
        return color.replace(/hsla?\(([^)]+)\)/, (m, val) => {
            const parts = val.split(',').map(s => s.trim());
            return `hsla(${parts[0]}, ${parts[1]}, ${parts[2]}, ${alpha})`;
        });
    }
    return color;
}

export const SIDES_4 = [
    { side: 'top', key: 'W', angle: -Math.PI / 2, startAngle: -Math.PI * 3/4, endAngle: -Math.PI / 4 },
    { side: 'right', key: 'D', angle: 0, startAngle: -Math.PI / 4, endAngle: Math.PI / 4 },
    { side: 'bottom', key: 'S', angle: Math.PI / 2, startAngle: Math.PI / 4, endAngle: Math.PI * 3/4 },
    { side: 'left', key: 'A', angle: Math.PI, startAngle: Math.PI * 3/4, endAngle: Math.PI * 5/4 }
];

export const SIDES_8 = [
    { side: 'top', key: 'W', angle: -Math.PI / 2, startAngle: -Math.PI * 5/8, endAngle: -Math.PI * 3/8 },
    { side: 'top_right', key: 'E', angle: -Math.PI / 4, startAngle: -Math.PI * 3/8, endAngle: -Math.PI / 8 },
    { side: 'right', key: 'D', angle: 0, startAngle: -Math.PI / 8, endAngle: Math.PI / 8 },
    { side: 'bottom_right', key: 'C', angle: Math.PI / 4, startAngle: Math.PI / 8, endAngle: Math.PI * 3/8 },
    { side: 'bottom', key: 'S', angle: Math.PI / 2, startAngle: Math.PI * 3/8, endAngle: Math.PI * 5/8 },
    { side: 'bottom_left', key: 'Z', angle: Math.PI * 3/4, startAngle: Math.PI * 5/8, endAngle: Math.PI * 7/8 },
    { side: 'left', key: 'A', angle: Math.PI, startAngle: Math.PI * 7/8, endAngle: Math.PI * 9/8 },
    { side: 'top_left', key: 'Q', angle: -Math.PI * 3/4, startAngle: -Math.PI * 7/8, endAngle: -Math.PI * 5/8 }
];

export class GameRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d', { alpha: false });
        this.dpr = window.devicePixelRatio || 1;
        this.fontFamily = 'system-ui, -apple-system, sans-serif';

        // 900x900 Offscreen scene canvas for post-processing filters
        this.sceneCanvas = document.createElement('canvas');
        this.sceneCanvas.width = VIRTUAL_SIZE;
        this.sceneCanvas.height = VIRTUAL_SIZE;
        this.sceneCtx = this.sceneCanvas.getContext('2d', { alpha: false });

        // Low-res buffer for pixelate effect
        this.pixelCanvas = document.createElement('canvas');
        this.pixelCanvas.width = 100;
        this.pixelCanvas.height = 100;
        this.pixelCtx = this.pixelCanvas.getContext('2d', { alpha: false });

        this.resize();
    }

    resize() {
        const dpr = Math.min(window.devicePixelRatio || 1, 2.5);
        this.dpr = dpr;
        this.canvas.width = Math.round(window.innerWidth * dpr);
        this.canvas.height = Math.round(window.innerHeight * dpr);
    }

    getNoteColor(side, nowMs) {
        const rainbow = modSystem.getMod('rainbow');
        if (rainbow && rainbow.enabled) {
            const col = rainbow.getColor(side, nowMs);
            if (col) return col;
        }
        return COLORS.note[side] || '#ffffff';
    }

    getNoteDimColor(side, nowMs) {
        const rainbow = modSystem.getMod('rainbow');
        if (rainbow && rainbow.enabled) {
            const col = rainbow.getDimColor(side, nowMs);
            if (col) return col;
        }
        return COLORS.noteDim[side] || 'rgba(255, 255, 255, 0.3)';
    }

    render(state, nowMs, particlePool, engine) {
        const sctx = this.sceneCtx;

        // 1. Clear offscreen 900x900 scene
        sctx.fillStyle = COLORS.bg;
        sctx.fillRect(0, 0, VIRTUAL_SIZE, VIRTUAL_SIZE);

        sctx.save();

        // Screen Shake
        if (state.shakeTimer > 0) {
            const intensity = state.shakeIntensity;
            const shakeX = (Math.random() * 2 - 1) * intensity;
            const shakeY = (Math.random() * 2 - 1) * intensity;
            sctx.translate(shakeX, shakeY);
        }

        // Camera Zoom & Rotate events from level
        if (state.camZoom && state.camZoom !== 1.0) {
            sctx.translate(CENTER, CENTER);
            sctx.scale(state.camZoom, state.camZoom);
            sctx.translate(-CENTER, -CENTER);
        }
        if (state.camAngle) {
            sctx.translate(CENTER, CENTER);
            sctx.rotate((state.camAngle * Math.PI) / 180);
            sctx.translate(-CENTER, -CENTER);
        }

        // 2. Guide lines, Track Glow & Beat Glow
        this.renderTracks(sctx, state, nowMs);

        // 3. Center Target Ring
        this.renderCenter(sctx, state, nowMs);

        // 4. Notes (Hold trails first, then note bodies)
        this.renderNotes(sctx, state, nowMs);

        // 5. Particles from pool
        this.renderParticles(sctx, particlePool);

        // 6. Judgements (floating text)
        this.renderJudgements(sctx, state);

        // 7. Screen Flash on hit/miss
        if (state.flashTimer > 0) {
            sctx.fillStyle = state.flashColor;
            sctx.fillRect(0, 0, VIRTUAL_SIZE, VIRTUAL_SIZE);
        }

        // 8. Pre-game 3-2-1 Countdown
        this.renderCountdown(sctx, state);

        // 9. Game Over Animation
        this.renderGameOver(sctx, state);

        sctx.restore();

        // 10. Blit scene to main canvas with scaling and post-processing effects
        const w = this.canvas.width;
        const h = this.canvas.height;
        const scale = Math.min(w / VIRTUAL_SIZE, h / VIRTUAL_SIZE);
        const offsetX = (w - VIRTUAL_SIZE * scale) / 2;
        const offsetY = (h - VIRTUAL_SIZE * scale) / 2;

        this.ctx.fillStyle = COLORS.bg;
        this.ctx.fillRect(0, 0, w, h);

        this.renderPostProcessing(this.ctx, state, scale, offsetX, offsetY);

        // 10.5. Fullscreen Touch Zones across the entire mobile screen
        this.renderFullScreenTouchZones(this.ctx, state, nowMs, w, h, scale, offsetX, offsetY);

        // 11. HUD / UI Elements (Score, Combo, HP, Progress, Mod badges)
        this.renderHUD(this.ctx, state, nowMs, scale, offsetX, offsetY);
    }

    renderTracks(ctx, state, nowMs) {
        ctx.lineWidth = 3;
        const hasDiagonals = state.level?.notes?.some(n => 
            ['top_left', 'top_right', 'bottom_left', 'bottom_right'].includes(n.side)
        );
        const activeSides = hasDiagonals 
            ? ['left', 'top', 'right', 'bottom', 'top_left', 'top_right', 'bottom_left', 'bottom_right']
            : ['left', 'top', 'right', 'bottom'];

        // Whole-field Beat Glow
        if (state.beatGlowIntensity > 0) {
            for (const side of activeSides) {
                const pt = SPAWN_POINTS[side];
                if (!pt) continue;
                const col = this.getNoteColor(side, nowMs);
                ctx.save();
                ctx.strokeStyle = col;
                ctx.shadowColor = col;
                ctx.shadowBlur = 25 * state.beatGlowIntensity;
                ctx.globalAlpha = 0.5 * state.beatGlowIntensity;
                ctx.lineWidth = 12;
                ctx.beginPath();
                ctx.moveTo(pt.x, pt.y);
                ctx.lineTo(CENTER, CENTER);
                ctx.stroke();
                ctx.restore();
            }
        }

        for (const side of activeSides) {
            const pt = SPAWN_POINTS[side];
            if (!pt) continue;
            const glow = state.trackGlow[side] || 0;
            const col = this.getNoteColor(side, nowMs);

            // Track base line
            ctx.strokeStyle = COLORS.grid;
            ctx.beginPath();
            ctx.moveTo(pt.x, pt.y);
            ctx.lineTo(CENTER, CENTER);
            ctx.stroke();

            // Track active glow when key is pressed
            if (glow > 0.05) {
                ctx.save();
                ctx.strokeStyle = col;
                ctx.shadowColor = col;
                ctx.shadowBlur = 20 * glow;
                ctx.globalAlpha = Math.min(1, glow);
                ctx.lineWidth = 6 + 6 * glow;
                ctx.beginPath();
                ctx.moveTo(pt.x, pt.y);
                ctx.lineTo(CENTER, CENTER);
                ctx.stroke();
                ctx.restore();
            }
    }

    getTouchZoneSetting() {
        try {
            const saved = localStorage.getItem('keyy_full_settings');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (parsed?.graphics?.touch_zones) return parsed.graphics.touch_zones;
            }
        } catch(e) {}
        return 'auto';
    }

    renderFullScreenTouchZones(ctx, state, nowMs, w, h, scale, offsetX, offsetY) {
        if (!state || state.failed) return;
        // Do not display touch zone highlights during 3-2-1 countdown
        if (state.countdown > 0) return;

        // On desktop PC with keyboard/mouse, do NOT render touch zone divisions unless explicitly turned on
        const tzSetting = this.getTouchZoneSetting();
        if (tzSetting === 'off') return;
        if (tzSetting === 'auto') {
            const isCoarseTouch = typeof window !== 'undefined' && (
                window.matchMedia('(pointer: coarse)').matches ||
                ('ontouchstart' in window && window.innerWidth <= 1024)
            );
            const touchModeActive = isCoarseTouch || !!state.hasTouchInput;
            if (!touchModeActive) return;
        }

        const hasDiagonals = state.level?.notes?.some(n => 
            ['top_left', 'top_right', 'bottom_left', 'bottom_right'].includes(n.side)
        );
        const sectors = hasDiagonals ? SIDES_8 : SIDES_4;

        const cx = w / 2;
        const cy = h / 2;
        const maxRadius = Math.hypot(cx, cy) + 60;
        const centerR = CENTER_RADIUS * scale;

        for (let i = 0; i < sectors.length; i++) {
            const sector = sectors[i];
            const side = sector.side;
            const col = this.getNoteColor(side, nowMs);

            // Find incoming note proximity for this sector
            let maxProx = 0;
            let noteLabel = sector.key;

            for (let j = 0; j < state.activeNotes.length; j++) {
                const an = state.activeNotes[j];
                if (an.hit || an.missed || an.note.side !== side) continue;
                const diff = an.arrive_time_ms - nowMs;
                if (diff >= -80 && diff <= an.approach_ms) {
                    const prox = 1.0 - Math.max(0, diff) / an.approach_ms;
                    if (prox > maxProx) {
                        maxProx = prox;
                        if (an.note.key) {
                            noteLabel = an.note.key.toUpperCase();
                        }
                    }
                }
            }

            const isHeld = (state.trackGlow[side] > 0.05) || (state.heldTouchSides && state.heldTouchSides.has(side));

            ctx.save();

            // 1. Dividing border lines extending from center ring across whole display
            ctx.strokeStyle = isHeld || maxProx > 0.3 ? colorWithAlpha(col, 0.35) : 'rgba(255, 255, 255, 0.07)';
            ctx.lineWidth = Math.max(1, Math.round(1.5 * this.dpr));
            ctx.beginPath();
            ctx.moveTo(cx + Math.cos(sector.startAngle) * (centerR + 10), cy + Math.sin(sector.startAngle) * (centerR + 10));
            ctx.lineTo(cx + Math.cos(sector.startAngle) * maxRadius, cy + Math.sin(sector.startAngle) * maxRadius);
            ctx.stroke();

            // 2. Soft semi-transparent illumination (ONLY when approaching or held by thumb)
            if (maxProx > 0 || isHeld) {
                ctx.beginPath();
                ctx.arc(cx, cy, maxRadius, sector.startAngle, sector.endAngle);
                ctx.arc(cx, cy, centerR + 8, sector.endAngle, sector.startAngle, true);
                ctx.closePath();

                const baseAlpha = isHeld ? 0.28 : (0.03 + 0.18 * Math.pow(maxProx, 1.4));
                const grad = ctx.createRadialGradient(cx, cy, centerR + 8, cx, cy, maxRadius * 0.75);
                grad.addColorStop(0, colorWithAlpha(col, baseAlpha * 1.3));
                grad.addColorStop(0.5, colorWithAlpha(col, baseAlpha * 0.7));
                grad.addColorStop(1, colorWithAlpha(col, 0.0));
                ctx.fillStyle = grad;
                ctx.fill();
            }

            // 3. Subtle zone key label at comfortable thumb rest distance
            const labelDist = Math.min(w, h) * 0.38;
            const lx = cx + Math.cos(sector.angle) * labelDist;
            const ly = cy + Math.sin(sector.angle) * labelDist;

            const fontSize = Math.round(26 * this.dpr);
            ctx.font = `bold ${fontSize}px ${this.fontFamily}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            if (isHeld) {
                ctx.fillStyle = col;
                ctx.shadowColor = col;
                ctx.shadowBlur = 12 * this.dpr;
                ctx.globalAlpha = 1.0;
            } else if (maxProx > 0) {
                ctx.fillStyle = col;
                ctx.shadowColor = col;
                ctx.shadowBlur = 8 * maxProx * this.dpr;
                ctx.globalAlpha = 0.4 + 0.6 * maxProx;
            } else {
                ctx.fillStyle = 'rgba(200, 220, 245, 0.25)';
                ctx.shadowBlur = 0;
                ctx.globalAlpha = 1.0;
            }

            ctx.fillText(noteLabel, lx, ly);
            ctx.restore();
        }
    }

    renderCenter(ctx, state, nowMs) {
        ctx.save();
        const pulse = state.pulseTimer > 0 ? (state.pulseTimer / 0.15) * 6 : 0;
        const radius = CENTER_RADIUS + pulse;

        // Outer glow
        const rainbow = modSystem.getMod('rainbow');
        const glowColor = (rainbow && rainbow.enabled) ? rainbow.getColor('top', nowMs) : COLORS.center;

        ctx.shadowColor = glowColor;
        ctx.shadowBlur = 12 + pulse * 2;

        // Fill center target
        ctx.beginPath();
        ctx.arc(CENTER, CENTER, radius, 0, Math.PI * 2);
        ctx.fillStyle = COLORS.centerFill;
        ctx.fill();

        // Outline
        ctx.lineWidth = 4;
        ctx.strokeStyle = glowColor;
        ctx.stroke();

        // Inner decorative circle
        ctx.beginPath();
        ctx.arc(CENTER, CENTER, 18, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(240, 240, 255, 0.4)';
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.restore();
    }

    renderNotes(ctx, state, nowMs) {
        // Draw hold tails first so note heads render on top
        for (let i = 0; i < state.activeNotes.length; i++) {
            const an = state.activeNotes[i];
            if (an.is_hold && !an.missed) {
                this.renderHoldTail(ctx, an, nowMs);
            }
        }

        // Draw note heads
        for (let i = 0; i < state.activeNotes.length; i++) {
            const an = state.activeNotes[i];
            if (an.hit || an.missed) continue;
            this.renderNoteHead(ctx, an, nowMs);
        }
    }

    renderHoldTail(ctx, an, nowMs) {
        const side = an.note.side;
        const sp = SPAWN_POINTS[side];
        const arriveMs = an.arrive_time_ms;
        const endMs = an.end_time_ms;
        const approach = an.approach_ms;

        // Head position
        const headProg = an.hold_started ? 1.0 : Math.max(0, Math.min(1, (nowMs - an.spawn_time_ms) / approach));
        const headX = sp.x + (CENTER - sp.x) * headProg;
        const headY = sp.y + (CENTER - sp.y) * headProg;

        // Tail position
        const tailProg = Math.max(0, Math.min(1, (nowMs - (an.spawn_time_ms + (an.note.duration_ms || 0))) / approach));
        const tailX = sp.x + (CENTER - sp.x) * tailProg;
        const tailY = sp.y + (CENTER - sp.y) * tailProg;

        const col = this.getNoteColor(side, nowMs);

        ctx.save();
        ctx.strokeStyle = col;
        ctx.lineWidth = 14;
        ctx.lineCap = 'round';
        ctx.globalAlpha = 0.55;

        ctx.beginPath();
        ctx.moveTo(headX, headY);
        ctx.lineTo(tailX, tailY);
        ctx.stroke();

        // Inner bright line
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 4;
        ctx.globalAlpha = 0.85;
        ctx.beginPath();
        ctx.moveTo(headX, headY);
        ctx.lineTo(tailX, tailY);
        ctx.stroke();

        ctx.restore();
    }

    renderNoteHead(ctx, an, nowMs) {
        const side = an.note.side;
        const sp = SPAWN_POINTS[side];
        const prog = an.progress(nowMs);

        const x = sp.x + (CENTER - sp.x) * prog;
        const y = sp.y + (CENTER - sp.y) * prog;
        const col = this.getNoteColor(side, nowMs);
        const isFake = an.note.is_fake;

        ctx.save();

        if (isFake) {
            // Fake note: Black box, white border, red cross
            ctx.fillStyle = '#000000';
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 3;
            this.roundRect(ctx, x - NOTE_SIZE / 2, y - NOTE_SIZE / 2, NOTE_SIZE, NOTE_SIZE, 10, true, true);

            // Red warning cross
            ctx.strokeStyle = '#ff3232';
            ctx.lineWidth = 4;
            const cs = 14;
            ctx.beginPath();
            ctx.moveTo(x - cs, y - cs);
            ctx.lineTo(x + cs, y + cs);
            ctx.moveTo(x + cs, y - cs);
            ctx.lineTo(x - cs, y + cs);
            ctx.stroke();
        } else {
            // Regular note box
            ctx.shadowColor = col;
            ctx.shadowBlur = 10;
            ctx.fillStyle = col;
            this.roundRect(ctx, x - NOTE_SIZE / 2, y - NOTE_SIZE / 2, NOTE_SIZE, NOTE_SIZE, 10, true, false);

            // Darker inner plate
            ctx.shadowBlur = 0;
            ctx.fillStyle = 'rgba(16, 18, 28, 0.4)';
            this.roundRect(ctx, x - NOTE_SIZE / 2 + 5, y - NOTE_SIZE / 2 + 5, NOTE_SIZE - 10, NOTE_SIZE - 10, 6, true, false);

            // Key Letter
            ctx.fillStyle = '#ffffff';
            ctx.font = `bold 28px ${this.fontFamily}`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(an.note.key || 'A', x, y);

            // Slide Direction Arrow
            if (an.note.note_type === 'slide') {
                this.renderSlideArrow(ctx, x, y, an.note.slide_target || 'right');
            }

            // Double note indicator ring
            if (an.note.note_type === 'double') {
                ctx.strokeStyle = '#ffff64';
                ctx.lineWidth = 3;
                this.roundRect(ctx, x - NOTE_SIZE / 2 - 4, y - NOTE_SIZE / 2 - 4, NOTE_SIZE + 8, NOTE_SIZE + 8, 12, false, true);
            }
        }

        ctx.restore();
    }

    renderSlideArrow(ctx, x, y, targetSide) {
        ctx.save();
        ctx.fillStyle = '#ffff64';
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = 2;

        let angle = 0;
        if (targetSide === 'top') angle = -Math.PI / 2;
        else if (targetSide === 'right') angle = 0;
        else if (targetSide === 'bottom') angle = Math.PI / 2;
        else if (targetSide === 'left') angle = Math.PI;

        ctx.translate(x, y - NOTE_SIZE / 2 + 2);
        ctx.rotate(angle);

        ctx.beginPath();
        ctx.moveTo(8, 0);
        ctx.lineTo(-4, -6);
        ctx.lineTo(-2, 0);
        ctx.lineTo(-8, 0);
        ctx.lineTo(-8, 2);
        ctx.lineTo(-2, 2);
        ctx.lineTo(-4, 6);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        ctx.restore();
    }

    renderParticles(ctx, pool) {
        ctx.save();
        for (let i = 0; i < pool.pool.length; i++) {
            const p = pool.pool[i];
            if (!p.active) continue;

            const alpha = Math.max(0, p.life / p.maxLife);
            ctx.fillStyle = `rgba(${p.r}, ${p.g}, ${p.b}, ${alpha})`;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size * alpha, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    }

    renderJudgements(ctx, state) {
        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        for (let i = 0; i < state.judgements.length; i++) {
            const j = state.judgements[i];
            const alpha = Math.max(0, j.life / j.maxLife);
            const scale = 1.0 + (1.0 - alpha) * 0.3;
            const yOffset = (1.0 - alpha) * 30;

            ctx.shadowColor = j.color;
            ctx.shadowBlur = 10;
            ctx.fillStyle = j.color;
            ctx.globalAlpha = alpha;
            ctx.font = `900 ${Math.floor(28 * scale)}px ${this.fontFamily}`;
            ctx.fillText(j.text, CENTER, CENTER - 110 - i * 28 - yOffset);
        }
        ctx.restore();
    }

    renderCountdown(ctx, state) {
        if (state.countdown <= 0 || state.countdownDone) return;
        const remaining = state.countdown;
        let text = "3";
        let sub = "GET READY";
        if (remaining > 2.0) {
            text = "3";
        } else if (remaining > 1.0) {
            text = "2";
        } else if (remaining > 0.3) {
            text = "1";
        } else {
            text = "GO!";
            sub = "START";
        }

        const frac = remaining % 1.0;
        const scale = 1.0 + (1.0 - frac) * 0.35;
        const alpha = Math.min(1, Math.max(0.2, frac + 0.3));

        ctx.save();
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.shadowColor = '#78c8ff';
        ctx.shadowBlur = 25;

        ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
        ctx.font = `900 ${Math.floor(75 * scale)}px ${this.fontFamily}`;
        ctx.fillText(text, CENTER, CENTER - 10);

        ctx.font = `bold 20px ${this.fontFamily}`;
        ctx.fillStyle = '#78c8ff';
        ctx.fillText(sub, CENTER, CENTER + 55);

        ctx.restore();
    }

    renderGameOver(ctx, state) {
        if (!state.failed) return;

        // 1. Red flash overlay
        if (state.gameOverTimer < 0.6) {
            const flashAlpha = Math.max(0, 0.45 * (1.0 - state.gameOverTimer / 0.6));
            ctx.fillStyle = `rgba(255, 30, 30, ${flashAlpha})`;
            ctx.fillRect(0, 0, VIRTUAL_SIZE, VIRTUAL_SIZE);
        }

        // 2. Exploding note fragments
        for (const frag of state.fragments) {
            if (frag.life <= 0) continue;
            ctx.save();
            ctx.fillStyle = frag.color;
            ctx.globalAlpha = Math.max(0, frag.life);
            ctx.fillRect(frag.x - frag.size/2, frag.y - frag.size/2, frag.size, frag.size);
            ctx.restore();
        }

        // 3. FAILED banner & Statistics (after 0.4s)
        if (state.gameOverTimer > 0.4) {
            ctx.save();
            ctx.fillStyle = 'rgba(10, 12, 20, 0.88)';
            this.roundRect(ctx, CENTER - 220, CENTER - 180, 440, 360, 16, true, false);
            ctx.strokeStyle = '#dc3246';
            ctx.lineWidth = 3;
            this.roundRect(ctx, CENTER - 220, CENTER - 180, 440, 360, 16, false, true);

            ctx.textAlign = 'center';
            ctx.fillStyle = '#ff4664';
            ctx.font = `900 48px ${this.fontFamily}`;
            ctx.shadowColor = '#ff2222';
            ctx.shadowBlur = 18;
            ctx.fillText('FAILED', CENTER, CENTER - 110);
            ctx.shadowBlur = 0;

            const total = state.hits + state.stats.bad + state.stats.miss + state.stats.fakeHit;
            const acc = total > 0 ? ((state.hits / total) * 100).toFixed(1) : '0.0';

            ctx.fillStyle = '#e6e6e6';
            ctx.font = `bold 18px ${this.fontFamily}`;
            ctx.fillText(`Точность: ${acc}%`, CENTER, CENTER - 50);
            ctx.fillText(`Лучшее комбо: ${state.bestCombo}`, CENTER, CENTER - 20);
            ctx.fillText(`Очки: ${state.score}`, CENTER, CENTER + 10);

            // Action hints
            ctx.fillStyle = '#78ffa0';
            ctx.font = `bold 16px ${this.fontFamily}`;
            ctx.fillText('Попробовать снова (R)', CENTER, CENTER + 70);
            ctx.fillStyle = '#78c8ff';
            ctx.fillText('В меню (Esc / Enter)', CENTER, CENTER + 105);

            ctx.restore();
        }
    }

    renderPostProcessing(targetCtx, state, scale, offsetX, offsetY) {
        const effects = state.activeEffects || new Set();

        let filterString = '';
        if (effects.has('blur')) filterString += 'blur(3px) ';
        if (effects.has('invert')) filterString += 'invert(100%) ';
        if (effects.has('grayscale')) filterString += 'grayscale(100%) ';
        if (effects.has('desaturate')) filterString += 'saturate(20%) ';
        if (effects.has('contrast')) filterString += 'contrast(160%) ';

        targetCtx.save();
        targetCtx.translate(offsetX, offsetY);
        targetCtx.scale(scale, scale);

        if (effects.has('pixelate')) {
            this.pixelCtx.drawImage(this.sceneCanvas, 0, 0, 100, 100);
            targetCtx.imageSmoothingEnabled = false;
            targetCtx.drawImage(this.pixelCanvas, 0, 0, VIRTUAL_SIZE, VIRTUAL_SIZE);
            targetCtx.imageSmoothingEnabled = true;
        } else {
            if (filterString) targetCtx.filter = filterString.trim();
            targetCtx.drawImage(this.sceneCanvas, 0, 0);
            targetCtx.filter = 'none';
        }

        // Chroma Shift (RGB split)
        if (effects.has('chroma_shift')) {
            targetCtx.save();
            targetCtx.globalCompositeOperation = 'screen';
            targetCtx.globalAlpha = 0.55;
            targetCtx.drawImage(this.sceneCanvas, -4, 0);
            targetCtx.drawImage(this.sceneCanvas, 4, 0);
            targetCtx.restore();
        }

        // Glow Boost (bloom)
        if (effects.has('glow_boost')) {
            targetCtx.save();
            targetCtx.globalCompositeOperation = 'lighter';
            targetCtx.globalAlpha = 0.35;
            targetCtx.drawImage(this.sceneCanvas, -6, -6, VIRTUAL_SIZE + 12, VIRTUAL_SIZE + 12);
            targetCtx.restore();
        }

        // Vignette
        if (effects.has('vignette')) {
            const grad = targetCtx.createRadialGradient(CENTER, CENTER, 220, CENTER, CENTER, 480);
            grad.addColorStop(0, 'rgba(0, 0, 0, 0)');
            grad.addColorStop(0.7, 'rgba(0, 0, 0, 0.45)');
            grad.addColorStop(1, 'rgba(0, 0, 0, 0.85)');
            targetCtx.fillStyle = grad;
            targetCtx.fillRect(0, 0, VIRTUAL_SIZE, VIRTUAL_SIZE);
        }

        targetCtx.restore();
    }

    renderHUD(ctx, state, nowMs, scale, offsetX, offsetY) {
        ctx.save();
        ctx.translate(offsetX, offsetY);
        ctx.scale(scale, scale);

        // 1. Score & Accuracy (Top Left)
        ctx.font = `bold 32px ${this.fontFamily}`;
        ctx.fillStyle = COLORS.text;
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText(String(state.score).padStart(7, '0'), 30, 75);

        const total = state.hits + state.stats.bad + state.stats.miss + state.stats.fakeHit;
        const acc = total > 0 ? ((state.hits / total) * 100).toFixed(1) : '100.0';
        ctx.font = `bold 16px ${this.fontFamily}`;
        ctx.fillStyle = COLORS.subtext;
        ctx.fillText(`ACCURACY  ${acc}%`, 30, 112);

        // 2. Combo (Top Right)
        if (state.combo > 0) {
            ctx.textAlign = 'right';
            ctx.fillStyle = '#ffffff';
            ctx.font = `900 48px ${this.fontFamily}`;
            ctx.fillText(`${state.combo}x`, VIRTUAL_SIZE - 30, 75);

            ctx.font = `bold 16px ${this.fontFamily}`;
            ctx.fillStyle = '#78c8ff';
            ctx.fillText('COMBO', VIRTUAL_SIZE - 30, 100);
        }

        // 3. Health Bar (Top Center)
        const hpBarW = 320;
        const hpBarH = 14;
        const hpBarX = CENTER - hpBarW / 2;
        const hpBarY = 40;

        ctx.fillStyle = COLORS.hpBg;
        this.roundRect(ctx, hpBarX, hpBarY, hpBarW, hpBarH, 4, true, false);

        const currentHpW = Math.max(0, (state.hp / state.maxHp) * hpBarW);
        if (currentHpW > 0) {
            ctx.fillStyle = state.hp > 30 ? COLORS.hp : '#ff2222';
            this.roundRect(ctx, hpBarX, hpBarY, currentHpW, hpBarH, 4, true, false);
        }

        // 4. Song Progress (Bottom thin bar)
        if (state.lastNoteEndTimeMs > 0) {
            const prog = Math.max(0, Math.min(1, nowMs / state.lastNoteEndTimeMs));
            ctx.fillStyle = COLORS.progressBg;
            ctx.fillRect(0, VIRTUAL_SIZE - 6, VIRTUAL_SIZE, 6);
            ctx.fillStyle = COLORS.progress;
            ctx.fillRect(0, VIRTUAL_SIZE - 6, VIRTUAL_SIZE * prog, 6);
        }

        // 5. Draw active mod badges via ModSystem
        modSystem.executeHook('onDrawUI', ctx, state, VIRTUAL_SIZE, VIRTUAL_SIZE);

        ctx.restore();
    }

    roundRect(ctx, x, y, width, height, radius, fill, stroke) {
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
        if (fill) ctx.fill();
        if (stroke) ctx.stroke();
    }
}
