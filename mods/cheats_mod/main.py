import json
import os
from typing import Any, Dict, List

import pygame

cheats_menu_open = False
settings: Dict[str, Any] = {}
selected_cheat = 0

ui_state = {
    "panel_pos": [80, 80],
    "drag": {"active": False, "dx": 0, "dy": 0},
    "scroll": 0,
    "prev_lmb": False,
    "speed_input_active": False,
    "speed_input": "",
}

CHEATS: List[Dict[str, Any]] = [
    {"name": "God Mode", "key": "god_mode", "type": "toggle", "desc": "HP never drops"},
    {"name": "No Fail", "key": "no_fail", "type": "toggle", "desc": "Cannot fail the level"},
    {"name": "Infinite HP", "key": "infinite_hp", "type": "toggle", "desc": "Keep HP at 100"},
    {"name": "Perfect Accuracy", "key": "perfect_accuracy", "type": "toggle", "desc": "Autohit with PERFECT timing"},
    {"name": "Auto Hit", "key": "auto_hit", "type": "toggle", "desc": "Autoplay notes"},
    {"name": "Combo Freeze", "key": "combo_freeze", "type": "toggle", "desc": "Combo does not fall"},
    {"name": "No Combo Break", "key": "no_combo_break_on_miss", "type": "toggle", "desc": "MISS won't break combo"},
    {"name": "Wide Window", "key": "wide_window", "type": "toggle", "desc": "Wider hit window"},
    {"name": "Ultra Window", "key": "ultra_window", "type": "toggle", "desc": "Very wide hit timing"},
    {"name": "Hold Assist", "key": "hold_assist", "type": "toggle", "desc": "Auto-hold active hold notes"},
    {"name": "HP Regen", "key": "hp_regen", "type": "toggle", "desc": "Regenerate HP over time"},
    {"name": "Chill FX", "key": "chill_fx", "type": "toggle", "desc": "Disable shake/flash/lowpass"},
    {"name": "Mute Miss", "key": "mute_miss", "type": "toggle", "desc": "Disable MISS sound"},
    {"name": "Mute All SFX", "key": "mute_all_sfx", "type": "toggle", "desc": "Disable all SFX"},
    {"name": "Speed", "key": "speed_slider", "type": "float", "min": 0.1, "max": 10.0, "step": 0.05, "desc": "Game speed"},
    {"name": "Score Mult", "key": "score_multiplier", "type": "choice", "values": [1.0, 1.5, 2.0, 3.0, 5.0, 10.0], "desc": "Score multiplier"},
]

KEY_TO_CHEAT = {c["key"]: c for c in CHEATS}

def _settings_path() -> str:
    return os.path.join(os.path.dirname(__file__), "mod_info.json")

def load_settings() -> None:
    global settings
    defaults = {
        "menu_open": False,
        "speed_slider": 1.0,
        "score_multiplier": 1.0,
    }
    for cheat in CHEATS:
        if cheat["type"] == "toggle":
            defaults.setdefault(cheat["key"], False)

    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        settings = data.get("settings", {})
    except Exception:
        settings = {}

    merged = dict(defaults)
    merged.update(settings)
    settings = merged
    normalize_settings()

def normalize_settings() -> None:
    # Handle legacy/broken values safely.
    try:
        settings["speed_slider"] = float(settings.get("speed_slider", 1.0))
    except Exception:
        settings["speed_slider"] = 1.0
    settings["speed_slider"] = max(0.1, min(10.0, round(settings["speed_slider"], 2)))

    sm = settings.get("score_multiplier", 1.0)
    if isinstance(sm, bool):
        sm = 2.0 if sm else 1.0
    try:
        sm = float(sm)
    except Exception:
        sm = 1.0
    choices = KEY_TO_CHEAT["score_multiplier"]["values"]
    if sm not in choices:
        sm = 1.0
    settings["score_multiplier"] = sm

