/**
 * Level loader and parser compatible with KeyY JSON levels.
 */

export class NoteData {
    constructor(data = {}) {
        this.time_ms = data.time_ms || 0;
        this.side = data.side || 'left'; // left | top | right | bottom
        this.key = data.key || 'A';
        this.duration_ms = data.duration_ms || 0; // > 0 for hold
        this.is_fake = Boolean(data.is_fake);
        this.note_type = data.note_type || (this.duration_ms > 50 ? 'hold' : 'tap');
        this.slide_target = data.slide_target || null;
    }
}

export class LevelData {
    constructor(data = {}) {
        this.title = data.title || 'Untitled';
        this.artist = data.artist || 'Unknown';
        this.audio = (data.audio || '').replace(/\\/g, '/');
        this.approach_ms = Number(data.approach_ms) || 1000;
        this.hit_window_ms = Number(data.hit_window_ms) || 120;
        this.difficulty = data.difficulty || 'normal';
        this.effects = Array.isArray(data.effects) ? data.effects : [];
        this.events = Array.isArray(data.events) ? data.events : [];
        
        const rawNotes = Array.isArray(data.notes) ? data.notes : [];
        this.notes = rawNotes.map(n => new NoteData(n));
        
        // Sort notes chronologically for fast binary search / linear scan
        this.notes.sort((a, b) => a.time_ms - b.time_ms);
    }

    static async loadFromUrl(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to load level from ${url} (status: ${response.status})`);
        }
        const json = await response.json();
        return new LevelData(json);
    }

    static loadFromJsonString(jsonString) {
        const json = JSON.parse(jsonString);
        return new LevelData(json);
    }
}
