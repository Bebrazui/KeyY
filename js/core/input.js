/**
 * Low-latency input handling with hardware timestamps and key-to-side mapping.
 */

export const KEY_TO_SIDE = {
    // WASD English
    'KeyA': 'left', 'KeyW': 'top', 'KeyD': 'right', 'KeyS': 'bottom',
    'keya': 'left', 'keyw': 'top', 'keyd': 'right', 'keys': 'bottom',
    'a': 'left', 'w': 'top', 'd': 'right', 's': 'bottom',
    'A': 'left', 'W': 'top', 'D': 'right', 'S': 'bottom',

    // Russian layout (Ф Ц В Ы)
    'ф': 'left', 'Ф': 'left',
    'ц': 'top',  'Ц': 'top',
    'в': 'right','В': 'right',
    'ы': 'bottom','Ы': 'bottom',

    // Arrows
    'ArrowLeft': 'left', 'ArrowUp': 'top', 'ArrowRight': 'right', 'ArrowDown': 'bottom',

    // IJKL (EN + RU)
    'KeyJ': 'left', 'KeyI': 'top', 'KeyL': 'right', 'KeyK': 'bottom',
    'j': 'left', 'i': 'top', 'l': 'right', 'k': 'bottom',
    'J': 'left', 'I': 'top', 'L': 'right', 'K': 'bottom',
    'о': 'left', 'ш': 'top', 'д': 'right', 'л': 'bottom',
    'О': 'left', 'Ш': 'top', 'Д': 'right', 'Л': 'bottom',

    // FTHG (EN + RU)
    'KeyF': 'left', 'KeyT': 'top', 'KeyH': 'right', 'KeyG': 'bottom',
    'f': 'left', 't': 'top', 'h': 'right', 'g': 'bottom',
    'F': 'left', 'T': 'top', 'H': 'right', 'G': 'bottom',
    'а': 'left', 'е': 'top', 'р': 'right', 'п': 'bottom',
    'А': 'left', 'Е': 'top', 'Р': 'right', 'П': 'bottom',

    // Numpad
    'Numpad4': 'left', 'Numpad8': 'top', 'Numpad6': 'right', 'Numpad5': 'bottom', 'Numpad2': 'bottom',
    'Numpad0': 'bottom', 'Numpad7': 'left', 'Numpad9': 'right', 'Numpad1': 'left', 'Numpad3': 'right',

    // QWERTY & additional keys matching game/main.py
    'KeyQ': 'top_left', 'q': 'top_left', 'Q': 'top_left', 'й': 'top_left', 'Й': 'top_left',
    'KeyE': 'top_right', 'e': 'top_right', 'E': 'top_right', 'у': 'top_right', 'У': 'top_right',
    'KeyU': 'top', 'u': 'top', 'U': 'top', 'г': 'top', 'Г': 'top',
    'KeyO': 'right', 'o': 'right', 'O': 'right', 'щ': 'right', 'Щ': 'right',
    'KeyP': 'right', 'p': 'right', 'P': 'right', 'з': 'right', 'З': 'right',
    'KeyZ': 'bottom_left', 'z': 'bottom_left', 'Z': 'bottom_left', 'я': 'bottom_left', 'Я': 'bottom_left',
    'KeyX': 'bottom', 'x': 'bottom', 'X': 'bottom', 'ч': 'bottom', 'Ч': 'bottom',
    'KeyC': 'bottom_right', 'c': 'bottom_right', 'C': 'bottom_right', 'с': 'bottom_right', 'С': 'bottom_right',
    'KeyV': 'bottom', 'v': 'bottom', 'V': 'bottom', 'м': 'bottom', 'М': 'bottom',
    'KeyB': 'bottom', 'b': 'bottom', 'B': 'bottom', 'и': 'bottom', 'И': 'bottom',
    'KeyN': 'bottom', 'n': 'bottom', 'N': 'bottom', 'т': 'bottom', 'Т': 'bottom',
    'KeyM': 'right', 'm': 'right', 'M': 'right', 'ь': 'right', 'Ь': 'right',

    // Digits
    'Digit1': 'left', 'Digit2': 'bottom', 'Digit3': 'right', 'Digit4': 'left',
    'Digit5': 'bottom', 'Digit6': 'right', 'Digit7': 'left', 'Digit8': 'top', 'Digit9': 'right', 'Digit0': 'bottom',
    '1': 'left', '2': 'bottom', '3': 'right', '4': 'left', '5': 'bottom', '6': 'right', '7': 'left', '8': 'top', '9': 'right', '0': 'bottom',

    // Space
    'Space': 'bottom',
    ' ': 'bottom'
};