def save_settings() -> None:
    try:
        with open(_settings_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}

    data["settings"] = settings
    with open(_settings_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _is_just_left_click() -> bool:
    lmb = pygame.mouse.get_pressed(num_buttons=3)[0]
    just = lmb and not ui_state["prev_lmb"]
    ui_state["prev_lmb"] = lmb
    return just

def _toggle_or_step_selected(forward: bool = True) -> None:
    cheat = CHEATS[selected_cheat]
    key = cheat["key"]
    ctype = cheat["type"]

    if ctype == "toggle":
        settings[key] = not bool(settings.get(key, False))
    elif ctype == "choice":
        vals = cheat["values"]
        cur = settings.get(key, vals[0])
        try:
            i = vals.index(cur)
        except ValueError:
            i = 0
        i = (i + (1 if forward else -1)) % len(vals)
        settings[key] = vals[i]
    elif ctype == "float":
        step = cheat["step"] if forward else -cheat["step"]
        cur = float(settings.get(key, 1.0))
        settings[key] = round(max(cheat["min"], min(cheat["max"], cur + step)), 2)

    save_settings()

def on_key_press(event, state, game_settings):
    global cheats_menu_open, selected_cheat

    if event.key == pygame.K_TAB:
        cheats_menu_open = not cheats_menu_open
        settings["menu_open"] = cheats_menu_open
        if cheats_menu_open:
            ui_state["speed_input_active"] = False
            ui_state["speed_input"] = ""
        save_settings()
        return True

    if not cheats_menu_open:
        return False

    # Manual numeric speed input mode
    if ui_state["speed_input_active"]:
        if event.key == pygame.K_ESCAPE:
            ui_state["speed_input_active"] = False
            ui_state["speed_input"] = ""
            return True
        if event.key == pygame.K_RETURN:
            txt = ui_state["speed_input"].strip().replace(",", ".")
            try:
                val = float(txt)
                settings["speed_slider"] = round(max(0.1, min(10.0, val)), 2)
                save_settings()
            except Exception:
                pass
            ui_state["speed_input_active"] = False
            ui_state["speed_input"] = ""
            return True
        if event.key == pygame.K_BACKSPACE:
            ui_state["speed_input"] = ui_state["speed_input"][:-1]
            return True
        ch = event.unicode or ""
        if ch and ch in "0123456789.,":
            ui_state["speed_input"] += ch
            return True
        return True

    if event.key in (pygame.K_UP, pygame.K_w):
        selected_cheat = (selected_cheat - 1) % len(CHEATS)
        return True
    if event.key in (pygame.K_DOWN, pygame.K_s):
        selected_cheat = (selected_cheat + 1) % len(CHEATS)
        return True
    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
        _toggle_or_step_selected(True)
        return True
    if event.key in (pygame.K_LEFT, pygame.K_a):
        _toggle_or_step_selected(False)
        return True
    if event.key in (pygame.K_RIGHT, pygame.K_d):
        _toggle_or_step_selected(True)
        return True

    # Start direct numeric input for speed
    if event.key == pygame.K_e and CHEATS[selected_cheat]["key"] == "speed_slider":
        ui_state["speed_input_active"] = True
        ui_state["speed_input"] = f"{settings.get('speed_slider', 1.0):.2f}"
        return True

    # Quick input from number keys when speed selected
    if CHEATS[selected_cheat]["key"] == "speed_slider":
        ch = event.unicode or ""
        if ch and ch in "0123456789.,":
            ui_state["speed_input_active"] = True
            ui_state["speed_input"] = ch
            return True

    return False

def _apply_mute(state) -> None:
    mute_all = settings.get("mute_all_sfx", False)
    mute_miss = settings.get("mute_miss", False)
    if mute_all:
        for snd_name in ("hit_snd", "miss_snd", "combo_snd", "perfect_snd", "good_snd", "bad_snd"):
            snd = getattr(state, snd_name, None)
            if snd:
                try:
                    snd.set_volume(0.0)
                except Exception:
                    pass
    elif mute_miss:
        snd = getattr(state, "miss_snd", None)
        if snd:
            try:
                snd.set_volume(0.0)
            except Exception:
                pass

def on_game_update(state, dt, now_ms):
    if not hasattr(state, "hp"):
        return

    if settings.get("god_mode", False):
        state.hp = max(state.hp, 100)
    if settings.get("infinite_hp", False):
        state.hp = 100
    if settings.get("no_fail", False):
        if state.hp <= 0:
            state.hp = 1
        state.failed = False

    if settings.get("hp_regen", False):
        state.hp = min(100, state.hp + dt * 0.01)

    if settings.get("combo_freeze", False) or settings.get("no_combo_break_on_miss", False):
        prev = getattr(state, "_cheat_last_combo", state.combo)
        if state.combo < prev:
            state.combo = prev
        state._cheat_last_combo = state.combo

    if settings.get("hold_assist", False) and hasattr(state, "notes") and hasattr(state, "side_holding"):
        for note in state.notes:
            if getattr(note, "is_hold", False) and getattr(note, "hold_started", False) and not note.hit and not note.missed:
                side = getattr(note.note, "side", None)
                if side in state.side_holding:
                    state.side_holding[side] = True

    if settings.get("chill_fx", False):
        if hasattr(state, "shake_timer"):
            state.shake_timer = 0
            state.shake_intensity = 0.0
        if hasattr(state, "lowpass_timer"):
            state.lowpass_timer = 0
            state.lowpass_intensity = 0.0
        if hasattr(state, "flash_timer"):
            state.flash_timer = 0

    # Timing cheats
    if hasattr(state, "level") and hasattr(state.level, "hit_window_ms"):
        base_hw = getattr(state, "_cheat_base_hit_window", None)
        if base_hw is None:
            state._cheat_base_hit_window = int(state.level.hit_window_ms)
            base_hw = state._cheat_base_hit_window
        hw = base_hw
        if settings.get("wide_window", False):
            hw = int(base_hw * 2)
        if settings.get("ultra_window", False):
            hw = int(base_hw * 4)
        state.level.hit_window_ms = max(base_hw, hw)

    spd = float(settings.get("speed_slider", 1.0))
    if hasattr(state, "bpm_multiplier"):
        state.bpm_multiplier = spd

    _apply_mute(state)

    # Auto/Perfect hit
    if (settings.get("auto_hit", False) or settings.get("perfect_accuracy", False)) and hasattr(state, "notes"):
        try:
            from game.main import KEY_TO_SIDE, handle_hit_input
        except Exception:
            KEY_TO_SIDE = {}
            handle_hit_input = None

        for note in state.notes:
            if note.hit or note.missed:
                continue
            side = getattr(note.note, "side", None)
            if not side:
                continue
            arrive_time = note.spawn_time_ms + state.level.approach_ms
            if settings.get("perfect_accuracy", False):
                trigger_window = 8
            elif settings.get("ultra_window", False):
                trigger_window = max(40, state.level.hit_window_ms // 2)
            else:
                trigger_window = max(20, state.level.hit_window_ms // 3)

            if abs(now_ms - arrive_time) <= trigger_window:
                key_code = None
                for k, s in KEY_TO_SIDE.items():
                    if s == side:
                        key_code = k
                        break
                if handle_hit_input and key_code is not None:
                    handle_hit_input(state, key_code, now_ms, {})
                else:
                    note.hit = True

    # Score multiplier
    mul = float(settings.get("score_multiplier", 1.0))
    if mul > 1.0 and hasattr(state, "score"):
        if not hasattr(state, "_cheat_last_score"):
            state._cheat_last_score = state.score
        delta = state.score - state._cheat_last_score
        if delta > 0:
            state.score += int(delta * (mul - 1.0))
        state._cheat_last_score = state.score

def on_draw_ui(screen, font, state):
    # Active tags
    active = []
    for cheat in CHEATS:
        key = cheat["key"]
        val = settings.get(key)
        if cheat["type"] == "toggle" and val:
            active.append(cheat["name"].upper())
    if float(settings.get("score_multiplier", 1.0)) > 1.0:
        active.append(f"SCORE x{settings['score_multiplier']}")
    if float(settings.get("speed_slider", 1.0)) != 1.0:
        active.append(f"SPD {settings['speed_slider']:.2f}x")

    if active:
        y = 220
        for i, tag in enumerate(active[:10]):
            surf = font.render(tag, True, (255, 230, 80))
            screen.blit(surf, (20, y + i * 22))

    if cheats_menu_open:
        _draw_cheats_overlay(screen, font)

def _draw_cheats_overlay(screen, font):
    global selected_cheat
    w, h = screen.get_size()

    panel_w = min(760, w - 40)
    panel_h = min(650, h - 40)
    x = max(20, min(ui_state["panel_pos"][0], w - panel_w - 20))
    y = max(20, min(ui_state["panel_pos"][1], h - panel_h - 20))
    ui_state["panel_pos"] = [x, y]

    root = pygame.Rect(x, y, panel_w, panel_h)
    header = pygame.Rect(x, y, panel_w, 42)
    body = pygame.Rect(x + 12, y + 50, panel_w - 24, panel_h - 88)
    footer = pygame.Rect(x + 12, y + panel_h - 32, panel_w - 24, 22)

    click = _is_just_left_click()
    mx, my = pygame.mouse.get_pos()

    if click and header.collidepoint(mx, my):
        ui_state["drag"]["active"] = True
        ui_state["drag"]["dx"] = mx - x
        ui_state["drag"]["dy"] = my - y
    if not pygame.mouse.get_pressed(num_buttons=3)[0]:
        ui_state["drag"]["active"] = False
    if ui_state["drag"]["active"]:
        ui_state["panel_pos"] = [mx - ui_state["drag"]["dx"], my - ui_state["drag"]["dy"]]

    pygame.draw.rect(screen, (15, 25, 42), root, border_radius=12)
    pygame.draw.rect(screen, (60, 120, 210), root, width=2, border_radius=12)
    pygame.draw.rect(screen, (32, 72, 132), header, border_radius=12)

    title = font.render("Cheats Panel (Tab to close)", True, (235, 235, 235))
    screen.blit(title, (header.x + 12, header.y + 10))

    rows_per_col = max(1, (body.height // 36))
    total_rows = (len(CHEATS) + 1) // 2
    max_scroll = max(0, total_rows - rows_per_col)

    # keyboard scroll by selection
    target_row = selected_cheat // 2
    if target_row < ui_state["scroll"]:
        ui_state["scroll"] = target_row
    elif target_row >= ui_state["scroll"] + rows_per_col:
        ui_state["scroll"] = target_row - rows_per_col + 1
    ui_state["scroll"] = max(0, min(ui_state["scroll"], max_scroll))

    col_w = (body.width - 16) // 2
    for idx, cheat in enumerate(CHEATS):
        col = idx % 2
        row = idx // 2
        row_view = row - ui_state["scroll"]
        if row_view < 0 or row_view >= rows_per_col:
            continue

        rx = body.x + col * (col_w + 16)
        ry = body.y + row_view * 36
        rect = pygame.Rect(rx, ry, col_w, 30)
        hovered = rect.collidepoint(mx, my)

        bg = (42, 92, 160) if idx == selected_cheat else (28, 62, 112)
        if hovered:
            bg = (54, 112, 188)
            selected_cheat = idx
        pygame.draw.rect(screen, bg, rect, border_radius=8)

        key = cheat["key"]
        val = settings.get(key)
        if cheat["type"] == "toggle":
            tail = "ON" if val else "OFF"
        elif cheat["type"] == "choice":
            tail = f"x{float(val):.2f}"
        else:
            tail = f"{float(val):.2f}x"

        txt = font.render(f"{cheat['name']}: {tail}", True, (235, 235, 235))
        screen.blit(txt, (rect.x + 8, rect.y + 6))

        if click and hovered:
            _toggle_or_step_selected(True)

    sel = CHEATS[selected_cheat]
    hint = "Arrows/WASD: navigate | Enter: toggle | E: type speed"
    if ui_state["speed_input_active"]:
        hint = "Speed input: type number, Enter apply, Esc cancel"
    hint_surf = font.render(hint, True, (205, 220, 245))
    desc_surf = font.render(sel.get("desc", ""), True, (180, 200, 230))
    screen.blit(hint_surf, (footer.x, footer.y))
    screen.blit(desc_surf, (footer.x, footer.y - 22))

    if ui_state["speed_input_active"]:
        box = pygame.Rect(root.centerx - 160, root.centery - 28, 320, 56)
        pygame.draw.rect(screen, (10, 20, 34), box, border_radius=10)
        pygame.draw.rect(screen, (90, 170, 255), box, width=2, border_radius=10)
        cap = font.render("Speed:", True, (230, 230, 230))
        val = font.render(ui_state["speed_input"] or "", True, (255, 220, 120))
        screen.blit(cap, (box.x + 12, box.y + 8))
        screen.blit(val, (box.x + 90, box.y + 8))

def on_mod_init():
    global cheats_menu_open
    load_settings()
    cheats_menu_open = bool(settings.get("menu_open", False))
    print("Мод читов загружен. Нажмите Tab для открытия меню читов.")

if "cheats_mod_initialized" not in globals():
    globals()["cheats_mod_initialized"] = True
    on_mod_init()

