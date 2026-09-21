import os
import math
import pygame
from typing import List, Tuple
import glob

from .level import load_level
from .main import play_level
from .editor import run_editor
from .settings import load_settings, save_settings, get_highscore
from .mod_system import mod_system

I18N = {
    'en': {
        'menu_title': 'Rhythm',
        'play_levels': 'Play Levels',
        'editor': 'Open Editor',
        'settings': 'Settings',
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
        'hint_settings': 'UP/DOWN select, LEFT/RIGHT change, ENTER/ESC save & back (Hint: disable Effects if laggy)'
    },
    'ru': {
        'menu_title': 'Ритм',
        'play_levels': 'Играть уровни',
        'editor': 'Редактор',
        'settings': 'Настройки',
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
        'hint_settings': 'ВВЕРХ/ВНИЗ выбор, ВЛЕВО/ВПРАВО изменить, ENTER/ESC сохранить (Если лагает — отключите эффекты)'
    }
}

COLOR_BG = (16, 18, 28)
COLOR_TEXT = (230, 230, 230)
COLOR_HL = (120, 200, 255)

def labels(settings):
    lang = settings.get('ui',{}).get('language','en')
    return I18N.get(lang, I18N['en'])

MENU_ITEMS = [
    ("Play Levels", "__levels__"),
    ("Open Editor", "__editor__"),
    ("Settings", "__settings__"),
]


def ensure_fonts():
    if not pygame.font.get_init():
        pygame.font.init()
    title_font = pygame.font.Font(None, 60)
    item_font = pygame.font.Font(None, 36)  # Уменьшил размер для лучшего отображения
    hint_font = pygame.font.Font(None, 24)  # Уменьшил размер
    return title_font, item_font, hint_font


def draw_button(screen: pygame.Surface, rect: pygame.Rect, label: str, font: pygame.font.Font, hovered: bool, selected: bool) -> None:
    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.004)
    base_col = (36, 90, 160)
    hl_col = (40, 120, 200)
    col = hl_col if (hovered or selected) else base_col
    # glow
    if hovered or selected:
        glow = pygame.Surface((rect.width+16, rect.height+16), pygame.SRCALPHA)
        pygame.draw.rect(glow, (120, 200, 255, int(70 * pulse + 30)), glow.get_rect(), border_radius=18)
        screen.blit(glow, glow.get_rect(center=rect.center))
    pygame.draw.rect(screen, col, rect, border_radius=14)
    cap = font.render(label, True, (230,230,230))
    screen.blit(cap, cap.get_rect(center=rect.center))


def init_display_and_fonts():
    if not pygame.get_init():
        pygame.init()
    # Respect settings fullscreen flag
    try:
        settings = load_settings()
        fullscreen = bool(settings.get('graphics', {}).get('fullscreen', True))
    except Exception:
        fullscreen = True
    flags = pygame.FULLSCREEN if fullscreen else 0
    screen = pygame.display.set_mode((0, 0), flags)
    pygame.display.set_caption("KeyY — Menu")
    fonts = ensure_fonts()
    return screen, fonts