export class InputManager {
    constructor() {
        this.pressedSides = new Set();
        this.heldSides = new Set();
        this.activeKeys = new Set();
        this.eventQueue = []; // { type: 'down'|'up', side: string, time: number }
        this.boundKeyDown = this.onKeyDown.bind(this);
        this.boundKeyUp = this.onKeyUp.bind(this);
        this.listeners = [];
        this.isListening = false;
    }

    startListening() {
        if (this.isListening) return;
        window.addEventListener('keydown', this.boundKeyDown, { passive: false });
        window.addEventListener('keyup', this.boundKeyUp, { passive: false });
        this.isListening = true;
    }

    stopListening() {
        if (!this.isListening) return;
        window.removeEventListener('keydown', this.boundKeyDown);
        window.removeEventListener('keyup', this.boundKeyUp);
        this.isListening = false;
        this.reset();
    }

    reset() {
        this.pressedSides.clear();
        this.heldSides.clear();
        this.activeKeys.clear();
        this.eventQueue.length = 0;
    }

    getSide(e) {
        return KEY_TO_SIDE[e.code] || KEY_TO_SIDE[e.key];
    }

    onKeyDown(e) {
        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
            e.preventDefault();
        }

        const side = this.getSide(e);
        if (!side) return;

        this.activeKeys.add(e.code || e.key);

        if (!e.repeat) {
            this.pressedSides.add(side);
            this.heldSides.add(side);
            this.eventQueue.push({
                type: 'down',
                side: side,
                code: e.code || e.key,
                time: performance.now()
            });

            for (const listener of this.listeners) {
                listener('down', side, e.code || e.key);
            }
        }
    }

    onKeyUp(e) {
        const side = this.getSide(e);
        this.activeKeys.delete(e.code || e.key);

        if (side) {
            let stillHeld = false;
            for (const k of this.activeKeys) {
                if (KEY_TO_SIDE[k] === side) {
                    stillHeld = true;
                    break;
                }
            }
            if (!stillHeld) {
                this.heldSides.delete(side);
                this.eventQueue.push({
                    type: 'up',
                    side: side,
                    code: e.code || e.key,
                    time: performance.now()
                });
                for (const listener of this.listeners) {
                    listener('up', side, e.code || e.key);
                }
            }
        }
    }

    triggerSideDown(side) {
        if (!this.heldSides.has(side)) {
            this.pressedSides.add(side);
            this.heldSides.add(side);
            this.eventQueue.push({
                type: 'down',
                side: side,
                code: 'Touch',
                time: performance.now()
            });
            for (const listener of this.listeners) {
                listener('down', side, 'Touch');
            }
        }
    }

    triggerSideUp(side) {
        if (this.heldSides.has(side)) {
            this.heldSides.delete(side);
            this.eventQueue.push({
                type: 'up',
                side: side,
                code: 'Touch',
                time: performance.now()
            });
            for (const listener of this.listeners) {
                listener('up', side, 'Touch');
            }
        }
    }

    isSideHeld(side) {
        return this.heldSides.has(side);
    }

    consumePresses() {
        const presses = Array.from(this.pressedSides);
        this.pressedSides.clear();
        return presses;
    }

    pollEvents() {
        if (this.eventQueue.length === 0) return [];
        const events = [...this.eventQueue];
        this.eventQueue.length = 0;
        return events;
    }

    addListener(fn) {
        this.listeners.push(fn);
    }

    removeListener(fn) {
        this.listeners = this.listeners.filter(l => l !== fn);
    }
}
