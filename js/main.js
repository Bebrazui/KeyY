/**
 * Application Bootstrap for KeyY Web Edition.
 * Instantly displays 1:1 Canvas Menu, with seamless transition to Game and 1:1 Level Editor.
 */

import { AudioManager } from './core/audio.js';
import { InputManager } from './core/input.js';
import { GameRenderer } from './game/renderer.js';
import { GameEngine } from './game/engine.js';
import { CanvasMenu } from './ui/canvas_menu.js';
import { LevelEditor } from './editor/editor.js';

window.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('game-canvas');
    const resultsScreen = document.getElementById('results-screen');
    const gameoverScreen = document.getElementById('gameover-screen');
    const touchControls = document.getElementById('touch-controls');

    // 1. Initialize core systems
    const audio = new AudioManager();
    const input = new InputManager();
    const renderer = new GameRenderer(canvas);
    const engine = new GameEngine(audio, input, renderer);

    let currentLevelData = null;
    let appMode = 'menu'; // 'menu' | 'game' | 'editor' | 'results' | 'gameover'
    let mainAnimFrame = null;
    let lastFrameTime = performance.now();

    // 2. Initialize 1:1 Level Editor
    const editor = new LevelEditor(canvas, audio, () => {
        // Return from editor to menu
        returnToMenu();
    });

    // 3. Initialize 1:1 Canvas Menu
    const canvasMenu = new CanvasMenu(
        canvas,
        audio,
        async (levelData) => {
            await startGame(levelData);
        },
        () => {
            startEditor();
        }
    );

    // Resize handler
    function handleResize() {
        renderer.resize();
    }
    window.addEventListener('resize', handleResize);
    handleResize();

    // 4. Preload SFX in background
    audio.preloadSfx({
        hit: 'assets/hit.wav',
        perfect: 'assets/perfect.wav',
        good: 'assets/good.wav',
        bad: 'assets/bad.wav',
        miss: 'assets/miss.wav',
        combo: 'assets/combo.wav'
    }).catch(err => console.warn('[KeyY Web] Preload note:', err));

    // 5. Main Canvas render loop (menu & editor)
    function canvasLoop(now) {
        if (appMode === 'menu' || appMode === 'editor') {
            const dt = Math.min((now - lastFrameTime) / 1000, 0.1);
            lastFrameTime = now;

            if (appMode === 'menu') {
                canvasMenu.render(dt);
            } else if (appMode === 'editor') {
                editor.render(dt);
            }

            mainAnimFrame = requestAnimationFrame(canvasLoop);
        }
    }

    function startMenuLoop() {
        if (mainAnimFrame) cancelAnimationFrame(mainAnimFrame);
        appMode = 'menu';
        lastFrameTime = performance.now();
        mainAnimFrame = requestAnimationFrame(canvasLoop);
    }

    function stopCanvasLoop() {
        if (mainAnimFrame) {
            cancelAnimationFrame(mainAnimFrame);
            mainAnimFrame = null;
        }
    }

    function startEditor() {
        appMode = 'editor';
        lastFrameTime = performance.now();
        if (touchControls) touchControls.classList.add('hidden');
        // If sample audio exists, preload into editor
        audio.loadMusic('assets/sample.mp3').catch(() => {});
        if (!mainAnimFrame) {
            mainAnimFrame = requestAnimationFrame(canvasLoop);
        }
    }

    function returnToMenu() {
        editor.stopAudio();
        startMenuLoop();
        canvasMenu.screenState = 'menu';
    }

    // Start in menu immediately
    startMenuLoop();

    // 6. Start Game handler
    async function startGame(levelData) {
        currentLevelData = levelData;
        stopCanvasLoop();
        appMode = 'game';

        if (touchControls) touchControls.classList.remove('hidden');

        try {
            if (levelData.audio) {
                await audio.loadMusic(levelData.audio);
            }
            engine.start(levelData);
        } catch(err) {
            alert(`Ошибка загрузки аудио трека: ${err.message}`);
            startMenuLoop();
            canvasMenu.screenState = 'levels';
        }
    }

    // 7. Escape / Enter key handling in gameplay
    window.addEventListener('keydown', (e) => {
        if (appMode === 'game') {
            if (e.key === 'Escape' || (e.key === 'Enter' && engine.state && engine.state.failed)) {
                engine.stop();
                if (touchControls) touchControls.classList.add('hidden');
                startMenuLoop();
                canvasMenu.screenState = 'levels';
            }
        }
    });

    // 8. Results & Game Over handlers
    engine.onFinishCallback = (state) => {
        appMode = 'results';
        if (touchControls) touchControls.classList.add('hidden');

        const total = state.hits + state.stats.bad + state.stats.miss + state.stats.fakeHit;
        const acc = total > 0 ? (state.hits / total) * 100 : 100;
        
        let rank = 'D';
        if (acc >= 98) rank = 'SS';
        else if (acc >= 95) rank = 'S';
        else if (acc >= 90) rank = 'A';
        else if (acc >= 80) rank = 'B';
        else if (acc >= 70) rank = 'C';

        document.getElementById('res-rank').textContent = rank;
        document.getElementById('res-rank').className = `rank-badge rank-${rank.toLowerCase()}`;
        document.getElementById('res-score').textContent = String(state.score).padStart(7, '0');
        document.getElementById('res-accuracy').textContent = `${acc.toFixed(1)}%`;
        document.getElementById('res-combo').textContent = `${state.bestCombo}x`;
        document.getElementById('res-perfect').textContent = state.stats.perfect;
        document.getElementById('res-great').textContent = state.stats.great;
        document.getElementById('res-good').textContent = state.stats.good;
        document.getElementById('res-miss').textContent = state.stats.miss + state.stats.bad;

        if (currentLevelData && currentLevelData.id) {
            const hsKey = `keyy_hs_${currentLevelData.id}`;
            const prev = localStorage.getItem(hsKey);
            let shouldSave = true;
            if (prev) {
                try {
                    if (JSON.parse(prev).score >= state.score) shouldSave = false;
                } catch(e) {}
            }
            if (shouldSave) {
                localStorage.setItem(hsKey, JSON.stringify({ score: state.score, rank, accuracy: acc }));
            }
        }

        resultsScreen.classList.remove('hidden');
        audio.playSfx('combo');
    };

    engine.onFailCallback = (state) => {
        appMode = 'gameover';
        if (touchControls) touchControls.classList.add('hidden');
        document.getElementById('go-score').textContent = String(state.score).padStart(7, '0');
        document.getElementById('go-combo').textContent = `${state.bestCombo}x`;
        gameoverScreen.classList.remove('hidden');
        audio.playSfx('miss');
    };

    // Results buttons
    document.getElementById('btn-results-retry')?.addEventListener('click', () => {
        resultsScreen.classList.add('hidden');
        if (currentLevelData) startGame(currentLevelData);
    });

    document.getElementById('btn-results-menu')?.addEventListener('click', () => {
        resultsScreen.classList.add('hidden');
        startMenuLoop();
        canvasMenu.screenState = 'levels';
    });

    // Game Over buttons
    document.getElementById('btn-gameover-retry')?.addEventListener('click', () => {
        gameoverScreen.classList.add('hidden');
        if (currentLevelData) startGame(currentLevelData);
    });

    document.getElementById('btn-gameover-menu')?.addEventListener('click', () => {
        gameoverScreen.classList.add('hidden');
        startMenuLoop();
        canvasMenu.screenState = 'levels';
    });

    // Mobile touch controls
    const bindTouch = (id, side) => {
        const btn = document.getElementById(id);
        if (!btn) return;
        btn.addEventListener('pointerdown', (e) => {
            e.preventDefault();
            input.triggerSideDown(side);
        });
        btn.addEventListener('pointerup', (e) => {
            e.preventDefault();
            input.triggerSideUp(side);
        });
        btn.addEventListener('pointercancel', (e) => {
            e.preventDefault();
            input.triggerSideUp(side);
        });
    };
    bindTouch('touch-left', 'left');
    bindTouch('touch-top', 'top');
    bindTouch('touch-right', 'right');
    bindTouch('touch-bottom', 'bottom');
});
