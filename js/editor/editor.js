/**
 * 1-to-1 exact reproduction of KeyY Level Editor (game/editor.py) in pure HTML5 Canvas.
 * Implements interactive timeline, BPM grid, live preview pane, audio playback,
 * hold note resizing, drag-and-drop, recording, tabs, effects, undo/redo, and JSON export.
 */

import { NoteData, LevelData } from '../game/level.js';

export const COLOR_BG = '#10121c';
export const COLOR_TEXT = '#e6e6e6';
export const COLOR_ACCENT = 'rgb(80, 150, 255)';
export const COLOR_TIMELINE = 'rgb(60, 70, 100)';
export const COLOR_GRID = 'rgb(60, 90, 140)';
export const COLOR_PREVIEW_CENTER = '#f0f0ff';
export const COLOR_PREVIEW_NOTE = {
    'left': '#78c8ff',
    'top': '#78ffa0',
    'right': '#ffaa78',
    'bottom': '#ff78c8'
};

export const EFFECT_LIST = [
    'invert', 'grayscale', 'blur', 'vignette', 'chroma_shift',
    'pixelate', 'desaturate', 'contrast', 'glow_boost'
];

export const KEY_TO_SIDE = {
    // WASD (English)
    'KeyA': 'left', 'KeyW': 'top', 'KeyD': 'right', 'KeyS': 'bottom',
    'a': 'left', 'w': 'top', 'd': 'right', 's': 'bottom',
    'A': 'left', 'W': 'top', 'D': 'right', 'S': 'bottom',

    // Russian layout (Ф Ц В Ы)
    'ф': 'left', 'ц': 'top', 'в': 'right', 'ы': 'bottom',
    'Ф': 'left', 'Ц': 'top', 'В': 'right', 'Ы': 'bottom',

    // Arrow keys
    'ArrowLeft': 'left', 'ArrowUp': 'top', 'ArrowRight': 'right', 'ArrowDown': 'bottom',

    // IJKL
    'KeyJ': 'left', 'KeyI': 'top', 'KeyL': 'right', 'KeyK': 'bottom',
    'j': 'left', 'i': 'top', 'l': 'right', 'k': 'bottom',
    'J': 'left', 'I': 'top', 'L': 'right', 'K': 'bottom',
    'о': 'left', 'ш': 'top', 'д': 'right', 'л': 'bottom',
    'О': 'left', 'Ш': 'top', 'Д': 'right', 'Л': 'bottom',

    // FTHG
    'KeyF': 'left', 'KeyT': 'top', 'KeyH': 'right', 'KeyG': 'bottom',
    'f': 'left', 't': 'top', 'h': 'right', 'g': 'bottom',
    'F': 'left', 'T': 'top', 'H': 'right', 'G': 'bottom',
    'а': 'left', 'е': 'top', 'р': 'right', 'п': 'bottom',
    'А': 'left', 'Е': 'top', 'Р': 'right', 'П': 'bottom',

    // Numpad
    'Numpad4': 'left', 'Numpad8': 'top', 'Numpad6': 'right', 'Numpad5': 'bottom',
    'Numpad2': 'bottom', 'Numpad0': 'bottom', 'Numpad7': 'left', 'Numpad9': 'right',
    'Numpad1': 'left', 'Numpad3': 'right',

    // QWERTY & additional keys matching game/main.py
    'KeyQ': 'left', 'q': 'left', 'Q': 'left', 'й': 'left', 'Й': 'left',
    'KeyE': 'right', 'e': 'right', 'E': 'right', 'у': 'right', 'У': 'right',
    'KeyU': 'top', 'u': 'top', 'U': 'top', 'г': 'top', 'Г': 'top',
    'KeyO': 'right', 'o': 'right', 'O': 'right', 'щ': 'right', 'Щ': 'right',
    'KeyP': 'right', 'p': 'right', 'P': 'right', 'з': 'right', 'З': 'right',
    'KeyZ': 'left', 'z': 'left', 'Z': 'left', 'я': 'left', 'Я': 'left',
    'KeyX': 'bottom', 'x': 'bottom', 'X': 'bottom', 'ч': 'bottom', 'Ч': 'bottom',
    'KeyC': 'right', 'c': 'right', 'C': 'right', 'с': 'right', 'С': 'right',
    'KeyV': 'bottom', 'v': 'bottom', 'V': 'bottom', 'м': 'bottom', 'М': 'bottom',
    'KeyB': 'bottom', 'b': 'bottom', 'B': 'bottom', 'и': 'bottom', 'И': 'bottom',
    'KeyN': 'bottom', 'n': 'bottom', 'N': 'bottom', 'т': 'bottom', 'Т': 'bottom',
    'KeyM': 'right', 'm': 'right', 'M': 'right', 'ь': 'right', 'Ь': 'right'
};

export const KEY_TO_LABEL = {
    'KeyA': 'A', 'a': 'A', 'A': 'A', 'ф': 'A', 'Ф': 'A',
    'KeyW': 'W', 'w': 'W', 'W': 'W', 'ц': 'W', 'Ц': 'W',
    'KeyD': 'D', 'd': 'D', 'D': 'D', 'в': 'D', 'В': 'D',
    'KeyS': 'S', 's': 'S', 'S': 'S', 'ы': 'S', 'Ы': 'S',

    'ArrowLeft': '←', 'ArrowUp': '↑', 'ArrowRight': '→', 'ArrowDown': '↓',

    'KeyJ': 'J', 'j': 'J', 'J': 'J', 'о': 'J', 'О': 'J',
    'KeyI': 'I', 'i': 'I', 'I': 'I', 'ш': 'I', 'Ш': 'I',
    'KeyL': 'L', 'l': 'L', 'L': 'L', 'д': 'L', 'Д': 'L',
    'KeyK': 'K', 'k': 'K', 'K': 'K', 'л': 'K', 'Л': 'K',

    'KeyF': 'F', 'f': 'F', 'F': 'F', 'а': 'F', 'А': 'F',
    'KeyT': 'T', 't': 'T', 'T': 'T', 'е': 'T', 'Е': 'T',
    'KeyH': 'H', 'h': 'H', 'H': 'H', 'р': 'H', 'Р': 'H',
    'KeyG': 'G', 'g': 'G', 'G': 'G', 'п': 'G', 'П': 'G',

    'Numpad4': '4', 'Numpad8': '8', 'Numpad6': '6', 'Numpad5': '5', 'Numpad2': '2',
    'Numpad0': '0', 'Numpad7': '7', 'Numpad9': '9', 'Numpad1': '1', 'Numpad3': '3',

    'KeyQ': 'Q', 'q': 'Q', 'Q': 'Q', 'й': 'Q', 'Й': 'Q',
    'KeyE': 'E', 'e': 'E', 'E': 'E', 'у': 'E', 'У': 'E',
    'KeyU': 'U', 'u': 'U', 'U': 'U', 'г': 'U', 'Г': 'U',
    'KeyO': 'O', 'o': 'O', 'O': 'O', 'щ': 'O', 'Щ': 'O',
    'KeyP': 'P', 'p': 'P', 'P': 'P', 'з': 'P', 'З': 'P',
    'KeyZ': 'Z', 'z': 'Z', 'Z': 'Z', 'я': 'Z', 'Я': 'Z',
    'KeyX': 'X', 'x': 'X', 'X': 'X', 'ч': 'X', 'Ч': 'X',
    'KeyC': 'C', 'c': 'C', 'C': 'C', 'с': 'C', 'С': 'C',
    'KeyV': 'V', 'v': 'V', 'V': 'V', 'м': 'V', 'М': 'V',
    'KeyB': 'B', 'b': 'B', 'B': 'B', 'и': 'B', 'И': 'B',
    'KeyN': 'N', 'n': 'N', 'N': 'N', 'т': 'N', 'Т': 'N',
    'KeyM': 'M', 'm': 'M', 'M': 'M', 'ь': 'M', 'Ь': 'M'
};

