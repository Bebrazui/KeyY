/**
 * UI Controller for KeyY Web: Menus, Level Selection, Settings, and Results.
 */

export const BUILTIN_LEVELS = [
    { id: 'easy', title: 'Easy', path: 'levels/easy.json', desc: '4 notes intro' },
    { id: 'medium', title: 'Medium', path: 'levels/medium.json', desc: 'Normal rhythm pattern' },
    { id: 'hard', title: 'Hard', path: 'levels/hard.json', desc: 'Dense pattern with holds & slides' },
    { id: 'welcome', title: 'Welcome', path: 'levels/Welcome.json', desc: 'Welcome track' },
    { id: 'long_easy', title: 'Long Easy', path: 'levels/official_long_easy.json', desc: 'Full length relaxed' },
    { id: 'long_hard', title: 'Long Hard', path: 'levels/official_long_hard.json', desc: 'Full length challenge' }
];

export class UIManager {
    constructor(audioManager, gameEngine) {
        this.audio = audioManager;
        this.engine = gameEngine;

        // Cache elements
        this.screens = {
            loading: document.getElementById('loading-screen'),
            start: document.getElementById('start-screen'),
            menu: document.getElementById('menu-screen'),
            levels: document.getElementById('levels-screen'),
            settings: document.getElementById('settings-screen'),
            results: document.getElementById('results-screen'),
            gameover: document.getElementById('gameover-screen'),
            gameHud: document.getElementById('game-container')
        };

        this.currentLevel = null;
        this.settings = this.loadSettings();

        // Bind callbacks
        this.engine.onFinishCallback = this.showResults.bind(this);
        this.engine.onFailCallback = this.showGameOver.bind(this);

        this.initEventListeners();
        this.applySettings();
    }

    loadSettings() {
        const saved = localStorage.getItem('keyy_settings');
        if (saved) {
            try { return JSON.parse(saved); } catch(e) {}
        }
        return {
            musicVolume: 0.8,
            sfxVolume: 0.9,
            offsetMs: 0
        };
    }

    saveSettings() {
        localStorage.setItem('keyy_settings', JSON.stringify(this.settings));
        this.applySettings();
    }

    applySettings() {
        this.audio.setMusicVolume(this.settings.musicVolume);
        this.audio.setSfxVolume(this.settings.sfxVolume);
        this.audio.setUserOffset(this.settings.offsetMs);

        // Update settings inputs if present
        const mVol = document.getElementById('setting-music-vol');
        const sVol = document.getElementById('setting-sfx-vol');
        const off = document.getElementById('setting-offset');
        const offVal = document.getElementById('setting-offset-val');

        if (mVol) mVol.value = this.settings.musicVolume * 100;
        if (sVol) sVol.value = this.settings.sfxVolume * 100;
        if (off) off.value = this.settings.offsetMs;
        if (offVal) offVal.textContent = `${this.settings.offsetMs > 0 ? '+' : ''}${this.settings.offsetMs} ms`;
    }

    showScreen(screenKey) {
        for (const [key, el] of Object.entries(this.screens)) {
            if (!el) continue;
            if (key === screenKey) {
                el.classList.remove('hidden');
            } else if (key !== 'gameHud' || screenKey !== 'game') {
                el.classList.add('hidden');
            }
        }
        if (screenKey === 'game') {
            this.screens.gameHud.classList.remove('hidden');
        }
    }