def show_exit_confirmation(screen, font):
    """Показывает диалог подтверждения выхода"""
    w, h = screen.get_size()
    
    # Полупрозрачный фон
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    
    # Окно диалога
    dialog_w, dialog_h = 400, 200
    dialog_x = (w - dialog_w) // 2
    dialog_y = (h - dialog_h) // 2
    
    # Фон диалога
    dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_w, dialog_h)
    pygame.draw.rect(screen, (40, 40, 50), dialog_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 120), dialog_rect, width=2, border_radius=10)
    
    # Текст вопроса
    question_font = pygame.font.Font(None, 36)
    question_text = question_font.render("Вы уверены что хотите выйти?", True, (255, 255, 255))
    question_rect = question_text.get_rect(center=(w//2, dialog_y + 60))
    screen.blit(question_text, question_rect)
    
    # Кнопки
    button_font = pygame.font.Font(None, 32)
    
    # Кнопка "Да"
    yes_text = button_font.render("Да (Enter)", True, (255, 100, 100))
    yes_rect = yes_text.get_rect(center=(w//2 - 80, dialog_y + 130))
    pygame.draw.rect(screen, (60, 20, 20), yes_rect.inflate(20, 10), border_radius=5)
    screen.blit(yes_text, yes_rect)
    
    # Кнопка "Нет"
    no_text = button_font.render("Нет (Esc)", True, (100, 255, 100))
    no_rect = no_text.get_rect(center=(w//2 + 80, dialog_y + 130))
    pygame.draw.rect(screen, (20, 60, 20), no_rect.inflate(20, 10), border_radius=5)
    screen.blit(no_text, no_rect)
    
    pygame.display.flip()
    
    # Ждем ответа пользователя
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True  # Выйти
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return True  # Выйти
                elif event.key == pygame.K_ESCAPE:
                    return False  # Остаться
        
        clock.tick(60)


def run_menu():
    screen, (title_font, item_font, hint_font) = init_display_and_fonts()
    clock = pygame.time.Clock()

    selected = 0
    running = True
    time_acc = 0.0

    settings = load_settings()
    texts = labels(settings)
    menu_items = [
        (texts['play_levels'], "__levels__"),
        (texts['editor'], "__editor__"),
        ("Edit Levels", "__edit_levels__"),
        (texts['settings'], "__settings__"),
        ("Моды", "__mods__"),
    ]

    item_rects: List[pygame.Rect] = []
    scales = [1.0 for _ in menu_items]

    while running:
        dt = clock.tick(60)
        time_acc += dt / 1000.0
        w, h = screen.get_size()
        mx, my = pygame.mouse.get_pos()
        click = False

        for i in range(len(scales)):
            target = 1.08 if i == selected else 1.0
            scales[i] += (target - scales[i]) * min(1.0, dt/120)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Показываем диалог подтверждения выхода
                if show_exit_confirmation(screen, hint_font):
                    running = False
            elif event.type == pygame.KEYDOWN:
                # Выполняем хуки модов для обработки клавиш
                results = mod_system.execute_mod_hooks("on_key_press", event, None, {})
                if any(results):  # Если какой-то мод обработал клавишу
                    continue
                    
                if event.key == pygame.K_ESCAPE:
                    # Показываем диалог подтверждения выхода
                    if show_exit_confirmation(screen, hint_font):
                        running = False
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(menu_items)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(menu_items)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    _, target = menu_items[selected]
                    screen, (title_font, item_font, hint_font) = activate_by_target(target)
                    # reload settings/i18n after returning
                    settings = load_settings()
                    texts = labels(settings)
                    menu_items = [
                        (texts['play_levels'], "__levels__"),
                        (texts['editor'], "__editor__"),
                        ("Edit Levels", "__edit_levels__"),
                        (texts['settings'], "__settings__"),
                        ("Моды", "__mods__"),
                    ]
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        draw_menu_background(screen, time_acc)

        title = title_font.render(texts['menu_title'], True, (230,230,230))
        tr = title.get_rect(center=(w//2, int(h*0.18)))
        screen.blit(title, tr)

        start_y = int(h*0.34)
        gap = 92
        item_rects = []
        for i, (label, _) in enumerate(menu_items):
            scale = scales[i]
            bw, bh = 360, 64
            cx, cy = w//2, start_y + i*gap
            rect = pygame.Rect(0, 0, int(bw*scale), int(bh*scale))
            rect.center = (cx, cy)
            hovered = rect.collidepoint(mx, my)
            if hovered:
                selected = i
            draw_button(screen, rect, label, item_font, hovered, i == selected)
            item_rects.append(rect)

        hint = hint_font.render("UP/DOWN or MOUSE to select, ENTER/CLICK to activate, ESC to quit", True, (230,230,230))
        hr = hint.get_rect(center=(w//2, h-60))
        screen.blit(hint, hr)

        # Draw FPS counter
        fps = int(clock.get_fps())
        fps_text = hint_font.render(f"FPS: {fps}", True, (150, 150, 150))
        screen.blit(fps_text, (w - fps_text.get_width() - 10, 10))
        
        # Выполняем хуки модов для отрисовки UI
        mod_system.execute_mod_hooks("on_draw_ui", screen, hint_font, None)

        pygame.display.flip()

        if click:
            for i, r in enumerate(item_rects):
                if r.collidepoint(mx, my):
                    _, target = menu_items[i]
                    screen, (title_font, item_font, hint_font) = activate_by_target(target)
                    settings = load_settings()
                    texts = labels(settings)
                    menu_items = [
                        (texts['play_levels'], "__levels__"),
                        (texts['editor'], "__editor__"),
                        ("Edit Levels", "__edit_levels__"),
                        (texts['settings'], "__settings__"),
                        ("Моды", "__mods__"),
                    ]
                    break

    pygame.quit()


def run_mods_screen():
    """Экран управления модами"""
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    title_font, item_font, hint_font = ensure_fonts()
    
    selected = 0
    running = True
    
    # Загружаем моды только один раз при входе в меню
    mod_system.scan_mods()
    
    while running:
        dt = clock.tick(60)
        w, h = screen.get_size()
        
        # Получаем список модов без повторного сканирования
        mods = mod_system.get_all_mods()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                # Выполняем хуки модов для обработки клавиш
                results = mod_system.execute_mod_hooks("on_key_press", event, None, {})
                if any(results):
                    continue
                    
                if event.key == pygame.K_ESCAPE:
                    return
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % max(1, len(mods))
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % max(1, len(mods))
                elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if mods and selected < len(mods):
                        mod_id = list(mod_system.mods.keys())[selected]
                        mod_system.toggle_mod(mod_id)
        
        # Отрисовка
        draw_menu_background(screen, pygame.time.get_ticks()/1000.0)
        
        title = title_font.render("Управление модами", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(w//2, int(h*0.15))))
        
        if not mods:
            no_mods_text = item_font.render("Нет установленных модов", True, COLOR_TEXT)
            screen.blit(no_mods_text, no_mods_text.get_rect(center=(w//2, h//2)))
            
            info_text = hint_font.render("Поместите .mod файлы или папки с модами в папку 'mods'", True, COLOR_TEXT)
            screen.blit(info_text, info_text.get_rect(center=(w//2, h//2 + 40)))
        else:
            start_y = int(h*0.25)
            gap = 56
            
            for i, mod in enumerate(mods):
                y_pos = start_y + i * gap
                bw, bh = 800, 56
                rect = pygame.Rect(0, 0, bw, bh)
                rect.center = (w//2, y_pos)
                hovered = rect.collidepoint(pygame.mouse.get_pos())
                if hovered:
                    selected = i
                status = "[ВКЛ]" if mod.enabled else "[ВЫКЛ]"
                label = f"{status} {mod.name} v{mod.version}"
                draw_button(screen, rect, label, item_font, hovered, i == selected)
                desc_surf = hint_font.render(mod.description, True, (180, 180, 180))
                screen.blit(desc_surf, desc_surf.get_rect(midtop=(rect.centerx, rect.bottom + 4)))
        
        hint = hint_font.render("UP/DOWN выбор, ENTER/SPACE переключить, ESC назад", True, COLOR_TEXT)
        screen.blit(hint, hint.get_rect(center=(w//2, h-60)))
        
        # Draw FPS counter
        fps = int(clock.get_fps())
        fps_text = hint_font.render(f"FPS: {fps}", True, (150, 150, 150))
        screen.blit(fps_text, (w - fps_text.get_width() - 10, 10))
        
        # Выполняем хуки модов для отрисовки UI
        mod_system.execute_mod_hooks("on_draw_ui", screen, hint_font, None)
        
        pygame.display.flip()
        # Mouse click toggles
        click = False
        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if event.button == 1:
                click = True
        if click and mods:
            mx, my = pygame.mouse.get_pos()
            for i, mod in enumerate(mods):
                rect = pygame.Rect(0, 0, 800, 56)
                rect.center = (w//2, start_y + i*gap)
                if rect.collidepoint(mx, my):
                    mod_id = list(mod_system.mods.keys())[i]
                    mod_system.toggle_mod(mod_id)
                    break


def activate_by_target(target: str):
    """Обрабатывает выбор пункта меню"""
    screen = pygame.display.get_surface()
    # fade out before leaving menu
    fade(screen, fade_out=True, duration_ms=250)
    
    if target == "__editor__":
        audio = "assets/sample.mp3"
        if not os.path.exists(audio):
            audio = "assets/sample.wav"
        if not os.path.exists(audio):
            print("No sample audio found in assets/. Place a file and reopen editor.")
        else:
            run_editor(audio_path=audio, title="Custom", artist="You", bpm=120.0, out_path=None, screen=screen)
    elif target == "__levels__":
        select_and_play_level()
    elif target == "__edit_levels__":
        select_and_edit_level()
    elif target == "__settings__":
        run_settings_screen()
    elif target == "__mods__":
        run_mods_screen()
    
    # re-init menu and fade in
    s, fonts = init_display_and_fonts()
    fade(s, fade_out=False, duration_ms=250)
    return s, fonts


def draw_menu_background(screen: pygame.Surface, t: float) -> None:
    import math
    w, h = screen.get_size()
    mx, my = pygame.mouse.get_pos()
    cx, cy = w * 0.5, h * 0.5
    
    # Градиентные полосы
    step = 4
    for y in range(0, h, step):
        k = y / h
        r = int(16 + 10 * (1 + math.sin(t + k * 6)) * 0.5)
        g = int(18 + 12 * (1 + math.sin(t * 0.8 + k * 5)) * 0.5)
        b = int(28 + 14 * (1 + math.cos(t * 0.6 + k * 4)) * 0.5)
        pygame.draw.rect(screen, (r, g, b), (0, y, w, step))
    
    # Параллакс-слои (круги/пятна)
    layers = [
        {"count": 12, "radius": 90, "alpha": 24, "speed": 0.05, "parallax": 0.02},
        {"count": 8,  "radius": 140, "alpha": 18, "speed": 0.03, "parallax": 0.035},
        {"count": 5,  "radius": 220, "alpha": 12, "speed": 0.02, "parallax": 0.05},
    ]
    for li, layer in enumerate(layers):
        for i in range(layer["count"]):
            ang = t * layer["speed"] + (i * 6.28318 / max(1, layer["count"])) + li
            rx = cx + math.cos(ang) * (0.28 * w) + (mx - cx) * layer["parallax"]
            ry = cy + math.sin(ang * 0.8) * (0.28 * h) + (my - cy) * layer["parallax"]
            rad = layer["radius"]
            surf = pygame.Surface((rad*2, rad*2), pygame.SRCALPHA)
            col = (120 + li*20, 160 + li*10, 240 - li*20, layer["alpha"])
            pygame.draw.circle(surf, col, (rad, rad), rad)
            screen.blit(surf, (int(rx - rad), int(ry - rad)))


def list_levels() -> list:
    files = sorted(glob.glob(os.path.join("levels", "*.json")))
    return files


def select_and_play_level() -> None:
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    title_font, item_font, hint_font = ensure_fonts()
    files = list_levels()
    if not files:
        return
    selected = 0
    running = True
    while running:
        dt = clock.tick(60)
        w, h = screen.get_size()
        mx, my = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,):
                    return
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(files)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(files)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    try_play(files[selected])
                    # After return, refresh list in case of new files
                    files = list_levels()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
        draw_menu_background(screen, pygame.time.get_ticks()/1000.0)
        title = title_font.render("Select Level", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(w//2, int(h*0.18))))
        start_y = int(h*0.30)
        gap = 56
        rects = []
        for i, fp in enumerate(files[:24]):
            name = os.path.basename(fp)
            # progress percent from best accuracy
            try:
                lvl = load_level(fp)
                hs = get_highscore(lvl.title)
                acc = hs.get("accuracy", 0.0)
                percent = int(acc * 100)
                name_disp = f"{name}  —  {percent}%"
            except:
                name_disp = name
            bw, bh = 520, 48
            rect = pygame.Rect(0, 0, bw, bh)
            rect.center = (w//2, start_y + i*gap)
            hovered = rect.collidepoint(mx, my)
            if hovered:
                selected = i
            draw_button(screen, rect, name_disp, item_font, hovered, i == selected)
            rects.append((rect, i))
        hint = hint_font.render("UP/DOWN to select, ENTER/CLICK to play, ESC to back", True, COLOR_TEXT)
        screen.blit(hint, hint.get_rect(center=(w//2, h-60)))
        pygame.display.flip()
        if click:
            for sr, i in rects:
                if sr.collidepoint(mx, my):
                    try_play(files[i])
                    files = list_levels()
                    break


def try_play(level_path: str):
    from .level import load_level
    from .main import play_level
    try:
        level = load_level(level_path)
    except Exception as exc:
        print(f"Failed to load level {level_path}: {exc}")
        return
    screen = pygame.display.get_surface()
    play_level(level, screen=screen)


def run_settings_screen():
    settings = load_settings()
    texts = labels(settings)
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    title_font, item_font, hint_font = ensure_fonts()
    # Sidebar categories and options per category
    cats = [
        ("Graphics", [
        (texts['graphics_quality'], ["low","medium","high"], ("graphics","quality")),
        (texts['effects_enabled'], ["True","False"], ("graphics","effects_enabled")),
        (texts['effects_mode'], ["off","light","full"], ("graphics","effects_mode")),
        (texts['fullscreen'], ["True","False"], ("graphics","fullscreen")),
        (texts['parallax_circles'], ["True","False"], ("graphics","parallax_circles")),
        ]),
        ("Timing", [
        (texts['visible_lead'], [], ("timing","visible_lead_ms")),
        (texts['linger'], [], ("timing","linger_ms")),
        (texts['hit_window'], [], ("timing","hit_window_ms")),
            ("Difficulty", ["easy","normal","hard","insane"], ("timing","difficulty")),
        ]),
        ("Audio", [
        (texts['music_volume'], [], ("audio","music_volume")),
        (texts['sfx_volume'], [], ("audio","sfx_volume")),
        (texts['layered_hitsounds'], ["True","False"], ("audio","layered_hitsounds")),
        (texts['pitch_shift_combo'], ["True","False"], ("audio","pitch_shift_combo")),
        (texts['lowpass_on_bad'], ["True","False"], ("audio","lowpass_on_bad")),
        ]),
        ("UI", [
        (texts['language'], ["en","ru"], ("ui","language")),
        ]),
    ]
    active_cat = 0
    idx = 0
    top_index = 0
    running = True
    while running:
        dt = clock.tick(60)
        w, h = screen.get_size()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    save_settings(settings)
                    return
                elif event.key == pygame.K_ESCAPE:
                    save_settings(settings)
                    return
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    active_cat = (active_cat - 1) % len(cats)
                    idx = 0; top_index = 0
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    active_cat = (active_cat + 1) % len(cats)
                    idx = 0; top_index = 0
                elif event.key in (pygame.K_UP, pygame.K_w):
                    idx = max(0, idx - 1)
                    if idx < top_index:
                        top_index = idx
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    max_items = len(cats[active_cat][1]) - 1
                    idx = min(max_items, idx + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_LEFT, pygame.K_a, pygame.K_RIGHT, pygame.K_d):
                    name, choices, path = cats[active_cat][1][idx]
                    sec, key = path
                    if choices:
                        cur = str(settings[sec][key])
                        i = choices.index(cur) if cur in choices else 0
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            i = (i - 1) % len(choices)
                        else:
                            i = (i + 1) % len(choices)
                        val = choices[i]
                        settings[sec][key] = (val == "True") if val in ("True","False") else val
                    else:
                        if name in ("Music Volume","SFX Volume"):
                            delta = -0.1 if event.key in (pygame.K_LEFT, pygame.K_a) else 0.1
                            nv = float(settings[sec][key]) + delta
                            if nv < 0: nv = 0.0
                            if nv > 1: nv = 1.0
                            settings[sec][key] = round(nv, 1)
                        else:
                            step = 10 if name == "Hit Window (ms)" else 50
                            delta = -step if event.key in (pygame.K_LEFT, pygame.K_a) else step
                            nv = max(10, int(settings[sec][key]) + delta)
                            settings[sec][key] = nv
        draw_menu_background(screen, pygame.time.get_ticks()/1000.0)
        title = title_font.render(texts['settings_title'], True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(w//2, int(h*0.18))))
        # Sidebar
        sidebar_w = 260
        sidebar_rects = []
        cat_start_y = int(h*0.30)
        cat_gap = 56
        for ci, (cname, _) in enumerate(cats):
            rect = pygame.Rect(40, cat_start_y + ci*cat_gap, sidebar_w, 44)
            hovered = rect.collidepoint(*pygame.mouse.get_pos())
            draw_button(screen, rect, cname, item_font, hovered, ci == active_cat)
            sidebar_rects.append((rect, ci))
        # Content list with simple index scrolling
        content_x = 40 + sidebar_w + 40
        start_y = int(h*0.28)
        gap = 56
        visible = max(1, (h - start_y - 120) // gap)
        items = cats[active_cat][1]
        top_index = min(max(0, top_index), max(0, len(items)-visible))
        idx = min(max(0, idx), max(0, len(items)-1))
        end_index = min(len(items), top_index + visible)
        for i in range(top_index, end_index):
            name, choices, path = items[i]
            sec, key = path
            val = settings[sec][key]
            disp = f"{name}: {val}"
            bw, bh = 720, 48
            rect = pygame.Rect(0, 0, bw, bh)
            rect.topleft = (content_x, start_y + (i - top_index)*gap)
            hovered = rect.collidepoint(*pygame.mouse.get_pos())
            if hovered:
                idx = i
            draw_button(screen, rect, disp, item_font, hovered, i == idx)
        hint = hint_font.render(texts['hint_settings'], True, COLOR_TEXT)
        screen.blit(hint, hint.get_rect(center=(w//2, h-60)))
        pygame.display.flip()
        # mouse click to apply changes and sidebar selection; mouse wheel to scroll
        click = False
        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if event.button == 1:
                click = True
            elif event.button == 4:
                idx = max(0, idx - 1)
                top_index = max(0, top_index - 1)
            elif event.button == 5:
                idx = min(len(cats[active_cat][1]) - 1, idx + 1)
                top_index = min(max(0, len(cats[active_cat][1]) - visible), top_index + 1)
        if click:
            mx, my = pygame.mouse.get_pos()
            # Sidebar click
            for rect, ci in sidebar_rects:
                if rect.collidepoint(mx, my):
                    active_cat = ci
                    idx = 0
                    top_index = 0
                    break
            # Content click
            # Recompute bounds if category changed
            items = cats[active_cat][1]
            visible = max(1, (h - start_y - 120) // gap)
            top_index = min(max(0, top_index), max(0, len(items)-visible))
            end_index = min(len(items), top_index + visible)
            for i in range(top_index, end_index):
                if i < 0 or i >= len(items):
                    continue
                name, choices, path = items[i]
                bw, bh = 720, 48
                rect = pygame.Rect(0, 0, bw, bh)
                rect.topleft = (content_x, start_y + (i - top_index)*gap)
                if rect.collidepoint(mx, my):
                    sec, key = path
                    if choices:
                        cur = str(settings[sec][key])
                        j = choices.index(cur) if cur in choices else 0
                        j = (j + 1) % len(choices)
                        val = choices[j]
                        settings[sec][key] = (val == "True") if val in ("True","False") else val
                    else:
                        step = 10 if name == "Hit Window (ms)" else 50
                        nv = max(10, int(settings[sec][key]) + step)
                        settings[sec][key] = nv


def fade(screen: pygame.Surface, fade_out: bool, duration_ms: int = 300):
    clock = pygame.time.Clock()
    overlay = pygame.Surface(screen.get_size())
    overlay.fill((0, 0, 0))
    elapsed = 0
    while elapsed < duration_ms:
        dt = clock.tick(60)
        elapsed += dt
        k = max(0.0, min(1.0, elapsed / duration_ms))
        alpha = int(255 * (k if fade_out else (1.0 - k)))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))
        pygame.display.flip()





def select_and_edit_level():
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    title_font, item_font, hint_font = ensure_fonts()
    files = sorted(glob.glob(os.path.join("levels", "*.json")))
    if not files:
        return
    selected = 0
    while True:
        dt = clock.tick(60)
        w, h = screen.get_size()
        mx, my = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                # Выполняем хуки модов для обработки клавиш
                results = mod_system.execute_mod_hooks("on_key_press", event, None, {})
                if any(results):
                    continue
                    
                if event.key in (pygame.K_ESCAPE,):
                    return
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(files)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(files)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    try_edit(files[selected])
                    files = sorted(glob.glob(os.path.join("levels", "*.json")))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
        draw_menu_background(screen, pygame.time.get_ticks()/1000.0)
        title = title_font.render("Edit Level", True, COLOR_TEXT)
        screen.blit(title, title.get_rect(center=(w//2, int(h*0.18))))
        start_y = int(h*0.30)
        gap = 56
        rects = []
        for i, fp in enumerate(files[:30]):
            name = os.path.basename(fp)
            bw, bh = 520, 48
            rect = pygame.Rect(0, 0, bw, bh)
            rect.center = (w//2, start_y + i*gap)
            hovered = rect.collidepoint(mx, my)
            if hovered:
                selected = i
            draw_button(screen, rect, name, item_font, hovered, i == selected)
            rects.append((rect, i))
        hint = hint_font.render("UP/DOWN select, ENTER/CLICK to edit, ESC to back", True, COLOR_TEXT)
        screen.blit(hint, hint.get_rect(center=(w//2, h-60)))
        
        # Draw FPS counter
        fps = int(clock.get_fps())
        fps_text = hint_font.render(f"FPS: {fps}", True, (150, 150, 150))
        screen.blit(fps_text, (w - fps_text.get_width() - 10, 10))
        
        # Выполняем хуки модов для отрисовки UI
        mod_system.execute_mod_hooks("on_draw_ui", screen, hint_font, None)
        
        pygame.display.flip()
        if click:
            for sr, i in rects:
                if sr.collidepoint(mx, my):
                    try_edit(files[i])
                    files = sorted(glob.glob(os.path.join("levels", "*.json")))
                    break


def try_edit(level_path: str):
    from .level import load_level
    try:
        lvl = load_level(level_path)
    except Exception as exc:
        print(f"Failed to load level {level_path}: {exc}")
        return
    screen = pygame.display.get_surface()
    # open editor with this level's data
    from .editor import run_editor
    run_editor(audio_path=lvl.audio, title=lvl.title, artist=lvl.artist, bpm=0.0, out_path=level_path, screen=screen)


if __name__ == "__main__":
    run_menu()