export const DISPLAY_FOR_KEY = {
    'left': 'A',
    'top': 'W',
    'right': 'D',
    'bottom': 'S'
};

export function getKeyLabel(code, key, side) {
    if (code && KEY_TO_LABEL[code]) return KEY_TO_LABEL[code];
    if (key && KEY_TO_LABEL[key]) return KEY_TO_LABEL[key];
    if (key && key.length === 1 && /[a-zA-Z0-9]/.test(key)) return key.toUpperCase();
    return DISPLAY_FOR_KEY[side] || 'A';
}

function msToTimeStr(ms) {
    const totalSec = Math.floor(ms / 1000);
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    const cs = Math.floor((ms % 1000) / 10);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}.${String(cs).padStart(2, '0')}`;
}

export class LevelEditor {
    constructor(canvas, audioManager, onExitCallback) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d', { alpha: false });
        this.audio = audioManager;
        this.onExit = onExitCallback;

        // Level metadata
        this.title = 'Custom';
        this.artist = 'You';
        this.audioPath = 'assets/sample.mp3';
        this.bpm = 120.0;
        this.approachMs = 1000;
        this.hitWindowMs = 120;
        this.notes = [];
        this.events = [];
        this.activeEffects = {};
        for (const eff of EFFECT_LIST) this.activeEffects[eff] = false;

        // Transport & playback
        this.playing = false;
        this.recording = false;
        this.baseOffsetMs = 0;
        this.playStartTime = 0;

        // View options
        this.zoom = 0.08;
        this.gridDiv = 4;
        this.metronome = false;
        this.lastBeatPlay = -1;
        this.showHelp = true;

        // Toolbars & tabs
        this.toolbarPage = 'main'; // 'main' | 'controls' | 'effects'
        this.currentNoteType = 'tap'; // 'tap' | 'double' | 'slide'
        this.currentSlideTarget = 'right';

        // Selection & Drag state
        this.selectedIdx = null;
        this.draggingNoteIdx = null;
        this.draggingMode = null; // 'move' | 'resize'
        this.scrubbing = false;
        this.scrubStartX = 0;
        this.scrubStartBase = 0;

        // Active holds when recording
        this.activeHolds = new Map(); // key -> startMs

        // Undo/Redo
        this.undoStack = [];
        this.redoStack = [];

        // Prompt input modal
        this.inputMode = null; // 'title' | 'artist' | 'audio'
        this.inputText = '';
        this.message = '';
        this.messageTimer = 0;

        // Effect insert modal (RMB on timeline)
        this.effectInsert = {
            active: false,
            startTime: 0,
            durationMs: 1000,
            effectIdx: 0,
            x: 0,
            y: 0
        };

        this.boundOnKeyDown = this.onKeyDown.bind(this);
        this.boundOnKeyUp = this.onKeyUp.bind(this);
        this.boundOnMouseMove = this.onMouseMove.bind(this);
        this.boundOnMouseDown = this.onMouseDown.bind(this);
        this.boundOnMouseUp = this.onMouseUp.bind(this);

        this.initInput();
    }

    initInput() {
        window.addEventListener('keydown', this.boundOnKeyDown);
        window.addEventListener('keyup', this.boundOnKeyUp);
        window.addEventListener('mousemove', this.boundOnMouseMove);
        window.addEventListener('mousedown', this.boundOnMouseDown);
        window.addEventListener('mouseup', this.boundOnMouseUp);
    }

    destroyInput() {
        window.removeEventListener('keydown', this.boundOnKeyDown);
        window.removeEventListener('keyup', this.boundOnKeyUp);
        window.removeEventListener('mousemove', this.boundOnMouseMove);
        window.removeEventListener('mousedown', this.boundOnMouseDown);
        window.removeEventListener('mouseup', this.boundOnMouseUp);
        this.stopAudio();
    }

    getNowMs() {
        if (!this.playing) {
            return this.baseOffsetMs;
        }
        return this.baseOffsetMs + (performance.now() - this.playStartTime);
    }

    play(rec = false) {
        if (!this.playing) {
            this.playStartTime = performance.now();
            this.playing = true;
            this.recording = rec;
            this.audio.playMusic(this.baseOffsetMs);
        }
    }

    pause() {
        if (this.playing) {
            this.baseOffsetMs = this.getNowMs();
            this.playing = false;
            this.recording = false;
            this.audio.pauseMusic();
        }
    }

    stopAudio() {
        this.playing = false;
        this.recording = false;
        this.audio.stopMusic();
    }

    saveStateForUndo() {
        this.redoStack.length = 0;
        this.undoStack.push(JSON.parse(JSON.stringify(this.notes)));
        if (this.undoStack.length > 50) this.undoStack.shift();
    }

    undo() {
        if (this.undoStack.length === 0) return;
        this.redoStack.push(JSON.parse(JSON.stringify(this.notes)));
        this.notes = this.undoStack.pop();
        this.selectedIdx = null;
        this.setMessage('Undo');
    }

    redo() {
        if (this.redoStack.length === 0) return;
        this.undoStack.push(JSON.parse(JSON.stringify(this.notes)));
        this.notes = this.redoStack.pop();
        this.selectedIdx = null;
        this.setMessage('Redo');
    }

    setMessage(msg, timeMs = 2000) {
        this.message = msg;
        this.messageTimer = timeMs;
    }

    timeToX(t, centerX) {
        return Math.floor((t - this.getNowMs()) * this.zoom + centerX);
    }

    xToTime(x, centerX) {
        return Math.floor((x - centerX) / this.zoom + this.getNowMs());
    }

    getCanvasPos(e) {
        const rect = this.canvas.getBoundingClientRect();
        return {
            x: (e.clientX - rect.left) * (this.canvas.width / rect.width),
            y: (e.clientY - rect.top) * (this.canvas.height / rect.height)
        };
    }

    hitTestNote(mx, my, centerX, w, h) {
        const timelineH = Math.floor(h * 0.25);
        const by = h - timelineH + 40;
        const bw = 44;
        const bh = 28;

        if (my < h - timelineH || my > h) return null;

        for (let i = this.notes.length - 1; i >= 0; i--) {
            const n = this.notes[i];
            const x = this.timeToX(n.time_ms, centerX);

            // Resize handle on hold tail
            if (n.duration_ms > 0) {
                const endX = this.timeToX(n.time_ms + n.duration_ms, centerX);
                if (mx >= endX - 10 && mx <= endX + 10 && my >= by - 14 && my <= by + 14) {
                    return { idx: i, mode: 'resize' };
                }
            }

            // Note body
            if (mx >= x - bw/2 && mx <= x + bw/2 && my >= by - bh/2 && my <= by + bh/2) {
                return { idx: i, mode: 'move' };
            }
        }
        return null;
    }

    onKeyDown(e) {
        // Text input prompt mode
        if (this.inputMode) {
            if (e.key === 'Escape') {
                this.inputMode = null;
            } else if (e.key === 'Enter') {
                const val = this.inputText.trim();
                if (this.inputMode === 'title' && val) this.title = val;
                if (this.inputMode === 'artist' && val) this.artist = val;
                if (this.inputMode === 'audio' && val) {
                    this.audioPath = val;
                    this.audio.loadMusic(val).catch(() => {});
                }
                this.inputMode = null;
                this.setMessage('Updated');
            } else if (e.key === 'Backspace') {
                this.inputText = this.inputText.slice(0, -1);
            } else if (e.key.length === 1) {
                this.inputText += e.key;
            }
            return;
        }

        // Effect insert modal
        if (this.effectInsert.active) {
            if (e.key === 'Escape') {
                this.effectInsert.active = false;
            } else if (e.key === 'ArrowLeft' || e.key === 'a') {
                this.effectInsert.effectIdx = (this.effectInsert.effectIdx - 1 + EFFECT_LIST.length) % EFFECT_LIST.length;
            } else if (e.key === 'ArrowRight' || e.key === 'd') {
                this.effectInsert.effectIdx = (this.effectInsert.effectIdx + 1) % EFFECT_LIST.length;
            } else if (e.key === '-' || e.key === '_') {
                this.effectInsert.durationMs = Math.max(100, this.effectInsert.durationMs - 100);
            } else if (e.key === '=' || e.key === '+') {
                this.effectInsert.durationMs = Math.min(30000, this.effectInsert.durationMs + 100);
            } else if (e.key === 'Enter') {
                const eff = EFFECT_LIST[this.effectInsert.effectIdx];
                const startT = this.effectInsert.startTime;
                const dur = this.effectInsert.durationMs;
                this.events.push({ time_ms: startT, type: 'effect_on', name: eff });
                this.events.push({ time_ms: startT + dur, type: 'effect_off', name: eff });
                this.events.sort((a, b) => a.time_ms - b.time_ms);
                this.setMessage(`Added ${eff} ${dur}ms @ ${startT}`);
                this.effectInsert.active = false;
            }
            return;
        }

        // Standard hotkeys
        if (e.key === 'Escape') {
            this.stopAudio();
            if (this.onExit) this.onExit();
            return;
        }

        if (e.key === 'F1') {
            this.showHelp = !this.showHelp;
            return;
        }

        if (e.key === 'Space' || e.code === 'Space') {
            e.preventDefault();
            if (this.playing) {
                this.pause();
            } else {
                this.play(this.recording);
            }
            return;
        }

        if (e.key === 'r' || e.key === 'R' || e.key === 'к' || e.key === 'К') {
            if (this.playing) {
                this.recording = !this.recording;
                this.setMessage(`Recording: ${this.recording ? 'ON' : 'OFF'}`);
            } else {
                this.play(true);
            }
            return;
        }

        // Undo / Redo
        if (e.ctrlKey || e.metaKey) {
            if (e.key === 'z' || e.key === 'Z' || e.key === 'я' || e.key === 'Я') {
                e.preventDefault();
                if (e.shiftKey) this.redo();
                else this.undo();
                return;
            }
            if (e.key === 'y' || e.key === 'Y' || e.key === 'н' || e.key === 'Н') {
                e.preventDefault();
                this.redo();
                return;
            }
            if (e.key === 's' || e.key === 'S' || e.key === 'ы' || e.key === 'Ы') {
                e.preventDefault();
                this.exportJson();
                return;
            }
        }

        // Arrow keys: scrub (only when paused without Shift)
        if (!this.playing) {
            if (e.key === 'ArrowLeft' && !e.shiftKey) {
                this.baseOffsetMs = Math.max(0, this.getNowMs() - 1000);
                this.stopAudio();
                return;
            }
            if (e.key === 'ArrowRight' && !e.shiftKey) {
                this.baseOffsetMs = this.getNowMs() + 1000;
                this.stopAudio();
                return;
            }
        }

        // Zoom +/-
        if (e.key === '=' || e.key === '+') {
            this.zoom = Math.min(0.5, this.zoom * 1.25);
            return;
        }
        if (e.key === '-' || e.key === '_') {
            this.zoom = Math.max(0.02, this.zoom / 1.25);
            return;
        }

        // Grid divisions [ / ]
        if (e.key === '[') {
            this.gridDiv = Math.max(1, this.gridDiv - 1);
            this.setMessage(`Grid: ${this.gridDiv}`);
            return;
        }
        if (e.key === ']') {
            this.gridDiv = Math.min(16, this.gridDiv + 1);
            this.setMessage(`Grid: ${this.gridDiv}`);
            return;
        }

        // Metronome
        if (e.key === 'm' || e.key === 'M' || e.key === 'ь' || e.key === 'Ь') {
            this.metronome = !this.metronome;
            this.setMessage(`Metronome: ${this.metronome ? 'ON' : 'OFF'}`);
            return;
        }

        // Note type hotkeys (1: Tap, 2: Double, 3: Slide)
        if (e.key === '1') {
            this.currentNoteType = 'tap';
            this.setMessage('Note type: TAP');
            return;
        }
        if (e.key === '2') {
            this.currentNoteType = 'double';
            this.setMessage('Note type: DOUBLE');
            return;
        }
        if (e.key === '3') {
            this.currentNoteType = 'slide';
            this.setMessage('Note type: SLIDE (target WASD / T)');
            return;
        }

        // Cycle slide target with 't' or 'T'
        if (e.key === 't' || e.key === 'T' || e.key === 'е' || e.key === 'Е') {
            const order = ['left', 'top', 'right', 'bottom'];
            const cur = this.currentSlideTarget || 'right';
            this.currentSlideTarget = order[(order.indexOf(cur) + 1) % order.length];
            this.setMessage(`Slide target: ${this.currentSlideTarget.toUpperCase()}`);
            if (this.selectedIdx !== null && this.selectedIdx < this.notes.length) {
                if (this.notes[this.selectedIdx].note_type === 'slide') {
                    this.notes[this.selectedIdx].slide_target = this.currentSlideTarget;
                }
            }
            return;
        }

        // Delete selected note
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (this.selectedIdx !== null && this.selectedIdx >= 0 && this.selectedIdx < this.notes.length) {
                this.saveStateForUndo();
                this.notes.splice(this.selectedIdx, 1);
                this.selectedIdx = null;
                this.setMessage('Note deleted');
            }
            return;
        }

        // Game keys note placement (WASD, Arrows, IJKL, FTHG, Numpad, Cyrillic, etc.)
        const side = KEY_TO_SIDE[e.code] || KEY_TO_SIDE[e.key];
        if (side) {
            const holdKey = e.code || e.key;

            // Prevent rapid key-repeat duplicates while key is held down
            if (e.repeat || this.activeHolds.has(holdKey)) return;

            const label = getKeyLabel(e.code, e.key, side);

            if (this.playing) {
                // ALWAYS record and place note during playback, even without pressing R
                const now = this.getNowMs();
                this.activeHolds.set(holdKey, now);
                this.recording = true; // Auto-activate recording flag
                this.saveStateForUndo();

                const newNote = {
                    time_ms: Math.floor(now),
                    side: side,
                    key: label,
                    duration_ms: 0,
                    is_fake: false,
                    note_type: this.currentNoteType,
                    slide_target: this.currentNoteType === 'slide' ? (this.currentSlideTarget || (side === 'left' ? 'right' : 'left')) : null
                };
                this.notes.push(newNote);
                this.notes.sort((a, b) => a.time_ms - b.time_ms);
                this.selectedIdx = this.notes.indexOf(newNote);
                this.audio.playSfx('hit');
                this.setMessage(`Recorded ${side.toUpperCase()} (${label}) @ ${Math.floor(now)}ms`, 1000);
            } else {
                // When paused
                if (this.selectedIdx !== null && this.selectedIdx >= 0 && this.selectedIdx < this.notes.length) {
                    // Change direction of selected note
                    this.saveStateForUndo();
                    this.notes[this.selectedIdx].side = side;
                    this.notes[this.selectedIdx].key = label;
                    this.audio.playSfx('hit');
                    this.setMessage(`Changed note to ${side.toUpperCase()} (${label})`, 1200);
                } else {
                    // Place note at timeline cursor snapped to BPM grid
                    let tnew = this.baseOffsetMs;
                    if (this.bpm > 0) {
                        const beatMs = 60000.0 / this.bpm;
                        const divMs = beatMs / this.gridDiv;
                        tnew = Math.round(tnew / divMs) * divMs;
                    }
                    this.saveStateForUndo();
                    const newNote = {
                        time_ms: Math.floor(tnew),
                        side: side,
                        key: label,
                        duration_ms: 0,
                        is_fake: false,
                        note_type: this.currentNoteType,
                        slide_target: this.currentNoteType === 'slide' ? (this.currentSlideTarget || (side === 'left' ? 'right' : 'left')) : null
                    };
                    this.notes.push(newNote);
                    this.notes.sort((a, b) => a.time_ms - b.time_ms);
                    this.selectedIdx = this.notes.indexOf(newNote);
                    this.audio.playSfx('hit');
                    this.setMessage(`Placed ${side.toUpperCase()} (${label}) @ ${Math.floor(tnew)}ms`, 1200);
                }
            }
        }
    }

    onKeyUp(e) {
        // Finalize hold note duration (always active, whether manually recording or not)
        const holdKey = e.code || e.key;
        if (this.activeHolds.has(holdKey)) {
            const startT = this.activeHolds.get(holdKey);
            this.activeHolds.delete(holdKey);
            const now = this.getNowMs();
            const dur = Math.floor(now - startT);
            if (dur >= 120) {
                // Find matching note and assign duration
                const side = KEY_TO_SIDE[e.code] || KEY_TO_SIDE[e.key];
                for (let i = this.notes.length - 1; i >= 0; i--) {
                    const n = this.notes[i];
                    if (n.side === side && Math.abs(n.time_ms - Math.floor(startT)) <= 50) {
                        n.duration_ms = dur;
                        n.note_type = 'hold';
                        this.setMessage(`Hold note: ${dur}ms`, 1200);
                        break;
                    }
                }
            }
        }
    }

    onMouseMove(e) {
        const pos = this.getCanvasPos(e);
        const w = this.canvas.width;
        const centerX = w / 2;

        if (this.scrubbing) {
            const dx = pos.x - this.scrubStartX;
            this.baseOffsetMs = Math.max(0, Math.floor(this.scrubStartBase - dx / this.zoom));
            return;
        }

        if (this.draggingNoteIdx !== null && this.draggingNoteIdx < this.notes.length) {
            const n = this.notes[this.draggingNoteIdx];
            if (this.draggingMode === 'move') {
                let newT = this.xToTime(pos.x, centerX);
                if (this.bpm > 0) {
                    const beatMs = 60000.0 / this.bpm;
                    const divMs = beatMs / this.gridDiv;
                    newT = Math.round(newT / divMs) * divMs;
                }
                n.time_ms = Math.max(0, Math.floor(newT));
                this.notes.sort((a, b) => a.time_ms - b.time_ms);
                this.draggingNoteIdx = this.notes.indexOf(n);
                this.selectedIdx = this.draggingNoteIdx;
            } else if (this.draggingMode === 'resize') {
                const endT = this.xToTime(pos.x, centerX);
                n.duration_ms = Math.max(0, Math.floor(endT - n.time_ms));
            }
        }
    }

    onMouseDown(e) {
        const pos = this.getCanvasPos(e);
        const mx = pos.x;
        const my = pos.y;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const centerX = w / 2;
        const timelineH = Math.floor(h * 0.25);

        // Right-Click (delete note or open effect modal)
        if (e.button === 2) {
            e.preventDefault();
            const hit = this.hitTestNote(mx, my, centerX, w, h);
            if (hit) {
                this.saveStateForUndo();
                this.notes.splice(hit.idx, 1);
                this.selectedIdx = null;
                this.setMessage('Note deleted');
            } else if (my >= h - timelineH) {
                const clickedTime = Math.max(0, this.xToTime(mx, centerX));
                this.effectInsert.active = true;
                this.effectInsert.startTime = clickedTime;
                this.effectInsert.x = mx;
                this.effectInsert.y = my;
                this.stopAudio();
            }
            return;
        }

        if (e.button !== 0) return;

        // 1. Check Tabs click
        const tabY = 50;
        let tx = 16;
        for (const [caption, page] of [["Main", 'main'], ["Controls", 'controls'], ["Effects", 'effects']]) {
            const wbtn = 120;
            if (mx >= tx && mx <= tx + wbtn && my >= tabY && my <= tabY + 28) {
                this.toolbarPage = page;
                return;
            }
            tx += wbtn + 8;
        }

        // 2. Check Toolbar Buttons click
        const btns = this.getToolbarButtons(w);
        for (const btn of btns) {
            if (mx >= btn.x && mx <= btn.x + btn.w && my >= btn.y && my <= btn.y + btn.h) {
                this.handleToolbarClick(btn.lbl);
                return;
            }
        }

        // 3. Check Bottom Control Pad (A, W, D, S buttons)
        const padH = 90;
        if (my >= h - padH) {
            const keys = [["A","left"], ["W","top"], ["D","right"], ["S","bottom"]];
            const gap = 20;
            const btnW = 80;
            const btnH = 44;
            const totalW = keys.length * btnW + (keys.length - 1) * gap;
            const startX = (w - totalW) / 2;
            const btnY = h - padH / 2 - btnH / 2;

            for (let idx = 0; idx < keys.length; idx++) {
                const bx = startX + idx * (btnW + gap);
                if (mx >= bx && mx <= bx + btnW && my >= btnY && my <= btnY + btnH) {
                    let tnew = this.getNowMs();
                    if (this.bpm > 0) {
                        const beatMs = 60000.0 / this.bpm;
                        const divMs = beatMs / this.gridDiv;
                        tnew = Math.round(tnew / divMs) * divMs;
                    }
                    this.saveStateForUndo();
                    const newNote = {
                        time_ms: Math.floor(tnew),
                        side: keys[idx][1],
                        key: keys[idx][0],
                        duration_ms: 0,
                        note_type: this.currentNoteType,
                        slide_target: this.currentNoteType === 'slide' ? this.currentSlideTarget : null
                    };
                    this.notes.push(newNote);
                    this.notes.sort((a, b) => a.time_ms - b.time_ms);
                    this.selectedIdx = this.notes.indexOf(newNote);
                    this.audio.playSfx('hit');
                    return;
                }
            }
        }

        // 4. Check Timeline Notes Drag & Click
        const hit = this.hitTestNote(mx, my, centerX, w, h);
        if (hit) {
            this.selectedIdx = hit.idx;
            this.draggingNoteIdx = hit.idx;
            this.draggingMode = hit.mode;
            this.saveStateForUndo();
            return;
        }

        // 5. Timeline Scrubbing click
        if (my >= h - timelineH) {
            this.scrubbing = true;
            this.scrubStartX = mx;
            this.scrubStartBase = this.getNowMs();
            this.baseOffsetMs = Math.max(0, this.xToTime(mx, centerX));
            this.stopAudio();
            return;
        }

        // Deselect if clicked in blank area
        this.selectedIdx = null;
    }

    onMouseUp(e) {
        this.scrubbing = false;
        this.draggingNoteIdx = null;
        this.draggingMode = null;
    }

    getToolbarButtons(w) {
        const buttons = [];
        let x = 16;
        let y = 86;

        if (this.toolbarPage === 'main') {
            const labels = ["Open Audio", "Open Level", "Set Title", "Set Artist", "Save JSON", "Export Level"];
            for (const lbl of labels) {
                const bw = 130;
                buttons.push({ lbl, x, y, w: bw, h: 36 });
                x += bw + 12;
            }
        } else if (this.toolbarPage === 'controls') {
            const labels = [
                this.playing ? "Pause" : "Play",
                this.recording ? "Stop Rec" : "Rec",
                "Stop", "BPM+", "BPM-", "Reset BPM", "Zoom+", "Zoom-", "Grid+", "Grid-",
                this.metronome ? "Metro:ON" : "Metro:OFF", "App+", "App-",
                "Type:Tap(1)", "Type:Double(2)", "Type:Slide(3)"
            ];
            for (const lbl of labels) {
                const bw = 105;
                buttons.push({ lbl, x, y, w: bw, h: 32 });
                x += bw + 8;
                if (x > w - 140) {
                    x = 16;
                    y += 38;
                }
            }
        } else if (this.toolbarPage === 'effects') {
            for (let i = 0; i < EFFECT_LIST.length; i++) {
                const eff = EFFECT_LIST[i];
                const active = this.activeEffects[eff];
                const lbl = `${i+1}:${eff.slice(0, 4)} ${active ? '✓' : ''}`;
                const bw = 100;
                buttons.push({ lbl, eff, x, y, w: bw, h: 32 });
                x += bw + 8;
            }
        }
        return buttons;
    }

    handleToolbarClick(lbl) {
        if (lbl === "Open Audio") {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'audio/*';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                try {
                    const url = URL.createObjectURL(file);
                    await this.audio.loadMusic(url);
                    this.audioPath = file.name;
                    this.setMessage(`Audio loaded: ${file.name}`);
                } catch(err) {
                    alert(`Audio error: ${err.message}`);
                }
            };
            input.click();
        } else if (lbl === "Open Level") {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = '.json';
            input.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                try {
                    const text = await file.text();
                    const data = JSON.parse(text);
                    this.title = data.title || 'Untitled';
                    this.artist = data.artist || 'Unknown';
                    this.approachMs = Number(data.approach_ms) || 1000;
                    this.hitWindowMs = Number(data.hit_window_ms) || 120;
                    this.notes = (data.notes || []).map(n => ({
                        time_ms: n.time_ms || 0,
                        side: n.side || 'left',
                        key: n.key || 'A',
                        duration_ms: n.duration_ms || 0,
                        note_type: n.note_type || (n.duration_ms > 50 ? 'hold' : 'tap'),
                        slide_target: n.slide_target || null
                    }));
                    this.events = data.events || [];
                    this.setMessage(`Level loaded: ${this.title}`);
                } catch(err) {
                    alert(`JSON error: ${err.message}`);
                }
            };
            input.click();
        } else if (lbl === "Set Title") {
            this.inputMode = 'title';
            this.inputText = this.title;
        } else if (lbl === "Set Artist") {
            this.inputMode = 'artist';
            this.inputText = this.artist;
        } else if (lbl === "Save JSON" || lbl === "Export Level") {
            this.exportJson();
        } else if (lbl === "Play" || lbl === "Pause") {
            if (this.playing) this.pause();
            else this.play(false);
        } else if (lbl === "Rec" || lbl === "Stop Rec") {
            if (this.playing) this.recording = !this.recording;
            else this.play(true);
        } else if (lbl === "Stop") {
            this.stopAudio();
            this.baseOffsetMs = 0;
        } else if (lbl === "BPM+") {
            this.bpm = Math.min(300, this.bpm + 5);
            this.setMessage(`BPM: ${this.bpm}`);
        } else if (lbl === "BPM-") {
            this.bpm = Math.max(40, this.bpm - 5);
            this.setMessage(`BPM: ${this.bpm}`);
        } else if (lbl === "Reset BPM") {
            this.bpm = 120.0;
        } else if (lbl === "Zoom+") {
            this.zoom = Math.min(0.5, this.zoom * 1.25);
        } else if (lbl === "Zoom-") {
            this.zoom = Math.max(0.02, this.zoom / 1.25);
        } else if (lbl === "Grid+") {
            this.gridDiv = Math.min(16, this.gridDiv + 1);
            this.setMessage(`Grid: ${this.gridDiv}`);
        } else if (lbl === "Grid-") {
            this.gridDiv = Math.max(1, this.gridDiv - 1);
            this.setMessage(`Grid: ${this.gridDiv}`);
        } else if (lbl.startsWith("Metro")) {
            this.metronome = !this.metronome;
            this.setMessage(`Metronome: ${this.metronome ? 'ON' : 'OFF'}`);
        } else if (lbl === "App+") {
            this.approachMs = Math.min(2000, this.approachMs + 50);
        } else if (lbl === "App-") {
            this.approachMs = Math.max(200, this.approachMs - 50);
        } else if (lbl.startsWith("Type:Tap")) {
            this.currentNoteType = 'tap';
        } else if (lbl.startsWith("Type:Double")) {
            this.currentNoteType = 'double';
        } else if (lbl.startsWith("Type:Slide")) {
            this.currentNoteType = 'slide';
        } else if (lbl.includes(':')) {
            // Effects toggle
            const shortName = lbl.split(':')[1].slice(0, 4);
            const eff = EFFECT_LIST.find(e => e.startsWith(shortName));
            if (eff) {
                this.activeEffects[eff] = !this.activeEffects[eff];
                this.setMessage(`Effect ${eff}: ${this.activeEffects[eff] ? 'ON' : 'OFF'}`);
            }
        }
    }

    exportJson() {
        const data = {
            title: this.title,
            artist: this.artist,
            audio: this.audioPath,
            approach_ms: this.approachMs,
            hit_window_ms: this.hitWindowMs,
            notes: this.notes.map(n => ({
                time_ms: n.time_ms,
                side: n.side,
                key: n.key,
                duration_ms: n.duration_ms || 0,
                is_fake: Boolean(n.is_fake),
                note_type: n.note_type || 'tap',
                slide_target: n.slide_target || null
            })),
            effects: Object.keys(this.activeEffects).filter(e => this.activeEffects[e]),
            events: this.events
        };

        const jsonStr = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.title.replace(/\s+/g, '_')}.json`;
        a.click();
        URL.revokeObjectURL(url);
        this.setMessage(`Exported: ${a.download}`);
    }

    // --- RENDER PIPELINE (Exact Pygame editor.py match) ---

    render(dt) {
        const ctx = this.ctx;
        const w = this.canvas.width;
        const h = this.canvas.height;
        const centerX = w / 2;
        const timelineH = Math.floor(h * 0.25);
        const nowMs = this.getNowMs();

        if (this.messageTimer > 0) {
            this.messageTimer -= dt * 1000;
            if (this.messageTimer <= 0) this.message = '';
        }

        // Metronome beat tick
        if (this.metronome && this.bpm > 0 && this.playing) {
            const beatMs = 60000.0 / this.bpm;
            const beatIdx = Math.floor(nowMs / beatMs);
            if (beatIdx !== this.lastBeatPlay) {
                this.lastBeatPlay = beatIdx;
                this.audio.playSfx('hit');
            }
        }

        // 1. Dark Background
        ctx.fillStyle = COLOR_BG;
        ctx.fillRect(0, 0, w, h);

        // 2. Info text lines (editor.py lines 964-972)
        ctx.fillStyle = COLOR_TEXT;
        ctx.font = '16px monospace';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        const info = "F1:Help  SPACE:Play/Pause  R:Rec  +/-:Zoom  []:Grid  m:Metro  1/2/3:Type  WASD:Side  DEL:Delete  Ctrl+S:Save  ESC:Back";
        ctx.fillText(info, 16, 12);

        const recFlag = this.recording ? "REC" : (this.playing ? "PLAY" : "STOP");
        const eff = Object.keys(this.activeEffects).filter(e => this.activeEffects[e]).join(', ') || 'none';
        const params = `${recFlag}  Time ${msToTimeStr(Math.floor(nowMs))}  BPM:${this.bpm.toFixed(1)}  Grid:${this.gridDiv}  Zoom:${this.zoom.toFixed(2)}  Notes:${this.notes.length}  Effects:[${eff}]  Title:${this.title}`;
        ctx.font = 'bold 18px sans-serif';
        ctx.fillText(params, 16, 36);

        // 3. Toolbar Tabs (editor.py lines 974-980)
        let tx = 16;
        const tabY = 62;
        for (const [caption, page] of [["Main", 'main'], ["Controls", 'controls'], ["Effects", 'effects']]) {
            const isActive = (page === this.toolbarPage);
            ctx.fillStyle = isActive ? '#78c8ff' : '#2878c8';
            this.roundRect(ctx, tx, tabY, 110, 26, 6, true, false);
            ctx.fillStyle = '#10121c';
            ctx.font = 'bold 14px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(caption, tx + 55, tabY + 13);
            tx += 118;
        }

        // 4. Toolbar Buttons (editor.py lines 982-1009)
        const btns = this.getToolbarButtons(w);
        for (const btn of btns) {
            ctx.fillStyle = COLOR_ACCENT;
            if (btn.lbl.includes('✓') || btn.lbl.includes('ON') || btn.lbl === 'Pause' || btn.lbl === 'Stop Rec') {
                ctx.fillStyle = '#78ffa0'; // Active green
            }
            this.roundRect(ctx, btn.x, btn.y + 10, btn.w, btn.h, 6, true, false);
            ctx.fillStyle = '#10121c';
            ctx.font = 'bold 13px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(btn.lbl, btn.x + btn.w / 2, btn.y + 10 + btn.h / 2);
        }

        // 5. Help overlay (F1, editor.py lines 1011-1028)
        if (this.showHelp) {
            const ovH = 140;
            const ovY = h - timelineH - ovH - 8;
            ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
            ctx.fillRect(0, ovY, w, ovH);

            const helpLines = [
                "F1 — Скрыть/показать подсказку",
                "SPACE — Воспроизведение / Пауза; R — Включение записи нот на лету",
                "1/2/3 — Выбор типа ноты (Tap / Double / Slide); WASD — направление ноты",
                "ЛКМ мыши — перетаскивание ноты по времени; правый край hold-ноты — изменение длины",
                "ПКМ мыши — удалить ноту или добавить эффект; Колесико / Стрелки — перемотка таймлайна",
                "Ctrl+Z / Ctrl+Y — Отмена и повтор действий; Ctrl+S — сохранение JSON уровня"
            ];
            ctx.fillStyle = '#e6e6e6';
            ctx.font = '14px sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            for (let i = 0; i < helpLines.length; i++) {
                ctx.fillText(helpLines[i], 20, ovY + 12 + i * 20);
            }
        }

        // 6. Live Preview Pane (editor.py lines 1199-1290)
        this.renderPreviewPane(ctx, w, h, nowMs);

        // 7. Timeline Background
        const timelineY = h - timelineH;
        ctx.fillStyle = COLOR_TIMELINE;
        ctx.fillRect(0, timelineY, w, timelineH);

        // 8. Grid by BPM (editor.py lines 1050-1085)
        if (this.bpm > 0) {
            const beatMs = 60000.0 / this.bpm;
            const divMs = beatMs / this.gridDiv;
            const leftT = nowMs - (w / this.zoom) / 2;
            const rightT = nowMs + (w / this.zoom) / 2;
            const startK = Math.floor(leftT / divMs) - 2;
            const endK = Math.ceil(rightT / divMs) + 4;

            for (let k = startK; k <= endK; k++) {
                const tmark = k * divMs;
                const gx = this.timeToX(tmark, centerX);
                if (gx >= 0 && gx < w) {
                    if (k % this.gridDiv === 0) {
                        ctx.strokeStyle = '#ffff64'; // Main beat
                        ctx.lineWidth = 2;
                        ctx.beginPath();
                        ctx.moveTo(gx, timelineY);
                        ctx.lineTo(gx, h);
                        ctx.stroke();
                    } else if (k % (this.gridDiv / 2) === 0) {
                        ctx.strokeStyle = '#c8c8ff';
                        ctx.lineWidth = 1.5;
                        ctx.beginPath();
                        ctx.moveTo(gx, timelineY);
                        ctx.lineTo(gx, timelineY + timelineH / 2);
                        ctx.stroke();
                    } else {
                        ctx.strokeStyle = '#6496c8';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(gx, timelineY);
                        ctx.lineTo(gx, timelineY + timelineH / 3);
                        ctx.stroke();
                    }
                }
            }
        }

        // 9. Render Notes on Timeline (editor.py lines 1087-1113)
        const noteBy = timelineY + 40;
        const bw = 44;
        const bh = 28;

        for (let i = 0; i < this.notes.length; i++) {
            const n = this.notes[i];
            const nx = this.timeToX(n.time_ms, centerX);
            if (nx >= -100 && nx <= w + 100) {
                const col = COLOR_PREVIEW_NOTE[n.side] || COLOR_ACCENT;

                // Hold duration tail line
                if (n.duration_ms > 0) {
                    const endX = this.timeToX(n.time_ms + n.duration_ms, centerX);
                    ctx.strokeStyle = col;
                    ctx.lineWidth = 6;
                    ctx.lineCap = 'round';
                    ctx.beginPath();
                    ctx.moveTo(nx + bw/2, noteBy);
                    ctx.lineTo(endX, noteBy);
                    ctx.stroke();

                    // Tail resize handle
                    ctx.fillStyle = '#ffffff';
                    this.roundRect(ctx, endX - 4, noteBy - 8, 8, 16, 2, true, false);
                }

                // Selection highlight
                if (i === this.selectedIdx) {
                    ctx.strokeStyle = '#ffffff';
                    ctx.lineWidth = 3;
                    this.roundRect(ctx, nx - bw/2 - 3, noteBy - bh/2 - 3, bw + 6, bh + 6, 8, false, true);
                }

                // Note Body
                ctx.fillStyle = col;
                this.roundRect(ctx, nx - bw/2, noteBy - bh/2, bw, bh, 6, true, false);

                // Key Label
                ctx.fillStyle = '#10121c';
                ctx.font = 'bold 15px sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText(n.key || 'A', nx, noteBy);

                // Type badge (Double / Slide)
                if (n.note_type === 'double') {
                    ctx.fillStyle = 'rgba(0,0,0,0.7)';
                    this.roundRect(ctx, nx + bw/2 - 14, noteBy - bh/2 - 12, 16, 14, 3, true, false);
                    ctx.fillStyle = '#ffffff';
                    ctx.font = 'bold 10px sans-serif';
                    ctx.fillText('D', nx + bw/2 - 6, noteBy - bh/2 - 5);
                } else if (n.note_type === 'slide') {
                    ctx.fillStyle = 'rgba(0,0,0,0.7)';
                    this.roundRect(ctx, nx + bw/2 - 18, noteBy - bh/2 - 12, 20, 14, 3, true, false);
                    ctx.fillStyle = '#ffff78';
                    ctx.font = 'bold 10px sans-serif';
                    ctx.fillText('SL', nx + bw/2 - 8, noteBy - bh/2 - 5);
                }
            }
        }

        // 10. Center Time Marker (White line, editor.py line 1123)
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(centerX, timelineY);
        ctx.lineTo(centerX, h);
        ctx.stroke();

        // 11. Bottom Control Pad (editor.py lines 1143-1160)
        const padH = 90;
        ctx.fillStyle = '#1e202c';
        ctx.fillRect(0, h - padH, w, padH);

        const keys = [["A","left"], ["W","top"], ["D","right"], ["S","bottom"]];
        const gap = 20;
        const btnW = 80;
        const btnH = 44;
        const totalW = keys.length * btnW + (keys.length - 1) * gap;
        const startX = (w - totalW) / 2;
        const btnY = h - padH / 2 - btnH / 2;

        for (let idx = 0; idx < keys.length; idx++) {
            const bx = startX + idx * (btnW + gap);
            ctx.fillStyle = COLOR_PREVIEW_NOTE[keys[idx][1]];
            this.roundRect(ctx, bx, btnY, btnW, btnH, 8, true, false);
            ctx.fillStyle = '#10121c';
            ctx.font = 'bold 24px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(keys[idx][0], bx + btnW / 2, btnY + btnH / 2);
        }

        // 12. Message Toast (editor.py line 1163)
        if (this.message) {
            ctx.fillStyle = '#78c8ff';
            ctx.font = 'bold 16px sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            ctx.fillText(this.message, 16, 130);
        }

        // 13. Prompt Modal Overlay (Set Title / Artist / Audio)
        if (this.inputMode) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            ctx.fillRect(0, h / 2 - 70, w, 140);
            ctx.fillStyle = COLOR_TEXT;
            ctx.font = 'bold 22px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(`Enter ${this.inputMode.toUpperCase()} (Enter to confirm, Esc to cancel):`, w / 2, h / 2 - 30);

            ctx.fillStyle = '#78c8ff';
            ctx.font = 'bold 26px sans-serif';
            ctx.fillText(`${this.inputText}|`, w / 2, h / 2 + 15);
        }
    }

    renderPreviewPane(ctx, w, h, nowMs) {
        const pw = Math.floor(w * 0.32);
        const ph = Math.floor(h * 0.32);
        const px = Math.floor(w * 0.83 - pw / 2);
        const py = Math.floor(h * 0.22 - ph / 2);
        const pcx = px + pw / 2;
        const pcy = py + ph / 2;
        const centerR = Math.floor(Math.min(pw, ph) * 0.08);

        // Preview box
        ctx.fillStyle = '#181a24';
        this.roundRect(ctx, px, py, pw, ph, 8, true, false);

        // Preview grid
        ctx.strokeStyle = 'rgba(60, 70, 90, 0.4)';
        ctx.lineWidth = 1;
        for (let gx = px; gx < px + pw; gx += 24) {
            ctx.beginPath(); ctx.moveTo(gx, py); ctx.lineTo(gx, py + ph); ctx.stroke();
        }
        for (let gy = py; gy < py + ph; gy += 24) {
            ctx.beginPath(); ctx.moveTo(px, gy); ctx.lineTo(px + pw, gy); ctx.stroke();
        }

        // Target Cross & Center Ring
        ctx.strokeStyle = 'rgba(200, 220, 255, 0.4)';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.moveTo(px + 10, pcy); ctx.lineTo(px + pw - 10, pcy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(pcx, py + 10); ctx.lineTo(pcx, py + ph - 10); ctx.stroke();

        ctx.strokeStyle = COLOR_PREVIEW_CENTER;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(pcx, pcy, centerR, 0, Math.PI * 2);
        ctx.stroke();

        // Flying notes in preview
        for (const n of this.notes) {
            const t = (nowMs - (n.time_ms - this.approachMs)) / this.approachMs;
            if (t >= 0.0 && t <= 1.0) {
                let sx = pcx, sy = pcy;
                if (n.side === 'left') { sx = px + 10; sy = pcy; }
                else if (n.side === 'right') { sx = px + pw - 10; sy = pcy; }
                else if (n.side === 'top') { sx = pcx; sy = py + 10; }
                else { sx = pcx; sy = py + ph - 10; }

                const curX = sx + (pcx - sx) * t;
                const curY = sy + (pcy - sy) * t;
                const col = COLOR_PREVIEW_NOTE[n.side] || '#ffffff';

                ctx.fillStyle = col;
                ctx.beginPath();
                ctx.arc(curX, curY, 8, 0, Math.PI * 2);
                ctx.fill();

                if (n.duration_ms > 0) {
                    const endT = (nowMs - (n.time_ms + n.duration_ms - this.approachMs)) / this.approachMs;
                    if (endT < 1.0) {
                        const endX = sx + (pcx - sx) * Math.max(0, endT);
                        const endY = sy + (pcy - sy) * Math.max(0, endT);
                        ctx.strokeStyle = col;
                        ctx.lineWidth = 3;
                        ctx.beginPath();
                        ctx.moveTo(curX, curY);
                        ctx.lineTo(endX, endY);
                        ctx.stroke();
                    }
                }
            }
        }

        // Preview border
        ctx.strokeStyle = 'rgb(100, 120, 160)';
        ctx.lineWidth = 2;
        this.roundRect(ctx, px, py, pw, ph, 8, false, true);
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
