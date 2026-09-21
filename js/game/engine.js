/**
 * Core game loop and rhythm logic processor.
 * Perfectly mirrors KeyY Python behavior with microsecond Web Audio clock,
 * modular mods (Autopilot, Cheats, Speed, Rainbow), 3-2-1 countdown, and visual effects.
 */

import { ActiveNote, GameState } from './state.js';
import { Particle, ObjectPool } from '../core/pool.js';
import { COLORS, CENTER, SPAWN_POINTS, VIRTUAL_SIZE } from './renderer.js';
import { modSystem } from '../mods/mod_system.js';

export class GameEngine {
    constructor(audioManager, inputManager, renderer) {
        this.audio = audioManager;
        this.input = inputManager;
        this.renderer = renderer;

        this.state = null;
        this.particlePool = new ObjectPool(() => new Particle(), 300);

        this.isRunning = false;
        this.isPaused = false;
        this.animationFrameId = null;
        this.lastFrameTime = 0;

        // Callback hooks
        this.onFinishCallback = null;
        this.onFailCallback = null;

        // Color RGB mapping for particles
        this.colorRgbMap = {
            left: [120, 200, 255],
            top: [120, 255, 160],
            right: [255, 170, 120],
            bottom: [255, 120, 200],
            top_left: [160, 160, 255],
            top_right: [160, 255, 255],
            bottom_left: [255, 160, 255],
            bottom_right: [255, 255, 160],
            center: [240, 240, 255],
            red: [255, 70, 70],
            gold: [255, 230, 80]
        };

        this.activePointers = new Map();

        this.boundOnKeyDown = this.onKeyDown.bind(this);
        this.boundPointerDown = this.onPointerDown.bind(this);
        this.boundPointerMove = this.onPointerMove.bind(this);
        this.boundPointerUp = this.onPointerUp.bind(this);
        this.boundPointerCancel = this.onPointerCancel.bind(this);
    }

    start(levelData) {
        this.stop();
        this.state = new GameState(levelData);
        this.particlePool.clear();
        this.activePointers.clear();
        this.input.reset();
        this.input.startListening();

        window.addEventListener('keydown', this.boundOnKeyDown);

        const canvas = this.renderer.canvas;
        canvas.addEventListener('pointerdown', this.boundPointerDown);
        canvas.addEventListener('pointermove', this.boundPointerMove);
        canvas.addEventListener('pointerup', this.boundPointerUp);
        canvas.addEventListener('pointercancel', this.boundPointerCancel);

        this.isRunning = true;
        this.isPaused = false;
        this.lastFrameTime = performance.now();

        // Initialize mods
        modSystem.executeHook('onInit', this);

        this.loop = this.loop.bind(this);
        this.animationFrameId = requestAnimationFrame(this.loop);
    }

    stop() {
        this.isRunning = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
        window.removeEventListener('keydown', this.boundOnKeyDown);

        const canvas = this.renderer.canvas;
        canvas.removeEventListener('pointerdown', this.boundPointerDown);
        canvas.removeEventListener('pointermove', this.boundPointerMove);
        canvas.removeEventListener('pointerup', this.boundPointerUp);
        canvas.removeEventListener('pointercancel', this.boundPointerCancel);
        this.activePointers.clear();

        this.audio.stopMusic();
        this.input.stopListening();
    }

    pause() {
        if (!this.isRunning || this.isPaused) return;
        this.isPaused = true;
        this.audio.pauseMusic();
    }

    resume() {
        if (!this.isRunning || !this.isPaused) return;
        this.isPaused = false;
        this.lastFrameTime = performance.now();
        this.audio.resumeMusic();
        this.animationFrameId = requestAnimationFrame(this.loop);
    }

    onKeyDown(e) {
        if (!this.isRunning) return;

        // Mod hotkeys (e.g. ']' for autopilot, '[' for cheats, '+/-' for speed)
        modSystem.executeHook('onKeyPress', e, this.state, this);

        // Fast-forward countdown with Space
        if (this.state && this.state.countdown > 0.4 && (e.key === ' ' || e.code === 'Space')) {
            this.state.countdown = 0.3;
        }

        // Restart on Game Over screen
        if (this.state && this.state.failed && this.state.gameOverTimer > 0.4) {
            if (e.key === 'r' || e.key === 'R' || e.key === 'к' || e.key === 'К') {
                this.start(this.state.level);
            }
        }
    }

