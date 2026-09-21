/**
 * 1-to-1 exact reproduction of KeyY Pygame Menu (game/menu.py) in pure HTML5 Canvas.
 * Instant responsive button clicks, zero-lag screen transitions, exact Pygame layout.
 */

import { modSystem } from '../mods/mod_system.js';

export const I18N = {
    'en': {
        'menu_title': 'Rhythm',
        'play_levels': 'Play Levels',
        'editor': 'Open Editor',
        'edit_levels': 'Edit Levels',
        'settings': 'Settings',
        'mods': 'Mods',
        'settings_title': 'Settings',
        'graphics_quality': 'Graphics Quality',
        'effects_enabled': 'Effects Enabled',
        'effects_mode': 'Effects Mode',
        'visible_lead': 'Visible Lead (ms)',
        'linger': 'Linger at Center (ms)',
        'language': 'Language',
        'parallax_circles': 'Parallax Circles',
        'layered_hitsounds': 'Layered Hit Sounds',
        'pitch_shift_combo': 'Pitch Shift Combo',
        'lowpass_on_bad': 'Lowpass on Bad',
        'hit_window': 'Hit Window (ms)',
        'music_volume': 'Music Volume',
        'sfx_volume': 'SFX Volume',
        'fullscreen': 'Fullscreen',
        'hint_settings': 'UP/DOWN select, LEFT/RIGHT change, ENTER/ESC save & back (Hint: disable Effects if laggy)',
        'hint_menu': 'UP/DOWN or MOUSE to select, ENTER/CLICK to activate, ESC to quit',
        'hint_levels': 'UP/DOWN to select, ENTER/CLICK to play, ESC to back',
        'hint_mods': 'UP/DOWN to select, ENTER/SPACE to toggle, ESC to back',
        'exit_question': 'Вы уверены что хотите выйти?',
        'yes': 'Да (Enter)',
        'no': 'Нет (Esc)'
    },
    'ru': {
        'menu_title': 'Ритм',
        'play_levels': 'Играть уровни',
        'editor': 'Редактор',
        'edit_levels': 'Редактировать уровни',
        'settings': 'Настройки',
        'mods': 'Моды',
        'settings_title': 'Настройки',
        'graphics_quality': 'Качество графики',
        'effects_enabled': 'Эффекты включены',
        'effects_mode': 'Режим эффектов',
        'visible_lead': 'Появление ноты (мс)',
        'linger': 'Время в центре (мс)',
        'language': 'Язык',
        'parallax_circles': 'Параллакс круги',
        'layered_hitsounds': 'Слоистые звуки',
        'pitch_shift_combo': 'Высота по комбо',
        'lowpass_on_bad': 'Приглушение при промахе',
        'hit_window': 'Окно попадания (мс)',
        'music_volume': 'Громкость музыки',
        'sfx_volume': 'Громкость звуков',
        'fullscreen': 'Полный экран',
        'hint_settings': 'ВВЕРХ/ВНИЗ выбор, ВЛЕВО/ВПРАВО изменить, ENTER/ESC сохранить (Если лагает — отключите эффекты)',
        'hint_menu': 'UP/DOWN or MOUSE to select, ENTER/CLICK to activate, ESC to quit',
        'hint_levels': 'UP/DOWN to select, ENTER/CLICK to play, ESC to back',
        'hint_mods': 'UP/DOWN выбор, ENTER/SPACE переключить, ESC назад',
        'exit_question': 'Вы уверены что хотите выйти?',
        'yes': 'Да (Enter)',
        'no': 'Нет (Esc)'
    }
};

export class CanvasMenu {
    constructor(canvas, audioManager, onPlayLevelCallback, onOpenEditorCallback) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d', { alpha: false });
        this.audio = audioManager;
        this.onPlayLevel = onPlayLevelCallback;
        this.onOpenEditor = onOpenEditorCallback;

        // Current UI state: 'menu' | 'levels' | 'settings' | 'mods' | 'exit_dialog'
        this.screenState = 'menu';
        this.returnScreenState = 'menu';

        this.selected = 0;
        this.scales = [1.0, 1.0, 1.0, 1.0, 1.0];
        this.timeAcc = 0;
        this.fps = 60;
        this.fpsCounter = 0;
        this.fpsLastTime = performance.now();

        this.mouseX = 0;
        this.mouseY = 0;

        // Settings from config/settings.json
        this.settings = this.loadSettings();

