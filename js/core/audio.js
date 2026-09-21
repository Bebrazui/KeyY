/**
 * High-performance Web Audio API engine for KeyY.
 * Lazy AudioContext initialization on first user interaction with zero blocking.
 */

export class AudioManager {
    constructor() {
        this.ctx = null;
        this.musicSource = null;
        this.musicGain = null;
        this.sfxGain = null;
        this.masterGain = null;

        this.sfxRawBuffers = new Map(); // name -> ArrayBuffer (pre-fetched)
        this.sfxBuffers = new Map();    // name -> AudioBuffer (decoded)
        this.musicBuffer = null;

        this.isPlaying = false;
        this.isPaused = false;
        this.playbackStartTime = 0;
        this.startOffsetSec = 0;
        this.userOffsetMs = 0;
        this.playbackRate = 1.0;

        this.musicVolume = 0.8;
        this.sfxVolume = 0.9;
        this.initialized = false;
    }

    /**
     * Initializes AudioContext safely on first user gesture.
     */
    async init() {
        if (this.initialized && this.ctx) {
            if (this.ctx.state === 'suspended') {
                try { await this.ctx.resume(); } catch(e) {}
            }
            return;
        }

        try {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContextClass({ latencyHint: 'interactive' });

            this.masterGain = this.ctx.createGain();
            this.masterGain.gain.value = 1.0;
            this.masterGain.connect(this.ctx.destination);

            this.musicGain = this.ctx.createGain();
            this.musicGain.gain.value = this.musicVolume;
            this.musicGain.connect(this.masterGain);

            this.sfxGain = this.ctx.createGain();
            this.sfxGain.gain.value = this.sfxVolume;
            this.sfxGain.connect(this.masterGain);

            this.initialized = true;

            // Decode any raw SFX that were pre-fetched
            for (const [name, rawBuffer] of this.sfxRawBuffers.entries()) {
                if (!this.sfxBuffers.has(name)) {
                    this.ctx.decodeAudioData(rawBuffer.slice(0))
                        .then(decoded => this.sfxBuffers.set(name, decoded))
                        .catch(err => console.warn(`Could not decode SFX ${name}:`, err));
                }
            }
        } catch(e) {
            console.warn('AudioContext init postponed:', e);
        }
    }

    setMusicVolume(v) {
        this.musicVolume = Math.max(0, Math.min(1, v));
        if (this.musicGain && this.ctx) {
            this.musicGain.gain.setValueAtTime(this.musicVolume, this.ctx.currentTime);
        }
    }

    setSfxVolume(v) {
        this.sfxVolume = Math.max(0, Math.min(1, v));
        if (this.sfxGain && this.ctx) {
            this.sfxGain.gain.setValueAtTime(this.sfxVolume, this.ctx.currentTime);
        }
    }

    setUserOffset(offsetMs) {
        this.userOffsetMs = offsetMs;
    }

    /**
     * Pre-fetches sound files as raw ArrayBuffers in background without needing AudioContext.
     */
    async preloadSfx(sfxMap) {
        const promises = [];
        for (const [name, path] of Object.entries(sfxMap)) {
            promises.push(
                fetch(path)
                    .then(res => res.arrayBuffer())
                    .then(buf => {
                        this.sfxRawBuffers.set(name, buf);
                        if (this.ctx && this.initialized) {
                            return this.ctx.decodeAudioData(buf.slice(0))
                                .then(decoded => this.sfxBuffers.set(name, decoded));
                        }
                    })
                    .catch(err => console.warn(`Could not preload sfx "${name}":`, err))
            );
        }
        await Promise.all(promises);
    }

    /**
     * Loads a music track for a level.
     */
    async loadMusic(url) {
        await this.init();
        this.stopMusic();
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to load audio from ${url} (status: ${response.status})`);
        }
        const arrayBuffer = await response.arrayBuffer();
        this.musicBuffer = await this.ctx.decodeAudioData(arrayBuffer);
        return this.musicBuffer;
    }

    playMusic(startOffsetMs = 0) {
        if (!this.musicBuffer || !this.ctx) return;
        this.stopMusic();

        this.startOffsetSec = Math.max(0, startOffsetMs / 1000);
        this.musicSource = this.ctx.createBufferSource();
        this.musicSource.buffer = this.musicBuffer;
        this.musicSource.playbackRate.value = this.playbackRate;
        this.musicSource.connect(this.musicGain);

        this.playbackStartTime = this.ctx.currentTime;
        this.musicSource.start(0, this.startOffsetSec);
        this.isPlaying = true;
        this.isPaused = false;
    }

    setPlaybackRate(rate) {
        const newRate = Math.max(0.25, Math.min(4.0, rate));
        if (this.isPlaying && !this.isPaused && this.ctx) {
            const now = this.ctx.currentTime;
            this.startOffsetSec += (now - this.playbackStartTime) * this.playbackRate;
            this.playbackStartTime = now;
        }
        this.playbackRate = newRate;
        if (this.musicSource && this.musicSource.playbackRate && this.ctx) {
            this.musicSource.playbackRate.setValueAtTime(this.playbackRate, this.ctx.currentTime);
        }
    }

    stopMusic() {
        if (this.musicSource) {
            try {
                this.musicSource.stop();
                this.musicSource.disconnect();
            } catch (e) {}
            this.musicSource = null;
        }
        this.isPlaying = false;
        this.isPaused = false;
    }

    pauseMusic() {
        if (this.isPlaying && !this.isPaused) {
            this.startOffsetSec = ((this.ctx.currentTime - this.playbackStartTime) * (this.playbackRate || 1.0)) + this.startOffsetSec;
            if (this.musicSource) {
                try { this.musicSource.stop(); } catch(e) {}
                this.musicSource = null;
            }
            this.isPlaying = false;
            this.isPaused = true;
        }
    }

    resumeMusic() {
        if (this.isPaused) {
            this.playMusic(this.startOffsetSec * 1000);
        }
    }

    getCurrentSongTimeMs() {
        if (!this.ctx) return 0;
        if (this.isPaused) {
            return (this.startOffsetSec * 1000) - this.userOffsetMs;
        }
        if (!this.isPlaying) {
            return 0;
        }
        const elapsedSec = (this.ctx.currentTime - this.playbackStartTime) * (this.playbackRate || 1.0);
        return ((this.startOffsetSec + elapsedSec) * 1000) - this.userOffsetMs;
    }

    playSfx(name, playbackRate = 1.0) {
        if (!this.ctx || !this.sfxBuffers.has(name)) return;
        const buf = this.sfxBuffers.get(name);
        if (!buf) return;

        try {
            const source = this.ctx.createBufferSource();
            source.buffer = buf;
            source.playbackRate.value = playbackRate;
            source.connect(this.sfxGain);
            source.start(0);
        } catch(e) {}
    }
}