    loop(currentTime) {
        if (!this.isRunning) return;

        const dt = Math.min((currentTime - this.lastFrameTime) / 1000, 0.1);
        this.lastFrameTime = currentTime;

        if (!this.isPaused) {
            this.update(dt);
        }

        const nowMs = this.state.countdownDone ? this.audio.getCurrentSongTimeMs() : 0;
        this.renderer.render(this.state, nowMs, this.particlePool, this);

        if (this.isRunning) {
            this.animationFrameId = requestAnimationFrame(this.loop);
        }
    }

    update(dt) {
        const state = this.state;
        const level = state.level;

        // 0. Update pre-game countdown (3 - 2 - 1 - GO!)
        if (state.countdown > 0) {
            state.countdown -= dt;
            if (state.countdown <= 0) {
                state.countdownDone = true;
                if (level.audio) {
                    this.audio.playMusic(0);
                }
            }
            return;
        }

        // Handle Failed / Game Over animation
        if (state.failed) {
            state.gameOverTimer += dt;
            for (const frag of state.fragments) {
                frag.x += frag.vx * dt;
                frag.y += frag.vy * dt;
                frag.life -= dt * 0.8;
            }
            return;
        }

        const nowMs = this.audio.getCurrentSongTimeMs();

        // 1. Update track glow from held sides
        for (const side of ['left', 'top', 'right', 'bottom', 'top_left', 'top_right', 'bottom_left', 'bottom_right']) {
            if (this.input.isSideHeld(side) || (state.heldTouchSides && state.heldTouchSides.has(side))) {
                state.trackGlow[side] = Math.min(1.0, (state.trackGlow[side] || 0) + dt * 10);
            } else {
                state.trackGlow[side] = Math.max(0, (state.trackGlow[side] || 0) - dt * 6);
            }
        }

        // 2. Decay beat glow intensity
        if (state.beatGlowIntensity > 0) {
            state.beatGlowIntensity = Math.max(0, state.beatGlowIntensity - dt * 2.5);
        }

        // 3. Process level events (effect_on, effect_off, zoom, rotate)
        if (level.events) {
            while (state.nextEventIdx < level.events.length && nowMs >= level.events[state.nextEventIdx].time_ms) {
                const ev = level.events[state.nextEventIdx];
                if (ev.type === 'effect_on' && ev.name) {
                    state.activeEffects.add(ev.name);
                } else if (ev.type === 'effect_off' && ev.name) {
                    state.activeEffects.delete(ev.name);
                } else if (ev.type === 'zoom' && ev.value) {
                    state.camZoom = ev.value;
                } else if (ev.type === 'rotate' && ev.value !== undefined) {
                    state.camAngle = ev.value;
                }
                state.nextEventIdx++;
            }
        }

        // 4. Spawn upcoming notes
        while (state.nextNoteIdx < level.notes.length) {
            const note = level.notes[state.nextNoteIdx];
            const spawnLead = level.approach_ms;
            if (nowMs >= note.time_ms - spawnLead) {
                state.activeNotes.push(new ActiveNote(note, level.approach_ms));
                state.nextNoteIdx++;
            } else {
                break;
            }
        }

        // 5. Execute mod hooks (e.g. Autopilot bot)
        modSystem.executeHook('onGameUpdate', state, dt, nowMs, this);

        // 6. Process Player Inputs
        const inputEvents = this.input.pollEvents();
        for (let i = 0; i < inputEvents.length; i++) {
            const evt = inputEvents[i];
            if (evt.type === 'down') {
                this.processHit(evt.side, nowMs);
            } else if (evt.type === 'up') {
                this.processRelease(evt.side, nowMs);
            }
        }

        // 7. Update ongoing Hold Notes
        for (let i = 0; i < state.activeNotes.length; i++) {
            const an = state.activeNotes[i];
            if (!an.is_hold || !an.hold_started || an.hit || an.missed) continue;

            const totalDuration = an.end_time_ms - an.arrive_time_ms;
            const elapsedHold = nowMs - an.arrive_time_ms;
            an.hold_progress = Math.max(0, Math.min(1, elapsedHold / totalDuration));

            // Pulse center during hold
            state.pulseTimer = 0.1;
            if (Math.random() < 0.3) {
                this.spawnParticles(CENTER, CENTER, an.note.side, 2, 100, 0.2);
            }

            // Successfully completed hold!
            if (nowMs >= an.end_time_ms - level.hit_window_ms) {
                an.hit = true;
                an.hold_completed = true;
                state.hits++;
                state.score += 300;
                state.combo++;
                state.bestCombo = Math.max(state.bestCombo, state.combo);
                state.addJudgement('HOLD OK', COLORS.judgement['HOLD OK']);
                this.spawnParticles(CENTER, CENTER, an.note.side, 20, 240, 0.4);
                this.audio.playSfx('perfect');
            }
        }

        // 8. Auto-miss overdue notes
        for (let i = 0; i < state.activeNotes.length; i++) {
            const an = state.activeNotes[i];
            if (an.hit || an.missed) continue;

            if (an.is_hold) {
                // If hold wasn't even started and the head is past hit window
                if (!an.hold_started && nowMs > an.arrive_time_ms + level.hit_window_ms) {
                    an.missed = true;
                    state.combo = 0;
                    state.stats.miss++;
                    this.applyDamage(10);
                    state.addJudgement('MISS', COLORS.judgement.MISS);
                    this.audio.playSfx('miss');
                }
            } else {
                // Tap note
                if (nowMs > an.arrive_time_ms + level.hit_window_ms) {
                    an.missed = true;
                    if (!an.note.is_fake) {
                        state.combo = 0;
                        state.stats.miss++;
                        this.applyDamage(10);
                        state.addJudgement('MISS', COLORS.judgement.MISS);
                        this.audio.playSfx('miss');
                    }
                }
            }
        }

        // 9. Clean up old finished notes
        if (state.activeNotes.length > 50) {
            state.activeNotes = state.activeNotes.filter(an => {
                if (an.hit || an.missed) {
                    return nowMs < an.end_time_ms + 1000;
                }
                return true;
            });
        }

        // 10. Update Particles
        this.particlePool.forEachActive(p => p.update(dt));

        // 11. Update Judgements decay
        for (let i = state.judgements.length - 1; i >= 0; i--) {
            const j = state.judgements[i];
            j.life -= dt;
            if (j.life <= 0) {
                state.judgements.splice(i, 1);
            }
        }

        // 12. Update Screen Shake & Juice Timers
        if (state.shakeTimer > 0) state.shakeTimer -= dt;
        if (state.pulseTimer > 0) state.pulseTimer -= dt;
        if (state.flashTimer > 0) state.flashTimer -= dt;

        // 13. Check End Conditions
        if (state.failed) {
            // Let the Canvas Game Over screen render!
            this.audio.pauseMusic();
            return;
        }

        if (state.nextNoteIdx >= level.notes.length &&
            state.activeNotes.every(an => an.hit || an.missed) &&
            nowMs >= state.lastNoteEndTimeMs + 1000) {
            this.state.finished = true;
            this.stop();
            if (this.onFinishCallback) this.onFinishCallback(state);
        }
    }