        // Level files list (levels/*.json)
        this.levelFiles = [
            { path: 'levels/easy.json', name: 'easy.json', title: 'Easy' },
            { path: 'levels/medium.json', name: 'medium.json', title: 'Medium' },
            { path: 'levels/hard.json', name: 'hard.json', title: 'Hard' },
            { path: 'levels/Welcome.json', name: 'Welcome.json', title: 'Welcome' },
            { path: 'levels/official_long_easy.json', name: 'official_long_easy.json', title: 'Official Long Easy' },
            { path: 'levels/official_long_hard.json', name: 'official_long_hard.json', title: 'Official Long Hard' },
            { path: 'levels/sample_level.json', name: 'sample_level.json', title: 'Sample' },
            { path: 'levels/Custom.json', name: 'Custom.json', title: 'Custom' },
            { path: 'levels/test.json', name: 'test.json', title: 'test' }
        ];

        // Settings navigation
        this.activeCat = 0;
        this.settingsIdx = 0;

        // Mods list
        // Mods list from modSystem
        this.mods = [];
        for (const mod of modSystem.mods.values()) {
            this.mods.push({
                id: mod.id,
                name: mod.name,
                version: mod.version,
                desc: mod.desc,
                enabled: mod.enabled
            });
        }

        this.fadeAlpha = 0.0;

        this.boundOnKeyDown = this.onKeyDown.bind(this);
        this.boundOnMouseMove = this.onMouseMove.bind(this);
        this.boundOnMouseDown = this.onMouseDown.bind(this);
        this.boundOnWheel = this.onWheel.bind(this);
        this.boundOnPointerDown = (e) => {
            if (e.pointerType === 'mouse' && e.button !== 0) return;
            if (e.cancelable) e.preventDefault();
            this.audio.init();
            const fakeE = {
                button: 0,
                clientX: e.clientX,
                clientY: e.clientY
            };
            this.onMouseDown(fakeE);
        };

