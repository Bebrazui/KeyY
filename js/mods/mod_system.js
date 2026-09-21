/**
 * Modular Mod System for KeyY Web Edition.
 * Dynamically loads and executes mod hooks in gameplay, matching game/mod_system.py.
 */

import { AutopilotMod } from './autopilot_mod.js';
import { CheatsMod } from './cheats_mod.js';
import { SpeedMod } from './speed_mod.js';
import { RainbowMod } from './rainbow_mod.js';

export class ModSystem {
    constructor() {
        this.mods = new Map();
        this.registerMod(new AutopilotMod());
        this.registerMod(new CheatsMod());
        this.registerMod(new SpeedMod());
        this.registerMod(new RainbowMod());

        this.loadState();
    }

    registerMod(mod) {
        this.mods.set(mod.id, mod);
    }

    getMod(id) {
        return this.mods.get(id);
    }

    getEnabledMods() {
        const list = [];
        for (const mod of this.mods.values()) {
            if (mod.enabled) list.push(mod);
        }
        return list;
    }

    loadState() {
        try {
            const raw = localStorage.getItem('keyy_mods');
            if (raw) {
                const data = JSON.parse(raw);
                for (const [id, val] of Object.entries(data)) {
                    const mod = this.mods.get(id);
                    if (mod) mod.enabled = Boolean(val);
                }
            }
        } catch (e) {}
    }

    saveState() {
        try {
            const data = {};
            for (const [id, mod] of this.mods.entries()) {
                data[id] = mod.enabled;
            }
            localStorage.setItem('keyy_mods', JSON.stringify(data));
        } catch (e) {}
    }

    toggleMod(id) {
        const mod = this.mods.get(id);
        if (mod) {
            mod.enabled = !mod.enabled;
            this.saveState();
            return mod.enabled;
        }
        return false;
    }

    setModEnabled(id, enabled) {
        const mod = this.mods.get(id);
        if (mod) {
            mod.enabled = Boolean(enabled);
            this.saveState();
        }
    }

    executeHook(hookName, ...args) {
        let lastResult = undefined;
        for (const mod of this.mods.values()) {
            if (mod.enabled && typeof mod[hookName] === 'function') {
                try {
                    const res = mod[hookName](...args);
                    if (res !== undefined) {
                        lastResult = res;
                    }
                } catch (err) {
                    console.error(`[ModSystem] Error in ${mod.id}.${hookName}:`, err);
                }
            }
        }
        return lastResult;
    }
}

export const modSystem = new ModSystem();