    applyDamage(amount) {
        const finalAmount = modSystem.executeHook('onDamage', amount, this.state);
        if (finalAmount !== undefined && finalAmount <= 0) return;
        this.state.applyDamage(amount);
    }

    processHit(side, nowMs) {
        const state = this.state;
        if (!state || state.failed) return;
        const level = state.level;

        // Trigger Beat Glow pulse on note hit
        state.beatGlowIntensity = Math.min(1.0, state.beatGlowIntensity + 0.5);

        // Check slide follow-up first
        if (state.pendingSlideTarget && nowMs <= state.pendingSlideExpireMs && side === state.pendingSlideTarget) {
            state.pendingSlideTarget = null;
            state.score += 150;
            state.combo++;
            state.bestCombo = Math.max(state.bestCombo, state.combo);
            state.addJudgement('SLIDE!', COLORS.judgement.SLIDE);
            this.spawnParticles(CENTER, CENTER, side, 16, 260, 0.4);
            this.audio.playSfx('good');
            return;
        }

        // Find candidate note
        let bestNote = null;
        let bestDiff = Infinity;

        for (let i = 0; i < state.activeNotes.length; i++) {
            const an = state.activeNotes[i];
            if (an.hit || an.missed) continue;
            if (an.note.side !== side) continue;

            const diff = Math.abs(an.arrive_time_ms - nowMs);
            if (diff <= level.hit_window_ms && diff < bestDiff) {
                bestDiff = diff;
                bestNote = an;
            }
        }

        if (!bestNote) return;

        // Handle Fake Note hit
        if (bestNote.note.is_fake) {
            bestNote.hit = true;
            state.combo = 0;
            state.stats.fakeHit++;
            this.applyDamage(20);
            state.addJudgement('FAKE!', COLORS.judgement.FAKE);
            this.audio.playSfx('bad');
            return;
        }

        // Start hold note
        if (bestNote.is_hold) {
            bestNote.hold_started = true;
            bestNote.hold_side = side;
            state.pulseTimer = 0.15;
            state.addJudgement('HOLD START', COLORS.judgement['HOLD START']);
            this.spawnParticles(CENTER, CENTER, side, 12, 200, 0.3);
            this.audio.playSfx('hit');
            return;
        }

        // Regular tap note scoring
        bestNote.hit = true;
        state.hits++;
        state.pulseTimer = 0.15;

        let points = 100;
        let judge = 'GOOD';
        let sfx = 'good';

        if (bestDiff <= level.hit_window_ms * 0.25) {
            points = 300;
            judge = 'PERFECT';
            sfx = 'perfect';
            state.stats.perfect++;
        } else if (bestDiff <= level.hit_window_ms * 0.5) {
            points = 200;
            judge = 'GREAT';
            sfx = 'good';
            state.stats.great++;
        } else {
            points = 100;
            judge = 'GOOD';
            sfx = 'hit';
            state.stats.good++;
        }

        state.combo++;
        state.bestCombo = Math.max(state.bestCombo, state.combo);
        state.score += points;
        state.addJudgement(judge, COLORS.judgement[judge]);

        // Trigger mod hook on hit
        modSystem.executeHook('onHit', bestNote.note, judge, state);

        // Trigger combo sound milestone
        if (state.combo > 0 && state.combo % 50 === 0) {
            this.audio.playSfx('combo');
        } else {
            this.audio.playSfx(sfx);
        }

        // Spawn particles
        this.spawnParticles(CENTER, CENTER, side, judge === 'PERFECT' ? 20 : 12, 240, 0.35);

        // Slide mechanic arming
        if (bestNote.note.note_type === 'slide' && bestNote.note.slide_target) {
            state.pendingSlideTarget = bestNote.note.slide_target;
            state.pendingSlideExpireMs = nowMs + 180;
        }
    }