        this.initInput();
    }

    t(key) {
        const lang = this.settings.ui.language || 'ru';
        const dict = I18N[lang] || I18N['ru'];
        return dict[key] || key;
    }

    loadSettings() {
        const saved = localStorage.getItem('keyy_full_settings');
        if (saved) {
            try { return JSON.parse(saved); } catch(e) {}
        }
        return {
            graphics: {
                quality: 'high',
                effects_enabled: true,
                effects_mode: 'full',
                fullscreen: true,
                parallax_circles: true
            },
            timing: {
                visible_lead_ms: 1200,
                linger_ms: 200,
                hit_window_ms: 120,
                difficulty: 'normal',
                offset_ms: 0
            },
            audio: {
                music_volume: 0.8,
                sfx_volume: 0.9,
                layered_hitsounds: true,
                pitch_shift_combo: true,
                lowpass_on_bad: true
            },
            ui: {
                language: 'ru'
            }
        };
    }

    saveSettings() {
        localStorage.setItem('keyy_full_settings', JSON.stringify(this.settings));
        this.audio.setMusicVolume(this.settings.audio.music_volume);
        this.audio.setSfxVolume(this.settings.audio.sfx_volume);
        this.audio.setUserOffset(this.settings.timing.offset_ms);
    }

    initInput() {
        window.addEventListener('keydown', this.boundOnKeyDown);
        window.addEventListener('mousemove', this.boundOnMouseMove);
        window.addEventListener('mousedown', this.boundOnMouseDown);
        window.addEventListener('wheel', this.boundOnWheel, { passive: false });
        this.canvas.addEventListener('pointerdown', this.boundOnPointerDown);
    }

    destroyInput() {
        window.removeEventListener('keydown', this.boundOnKeyDown);
        window.removeEventListener('mousemove', this.boundOnMouseMove);
        window.removeEventListener('mousedown', this.boundOnMouseDown);
        window.removeEventListener('wheel', this.boundOnWheel);
        this.canvas.removeEventListener('pointerdown', this.boundOnPointerDown);
    }

    getCanvasPos(e) {
        const rect = this.canvas.getBoundingClientRect();
        const clientX = e.clientX !== undefined ? e.clientX : (e.touches ? e.touches[0].clientX : 0);
        const clientY = e.clientY !== undefined ? e.clientY : (e.touches ? e.touches[0].clientY : 0);
        const px = (clientX - rect.left) * (this.canvas.width / rect.width);
        const py = (clientY - rect.top) * (this.canvas.height / rect.height);
        const scale = this.canvas.height / 720;
        return {
            x: px / scale,
            y: py / scale
        };
    }

    onMouseMove(e) {
        const pos = this.getCanvasPos(e);
        this.mouseX = pos.x;
        this.mouseY = pos.y;
    }

    onWheel(e) {
        if (this.screenState === 'levels') {
            e.preventDefault();
            if (e.deltaY > 0) {
                this.selected = Math.min(this.levelFiles.length - 1, this.selected + 1);
            } else {
                this.selected = Math.max(0, this.selected - 1);
            }
        } else if (this.screenState === 'settings') {
            e.preventDefault();
            if (e.deltaY > 0) {
                this.settingsIdx++;
            } else {
                this.settingsIdx = Math.max(0, this.settingsIdx - 1);
            }
        }
    }

    onKeyDown(e) {
        this.audio.init();

        if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space'].includes(e.code)) {
            e.preventDefault();
        }

        // Exit Dialog input (game/menu.py lines 160-168)
        if (this.screenState === 'exit_dialog') {
            if (e.key === 'Enter') {
                window.location.reload();
            } else if (e.key === 'Escape') {
                this.screenState = this.returnScreenState;
            }
            return;
        }

        // Main Menu input (game/menu.py lines 205-236)
        if (this.screenState === 'menu') {
            const menuItemsCount = 5;
            if (e.key === 'Escape') {
                this.audio.playSfx('hit');
                this.returnScreenState = 'menu';
                this.screenState = 'exit_dialog';
            } else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'KeyS' || e.key === 'ы' || e.key === 'Ы') {
                this.selected = (this.selected + 1) % menuItemsCount;
                this.audio.playSfx('hit');
            } else if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'KeyW' || e.key === 'ц' || e.key === 'Ц') {
                this.selected = (this.selected - 1 + menuItemsCount) % menuItemsCount;
                this.audio.playSfx('hit');
            } else if (e.key === 'Enter' || e.key === 'Space') {
                this.activateMenuItem(this.selected);
            }
        } else if (this.screenState === 'levels') {
            if (e.key === 'Escape') {
                this.audio.playSfx('hit');
                this.screenState = 'menu';
                this.selected = 0;
            } else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'KeyS' || e.key === 'ы' || e.key === 'Ы') {
                this.selected = (this.selected + 1) % this.levelFiles.length;
                this.audio.playSfx('hit');
            } else if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'KeyW' || e.key === 'ц' || e.key === 'Ц') {
                this.selected = (this.selected - 1 + this.levelFiles.length) % this.levelFiles.length;
                this.audio.playSfx('hit');
            } else if (e.key === 'Enter' || e.key === 'Space') {
                this.playSelectedLevel();
            }
        } else if (this.screenState === 'settings') {
            this.handleSettingsKey(e);
        } else if (this.screenState === 'mods') {
            if (e.key === 'Escape') {
                this.screenState = 'menu';
                this.selected = 4;
            } else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'KeyS' || e.key === 'ы' || e.key === 'Ы') {
                this.selected = (this.selected + 1) % this.mods.length;
                this.audio.playSfx('hit');
            } else if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'KeyW' || e.key === 'ц' || e.key === 'Ц') {
                this.selected = (this.selected - 1 + this.mods.length) % this.mods.length;
                this.audio.playSfx('hit');
            } else if (e.key === 'Enter' || e.key === 'Space') {
                const targetMod = this.mods[this.selected];
                if (targetMod) {
                    modSystem.toggleMod(targetMod.id);
                    targetMod.enabled = modSystem.getMod(targetMod.id).enabled;
                    this.audio.playSfx('hit');
                }
            }
        }
    }

    onMouseDown(e) {
        if (e.button !== undefined && e.button !== 0) return;
        this.audio.init();

        const scale = this.canvas.height / 720;
        const w = this.canvas.width / scale;
        const h = 720;
        const pos = this.getCanvasPos(e);
        const mx = pos.x;
        const my = pos.y;

        // 1. Exit Dialog
        if (this.screenState === 'exit_dialog') {
            const dialogY = (h - 200) / 2;
            // "Да (Enter)" button at center (w//2 - 80, dialog_y + 130)
            if (this.isInsideRect(mx, my, w/2 - 140, dialogY + 110, 120, 40)) {
                window.location.reload();
                return;
            }
            // "Нет (Esc)" button at center (w//2 + 80, dialog_y + 130)
            if (this.isInsideRect(mx, my, w/2 + 20, dialogY + 110, 120, 40)) {
                this.screenState = this.returnScreenState;
                return;
            }
            return;
        }

        // 2. Main Menu Click (exact button bounds)
        if (this.screenState === 'menu') {
            const startY = 195;
            const gap = 82;
            const bw = 380;
            const bh = 58;

            for (let i = 0; i < 5; i++) {
                const cx = w / 2;
                const cy = startY + i * gap;
                if (this.isInsideRect(mx, my, cx - bw/2 - 15, cy - bh/2 - 10, bw + 30, bh + 20)) {
                    this.selected = i;
                    this.activateMenuItem(i);
                    return;
                }
            }
            return;
        }

        // 3. Level Select Click
        if (this.screenState === 'levels') {
            const startY = 190;
            const gap = 58;
            const bw = 520;
            const bh = 48;
            const visibleCount = Math.floor((h - startY - 80) / gap);

            const topIndex = Math.max(0, Math.min(this.selected - Math.floor(visibleCount / 2), this.levelFiles.length - visibleCount));
            const endIndex = Math.min(this.levelFiles.length, topIndex + visibleCount);

            for (let i = topIndex; i < endIndex; i++) {
                const cy = startY + (i - topIndex) * gap;
                const cx = w / 2;
                if (this.isInsideRect(mx, my, cx - bw/2 - 10, cy - bh/2 - 5, bw + 20, bh + 10)) {
                    this.selected = i;
                    this.playSelectedLevel();
                    return;
                }
            }
            return;
        }

        // 4. Settings Screen Click
        if (this.screenState === 'settings') {
            this.handleSettingsClick(mx, my);
            return;
        }

        // 5. Mods Screen Click
        if (this.screenState === 'mods') {
            const startY = Math.floor(h * 0.25);
            const gap = 70;
            const bw = Math.min(800, w - 80);
            const bh = 56;

            for (let i = 0; i < this.mods.length; i++) {
                const cy = startY + i * gap + bh / 2;
                const cx = w / 2;
                if (this.isInsideRect(mx, my, cx - bw/2, cy - bh/2, bw, bh)) {
                    this.selected = i;
                    const targetMod = this.mods[i];
                    if (targetMod) {
                        modSystem.toggleMod(targetMod.id);
                        targetMod.enabled = modSystem.getMod(targetMod.id).enabled;
                        this.audio.playSfx('hit');
                    }
                    return;
                }
            }
        }
    }

    activateMenuItem(index) {
        this.audio.playSfx('perfect');
        this.fadeAlpha = 0.35; // Quick smooth transition flash

        if (index === 0) {
            this.screenState = 'levels';
            this.selected = 0;
        } else if (index === 1 || index === 2) {
            // Open Editor / Edit Levels
            if (this.onOpenEditor) {
                this.onOpenEditor();
            }
        } else if (index === 3) {
            this.screenState = 'settings';
            this.activeCat = 0;
            this.settingsIdx = 0;
        } else if (index === 4) {
            this.screenState = 'mods';
            this.selected = 0;
        }
    }

    async playSelectedLevel() {
        const file = this.levelFiles[this.selected];
        if (!file) return;
        this.audio.playSfx('perfect');

        try {
            const { LevelData } = await import('../game/level.js');
            const levelData = await LevelData.loadFromUrl(file.path);
            levelData.id = file.name;
            this.onPlayLevel(levelData);
        } catch(err) {
            alert(`Ошибка загрузки уровня: ${err.message}`);
            this.screenState = 'levels';
        }
    }

    // --- RENDER PIPELINE ---

    render(dt) {
        const ctx = this.ctx;
        const rawW = this.canvas.width;
        const rawH = this.canvas.height;
        this.timeAcc += dt;

        // Base design HD virtual height: 720
        const vh = 720;
        const scale = rawH / vh;
        const vw = rawW / scale;

        ctx.save();
        ctx.scale(scale, scale);

        // FPS counter
        this.fpsCounter++;
        const now = performance.now();
        if (now - this.fpsLastTime >= 1000) {
            this.fps = this.fpsCounter;
            this.fpsCounter = 0;
            this.fpsLastTime = now;
        }

        // 1. Exact Pygame draw_menu_background (game/menu.py lines 419-450)
        this.drawMenuBackground(ctx, vw, vh, this.timeAcc);

        // 2. Active Screen Content
        let isCursorPointer = false;

        if (this.screenState === 'menu') {
            isCursorPointer = this.renderMainMenu(ctx, vw, vh, dt);
        } else if (this.screenState === 'levels') {
            isCursorPointer = this.renderLevelsScreen(ctx, vw, vh, dt);
        } else if (this.screenState === 'settings') {
            isCursorPointer = this.renderSettingsScreen(ctx, vw, vh, dt);
        } else if (this.screenState === 'mods') {
            isCursorPointer = this.renderModsScreen(ctx, vw, vh, dt);
        }

        // 3. Exit Confirmation Dialog (game/menu.py lines 115-170)
        if (this.screenState === 'exit_dialog') {
            this.renderExitDialog(ctx, vw, vh);
            isCursorPointer = true;
        }

        // Update mouse cursor style
        this.canvas.style.cursor = isCursorPointer ? 'pointer' : 'default';

        // 4. FPS counter (top right, menu.py line 265: color (150, 150, 150))
        ctx.fillStyle = 'rgb(150, 150, 150)';
        ctx.font = '24px sans-serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'top';
        ctx.fillText(`FPS: ${this.fps}`, vw - 15, 12);

        // 5. Smooth fade decay
        if (this.fadeAlpha > 0.01) {
            ctx.fillStyle = `rgba(0, 0, 0, ${this.fadeAlpha.toFixed(2)})`;
            ctx.fillRect(0, 0, vw, vh);
            this.fadeAlpha = Math.max(0, this.fadeAlpha - dt * 4);
        }

        ctx.restore();
    }

    drawMenuBackground(ctx, w, h, t) {
        const cx = w * 0.5;
        const cy = h * 0.5;
        const mx = this.mouseX;
        const my = this.mouseY;

        // Gradient stripes step = 4 (menu.py lines 426-432)
        const step = 4;
        for (let y = 0; y < h; y += step) {
            const k = y / h;
            const r = Math.floor(16 + 10 * (1 + Math.sin(t + k * 6)) * 0.5);
            const g = Math.floor(18 + 12 * (1 + Math.sin(t * 0.8 + k * 5)) * 0.5);
            const b = Math.floor(28 + 14 * (1 + Math.cos(t * 0.6 + k * 4)) * 0.5);
            ctx.fillStyle = `rgb(${r},${g},${b})`;
            ctx.fillRect(0, y, w, step);
        }

        if (!this.settings.graphics.parallax_circles) return;

        // Parallax layers (menu.py lines 435-449)
        const layers = [
            { count: 12, radius: 90, alpha: 24 / 255, speed: 0.05, parallax: 0.02 },
            { count: 8,  radius: 140, alpha: 18 / 255, speed: 0.03, parallax: 0.035 },
            { count: 5,  radius: 220, alpha: 12 / 255, speed: 0.02, parallax: 0.05 }
        ];

        for (let li = 0; li < layers.length; li++) {
            const layer = layers[li];
            for (let i = 0; i < layer.count; i++) {
                const ang = t * layer.speed + (i * 6.28318 / Math.max(1, layer.count)) + li;
                const rx = cx + Math.cos(ang) * (0.28 * w) + (mx - cx) * layer.parallax;
                const ry = cy + Math.sin(ang * 0.8) * (0.28 * h) + (my - cy) * layer.parallax;
                const rad = layer.radius;

                ctx.save();
                ctx.beginPath();
                ctx.arc(rx, ry, rad, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${120 + li * 20}, ${160 + li * 10}, ${240 - li * 20}, ${layer.alpha})`;
                ctx.fill();
                ctx.restore();
            }
        }
    }

    drawButton(ctx, centerX, centerY, width, height, label, fontSize, hovered, selected) {
        const pulse = 0.5 + 0.5 * Math.sin(performance.now() * 0.004);
        const baseCol = 'rgb(36, 90, 160)';
        const hlCol = 'rgb(40, 120, 200)';
        const col = (hovered || selected) ? hlCol : baseCol;
        const x = centerX - width / 2;
        const y = centerY - height / 2;

        // Glow around button (menu.py lines 89-93)
        if (hovered || selected) {
            ctx.save();
            const glowAlpha = (70 * pulse + 30) / 255;
            ctx.fillStyle = `rgba(120, 200, 255, ${glowAlpha.toFixed(2)})`;
            this.roundRect(ctx, x - 8, y - 8, width + 16, height + 16, 18, true, false);
            ctx.restore();
        }

        // Button body (menu.py line 94: border_radius 14)
        ctx.fillStyle = col;
        this.roundRect(ctx, x, y, width, height, 14, true, false);

        // Button text (menu.py line 95: (230,230,230))
        ctx.fillStyle = 'rgb(230, 230, 230)';
        ctx.font = `${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, centerX, centerY);
    }

    renderMainMenu(ctx, w, h, dt) {
        // Title (menu.py line 241: title_font 60, center=(w//2, int(h*0.18)))
        ctx.fillStyle = 'rgb(230, 230, 230)';
        ctx.font = '54px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.t('menu_title'), w / 2, 105);

        const menuItems = [
            this.t('play_levels'),
            this.t('editor'),
            this.t('edit_levels'),
            this.t('settings'),
            this.t('mods')
        ];

        const startY = 195;
        const gap = 82;
        const bw = 380;
        const bh = 58;

        let isAnyHovered = false;

        for (let i = 0; i < menuItems.length; i++) {
            const targetScale = (i === this.selected) ? 1.06 : 1.0;
            this.scales[i] += (targetScale - this.scales[i]) * Math.min(1.0, dt * 8);
            const scale = this.scales[i];

            const curW = Math.floor(bw * scale);
            const curH = Math.floor(bh * scale);
            const cx = w / 2;
            const cy = startY + i * gap;

            const isHover = this.isInsideRect(this.mouseX, this.mouseY, cx - curW/2 - 10, cy - curH/2 - 5, curW + 20, curH + 10);
            if (isHover) {
                this.selected = i;
                isAnyHovered = true;
            }

            this.drawButton(ctx, cx, cy, curW, curH, menuItems[i], Math.round(30 * scale), isHover, i === this.selected);
        }

        // Hint (menu.py line 260: hint_font 24, center=(w//2, h-60))
        ctx.fillStyle = 'rgb(200, 210, 230)';
        ctx.font = '20px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.t('hint_menu'), w / 2, h - 35);

        return isAnyHovered;
    }

    renderLevelsScreen(ctx, w, h, dt) {
        ctx.fillStyle = 'rgb(230, 230, 230)';
        ctx.font = '54px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Select Level', w / 2, 105);

        const startY = 190;
        const gap = 58;
        const bw = 520;
        const bh = 48;
        const visibleCount = Math.floor((h - startY - 80) / gap);

        let isAnyHovered = false;

        const topIndex = Math.max(0, Math.min(this.selected - Math.floor(visibleCount / 2), this.levelFiles.length - visibleCount));
        const endIndex = Math.min(this.levelFiles.length, topIndex + visibleCount);

        for (let i = topIndex; i < endIndex; i++) {
            const file = this.levelFiles[i];
            const cy = startY + (i - topIndex) * gap;
            const cx = w / 2;

            const hsKey = `keyy_hs_${file.name}`;
            const hsSaved = localStorage.getItem(hsKey);
            let percent = 0;
            if (hsSaved) {
                try { percent = Math.round(JSON.parse(hsSaved).accuracy); } catch(e) {}
            }

            const label = `${file.name}  —  ${percent}%`;
            const isHover = this.isInsideRect(this.mouseX, this.mouseY, cx - bw/2, cy - bh/2, bw, bh);
            if (isHover) {
                this.selected = i;
                isAnyHovered = true;
            }

            this.drawButton(ctx, cx, cy, bw, bh, label, 28, isHover, i === this.selected);
        }

        // Hint (menu.py line 512: center=(w//2, h-60))
        ctx.fillStyle = 'rgb(200, 210, 230)';
        ctx.font = '20px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.t('hint_levels'), w / 2, h - 35);

        return isAnyHovered;
    }

    renderSettingsScreen(ctx, w, h, dt) {
        ctx.fillStyle = 'rgb(230, 230, 230)';
        ctx.font = '60px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.t('settings_title'), w / 2, Math.floor(h * 0.18));

        const cats = [
            { name: 'Graphics', items: [
                { name: this.t('graphics_quality'), choices: ['low', 'medium', 'high'], path: ['graphics', 'quality'] },
                { name: this.t('effects_enabled'), choices: ['True', 'False'], path: ['graphics', 'effects_enabled'] },
                { name: this.t('effects_mode'), choices: ['off', 'light', 'full'], path: ['graphics', 'effects_mode'] },
                { name: this.t('fullscreen'), choices: ['True', 'False'], path: ['graphics', 'fullscreen'] },
                { name: this.t('parallax_circles'), choices: ['True', 'False'], path: ['graphics', 'parallax_circles'] }
            ]},
            { name: 'Timing', items: [
                { name: this.t('visible_lead'), choices: [], path: ['timing', 'visible_lead_ms'] },
                { name: this.t('linger'), choices: [], path: ['timing', 'linger_ms'] },
                { name: this.t('hit_window'), choices: [], path: ['timing', 'hit_window_ms'] },
                { name: 'Difficulty', choices: ['easy', 'normal', 'hard', 'insane'], path: ['timing', 'difficulty'] }
            ]},
            { name: 'Audio', items: [
                { name: this.t('music_volume'), choices: [], path: ['audio', 'music_volume'] },
                { name: this.t('sfx_volume'), choices: [], path: ['audio', 'sfx_volume'] },
                { name: this.t('layered_hitsounds'), choices: ['True', 'False'], path: ['audio', 'layered_hitsounds'] },
                { name: this.t('pitch_shift_combo'), choices: ['True', 'False'], path: ['audio', 'pitch_shift_combo'] },
                { name: this.t('lowpass_on_bad'), choices: ['True', 'False'], path: ['audio', 'lowpass_on_bad'] }
            ]},
            { name: 'UI', items: [
                { name: this.t('language'), choices: ['ru', 'en'], path: ['ui', 'language'] }
            ]}
        ];

        let isAnyHovered = false;

        // Sidebar categories (menu.py line 625: x=40, cat_start_y=int(h*0.30), sidebar_w=260, h=44, gap=56)
        const sidebarW = 260;
        const catStartY = Math.floor(h * 0.30);
        const catGap = 56;
        for (let ci = 0; ci < cats.length; ci++) {
            const cy = catStartY + ci * catGap + 22;
            const cx = 40 + sidebarW / 2;
            const isHover = this.isInsideRect(this.mouseX, this.mouseY, 40, catStartY + ci * catGap, sidebarW, 44);
            if (isHover) isAnyHovered = true;
            this.drawButton(ctx, cx, cy, sidebarW, 44, cats[ci].name, 28, isHover, ci === this.activeCat);
        }

        // Content list (menu.py line 635)
        const contentX = 40 + sidebarW + 40;
        const startY = Math.floor(h * 0.28);
        const gap = 56;
        const bw = Math.min(720, w - contentX - 40);
        const bh = 48;
        const items = cats[this.activeCat].items;

        for (let i = 0; i < items.length; i++) {
            const it = items[i];
            const val = this.settings[it.path[0]][it.path[1]];
            const disp = `${it.name}: ${val}`;
            const cy = startY + i * gap + bh / 2;
            const cx = contentX + bw / 2;

            const isHover = this.isInsideRect(this.mouseX, this.mouseY, contentX, startY + i * gap, bw, bh);
            if (isHover) {
                this.settingsIdx = i;
                isAnyHovered = true;
            }

            this.drawButton(ctx, cx, cy, bw, bh, disp, 26, isHover, i === this.settingsIdx);
        }

        // Hint (menu.py line 655: center=(w//2, h-60))
        ctx.fillStyle = 'rgb(230, 230, 230)';
        ctx.font = '22px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.t('hint_settings'), w / 2, h - 60);

        return isAnyHovered;
    }

    handleSettingsKey(e) {
        if (e.key === 'Escape' || e.key === 'Enter') {
            this.saveSettings();
            this.screenState = 'menu';
            this.selected = 3;
            return;
        }

        const counts = [5, 4, 5, 1];

        if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'KeyA' || e.key === 'ф' || e.key === 'Ф') {
            this.modifySettingValue(-1);
        } else if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'KeyD' || e.key === 'в' || e.key === 'В') {
            this.modifySettingValue(1);
        } else if (e.key === 'ArrowUp' || e.key === 'w' || e.key === 'KeyW' || e.key === 'ц' || e.key === 'Ц') {
            this.settingsIdx = Math.max(0, this.settingsIdx - 1);
            this.audio.playSfx('hit');
        } else if (e.key === 'ArrowDown' || e.key === 's' || e.key === 'KeyS' || e.key === 'ы' || e.key === 'Ы') {
            this.settingsIdx = Math.min(counts[this.activeCat] - 1, this.settingsIdx + 1);
            this.audio.playSfx('hit');
        } else if (e.key === 'Tab') {
            this.activeCat = (this.activeCat + 1) % 4;
            this.settingsIdx = 0;
            this.audio.playSfx('hit');
        }
    }

    handleSettingsClick(mx, my) {
        const h = this.canvas.height;
        const sidebarW = 260;
        const catStartY = Math.floor(h * 0.30);
        const catGap = 56;

        for (let ci = 0; ci < 4; ci++) {
            const y = catStartY + ci * catGap;
            if (this.isInsideRect(mx, my, 40, y, sidebarW, 44)) {
                this.activeCat = ci;
                this.settingsIdx = 0;
                this.audio.playSfx('hit');
                return;
            }
        }

        this.modifySettingValue(1);
    }

    modifySettingValue(dir) {
        const catKeys = ['graphics', 'timing', 'audio', 'ui'];
        const cat = catKeys[this.activeCat];
        const s = this.settings;

        if (cat === 'graphics') {
            const keys = ['quality', 'effects_enabled', 'effects_mode', 'fullscreen', 'parallax_circles'];
            const k = keys[this.settingsIdx];
            if (typeof s.graphics[k] === 'boolean') {
                s.graphics[k] = !s.graphics[k];
            } else if (k === 'quality') {
                const q = ['low', 'medium', 'high'];
                s.graphics[k] = q[(q.indexOf(s.graphics[k]) + dir + 3) % 3];
            } else if (k === 'effects_mode') {
                const em = ['off', 'light', 'full'];
                s.graphics[k] = em[(em.indexOf(s.graphics[k]) + dir + 3) % 3];
            }
        } else if (cat === 'timing') {
            const keys = ['visible_lead_ms', 'linger_ms', 'hit_window_ms', 'difficulty'];
            const k = keys[this.settingsIdx];
            if (k === 'difficulty') {
                const d = ['easy', 'normal', 'hard', 'insane'];
                s.timing[k] = d[(d.indexOf(s.timing[k]) + dir + 4) % 4];
            } else {
                s.timing[k] = Math.max(20, s.timing[k] + dir * 50);
            }
        } else if (cat === 'audio') {
            const keys = ['music_volume', 'sfx_volume', 'layered_hitsounds', 'pitch_shift_combo', 'lowpass_on_bad'];
            const k = keys[this.settingsIdx];
            if (typeof s.audio[k] === 'boolean') {
                s.audio[k] = !s.audio[k];
            } else {
                s.audio[k] = Math.max(0, Math.min(1, Math.round((s.audio[k] + dir * 0.1) * 10) / 10));
            }
        } else if (cat === 'ui') {
            s.ui.language = s.ui.language === 'ru' ? 'en' : 'ru';
        }

        this.audio.playSfx('hit');
        this.saveSettings();
    }

    renderModsScreen(ctx, w, h, dt) {
        ctx.fillStyle = 'rgb(230, 230, 230)';
        ctx.font = '60px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('Управление модами', w / 2, Math.floor(h * 0.15));

        const startY = Math.floor(h * 0.25);
        const gap = 70;
        const bw = Math.min(800, w - 80);
        const bh = 56;

        let isAnyHovered = false;

        for (let i = 0; i < this.mods.length; i++) {
            const mod = this.mods[i];
            mod.enabled = modSystem.getMod(mod.id)?.enabled ?? mod.enabled;
            const cy = startY + i * gap + bh / 2;
            const cx = w / 2;

            const isHover = this.isInsideRect(this.mouseX, this.mouseY, cx - bw/2, cy - bh/2, bw, bh);
            if (isHover) {
                this.selected = i;
                isAnyHovered = true;
            }

            const status = mod.enabled ? '[ВКЛ]' : '[ВЫКЛ]';
            const label = `${status} ${mod.name} v${mod.version}`;

            this.drawButton(ctx, cx, cy, bw, bh, label, 28, isHover, i === this.selected);

            ctx.fillStyle = 'rgb(180, 180, 180)';
            ctx.font = '18px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillText(mod.desc, w / 2, cy + bh / 2 + 4);
        }

        ctx.fillStyle = 'rgb(230, 230, 230)';
        ctx.font = '24px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.t('hint_mods'), w / 2, h - 60);

        return isAnyHovered;
    }

    renderExitDialog(ctx, w, h) {
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        ctx.fillRect(0, 0, w, h);

        const dw = 400;
        const dh = 200;
        const dx = (w - dw) / 2;
        const dy = (h - dh) / 2;

        ctx.fillStyle = 'rgb(40, 40, 50)';
        ctx.strokeStyle = 'rgb(100, 100, 120)';
        ctx.lineWidth = 2;
        this.roundRect(ctx, dx, dy, dw, dh, 10, true, true);

        ctx.fillStyle = 'rgb(255, 255, 255)';
        ctx.font = '36px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.t('exit_question'), w / 2, dy + 60);

        const yesCx = w / 2 - 80;
        const yesCy = dy + 130;
        ctx.fillStyle = 'rgb(60, 20, 20)';
        this.roundRect(ctx, yesCx - 60, yesCy - 20, 120, 40, 5, true, false);
        ctx.fillStyle = 'rgb(255, 100, 100)';
        ctx.font = '30px sans-serif';
        ctx.fillText(this.t('yes'), yesCx, yesCy);

        const noCx = w / 2 + 80;
        const noCy = dy + 130;
        ctx.fillStyle = 'rgb(20, 60, 20)';
        this.roundRect(ctx, noCx - 60, noCy - 20, 120, 40, 5, true, false);
        ctx.fillStyle = 'rgb(100, 255, 100)';
        ctx.font = '30px sans-serif';
        ctx.fillText(this.t('no'), noCx, noCy);
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

    isInsideRect(px, py, rx, ry, rw, rh) {
        return px >= rx && px <= rx + rw && py >= ry && py <= ry + rh;
    }
}