    initEventListeners() {
        // Start Click (satisfies audio autoplay)
        const btnStart = document.getElementById('btn-start-app');
        if (btnStart) {
            btnStart.addEventListener('click', async () => {
                await this.audio.init();
                this.audio.playSfx('perfect');
                this.showScreen('menu');
            });
        }

        // Menu Buttons
        document.getElementById('btn-play')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            this.renderLevelList();
            this.showScreen('levels');
        });

        document.getElementById('btn-settings')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            this.showScreen('settings');
        });

        document.getElementById('btn-back-to-menu')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            this.showScreen('menu');
        });

        document.getElementById('btn-back-from-settings')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            this.showScreen('menu');
        });

        // Settings sliders
        document.getElementById('setting-music-vol')?.addEventListener('input', (e) => {
            this.settings.musicVolume = e.target.value / 100;
            this.saveSettings();
        });

        document.getElementById('setting-sfx-vol')?.addEventListener('input', (e) => {
            this.settings.sfxVolume = e.target.value / 100;
            this.saveSettings();
            this.audio.playSfx('hit');
        });

        document.getElementById('setting-offset')?.addEventListener('input', (e) => {
            this.settings.offsetMs = parseInt(e.target.value, 10);
            this.saveSettings();
        });

        // Results Buttons
        document.getElementById('btn-results-retry')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            if (this.currentLevel) this.startLevel(this.currentLevel);
        });

        document.getElementById('btn-results-menu')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            this.showScreen('menu');
        });

        // Game Over Buttons
        document.getElementById('btn-gameover-retry')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            if (this.currentLevel) this.startLevel(this.currentLevel);
        });

        document.getElementById('btn-gameover-menu')?.addEventListener('click', () => {
            this.audio.playSfx('hit');
            this.showScreen('menu');
        });

        // Custom Level File Upload
        const fileInput = document.getElementById('custom-level-input');
        if (fileInput) {
            fileInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (!file) return;
                try {
                    const text = await file.text();
                    const json = JSON.parse(text);
                    import('../game/level.js').then(({ LevelData }) => {
                        const levelData = new LevelData(json);
                        this.startLevel(levelData);
                    });
                } catch(err) {
                    alert(`Error loading custom level: ${err.message}`);
                }
            });
        }

        // Fullscreen toggle
        document.getElementById('btn-fullscreen')?.addEventListener('click', () => {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen().catch(() => {});
            } else {
                document.exitFullscreen().catch(() => {});
            }
        });

        // Touch buttons for mobile
        const bindTouch = (id, side) => {
            const btn = document.getElementById(id);
            if (!btn) return;
            btn.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                this.engine.input.triggerSideDown(side);
            });
            btn.addEventListener('pointerup', (e) => {
                e.preventDefault();
                this.engine.input.triggerSideUp(side);
            });
            btn.addEventListener('pointercancel', (e) => {
                e.preventDefault();
                this.engine.input.triggerSideUp(side);
            });
        };
        bindTouch('touch-left', 'left');
        bindTouch('touch-top', 'top');
        bindTouch('touch-right', 'right');
        bindTouch('touch-bottom', 'bottom');

        // Escape to exit level back to menu
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.engine.isRunning) {
                this.engine.stop();
                this.showScreen('menu');
            }
        });
    }

    renderLevelList() {
        const listEl = document.getElementById('level-list');
        if (!listEl) return;
        listEl.innerHTML = '';

        BUILTIN_LEVELS.forEach(lvl => {
            const card = document.createElement('div');
            card.className = 'level-card';
            
            // Highscore
            const hs = this.getHighscore(lvl.id);
            const hsText = hs ? `Record: ${hs.score} pts (${hs.rank})` : 'Not played yet';

            card.innerHTML = `
                <div class="level-info">
                    <div class="level-title">${lvl.title}</div>
                    <div class="level-desc">${lvl.desc}</div>
                    <div class="level-hs">${hsText}</div>
                </div>
                <button class="btn btn-play-level">PLAY</button>
            `;

            card.querySelector('.btn-play-level').addEventListener('click', async () => {
                this.audio.playSfx('perfect');
                const { LevelData } = await import('../game/level.js');
                try {
                    const levelData = await LevelData.loadFromUrl(lvl.path);
                    levelData.id = lvl.id;
                    this.startLevel(levelData);
                } catch(err) {
                    alert(`Failed to load level: ${err.message}`);
                }
            });

            listEl.appendChild(card);
        });
    }

    async startLevel(levelData) {
        this.currentLevel = levelData;
        this.showScreen('loading');

        try {
            // Load song audio
            if (levelData.audio) {
                await this.audio.loadMusic(levelData.audio);
            }
            this.showScreen('game');
            this.engine.start(levelData);
        } catch(err) {
            alert(`Error loading audio: ${err.message}`);
            this.showScreen('levels');
        }
    }

    calculateRank(accuracy, failed = false) {
        if (failed) return 'F';
        if (accuracy >= 98) return 'SS';
        if (accuracy >= 95) return 'S';
        if (accuracy >= 90) return 'A';
        if (accuracy >= 80) return 'B';
        if (accuracy >= 70) return 'C';
        return 'D';
    }

    showResults(state) {
        this.showScreen('results');
        const total = state.hits + state.stats.bad + state.stats.miss + state.stats.fakeHit;
        const acc = total > 0 ? (state.hits / total) * 100 : 100;
        const rank = this.calculateRank(acc);

        document.getElementById('res-rank').textContent = rank;
        document.getElementById('res-rank').className = `rank-badge rank-${rank.toLowerCase()}`;
        document.getElementById('res-score').textContent = String(state.score).padStart(7, '0');
        document.getElementById('res-accuracy').textContent = `${acc.toFixed(1)}%`;
        document.getElementById('res-combo').textContent = `${state.bestCombo}x`;

        document.getElementById('res-perfect').textContent = state.stats.perfect;
        document.getElementById('res-great').textContent = state.stats.great;
        document.getElementById('res-good').textContent = state.stats.good;
        document.getElementById('res-bad').textContent = state.stats.bad;
        document.getElementById('res-miss').textContent = state.stats.miss;

        if (this.currentLevel && this.currentLevel.id) {
            this.saveHighscore(this.currentLevel.id, state.score, rank, acc);
        }

        this.audio.playSfx('combo');
    }

    showGameOver(state) {
        this.showScreen('gameover');
        document.getElementById('go-score').textContent = String(state.score).padStart(7, '0');
        document.getElementById('go-combo').textContent = `${state.bestCombo}x`;
        this.audio.playSfx('miss');
    }

    saveHighscore(levelId, score, rank, accuracy) {
        const hsKey = `keyy_hs_${levelId}`;
        const prev = localStorage.getItem(hsKey);
        let save = true;
        if (prev) {
            const parsed = JSON.parse(prev);
            if (parsed.score >= score) save = false;
        }
        if (save) {
            localStorage.setItem(hsKey, JSON.stringify({ score, rank, accuracy }));
        }
    }

    getHighscore(levelId) {
        const hsKey = `keyy_hs_${levelId}`;
        const item = localStorage.getItem(hsKey);
        if (!item) return null;
        try { return JSON.parse(item); } catch(e) { return null; }
    }
}