    processRelease(side, nowMs) {
        const state = this.state;
        if (!state) return;
        const level = state.level;

        for (let i = 0; i < state.activeNotes.length; i++) {
            const an = state.activeNotes[i];
            if (!an.is_hold || !an.hold_started || an.hit || an.missed) continue;
            if (an.hold_side !== side) continue;

            // Early release before end window (main.py line 1453)
            if (nowMs < an.end_time_ms - level.hit_window_ms) {
                an.missed = true;
                state.combo = 0;
                state.stats.miss++;
                this.applyDamage(10);
                state.addJudgement('MISS', COLORS.judgement.MISS);
                if (this.audio) this.audio.playSfx('miss');
            }
        }
    }

    spawnParticles(x, y, sideOrColorKey, count, speed, life) {
        const rgb = this.colorRgbMap[sideOrColorKey] || [255, 255, 255];
        const hex = COLORS.note[sideOrColorKey] || '#ffffff';
        for (let i = 0; i < count; i++) {
            const p = this.particlePool.get();
            p.init(x, y, hex, rgb, Math.random() * 5 + 3, speed, life);
        }
    }

    getVirtualCoords(e) {
        const canvas = this.renderer.canvas;
        const rect = canvas.getBoundingClientRect();
        const px = e.clientX - rect.left;
        const py = e.clientY - rect.top;
        const w = canvas.width;
        const h = canvas.height;
        const scale = Math.min(w / VIRTUAL_SIZE, h / VIRTUAL_SIZE, 1.2);
        const offsetX = (w - VIRTUAL_SIZE * scale) / 2;
        const offsetY = (h - VIRTUAL_SIZE * scale) / 2;
        const vx = (px - offsetX) / scale;
        const vy = (py - offsetY) / scale;
        return { vx, vy };
    }

    getSideFromVirtualCoords(vx, vy, hasDiagonals) {
        const dx = vx - CENTER;
        const dy = vy - CENTER;
        const dist = Math.hypot(dx, dy);
        if (dist < 35) return null; // Inside center ring

        const theta = Math.atan2(dy, dx); // [-PI, PI]
        const a = theta < 0 ? theta + Math.PI * 2 : theta; // [0, 2*PI)

        if (!hasDiagonals) {
            // 4 sectors
            if (a >= Math.PI * 7/4 || a < Math.PI / 4) return 'right';
            if (a >= Math.PI / 4 && a < Math.PI * 3/4) return 'bottom';
            if (a >= Math.PI * 3/4 && a < Math.PI * 5/4) return 'left';
            return 'top';
        } else {
            // 8 sectors
            if (a >= Math.PI * 15/8 || a < Math.PI / 8) return 'right';
            if (a >= Math.PI / 8 && a < Math.PI * 3/8) return 'bottom_right';
            if (a >= Math.PI * 3/8 && a < Math.PI * 5/8) return 'bottom';
            if (a >= Math.PI * 5/8 && a < Math.PI * 7/8) return 'bottom_left';
            if (a >= Math.PI * 7/8 && a < Math.PI * 9/8) return 'left';
            if (a >= Math.PI * 9/8 && a < Math.PI * 11/8) return 'top_left';
            if (a >= Math.PI * 11/8 && a < Math.PI * 13/8) return 'top';
            return 'top_right';
        }
    }

    onPointerDown(e) {
        if (!this.isRunning || !this.state) return;

        // Fast-forward countdown on tap
        if (this.state.countdown > 0.4) {
            this.state.countdown = 0.3;
            return;
        }

        // Tap to restart on Game Over screen
        if (this.state.failed && this.state.gameOverTimer > 0.4) {
            this.start(this.state.level);
            return;
        }

        const { vx, vy } = this.getVirtualCoords(e);
        const hasDiagonals = this.state.level?.notes?.some(n => 
            ['top_left', 'top_right', 'bottom_left', 'bottom_right'].includes(n.side)
        );
        const side = this.getSideFromVirtualCoords(vx, vy, hasDiagonals);
        if (!side) return;

        this.activePointers.set(e.pointerId, {
            side,
            startX: vx,
            startY: vy,
            startTime: performance.now()
        });

        if (this.state.heldTouchSides) {
            this.state.heldTouchSides.add(side);
        }
        this.input.triggerSideDown(side);

        if (navigator.vibrate) {
            try { navigator.vibrate(15); } catch(err) {}
        }
    }

    onPointerMove(e) {
        if (!this.isRunning || !this.state) return;
        const pt = this.activePointers.get(e.pointerId);
        if (!pt) return;

        const { vx, vy } = this.getVirtualCoords(e);

        // Slide swipe gesture detection
        if (this.state.pendingSlideTarget) {
            const dx = vx - pt.startX;
            const dy = vy - pt.startY;
            if (Math.hypot(dx, dy) > 28) {
                const hasDiagonals = this.state.level?.notes?.some(n => 
                    ['top_left', 'top_right', 'bottom_left', 'bottom_right'].includes(n.side)
                );
                const swipeSide = this.getSideFromVirtualCoords(vx, vy, hasDiagonals);
                if (swipeSide === this.state.pendingSlideTarget) {
                    const nowMs = this.audio.getCurrentSongTimeMs();
                    this.processHit(swipeSide, nowMs);
                }
            }
        }
    }

    onPointerUp(e) {
        if (!this.activePointers.has(e.pointerId)) return;
        const pt = this.activePointers.get(e.pointerId);
        this.activePointers.delete(e.pointerId);

        let stillHeld = false;
        for (const other of this.activePointers.values()) {
            if (other.side === pt.side) {
                stillHeld = true;
                break;
            }
        }

        if (!stillHeld && this.state && this.state.heldTouchSides) {
            this.state.heldTouchSides.delete(pt.side);
        }

        this.input.triggerSideUp(pt.side);
    }

    onPointerCancel(e) {
        this.onPointerUp(e);
    }
}
