import argparse
import os
import sys
import math
import random
import json
import math
from typing import List, Tuple, Optional, Dict
import pygame

from .level import load_level, Note, Level, Event
from .settings import load_settings
from .mod_system import mod_system

# Убираем глобальные переменные модов - моды должны быть независимыми

WINDOW_SIZE = (900, 900)
CENTER = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)
CENTER_RADIUS = 60
NOTE_SIZE = 64
SPAWN_PADDING = 40
FONT_NAME = None  # default

COLOR_BG = (16, 18, 28)
COLOR_GRID = (26, 30, 42)
COLOR_CENTER = (240, 240, 255)
COLOR_TEXT = (230, 230, 230)
COLOR_NOTE = {
    "left": (120, 200, 255),
    "top": (120, 255, 160),
    "right": (255, 170, 120),
    "bottom": (255, 120, 200),
}
COLOR_NOTE_DIM = {k: (v[0]//2, v[1]//2, v[2]//2) for k, v in COLOR_NOTE.items()}
COLOR_HP_BG = (60, 40, 40)
COLOR_HP = (220, 70, 70)
COLOR_PROGRESS_BG = (40, 44, 56)
COLOR_PROGRESS = (120, 200, 255)

# Auto-miss if a note stays on the circle longer than this
CENTER_LINGER_AUTO_MISS_MS = 100

# Notes shorter than this are taps, not holds
HOLD_THRESHOLD_MS = 50  # Уменьшили порог чтобы короткие hold-ноты тоже работали

# Поддержка ВСЕХ клавиш - каждая клавиша может быть назначена на любую сторону
KEY_TO_SIDE = {
    # Основные WASD
    pygame.K_a: "left", pygame.K_w: "top", pygame.K_d: "right", pygame.K_s: "bottom",
    # Стрелки
    pygame.K_LEFT: "left", pygame.K_UP: "top", pygame.K_RIGHT: "right", pygame.K_DOWN: "bottom",
    # IJKL
    pygame.K_j: "left", pygame.K_i: "top", pygame.K_l: "right", pygame.K_k: "bottom",
    # FTHG
    pygame.K_f: "left", pygame.K_t: "top", pygame.K_h: "right", pygame.K_g: "bottom",
    # Цифровая клавиатура
    pygame.K_KP4: "left", pygame.K_KP8: "top", pygame.K_KP6: "right", pygame.K_KP5: "bottom",
    pygame.K_KP1: "left", pygame.K_KP2: "bottom", pygame.K_KP3: "right", pygame.K_KP7: "left",
    pygame.K_KP9: "right", pygame.K_KP0: "bottom",
    # Цифры
    pygame.K_1: "left", pygame.K_2: "bottom", pygame.K_3: "right", pygame.K_4: "left",
    pygame.K_5: "bottom", pygame.K_6: "right", pygame.K_7: "left", pygame.K_8: "top",
    pygame.K_9: "right", pygame.K_0: "bottom",
    # Буквы QWERTY
    pygame.K_q: "left", pygame.K_e: "right", pygame.K_r: "top", pygame.K_y: "top",
    pygame.K_u: "top", pygame.K_o: "right", pygame.K_p: "right",
    pygame.K_z: "left", pygame.K_x: "bottom", pygame.K_c: "right", pygame.K_v: "bottom",
    pygame.K_b: "bottom", pygame.K_n: "bottom", pygame.K_m: "right",
    # Дополнительные клавиши
    pygame.K_SPACE: "bottom", pygame.K_LSHIFT: "left", pygame.K_RSHIFT: "right",
    pygame.K_LCTRL: "left", pygame.K_RCTRL: "right", pygame.K_LALT: "left", pygame.K_RALT: "right",
    # Фейковые клавиши (Win и Alt)
    pygame.K_LMETA: "left", pygame.K_RMETA: "right",
    pygame.K_TAB: "left", pygame.K_CAPSLOCK: "left", pygame.K_RETURN: "bottom",
    pygame.K_BACKSPACE: "right", pygame.K_DELETE: "right",
    # Функциональные клавиши
    pygame.K_F1: "left", pygame.K_F2: "bottom", pygame.K_F3: "right", pygame.K_F4: "top",
    pygame.K_F5: "left", pygame.K_F6: "bottom", pygame.K_F7: "right", pygame.K_F8: "top",
    pygame.K_F9: "left", pygame.K_F10: "bottom", pygame.K_F11: "right", pygame.K_F12: "top",
    # Символы
    pygame.K_SEMICOLON: "right", pygame.K_QUOTE: "right", pygame.K_COMMA: "left",
    pygame.K_PERIOD: "right", pygame.K_SLASH: "right", pygame.K_BACKQUOTE: "left",
    pygame.K_MINUS: "left", pygame.K_EQUALS: "right", pygame.K_LEFTBRACKET: "left",
    pygame.K_RIGHTBRACKET: "right", pygame.K_BACKSLASH: "right",
}

DISPLAY_FOR_KEY = {
    # Основные
    pygame.K_a: "A", pygame.K_w: "W", pygame.K_d: "D", pygame.K_s: "S",
    pygame.K_LEFT: "←", pygame.K_UP: "↑", pygame.K_RIGHT: "→", pygame.K_DOWN: "↓",
    pygame.K_j: "J", pygame.K_i: "I", pygame.K_l: "L", pygame.K_k: "K",
    pygame.K_f: "F", pygame.K_t: "T", pygame.K_h: "H", pygame.K_g: "G",
    # Цифровая клавиатура
    pygame.K_KP4: "4", pygame.K_KP8: "8", pygame.K_KP6: "6", pygame.K_KP5: "5",
    pygame.K_KP1: "1", pygame.K_KP2: "2", pygame.K_KP3: "3", pygame.K_KP7: "7",
    pygame.K_KP9: "9", pygame.K_KP0: "0",
    # Цифры
    pygame.K_1: "1", pygame.K_2: "2", pygame.K_3: "3", pygame.K_4: "4",
    pygame.K_5: "5", pygame.K_6: "6", pygame.K_7: "7", pygame.K_8: "8",
    pygame.K_9: "9", pygame.K_0: "0",
    # Буквы
    pygame.K_q: "Q", pygame.K_e: "E", pygame.K_r: "R", pygame.K_y: "Y",
    pygame.K_u: "U", pygame.K_o: "O", pygame.K_p: "P",
    pygame.K_z: "Z", pygame.K_x: "X", pygame.K_c: "C", pygame.K_v: "V",
    pygame.K_b: "B", pygame.K_n: "N", pygame.K_m: "M",
    # Специальные
    pygame.K_SPACE: "SPC", pygame.K_LSHIFT: "⇧", pygame.K_RSHIFT: "⇧",
    pygame.K_LCTRL: "Ctrl", pygame.K_RCTRL: "Ctrl", pygame.K_LALT: "Alt", pygame.K_RALT: "Alt",
    # Фейковые клавиши
    pygame.K_LMETA: "Win", pygame.K_RMETA: "Win",
    pygame.K_TAB: "Tab", pygame.K_CAPSLOCK: "Caps", pygame.K_RETURN: "↵",
    pygame.K_BACKSPACE: "⌫", pygame.K_DELETE: "Del",
    # F-клавиши
    pygame.K_F1: "F1", pygame.K_F2: "F2", pygame.K_F3: "F3", pygame.K_F4: "F4",
    pygame.K_F5: "F5", pygame.K_F6: "F6", pygame.K_F7: "F7", pygame.K_F8: "F8",
    pygame.K_F9: "F9", pygame.K_F10: "F10", pygame.K_F11: "F11", pygame.K_F12: "F12",
    # Символы
    pygame.K_SEMICOLON: ";", pygame.K_QUOTE: "'", pygame.K_COMMA: ",",
    pygame.K_PERIOD: ".", pygame.K_SLASH: "/", pygame.K_BACKQUOTE: "`",
    pygame.K_MINUS: "-", pygame.K_EQUALS: "=", pygame.K_LEFTBRACKET: "[",
    pygame.K_RIGHTBRACKET: "]", pygame.K_BACKSLASH: "\\",
}

# extend key mapping for diagonals (UO for up-right, Y for up-left, N for down-left, M for down-right)
KEY_TO_SIDE.update({
    pygame.K_e: "top_right",  # example diag keys
    pygame.K_q: "top_left",
    pygame.K_z: "bottom_left",
    pygame.K_c: "bottom_right",
})

# color for new directions
COLOR_NOTE.update({
    "top_left": (160, 160, 255),
    "top_right": (160, 255, 255),
    "bottom_left": (255, 160, 255),
    "bottom_right": (255, 255, 160),
})
COLOR_NOTE_DIM.update({k: (v[0]//2, v[1]//2, v[2]//2) for k,v in COLOR_NOTE.items()})

# spawn points for diagonals
def spawn_point_for_side(side: str) -> Tuple[int, int]:
    if side == "left":
        return (SPAWN_PADDING, CENTER[1])
    if side == "right":
        return (WINDOW_SIZE[0] - SPAWN_PADDING, CENTER[1])
    if side == "top":
        return (CENTER[0], SPAWN_PADDING)
    if side == "bottom":
        return (CENTER[0], WINDOW_SIZE[1] - SPAWN_PADDING)
    if side == "top_left":
        return (SPAWN_PADDING, SPAWN_PADDING)
    if side == "top_right":
        return (WINDOW_SIZE[0] - SPAWN_PADDING, SPAWN_PADDING)
    if side == "bottom_left":
        return (SPAWN_PADDING, WINDOW_SIZE[1] - SPAWN_PADDING)
    if side == "bottom_right":
        return (WINDOW_SIZE[0] - SPAWN_PADDING, WINDOW_SIZE[1] - SPAWN_PADDING)
    return CENTER


class Particle:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int]):
        self.x = float(x)
        self.y = float(y)
        self.vx = (random.random() * 2 - 1) * 0.25
        self.vy = (random.random() * 2 - 1) * 0.25
        self.life = 380
        self.color = color

    def update(self, dt: int):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, screen: pygame.Surface):
        if self.life > 0:
            alpha = max(0, min(255, int(255 * (self.life / 380))))
            # Quantize alpha to reuse cached sprites and reduce per-frame allocations.
            alpha_q = max(0, min(255, ((alpha + 7) // 16) * 16))
            sprite = get_particle_sprite(self.color, alpha_q)
            screen.blit(sprite, (int(self.x)-5, int(self.y)-5))


_PARTICLE_SPRITE_CACHE: Dict[Tuple[int, int, int, int], pygame.Surface] = {}


def get_particle_sprite(color: Tuple[int, int, int], alpha: int) -> pygame.Surface:
    key = (color[0], color[1], color[2], alpha)
    cached = _PARTICLE_SPRITE_CACHE.get(key)
    if cached is not None:
        return cached
    surf = pygame.Surface((10, 10), pygame.SRCALPHA)
    pygame.draw.circle(surf, (color[0], color[1], color[2], alpha), (5, 5), 5)
    _PARTICLE_SPRITE_CACHE[key] = surf
    return surf


class ActiveNote:
    def __init__(self, note: Note, spawn_time_ms: int, approach_ms: int):
        self.note = note
        self.spawn_time_ms = spawn_time_ms
        self.approach_ms = approach_ms
        self.hit = False
        self.missed = False
        # hold-related
        duration = getattr(note, 'duration_ms', 0) or 0
        self.is_hold = duration >= HOLD_THRESHOLD_MS
        self.hold_started = False
        self.hold_completed = False
        self.hold_side: Optional[str] = None

    def progress(self, now_ms: int) -> float:
        return max(0.0, min(1.0, (now_ms - self.spawn_time_ms) / self.approach_ms))

    def position(self, now_ms: int) -> Tuple[int, int]:
        t = self.progress(now_ms)
        sx, sy = spawn_point_for_side(self.note.side)
        cx, cy = CENTER
        x = int(sx + (cx - sx) * t)
        y = int(sy + (cy - sy) * t)
        return x, y

    def arrive_time(self) -> int:
        return self.spawn_time_ms + self.approach_ms

    def end_time(self) -> int:
        return self.arrive_time() + (getattr(self.note, 'duration_ms', 0) or 0)


class GameState:
    def __init__(self, level: Level):
        self.level = level
        self.notes: List[ActiveNote] = []
        self.next_note_idx = 0
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.judgements: List[Tuple[str, int]] = []
        self.all_judgements: List[str] = []
        self.start_time_ms = 0
        self.running = True
        self.audio_started = False
        self.pulse_timer = 0
        self.particles: List[Particle] = []
        self.shake_timer = 0
        self.shake_intensity = 0.0
        self.total_notes = 0
        self.hits = 0
        self.finished = False
        self.failed = False
        self.hp = 100
        # Новые поля для BPM и зажатия клавиш
        self.bpm_multiplier = 1.0  # Множитель скорости (1.0 = нормальная скорость)
        self.keys_held = set()  # Множество зажатых клавиш
        self.hit_snd: Optional[pygame.mixer.Sound] = None
        self.miss_snd: Optional[pygame.mixer.Sound] = None
        # Layered hit sounds
        self.perfect_snd: Optional[pygame.mixer.Sound] = None
        self.good_snd: Optional[pygame.mixer.Sound] = None
        self.bad_snd: Optional[pygame.mixer.Sound] = None
        self.combo_snd: Optional[pygame.mixer.Sound] = None
        # Audio effects
        self.lowpass_timer = 0
        self.lowpass_intensity = 0.0
        self.cam_zoom = 1.0
        self.cam_angle = 0.0
        self.active_effects_override: Optional[List[str]] = None
        self.next_event_idx = 0
        # holding state per side
        self.side_holding: Dict[str, bool] = {"left": False, "top": False, "right": False, "bottom": False}
        # New visual effects
        self.track_glow = {"left": 0.0, "top": 0.0, "right": 0.0, "bottom": 0.0}
        self.beat_glow_timer = 0
        self.beat_glow_intensity = 0.0
        self.hit_sparks: List[Dict] = []
        self.parallax_layers = []
        # UI animations
        self.animated_labels: List[Dict] = []
        self.combo_pulse_timer = 0
        self.combo_pulse_intensity = 0.0
        self.rank_animation = None
        # Game over animation state
        self.game_over_timer = 0
        self.game_over_zoom = 1.0
        self.game_over_red_flash = 0.0
        self.note_fragments: List[Dict] = []
        self.slow_motion_factor = 1.0
        self.music_fade_timer = 0
        self.screen_crack_timer = 0
        # Progression
        self.achievements_earned: List[str] = []
        # Slide mechanic state
        self.pending_slide_target: Optional[str] = None
        self.pending_slide_expire_ms: int = 0
        self.scene = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        # Precompute final note end time based on level data (center times)
        try:
            if level.notes:
                self.level_last_note_end_center_ms = max(
                    (getattr(n, 'time_ms', 0) or 0) + (getattr(n, 'duration_ms', 0) or 0)
                    for n in level.notes
                )
            else:
                self.level_last_note_end_center_ms = None
        except Exception:
            self.level_last_note_end_center_ms = None
        # Убираем встроенный автопилот - теперь это мод

    def reset(self):
        self.notes.clear()
        self.next_note_idx = 0
        self.score = 0
        self.combo = 0
        self.best_combo = 0
        self.judgements.clear()
        self.start_time_ms = pygame.time.get_ticks()
        self.audio_started = False
        self.pulse_timer = 0
        self.particles.clear()
        self.shake_timer = 0
        self.shake_intensity = 0.0
        self.finished = False
        self.failed = False
        self.total_notes = len(self.level.notes)
        self.hits = 0
        self.hp = 100
        self.cam_zoom = 1.0
        self.cam_angle = 0.0
        self.active_effects_override = None
        self.next_event_idx = 0
        self.side_holding = {"left": False, "top": False, "right": False, "bottom": False}
        # Reset visual effects
        self.track_glow = {"left": 0.0, "top": 0.0, "right": 0.0, "bottom": 0.0}
        self.beat_glow_timer = 0
        self.beat_glow_intensity = 0.0
        self.hit_sparks.clear()
        self.parallax_layers = []
        # Reset UI animations
        self.animated_labels.clear()
        self.combo_pulse_timer = 0
        self.combo_pulse_intensity = 0.0
        self.rank_animation = None
        self.all_judgements = []
        # Reset game over animation
        self.game_over_timer = 0
        self.game_over_zoom = 1.0
        self.game_over_red_flash = 0.0
        self.note_fragments.clear()
        self.slow_motion_factor = 1.0
        self.music_fade_timer = 0
        self.screen_crack_timer = 0



def draw_regular_note(scene, an, x, y, col, now_ms, is_fake):
    """Draw a regular tap/hold note."""
    rect = pygame.Rect(x - NOTE_SIZE//2, y - NOTE_SIZE//2, NOTE_SIZE, NOTE_SIZE)
    
    if is_fake:
        # Фейковая нота - черная с белой обводкой
        fake_glow_rect = pygame.Rect(rect.x-12, rect.y-12, NOTE_SIZE+24, NOTE_SIZE+24)
        pygame.draw.rect(scene, (255, 255, 255), fake_glow_rect, width=3, border_radius=15)
        pygame.draw.rect(scene, (0, 0, 0), rect, border_radius=8)
        pygame.draw.rect(scene, (255, 255, 255), rect, width=2, border_radius=8)
        
        # Красный крестик внутри для предупреждения
        cross_size = NOTE_SIZE // 3
        cross_x = rect.centerx
        cross_y = rect.centery
        pygame.draw.line(scene, (255, 0, 0), 
                       (cross_x - cross_size//2, cross_y - cross_size//2),
                       (cross_x + cross_size//2, cross_y + cross_size//2), 3)
        pygame.draw.line(scene, (255, 0, 0),
                       (cross_x - cross_size//2, cross_y + cross_size//2),
                       (cross_x + cross_size//2, cross_y - cross_size//2), 3)
    else:
        # Обычные ноты
        # Особая отрисовка для hold-нот
        if an.is_hold:
            # Двойная рамка для hold-нот
            hold_glow_rect = pygame.Rect(rect.x-15, rect.y-15, NOTE_SIZE+30, NOTE_SIZE+30)
            pygame.draw.rect(scene, (*col, 80), hold_glow_rect, border_radius=18)
            pygame.draw.rect(scene, (255, 255, 255, 100), hold_glow_rect, width=2, border_radius=18)
        else:
            # Обычное свечение для tap-нот
            glow_rect = pygame.Rect(rect.x-10, rect.y-10, NOTE_SIZE+20, NOTE_SIZE+20)
            pygame.draw.rect(scene, (*col, 60), glow_rect, border_radius=15)
        
        # Основная нота
        pygame.draw.rect(scene, col, rect, border_radius=8)
        
        # Внутренний блик
        inner_rect = pygame.Rect(rect.x+2, rect.y+2, NOTE_SIZE-4, NOTE_SIZE-4)
        lighter_col = tuple(min(255, c + 40) for c in col)
        pygame.draw.rect(scene, lighter_col, inner_rect, border_radius=6)
    
    # Индикатор hold-ноты
    if an.is_hold:
        # Маленький кружок в углу для обозначения hold-ноты
        hold_indicator = pygame.Rect(rect.x + NOTE_SIZE - 12, rect.y + 2, 10, 10)
        pygame.draw.ellipse(scene, (255, 255, 255), hold_indicator)
        pygame.draw.ellipse(scene, col, hold_indicator.inflate(-2, -2))


def draw_double_note(scene, an, x, y, col, now_ms, is_fake):
    """Draw a double note (two overlapping circles)."""
    rect1 = pygame.Rect(x - NOTE_SIZE//2 - 8, y - NOTE_SIZE//2, NOTE_SIZE, NOTE_SIZE)
    rect2 = pygame.Rect(x - NOTE_SIZE//2 + 8, y - NOTE_SIZE//2, NOTE_SIZE, NOTE_SIZE)
    
    if is_fake:
        # Фейковые двойные ноты
        for rect in [rect1, rect2]:
            fake_glow_rect = pygame.Rect(rect.x-8, rect.y-8, NOTE_SIZE+16, NOTE_SIZE+16)
            pygame.draw.rect(scene, (255, 255, 255), fake_glow_rect, width=2, border_radius=12)
            pygame.draw.rect(scene, (0, 0, 0), rect, border_radius=6)
    else:
        # Обычные двойные ноты
        for rect in [rect1, rect2]:
            glow_rect = pygame.Rect(rect.x-6, rect.y-6, NOTE_SIZE+12, NOTE_SIZE+12)
            pygame.draw.rect(scene, (*col, 60), glow_rect, border_radius=12)
            pygame.draw.rect(scene, col, rect, border_radius=6)
            
            # Внутренний блик
            inner_rect = pygame.Rect(rect.x+1, rect.y+1, NOTE_SIZE-2, NOTE_SIZE-2)
            lighter_col = tuple(min(255, c + 30) for c in col)
            pygame.draw.rect(scene, lighter_col, inner_rect, border_radius=4)


def draw_slide_note(scene, an, x, y, col, now_ms, is_fake):
    """Draw a slide note (arrow pointing to target)."""
    rect = pygame.Rect(x - NOTE_SIZE//2, y - NOTE_SIZE//2, NOTE_SIZE, NOTE_SIZE)
    
    if is_fake:
        # Фейковая slide нота
        fake_glow_rect = pygame.Rect(rect.x-10, rect.y-10, NOTE_SIZE+20, NOTE_SIZE+20)
        pygame.draw.rect(scene, (255, 255, 255), fake_glow_rect, width=2, border_radius=12)
        pygame.draw.rect(scene, (0, 0, 0), rect, border_radius=6)
    else:
        # Обычная slide нота
        glow_rect = pygame.Rect(rect.x-8, rect.y-8, NOTE_SIZE+16, NOTE_SIZE+16)
        pygame.draw.rect(scene, (*col, 60), glow_rect, border_radius=12)
        pygame.draw.rect(scene, col, rect, border_radius=6)
        
        # Внутренний блик
        inner_rect = pygame.Rect(rect.x+1, rect.y+1, NOTE_SIZE-2, NOTE_SIZE-2)
        lighter_col = tuple(min(255, c + 30) for c in col)
        pygame.draw.rect(scene, lighter_col, inner_rect, border_radius=4)
    
    # Draw arrow pointing to target
    target_side = getattr(an.note, 'slide_target', None)
    if target_side:
        arrow_color = (255, 255, 255) if is_fake else (255, 255, 255)
        arrow_size = 8
        
        # Calculate arrow direction based on target side
        if target_side == "left":
            arrow_points = [(rect.right, rect.centery), (rect.right + arrow_size, rect.centery - arrow_size//2), (rect.right + arrow_size, rect.centery + arrow_size//2)]
        elif target_side == "right":
            arrow_points = [(rect.left, rect.centery), (rect.left - arrow_size, rect.centery - arrow_size//2), (rect.left - arrow_size, rect.centery + arrow_size//2)]
        elif target_side == "top":
            arrow_points = [(rect.centerx, rect.bottom), (rect.centerx - arrow_size//2, rect.bottom + arrow_size), (rect.centerx + arrow_size//2, rect.bottom + arrow_size)]
        elif target_side == "bottom":
            arrow_points = [(rect.centerx, rect.top), (rect.centerx - arrow_size//2, rect.top - arrow_size), (rect.centerx + arrow_size//2, rect.top - arrow_size)]
        else:
            arrow_points = []
        
        if arrow_points:
            pygame.draw.polygon(scene, arrow_color, arrow_points)


def draw_grid(screen: pygame.Surface, offset: Tuple[int, int]):
    step = 60
    ox, oy = offset
    sw, sh = screen.get_size()
    for x in range(-step + (ox % step), sw, step):
        pygame.draw.line(screen, COLOR_GRID, (x, 0), (x, sh), 1)
    for y in range(-step + (oy % step), sh, step):
        pygame.draw.line(screen, COLOR_GRID, (0, y), (sw, y), 1)


def draw_fps(screen: pygame.Surface, clock: pygame.time.Clock, font: pygame.font.Font):
    """Draw FPS counter in top right corner"""
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, COLOR_TEXT)
    w, h = screen.get_size()
    screen.blit(fps_text, (w - fps_text.get_width() - 10, 10))


# Убираем все встроенные функции модов - моды должны быть независимыми


def apply_hp_damage(state: GameState, damage: int):
    """Применяет урон с учетом читов"""
    try:
        # Проверяем читы
        god_mode = False
        infinite_hp = False
        
        for mod in mod_system.get_enabled_mods():
            if mod.name == "Читы":
                with open(mod.file_path + "/mod_info.json", 'r', encoding='utf-8') as f:
                    mod_data = json.load(f)
                    cheat_settings = mod_data.get('settings', {})
                    god_mode = cheat_settings.get('god_mode', False)
                    infinite_hp = cheat_settings.get('infinite_hp', False)
                break
        
        # Применяем урон только если читы не активны
        if not god_mode and not infinite_hp:
            state.hp = max(0, state.hp - damage)
    except:
        # Если ошибка с модами, применяем урон как обычно
        state.hp = max(0, state.hp - damage)


# Убираем встроенную функцию автопилота - теперь это мод


# Убираем вторую встроенную функцию автопилота - теперь это мод


def init_parallax_layers(state: GameState):
    """Initialize parallax background layers"""
    state.parallax_layers = [
        {"speed": 0.1, "offset": (0, 0), "color": (20, 25, 35)},
        {"speed": 0.2, "offset": (0, 0), "color": (25, 30, 40)},
        {"speed": 0.3, "offset": (0, 0), "color": (30, 35, 45)},
    ]


def update_parallax_layers(state: GameState, dt: float, beat_time: float):
    """Update parallax layer positions based on beat timing"""
    for layer in state.parallax_layers:
        layer["offset"] = (
            layer["offset"][0] + layer["speed"] * math.sin(beat_time * 0.01) * dt,
            layer["offset"][1] + layer["speed"] * math.cos(beat_time * 0.01) * dt
        )


def draw_parallax_layers(screen: pygame.Surface, state: GameState, offset: Tuple[int, int], settings: Dict):
    """Draw optimized parallax background layers"""
    if not settings.get("graphics", {}).get("parallax_circles", True):
        return
        
    w, h = screen.get_size()
    ox, oy = offset
    
    # Оптимизированная отрисовка - меньше кругов, прямая отрисовка
    for i, layer in enumerate(state.parallax_layers):
        alpha = 20 + i * 10
        color = (*layer["color"], alpha)
        
        # Красивые параллакс круги с оптимизацией
        for x in range(0, w + 100, 100):  # Компромисс между красотой и производительностью
            for y in range(0, h + 100, 100):
                circle_x = x + int(layer["offset"][0]) % 100 + ox - 50
                circle_y = y + int(layer["offset"][1]) % 100 + oy - 50
                pygame.draw.circle(screen, color, (circle_x, circle_y), 15)


def add_hit_spark(state: GameState, x: int, y: int, judgment: str):
    """Add colored hit spark based on judgment"""
    colors = {
        "PERFECT": (0, 255, 0),    # Green
        "GOOD": (255, 255, 0),     # Yellow  
        "BAD": (255, 0, 0),        # Red
        "MISS": (255, 100, 100),   # Light red
        "HOLD": (0, 200, 255),     # Cyan
    }
    
    color = colors.get(judgment, (255, 255, 255))
    state.hit_sparks.append({
        "x": x, "y": y, "color": color, "life": 1.0, "size": 20,
        "vx": random.uniform(-3, 3), "vy": random.uniform(-3, 3)
    })


def update_hit_sparks(state: GameState, dt: float):
    """Update hit spark particles"""
    alive_sparks = []
    for spark in state.hit_sparks:
        spark["life"] -= dt * 0.003
        spark["x"] += spark["vx"] * dt * 0.1
        spark["y"] += spark["vy"] * dt * 0.1
        spark["size"] *= 0.98
        if spark["life"] > 0:
            alive_sparks.append(spark)
    state.hit_sparks = alive_sparks


def draw_hit_sparks(screen: pygame.Surface, state: GameState, offset: Tuple[int, int]):
    """Draw hit spark particles"""
    ox, oy = offset
    for spark in state.hit_sparks:
        alpha = int(255 * spark["life"])
        size = int(spark["size"])
        if size > 0 and alpha > 0:
            color = (spark["color"][0], spark["color"][1], spark["color"][2], alpha)
            pygame.draw.circle(screen, color, (int(spark["x"] + ox), int(spark["y"] + oy)), size)


def draw_track_glow(screen: pygame.Surface, state: GameState, offset: Tuple[int, int]):
    """Draw glowing tracks based on hit activity"""
    ox, oy = offset
    w, h = screen.get_size()
    
    for side, intensity in state.track_glow.items():
        if intensity <= 0:
            continue
            
        color = COLOR_NOTE.get(side, (255, 255, 255))
        alpha = int(30 * intensity)
        
        # Draw track line with glow
        if side == "left":
            start_x, start_y = 0, CENTER[1]
            end_x, end_y = CENTER[0], CENTER[1]
        elif side == "right":
            start_x, start_y = w, CENTER[1]
            end_x, end_y = CENTER[0], CENTER[1]
        elif side == "top":
            start_x, start_y = CENTER[0], 0
            end_x, end_y = CENTER[0], CENTER[1]
        elif side == "bottom":
            start_x, start_y = CENTER[0], h
            end_x, end_y = CENTER[0], CENTER[1]
        else:
            continue
            
        # Draw thick glow line
        for i in range(5):
            width = 8 - i
            glow_color = (*color, alpha // (i + 1))
            pygame.draw.line(screen, glow_color, 
                           (start_x + ox, start_y + oy), 
                           (end_x + ox, end_y + oy), width)


def update_track_glow(state: GameState, dt: float):
    """Update track glow intensity"""
    for side in state.track_glow:
        state.track_glow[side] = max(0.0, state.track_glow[side] - dt * 0.002)


def update_beat_glow(state: GameState, dt: float, beat_time: float):
    """Update beat-based glow effect"""
    if state.beat_glow_timer > 0:
        state.beat_glow_timer -= dt
        state.beat_glow_intensity = state.beat_glow_timer / 200.0
    else:
        state.beat_glow_intensity = 0.0


def draw_beat_glow(screen: pygame.Surface, state: GameState, offset: Tuple[int, int]):
    """Draw beat-based glow effect on all tracks"""
    if state.beat_glow_intensity <= 0:
        return
        
    ox, oy = offset
    w, h = screen.get_size()
    # Glow all tracks
    for side in ["left", "right", "top", "bottom"]:
        color = COLOR_NOTE.get(side, (255, 255, 255))
        alpha = int(50 * state.beat_glow_intensity)
        
        if side == "left":
            start_x, start_y = 0, CENTER[1]
            end_x, end_y = CENTER[0], CENTER[1]
        elif side == "right":
            start_x, start_y = w, CENTER[1]
            end_x, end_y = CENTER[0], CENTER[1]
        elif side == "top":
            start_x, start_y = CENTER[0], 0
            end_x, end_y = CENTER[0], CENTER[1]
        elif side == "bottom":
            start_x, start_y = CENTER[0], h
            end_x, end_y = CENTER[0], CENTER[1]
        else:
            continue
            
        # Draw glow line
        for i in range(3):
            width = 12 - i * 2
            glow_color = (*color, alpha // (i + 1))
            pygame.draw.line(screen, glow_color, 
                           (start_x + ox, start_y + oy), 
                           (end_x + ox, end_y + oy), width)


def play_layered_hit_sound(state: GameState, judgment: str, combo: int, settings: Dict):
    """Play appropriate hit sound based on judgment and combo"""
    if not settings.get("audio", {}).get("layered_hitsounds", True):
        # Fallback to original hit sound
        if state.hit_snd:
            state.hit_snd.play()
        return
    
    # Play judgment-specific sound
    sound = None
    if judgment == "PERFECT" and state.perfect_snd:
        sound = state.perfect_snd
    elif judgment == "GOOD" and state.good_snd:
        sound = state.good_snd
    elif judgment == "BAD" and state.bad_snd:
        sound = state.bad_snd
    elif judgment in ["GREAT", "HOLD"] and state.good_snd:
        sound = state.good_snd
    else:
        # Fallback
        if state.hit_snd:
            state.hit_snd.play()
        return
    
    if sound:
        # Apply pitch shift for combo if enabled
        if settings.get("audio", {}).get("pitch_shift_combo", True) and combo > 1:
            # Simple pitch shift by changing playback speed
            pitch_multiplier = min(1.5, 1.0 + (combo - 1) * 0.02)
            # Note: pygame doesn't support pitch shifting directly, so we'll just play the sound
            # In a real implementation, you'd use a more advanced audio library
            sound.play()
        else:
            sound.play()
        
        # Play combo sound for milestones
        if combo > 0 and combo % 10 == 0 and state.combo_snd:
            state.combo_snd.play()


def update_lowpass_filter(state: GameState, dt: float, settings: Dict):
    """Update lowpass filter effect on background music"""
    if not settings.get("audio", {}).get("lowpass_on_bad", True):
        return
        
    if state.lowpass_timer > 0:
        state.lowpass_timer -= dt
        state.lowpass_intensity = state.lowpass_timer / 1000.0  # 1 second duration
    else:
        state.lowpass_intensity = 0.0
    
    # Apply lowpass effect by reducing music volume
    if state.lowpass_intensity > 0:
        # Reduce music volume based on lowpass intensity
        volume = 1.0 - (state.lowpass_intensity * 0.5)  # Max 50% reduction
        pygame.mixer.music.set_volume(volume)
    else:
        # Restore normal volume
        music_volume = settings.get("audio", {}).get("music_volume", 0.8)
        pygame.mixer.music.set_volume(music_volume)


def trigger_lowpass_filter(state: GameState):
    """Trigger lowpass filter effect for bad hits"""
    state.lowpass_timer = 1000  # 1 second duration


def add_animated_label(state: GameState, text: str, x: int, y: int, color: Tuple[int, int, int], duration: int = 1000):
    """Add animated label with jumping, scaling, fading effects"""
    state.animated_labels.append({
        "text": text,
        "x": x,
        "y": y,
        "color": color,
        "life": duration,
        "max_life": duration,
        "scale": 0.5,
        "target_scale": 1.2,
        "velocity_y": -3.0,
        "gravity": 0.1,
        "bounce": 0.7,
        "bounced": False
    })


def update_animated_labels(state: GameState, dt: float):
    """Update animated labels with physics and scaling"""
    for label in list(state.animated_labels):
        label["life"] -= dt
        
        if label["life"] <= 0:
            state.animated_labels.remove(label)
            continue
            
        # Physics: gravity and bouncing
        label["velocity_y"] += label["gravity"] * dt * 0.1
        label["y"] += label["velocity_y"] * dt * 0.1
        
        # Bounce effect
        if label["y"] > CENTER[1] and not label["bounced"]:
            label["velocity_y"] *= -label["bounce"]
            label["bounced"] = True
            
        # Scale animation
        progress = 1.0 - (label["life"] / label["max_life"])
        if progress < 0.3:
            # Scale up
            label["scale"] = 0.5 + (progress / 0.3) * (label["target_scale"] - 0.5)
        else:
            # Scale down
            label["scale"] = label["target_scale"] - ((progress - 0.3) / 0.7) * (label["target_scale"] - 0.8)


def draw_animated_labels(screen: pygame.Surface, state: GameState, offset: Tuple[int, int], font: pygame.font.Font):
    """Draw animated labels with scaling and fading"""
    ox, oy = offset
    
    for label in state.animated_labels:
        # Calculate alpha based on life
        alpha = int(255 * (label["life"] / label["max_life"]))
        alpha = max(0, min(255, alpha))
        
        # Create scaled text surface
        scale = label["scale"]
        text_surf = font.render(label["text"], True, label["color"])
        
        if scale != 1.0:
            new_size = (int(text_surf.get_width() * scale), int(text_surf.get_height() * scale))
            if new_size[0] > 0 and new_size[1] > 0:
                text_surf = pygame.transform.scale(text_surf, new_size)
        
        # Apply alpha
        if alpha < 255:
            text_surf.set_alpha(alpha)
        
        # Draw with offset
        screen.blit(text_surf, (label["x"] - text_surf.get_width()//2 + ox, 
                               label["y"] - text_surf.get_height()//2 + oy))


def update_combo_pulse(state: GameState, dt: float, beat_time: float):
    """Update combo counter pulse animation"""
    if state.combo > 0:
        # Pulse with music rhythm
        beat_freq = 2.0  # 2 beats per second
        pulse = 0.5 + 0.5 * math.sin(beat_time * beat_freq * 0.01)
        state.combo_pulse_intensity = pulse
        state.combo_pulse_timer = 200  # Keep pulsing
    else:
        state.combo_pulse_intensity = 0.0
        state.combo_pulse_timer = max(0, state.combo_pulse_intensity - dt)


def draw_combo_counter(screen: pygame.Surface, state: GameState, offset: Tuple[int, int], font: pygame.font.Font):
    """Draw large pulsing combo counter"""
    if state.combo <= 0:
        return
        
    ox, oy = offset
    w, h = screen.get_size()
    
    # Calculate pulse scale
    pulse_scale = 1.0 + state.combo_pulse_intensity * 0.3
    
    # Create combo text
    combo_text = f"{state.combo}x"
    combo_surf = font.render(combo_text, True, (255, 255, 255))
    
    # Scale the text
    if pulse_scale != 1.0:
        new_size = (int(combo_surf.get_width() * pulse_scale), int(combo_surf.get_height() * pulse_scale))
        combo_surf = pygame.transform.scale(combo_surf, new_size)
    
    # Position at top center
    x = w // 2 + ox
    y = 100 + oy
    
    # Add glow effect
    glow_surf = pygame.Surface((combo_surf.get_width() + 20, combo_surf.get_height() + 20), pygame.SRCALPHA)
    glow_color = (120, 200, 255, 100)
    pygame.draw.rect(glow_surf, glow_color, glow_surf.get_rect(), border_radius=10)
    screen.blit(glow_surf, (x - combo_surf.get_width()//2 - 10, y - combo_surf.get_height()//2 - 10))
    
    # Draw combo text
    screen.blit(combo_surf, (x - combo_surf.get_width()//2, y - combo_surf.get_height()//2))


def calculate_rank(score: int, total_notes: int, accuracy: float) -> str:
    """Calculate rank based on score, total notes, and accuracy"""
    if total_notes == 0:
        return "C"
    
    # Calculate score per note
    score_per_note = score / total_notes if total_notes > 0 else 0
    
    # Rank criteria
    if accuracy >= 0.95 and score_per_note >= 250:
        return "S"
    elif accuracy >= 0.85 and score_per_note >= 200:
        return "A"
    elif accuracy >= 0.70 and score_per_note >= 150:
        return "B"
    else:
        return "C"


def start_rank_animation(state: GameState, rank: str):
    """Start rank letter animation"""
    state.rank_animation = {
        "rank": rank,
        "scale": 0.1,
        "target_scale": 2.0,
        "life": 2000,
        "max_life": 2000,
        "rotation": 0.0,
        "x": CENTER[0],
        "y": CENTER[1]
    }


def update_rank_animation(state: GameState, dt: float):
    """Update rank animation"""
    if not state.rank_animation:
        return
        
    anim = state.rank_animation
    anim["life"] -= dt
    
    if anim["life"] <= 0:
        state.rank_animation = None
        return
    
    # Scale animation
    progress = 1.0 - (anim["life"] / anim["max_life"])
    if progress < 0.2:
        # Scale up quickly
        anim["scale"] = 0.1 + (progress / 0.2) * (anim["target_scale"] - 0.1)
    elif progress < 0.8:
        # Hold at target scale
        anim["scale"] = anim["target_scale"]
    else:
        # Scale down slowly
        anim["scale"] = anim["target_scale"] - ((progress - 0.8) / 0.2) * (anim["target_scale"] - 0.5)
    
    # Rotation
    anim["rotation"] += dt * 0.002


def draw_rank_animation(screen: pygame.Surface, state: GameState, offset: Tuple[int, int], font: pygame.font.Font):
    """Draw rank letter animation"""
    if not state.rank_animation:
        return
        
    anim = state.rank_animation
    ox, oy = offset
    
    # Calculate alpha
    alpha = int(255 * (anim["life"] / anim["max_life"]))
    alpha = max(0, min(255, alpha))
    
    # Create rank text
    rank_surf = font.render(anim["rank"], True, (255, 215, 0))  # Gold color
    
    # Scale
    if anim["scale"] != 1.0:
        new_size = (int(rank_surf.get_width() * anim["scale"]), int(rank_surf.get_height() * anim["scale"]))
        if new_size[0] > 0 and new_size[1] > 0:
            rank_surf = pygame.transform.scale(rank_surf, new_size)
    
    # Rotate
    if abs(anim["rotation"]) > 0.01:
        rank_surf = pygame.transform.rotate(rank_surf, anim["rotation"])
    
    # Apply alpha
    if alpha < 255:
        rank_surf.set_alpha(alpha)
    
    # Draw
    screen.blit(rank_surf, (anim["x"] - rank_surf.get_width()//2 + ox, 
                           anim["y"] - rank_surf.get_height()//2 + oy))


def start_game_over_animation(state: GameState):
    """Start simplified game over animation for better performance"""
    state.game_over_timer = 0
    state.game_over_zoom = 1.0
    state.game_over_red_flash = 1.0
    state.slow_motion_factor = 1.0
    state.music_fade_timer = 0
    state.screen_crack_timer = 0
    
    # Упрощенная анимация - только несколько фрагментов
    state.note_fragments.clear()
    fragment_count = min(10, len(state.notes))  # Максимум 10 фрагментов
    for i in range(fragment_count):
        if i < len(state.notes):
            note = state.notes[i]
            x, y = note.position(pygame.time.get_ticks() - state.start_time_ms)
            fragment = {
                "x": x,
                "y": y,
                "vx": (i % 4 - 2) * 2,
                "vy": (i % 4 - 2) * 2,
                "life": 1.0,
                "rotation": 0.0,
                "rotation_speed": 0.0,  # Убираем вращение для производительности
                "color": COLOR_NOTE.get(note.note.side, (255, 255, 255)),
                "size": 8
            }
            state.note_fragments.append(fragment)
    
    # Stop music with fade
    pygame.mixer.music.fadeout(1000)  # Быстрее


def update_game_over_animation(state: GameState, dt: float):
    """Update simplified game over animation for better performance"""
    if not state.failed:
        return
    
    state.game_over_timer += dt
    
    # Убираем zoom для избежания пиксельности
    state.game_over_zoom = 1.0
    
    # Red flash effect
    if state.game_over_timer < 500:
        state.game_over_red_flash = 1.0 - (state.game_over_timer / 500.0)
    else:
        state.game_over_red_flash = 0.0
    
    # Убираем slow motion
    state.slow_motion_factor = 1.0
    
    # Упрощенное обновление фрагментов
    state.note_fragments = [f for f in state.note_fragments if f["life"] > 0]
    for fragment in state.note_fragments:
        fragment["x"] += fragment["vx"] * dt * 0.1
        fragment["y"] += fragment["vy"] * dt * 0.1
        fragment["life"] -= dt * 0.003


def draw_game_over_animation(screen: pygame.Surface, state: GameState, offset: Tuple[int, int], font: pygame.font.Font, big_font: pygame.font.Font):
    """Draw simplified game over animation for better performance"""
    if not state.failed:
        return
    
    ox, oy = offset
    w, h = screen.get_size()
    
    # Упрощенный red flash overlay
    if state.game_over_red_flash > 0:
        flash_surf = pygame.Surface((w, h))
        flash_surf.fill((255, 0, 0))
        flash_surf.set_alpha(int(255 * state.game_over_red_flash * 0.2))
        screen.blit(flash_surf, (0, 0))
    
    # Упрощенная отрисовка фрагментов
    for fragment in state.note_fragments:
        if fragment["life"] <= 0:
            continue
        
        # Простые прямоугольники вместо кругов для производительности
        size = 6
        color = fragment["color"]
        alpha = int(255 * fragment["life"])
        
        rect = pygame.Rect(fragment["x"] - size//2 + ox, fragment["y"] - size//2 + oy, size, size)
        surf = pygame.Surface((size, size))
        surf.fill(color)
        surf.set_alpha(alpha)
        screen.blit(surf, rect)
    
    # Game over text
    if state.game_over_timer > 1000:  # Показываем раньше
        failed_text = big_font.render("FAILED", True, (255, 50, 50))
        text_rect = failed_text.get_rect(center=(w//2 + ox, h//2 - 100 + oy))
        screen.blit(failed_text, text_rect)


def draw_game_over_menu(screen: pygame.Surface, state: GameState, offset: Tuple[int, int], font: pygame.font.Font, big_font: pygame.font.Font):
    """Draw game over menu with statistics and options"""
    if not state.failed or state.game_over_timer < 4000:  # Show menu after 4 seconds
        return []
    
    ox, oy = offset
    w, h = screen.get_size()
    
    # Semi-transparent overlay
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))
    
    # Calculate statistics
    accuracy = (state.hits / state.total_notes * 100) if state.total_notes > 0 else 0
    rank = calculate_rank(state.score, state.total_notes, accuracy)
    
    # Statistics text
    stats_y = h//2 - 100
    stats_text = [
        f"Точность: {accuracy:.1f}%",
        f"Комбо: {state.best_combo}",
        f"Ранг: {rank}",
        f"Очки: {state.score}"
    ]
    
    for i, stat in enumerate(stats_text):
        stat_surf = font.render(stat, True, (255, 255, 255))
        stat_rect = stat_surf.get_rect(center=(w//2 + ox, stats_y + i * 30 + oy))
        screen.blit(stat_surf, stat_rect)
    
    # Menu buttons with keyboard shortcuts
    button_y = h//2 + 50
    buttons = [
        ("Попробовать снова (R)", "restart"),
        ("В меню (Enter)", "menu"),
        ("Статистика (S)", "stats")
    ]
    
    button_rects = []
    for i, (text, action) in enumerate(buttons):
        button_surf = font.render(text, True, (255, 255, 255))
        button_rect = button_surf.get_rect(center=(w//2 + ox, button_y + i * 40 + oy))
        
        # Simple button background
        bg_rect = button_rect.inflate(20, 10)
        pygame.draw.rect(screen, (50, 50, 50), bg_rect, border_radius=5)
        pygame.draw.rect(screen, (150, 150, 150), bg_rect, 2, border_radius=5)
        
        screen.blit(button_surf, button_rect)
        button_rects.append((bg_rect, action))
    
    return button_rects


_vignette_cache = {}

def apply_effects(screen: pygame.Surface, effects: Optional[List[str]], perf_mode: bool=False, quality: str="medium", frame_counter: int=0):
    if not effects:
        return
    w, h = screen.get_size()
    skip_heavy = perf_mode and (frame_counter % 2 == 1)

    if quality == "high":
        scale = 1.0
    elif quality == "medium":
        scale = 0.5
    else:
        scale = 0.35
    if perf_mode and quality != "high":
        scale = min(scale, 0.35)
    tw = max(1, int(w * scale))
    th = max(1, int(h * scale))
    src = pygame.transform.smoothscale(screen, (tw, th)) if scale != 1.0 else screen.copy()

    def blit_back(s: pygame.Surface):
        if scale == 1.0:
            screen.blit(s, (0, 0))
        else:
            up = pygame.transform.smoothscale(s, (w, h))
            screen.blit(up, (0, 0))

    work = src

    if quality != "low":
        if "blur" in effects:
            small = pygame.transform.smoothscale(work, (max(1, tw//3), max(1, th//3)))
            work = pygame.transform.smoothscale(small, (tw, th))
        if "pixelate" in effects and quality == "high" and not skip_heavy:
            small = pygame.transform.scale(work, (max(1, tw//18), max(1, th//18)))
            work = pygame.transform.scale(small, (tw, th))
    else:
        if "blur" in effects or "pixelate" in effects:
            small = pygame.transform.smoothscale(work, (max(1, tw//4), max(1, th//4)))
            work = pygame.transform.smoothscale(small, (tw, th))

    if quality == "high" and not perf_mode and ("grayscale" in effects or "desaturate" in effects or "invert" in effects or "contrast" in effects) and not skip_heavy:
        try:
            arr = pygame.surfarray.pixels3d(work).copy()
            if "grayscale" in effects or "desaturate" in effects:
                gray = (arr[:,:,0]*0.3 + arr[:,:,1]*0.59 + arr[:,:,2]*0.11).astype('uint8')
                arr[:,:,0] = gray; arr[:,:,1] = gray; arr[:,:,2] = gray
            if "invert" in effects:
                arr = 255 - arr
            if "contrast" in effects:
                import numpy as np
                a = arr.astype('int16')
                a = (a - 128) * 1.2 + 128
                arr = a.clip(0,255).astype('uint8')
            work = pygame.surfarray.make_surface(arr)
        except Exception:
            pass

    blit_back(work)

    if "vignette" in effects:
        key = (w, h)
        ov = _vignette_cache.get(key)
        if ov is None:
            ov = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.circle(ov, (0,0,0,120), (w//2, h//2), max(w,h)//2)
            _vignette_cache[key] = ov
        screen.blit(ov, (0,0))
    if "chroma_shift" in effects and quality == "high" and not skip_heavy:
        shifted = src if scale == 1.0 else pygame.transform.smoothscale(src, (tw, th))
        up = shifted if scale == 1.0 else pygame.transform.smoothscale(shifted, (w, h))
        screen.blit(up, (-2, 0), special_flags=pygame.BLEND_ADD)
        screen.blit(up, (2, 0), special_flags=pygame.BLEND_ADD)
    if "glow_boost" in effects and quality != "low":
        glow = src if scale == 1.0 else pygame.transform.smoothscale(src, (int(tw*1.04), int(th*1.04)))
        if scale != 1.0:
            glow = pygame.transform.smoothscale(glow, (w, h))
        glow.set_alpha(60)
        screen.blit(glow, (-(glow.get_width()-w)//2, -(glow.get_height()-h)//2))


def play_level(level: Level, screen: Optional[pygame.Surface] = None) -> None:
    if not pygame.get_init():
        pygame.init()
    created_screen = False
    if screen is None:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        created_screen = True
    w, h = screen.get_size()
    global WINDOW_SIZE, CENTER
    WINDOW_SIZE = (w, h)
    CENTER = (w // 2, h // 2)
    pygame.display.set_caption(f"KeyY: {level.title} - {level.artist}")
    clock = pygame.time.Clock()
    font = pygame.font.Font(FONT_NAME, 28)
    big_font = pygame.font.Font(FONT_NAME, 48)

    # Settings with safe defaults
    try:
        settings = load_settings()
    except Exception:
        settings = {}
    quality = settings.get("graphics", {}).get("quality", "medium")
    effects_enabled = settings.get("graphics", {}).get("effects_enabled", True)
    effects_mode = settings.get("graphics", {}).get("effects_mode", "light")
    visible_lead_ms = int(settings.get("timing", {}).get("visible_lead_ms", 500))
    linger_ms = int(settings.get("timing", {}).get("linger_ms", 500))
    visible_lead_ms = max(visible_lead_ms, level.approach_ms)
    # difficulty presets (allow per-level override)
    diff = (level.difficulty or settings.get("timing", {}).get("difficulty", "normal"))
    if diff == "easy":
        level.hit_window_ms = max(level.hit_window_ms, 160)
    elif diff == "hard":
        level.hit_window_ms = min(level.hit_window_ms, 90)
    elif diff == "insane":
        level.hit_window_ms = min(level.hit_window_ms, 70)

    audio_path = level.audio
    if not os.path.isabs(audio_path):
        audio_path = os.path.join(os.getcwd(), audio_path)
    if not os.path.exists(audio_path):
        print(f"Audio not found: {audio_path}")
        return
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    try:
        pygame.mixer.music.load(audio_path)
    except Exception as exc:
        print(f"Failed to load audio: {exc}")
        return
    
    # Apply initial audio volumes from settings
    try:
        music_volume = float(settings.get("audio", {}).get("music_volume", 0.8))
        pygame.mixer.music.set_volume(max(0.0, min(1.0, music_volume)))
    except Exception:
        pass

    # Estimate duration for progress bar
    duration_ms = 0
    try:
        snd = pygame.mixer.Sound(audio_path)
        duration_ms = int(snd.get_length() * 1000)
    except Exception:
        pass
    if duration_ms <= 0:
        last_note_time = max([n.time_ms for n in (level.notes or [Note(0,"left","A")])]) if level.notes else 0
        duration_ms = last_note_time + 3000

    # Load sound effects
    sound_paths = {
        "hit": "hit.wav",
        "miss": "miss.wav", 
        "perfect": "perfect.wav",
        "good": "good.wav",
        "bad": "bad.wav",
        "combo": "combo.wav"
    }
    
    state = GameState(level)
    
    for sound_name, filename in sound_paths.items():
        path = os.path.join("assets", filename)
        if os.path.exists(path):
            try:
                sound = pygame.mixer.Sound(path)
                if sound_name == "hit":
                    state.hit_snd = sound
                elif sound_name == "miss":
                    state.miss_snd = sound
                elif sound_name == "perfect":
                    state.perfect_snd = sound
                elif sound_name == "good":
                    state.good_snd = sound
                elif sound_name == "bad":
                    state.bad_snd = sound
                elif sound_name == "combo":
                    state.combo_snd = sound
            except Exception:
                pass

    # Apply SFX volume from settings
    try:
        sfx_volume = float(settings.get("audio", {}).get("sfx_volume", 0.9))
        for snd in (state.hit_snd, state.miss_snd, state.perfect_snd, state.good_snd, state.bad_snd, state.combo_snd):
            if snd:
                snd.set_volume(max(0.0, min(1.0, sfx_volume)))
    except Exception:
        pass

    state.reset()
    level.notes.sort(key=lambda n: n.time_ms)
    if level.events:
        level.events.sort(key=lambda e: e.time_ms)
    
    # Initialize visual effects
    init_parallax_layers(state)

    # Game over menu buttons
    game_over_buttons = []
    game_over_menu_active = False

    countdown_total = 3000
    countdown_start = pygame.time.get_ticks()

    perf_slow_frames = 0
    frame_counter = 0
    
    # Убираем встроенные переменные модов

    running = True
    while running:
        dt = clock.tick(60)  # Стабильные 60 FPS вместо 120
        frame_counter += 1
        
        # Применяем BPM множитель к времени игры
        real_time_ms = pygame.time.get_ticks() - state.start_time_ms
        now_ms = int(real_time_ms * state.bpm_multiplier)

        # --- Auto-miss: if a note "lies" on the center > 50ms ---
        if getattr(state, 'audio_started', False) and not getattr(state, 'finished', False) and not getattr(state, 'failed', False):
            for an in list(getattr(state, 'notes', [])):
                if getattr(an, 'hit', False) or getattr(an, 'missed', False):
                    continue
                arrive = an.spawn_time_ms + level.approach_ms
                # For hold notes: if not started yet, treat like tap for this rule
                is_hold = getattr(an.note, 'duration_ms', 0) and getattr(an.note, 'duration_ms', 0) > 0
                hold_started = getattr(an, 'hold_started', False)
                if now_ms > arrive + CENTER_LINGER_AUTO_MISS_MS and (not is_hold or not hold_started):
                    an.missed = True
                    # Skip penalties for fake notes
                    if getattr(an.note, 'is_fake', False):
                        continue
                    # HP / shake / flash if fields exist
                    if hasattr(state, 'combo'):
                        state.combo = 0
                    if hasattr(state, 'hp'):
                        apply_hp_damage(state, 10)
                    if hasattr(state, 'flash_timer'):
                        state.flash_timer = 200
                    if hasattr(state, 'shake_timer'):
                        state.shake_timer = max(getattr(state, 'shake_timer', 0), 140)
                    if hasattr(state, 'shake_intensity'):
                        state.shake_intensity = max(getattr(state, 'shake_intensity', 0.0), 0.6)
                    if hasattr(state, 'judgements'):
                        state.judgements.append(("MISS", now_ms))
                        state.all_judgements.append("MISS")
                        state.all_judgements.append("MISS")
                    try:
                        if state.miss_snd:
                            state.miss_snd.play()
                    except Exception:
                        pass

        # Включаем performance mode для лучшей производительности
        current_fps = clock.get_fps()
        perf_mode = current_fps < 55  # Автоматически включаем если FPS падает

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    state.reset()
                    pygame.mixer.music.stop()
                    countdown_start = pygame.time.get_ticks()
                    continue
                elif state.failed and state.game_over_timer > 4000:  # Game over menu is active
                    if event.key == pygame.K_r:  # Restart
                        state.reset()
                        pygame.mixer.music.stop()
                        countdown_start = pygame.time.get_ticks()
                        continue
                    elif event.key == pygame.K_RETURN:  # Menu
                        running = False
                    elif event.key == pygame.K_s:  # Statistics
                        # Show detailed statistics in console for now
                        print(f"=== СТАТИСТИКА ===")
                        print(f"Точность: {(state.hits / state.total_notes * 100) if state.total_notes > 0 else 0:.1f}%")
                        print(f"Лучшее комбо: {state.best_combo}")
                        print(f"Очки: {state.score}")
                        print(f"Попаданий: {state.hits}/{state.total_notes}")
                        rank = calculate_rank(state.score, state.total_notes, (state.hits / state.total_notes) if state.total_notes > 0 else 0)
                        print(f"Ранг: {rank}")
                        print("==================")
                else:
                    # Обработка изменения BPM
                    if event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                        state.bpm_multiplier = min(3.0, state.bpm_multiplier + 0.1)
                        print(f"BPM множитель: {state.bpm_multiplier:.1f}x")
                    elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                        state.bpm_multiplier = max(0.5, state.bpm_multiplier - 0.1)
                        print(f"BPM множитель: {state.bpm_multiplier:.1f}x")
                    elif event.key == pygame.K_EQUALS:  # Reset BPM
                        state.bpm_multiplier = 1.0
                        print("BPM сброшен на нормальную скорость")
                    
                    # Выполняем хуки модов для обработки клавиш
                    mod_system.execute_mod_hooks("on_key_press", event, state, settings)
                    
                    if state.audio_started and not state.finished and not state.failed:
                        # mark side as held
                        side_dn = find_side_for_key(event.key)
                        if side_dn:
                            state.side_holding[side_dn] = True
                            state.keys_held.add(event.key)  # Добавляем в зажатые клавиши
                        handle_hit_input(state, event.key, now_ms, settings)
            elif event.type == pygame.KEYUP:
                # handle release for holds
                side_up = find_side_for_key(event.key)
                if side_up:
                    state.side_holding[side_up] = False
                    state.keys_held.discard(event.key)  # Убираем из зажатых клавиш
                    # If there is an active hold note for this side not yet completed and before end => fail it
                    for an in state.notes:
                        if an.missed or an.hit:
                            continue
                        if not an.is_hold:
                            continue
                        if an.note.side != side_up:
                            continue
                        if not an.hold_started:
                            continue
                        # early release before end window
                        if now_ms < an.end_time() - state.level.hit_window_ms:
                            an.missed = True
                            state.combo = 0
                            state.judgements.append(("MISS", now_ms))
                            state.all_judgements.append("MISS")
                            state.all_judgements.append("MISS")
                            apply_hp_damage(state, 10)
                            if state.miss_snd:
                                state.miss_snd.play()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Handle game over menu button clicks
                if state.failed and state.game_over_timer > 4000 and game_over_buttons:
                    mx, my = event.pos
                    for i, (button_rect, action) in enumerate(game_over_buttons):
                        if button_rect.collidepoint(mx, my):
                            if action == "restart":
                                state.reset()
                                pygame.mixer.music.stop()
                                countdown_start = pygame.time.get_ticks()
                                game_over_menu_active = False
                                break
                            elif action == "menu":
                                running = False
                                break
                            elif action == "stats":
                                # Show detailed statistics in console for now
                                print(f"=== СТАТИСТИКА ===")
                                print(f"Точность: {(state.hits / state.total_notes * 100) if state.total_notes > 0 else 0:.1f}%")
                                print(f"Лучшее комбо: {state.best_combo}")
                                print(f"Очки: {state.score}")
                                print(f"Попаданий: {state.hits}/{state.total_notes}")
                                rank = calculate_rank(state.score, state.total_notes, (state.hits / state.total_notes) if state.total_notes > 0 else 0)
                                print(f"Ранг: {rank}")
                                print("==================")
                                break

        elapsed_cd = pygame.time.get_ticks() - countdown_start
        if elapsed_cd < countdown_total:
            screen.fill(COLOR_BG)
            draw_grid(screen, (0, 0))
            remaining = countdown_total - elapsed_cd
            if remaining > 2000:
                txt = "3"
            elif remaining > 1000:
                txt = "2"
            elif remaining > 0:
                txt = "1"
            else:
                txt = "GO!"
            surf = big_font.render(txt, True, COLOR_TEXT)
            sr = surf.get_rect(center=CENTER)
            screen.blit(surf, sr)
            pygame.display.flip()
            continue
        elif not state.audio_started:
            state.start_time_ms = pygame.time.get_ticks()
            now_ms = 0
            pygame.mixer.music.play()
            state.audio_started = True

        if state.audio_started and not state.finished and not state.failed:
            while state.next_note_idx < len(level.notes):
                note = level.notes[state.next_note_idx]
                spawn_time = note.time_ms - level.approach_ms
                if now_ms >= spawn_time - 5:
                    state.notes.append(ActiveNote(note, spawn_time, level.approach_ms))
                    state.next_note_idx += 1
                else:
                    break

        if state.audio_started and not state.finished and not state.failed:
            # complete holds when end time reached while still held
            for an in state.notes:
                if an.missed or an.hit:
                    continue
                if not an.is_hold:
                    continue
                if not an.hold_started:
                    continue
                if now_ms >= an.end_time() - state.level.hit_window_ms:
                    # to complete, side must still be held
                    if state.side_holding.get(an.note.side, False):
                        an.hit = True
                        state.hits += 1
                        # Красивые частицы для эффектов
                        state.particles.extend([Particle(*CENTER, COLOR_NOTE.get(an.note.side, (255,255,255))) for _ in range(15)])
                        state.shake_timer = 160
                        state.shake_intensity = 0.7
                        add = 300
                        judge = "HOLD"
                        state.combo += 1
                        state.best_combo = max(state.best_combo, state.combo)
                        state.score += add + int(state.combo * 0.5)
                        state.judgements.append((judge, now_ms))
                        if state.hit_snd:
                            state.hit_snd.play()

        if level.events and not state.finished and not state.failed:
            while state.next_event_idx < len(level.events) and now_ms >= level.events[state.next_event_idx].time_ms:
                ev = level.events[state.next_event_idx]
                if ev.type == 'zoom' and ev.value is not None:
                    state.cam_zoom = max(0.5, min(2.0, ev.value))
                elif ev.type == 'rotate' and ev.value is not None:
                    state.cam_angle = ev.value % 360.0
                elif ev.type == 'effect_on' and ev.name:
                    cur = list(level.effects or []) if state.active_effects_override is None else list(state.active_effects_override)
                    if ev.name not in cur:
                        cur.append(ev.name)
                    state.active_effects_override = cur
                elif ev.type == 'effect_off' and ev.name:
                    cur = list(level.effects or []) if state.active_effects_override is None else list(state.active_effects_override)
                    if ev.name in cur:
                        cur.remove(ev.name)
                    state.active_effects_override = cur
                state.next_event_idx += 1

        if state.pulse_timer > 0:
            state.pulse_timer = max(0, state.pulse_timer - dt)
        if state.shake_timer > 0:
            state.shake_timer = max(0, state.shake_timer - dt)
            state.shake_intensity = max(0.0, state.shake_intensity - dt * 0.006)
        # Высокооптимизированное обновление частиц
        alive_particles = []
        for p in state.particles:
            if p.life > 0:
                p.update(dt)
                alive_particles.append(p)
        state.particles = alive_particles
        
        # Update new visual effects
        update_track_glow(state, dt)
        update_beat_glow(state, dt, now_ms)
        update_hit_sparks(state, dt)
        update_parallax_layers(state, dt, now_ms)
        
        # Update UI animations
        update_animated_labels(state, dt)
        update_combo_pulse(state, dt, now_ms)
        update_rank_animation(state, dt)
        
        # Update audio effects
        update_lowpass_filter(state, dt, settings)
        
        # Убираем встроенный вызов автопилота - теперь это мод
        
        # Выполняем хуки модов
        mod_system.execute_mod_hooks("on_game_update", state, dt, now_ms)

        ox = oy = 0
        if state.shake_timer > 0 and state.shake_intensity > 0:
            ox = int(random.uniform(-1, 1) * 10 * state.shake_intensity)
            oy = int(random.uniform(-1, 1) * 10 * state.shake_intensity)

        scene = state.scene
        scene.fill(COLOR_BG)
        
        # Draw parallax background layers (disabled during game over)
        if not state.failed:
            draw_parallax_layers(scene, state, (ox, oy), settings)
        
        # Draw track glow effects (disabled during game over)
        if not state.failed:
            draw_track_glow(scene, state, (ox, oy))
            draw_beat_glow(scene, state, (ox, oy))
        
        # Draw grid
        draw_grid(scene, (ox, oy))
        # Subtle parallax circles behind playfield
        if settings.get("graphics", {}).get("parallax_circles", False):
            mx, my = pygame.mouse.get_pos()
            px = (mx - CENTER[0]) * 0.02
            py = (my - CENTER[1]) * 0.02
            for i in range(3):
                r = int(CENTER_RADIUS * (2.5 + i*0.8))
                a = 28 - i*6
                col = (140 + i*20, 180 + i*10, 255 - i*30, a)
                pygame.draw.circle(scene, col, (CENTER[0] + ox + int(px*i*6), CENTER[1] + oy + int(py*i*6)), r, width=2)
        pulse_scale = 1.0 + 0.2 * (state.pulse_timer / 150.0)
        radius = int(CENTER_RADIUS * pulse_scale)
        pygame.draw.circle(scene, (200, 220, 255, 40), (CENTER[0] + ox, CENTER[1] + oy), radius+24, width=8)
        pygame.draw.circle(scene, (200, 220, 255, 30), (CENTER[0] + ox, CENTER[1] + oy), radius+40, width=6)
        # Проверяем есть ли активные hold-ноты
        active_holds = [an for an in state.notes if an.is_hold and an.hold_started and not an.hit and not an.missed]
        
        if active_holds:
            # Специальное свечение для активных hold-нот
            hold_colors = [COLOR_NOTE.get(an.note.side, (255, 255, 255)) for an in active_holds]
            
            # Пульсирующее свечение
            pulse = 0.7 + 0.3 * math.sin(now_ms * 0.008)
            
            for i, hold_color in enumerate(hold_colors):
                # Многослойное свечение для каждой активной hold-ноты
                glow_radius = int(radius + 15 + i * 5)
                glow_alpha = int(80 * pulse)
                
                # Создаем поверхность для свечения
                pygame.draw.circle(scene, (*hold_color, glow_alpha), (CENTER[0] + ox, CENTER[1] + oy), glow_radius, width=4)
            
            # Яркий центральный круг
            bright_color = tuple(min(255, c + 50) for c in COLOR_CENTER)
            pygame.draw.circle(scene, bright_color, (CENTER[0]+ox, CENTER[1]+oy), radius, width=6)
        else:
            # Обычный центральный круг
            pygame.draw.circle(scene, COLOR_CENTER, (CENTER[0]+ox, CENTER[1]+oy), radius, width=4)
        # Оптимизированный цикл отрисовки нот - фильтруем активные ноты заранее
        active_notes = [an for an in state.notes if not (an.hit or an.missed)]
        
        for an in active_notes:
            # Предвычисляем значения для оптимизации
            arrival = an.spawn_time_ms + state.level.approach_ms
            
            # Быстрая проверка видимости
            if now_ms < arrival - visible_lead_ms:
                continue
                
            # Final guard: if a note overstayed on center, auto-miss and skip drawing
            is_hold = hasattr(an.note, 'duration_ms') and an.note.duration_ms > 0
            hold_started = getattr(an, 'hold_started', False)
            
            if now_ms >= arrival + CENTER_LINGER_AUTO_MISS_MS and (not is_hold or not hold_started):
                an.missed = True
                # Skip penalties for fake notes
                if getattr(an.note, 'is_fake', False):
                    continue
                state.combo = 0
                apply_hp_damage(state, 10)
                state.flash_timer = 200
                state.shake_timer = max(state.shake_timer, 140)
                state.shake_intensity = max(state.shake_intensity, 0.6)
                state.judgements.append(("MISS", now_ms))
                state.all_judgements.append("MISS")
                state.all_judgements.append("MISS")
                state.all_judgements.append("MISS")
                if state.miss_snd:
                    state.miss_snd.play()
                continue
                
            if now_ms > arrival + linger_ms and not an.missed and not is_hold:
                an.missed = True
                # Skip penalties for fake notes
                if getattr(an.note, 'is_fake', False):
                    continue
                state.combo = 0
                state.judgements.append(("MISS", now_ms))
                state.all_judgements.append("MISS")
                apply_hp_damage(state, 10)
                if state.miss_snd:
                    state.miss_snd.play()
                continue
            col = COLOR_NOTE.get(an.note.side, (200, 200, 200))
            x, y = an.position(now_ms)
            x += ox
            y += oy
            
            # Проверяем фейковую ноту
            is_fake = getattr(an.note, 'is_fake', False)
            
            # Handle different note types
            if getattr(an.note, 'note_type', 'tap') == "double":
                draw_double_note(scene, an, x, y, col, now_ms, is_fake)
            elif getattr(an.note, 'note_type', 'tap') == "slide":
                draw_slide_note(scene, an, x, y, col, now_ms, is_fake)
            else:
                # Regular tap/hold note
                draw_regular_note(scene, an, x, y, col, now_ms, is_fake)
            
            # Draw note label
            label = big_font.render(an.note.key, True, (20, 20, 30))
            lr = label.get_rect(center=(x, y))
            scene.blit(label, lr)
            # draw hold tail to indicate duration
            if an.is_hold:
                arr_t = an.arrive_time()
                end_t = an.end_time()
                
                # Вычисляем направление от центра в противоположную сторону
                sx0, sy0 = spawn_point_for_side(an.note.side)
                cx0, cy0 = CENTER
                
                # Направление от spawn к центру
                dx_to_center = cx0 - sx0
                dy_to_center = cy0 - sy0
                
                # Нормализуем направление
                length_to_center = math.sqrt(dx_to_center**2 + dy_to_center**2)
                if length_to_center > 0:
                    dx_norm = dx_to_center / length_to_center
                    dy_norm = dy_to_center / length_to_center
                else:
                    dx_norm, dy_norm = 0, 0
                
                # Длина hold-ноты в пикселях (пропорционально времени)
                hold_duration_ms = end_t - arr_t
                hold_length_pixels = min(200, hold_duration_ms * 0.2)  # Максимум 200 пикселей
                
                # Текущая позиция ноты
                current_prog = max(0.0, min(1.0, (now_ms - an.spawn_time_ms) / an.approach_ms))
                current_x = int(sx0 + (cx0 - sx0) * current_prog) + ox
                current_y = int(sy0 + (cy0 - sy0) * current_prog) + oy
                
                # Конечная точка hold-ноты (от текущей позиции ноты в противоположную сторону)
                end_x = int(current_x - dx_norm * hold_length_pixels)
                end_y = int(current_y - dy_norm * hold_length_pixels)
                
                # ВСЕГДА рисуем полоску hold-ноты (и когда летит, и когда активна)
                if now_ms < arr_t:
                    # Нота еще летит - рисуем полупрозрачную полоску с анимацией
                    
                    # Пульсирующая анимация для лучшей видимости
                    pulse = 0.7 + 0.3 * math.sin(now_ms * 0.005)
                    
                    # Основная полоска
                    dim_col = tuple(int(c // 2 * pulse) for c in col)
                    pygame.draw.line(scene, (*dim_col, int(150 * pulse)), (current_x, current_y), (end_x, end_y), 6)
                    
                    # Светлая полоска по центру
                    lighter_dim_col = tuple(min(255, int(c // 2 + 30 * pulse)) for c in col)
                    pygame.draw.line(scene, (*lighter_dim_col, int(120 * pulse)), (current_x, current_y), (end_x, end_y), 3)
                    
                    # Движущиеся точки вдоль полоски для анимации
                    dot_spacing = 20
                    total_length = math.sqrt((end_x - current_x)**2 + (end_y - current_y)**2)
                    if total_length > 0:
                        dx_dot = (end_x - current_x) / total_length
                        dy_dot = (end_y - current_y) / total_length
                        
                        # Анимированное смещение точек
                        offset = (now_ms * 0.1) % dot_spacing
                        
                        for i in range(int(offset), int(total_length), dot_spacing):
                            dot_x = int(current_x + dx_dot * i)
                            dot_y = int(current_y + dy_dot * i)
                            pygame.draw.circle(scene, (255, 255, 255, int(100 * pulse)), (dot_x, dot_y), 2)
                    
                    # Кружочек на конце (пульсирующий)
                    end_pulse = 0.8 + 0.2 * math.sin(now_ms * 0.008)
                    end_radius = int(8 * end_pulse)
                    pygame.draw.circle(scene, (*dim_col, int(120 * pulse)), (end_x, end_y), end_radius)
                    pygame.draw.circle(scene, (255, 255, 255, int(80 * pulse)), (end_x, end_y), max(1, end_radius - 3))
                
                # Если нота активна (достигла центра), рисуем яркую активную полоску
                elif now_ms < end_t:
                    # Позиция центра для активной ноты
                    center_x = cx0 + ox
                    center_y = cy0 + oy
                    end_x = int(center_x - dx_norm * hold_length_pixels)
                    end_y = int(center_y - dy_norm * hold_length_pixels)
                    # Рисуем полоску от центра до конечной точки
                    # Основная толстая полоска
                    pygame.draw.line(scene, col, (center_x, center_y), (end_x, end_y), 8)
                    # Светлая полоска по центру
                    lighter_col = tuple(min(255, c + 60) for c in col)
                    pygame.draw.line(scene, lighter_col, (center_x, center_y), (end_x, end_y), 4)
                    # Яркая тонкая линия по центру
                    bright_col = tuple(min(255, c + 100) for c in col)
                    pygame.draw.line(scene, bright_col, (center_x, center_y), (end_x, end_y), 2)
                    
                    # Рисуем кружочек на конце где нужно отпустить
                    end_circle_radius = 12
                    # Внешний круг (темный)
                    pygame.draw.circle(scene, col, (end_x, end_y), end_circle_radius)
                    # Средний круг (светлый)
                    pygame.draw.circle(scene, lighter_col, (end_x, end_y), end_circle_radius - 2)
                    # Внутренний круг (яркий)
                    pygame.draw.circle(scene, bright_col, (end_x, end_y), end_circle_radius - 4)
                    # Центральная точка (белая)
                    pygame.draw.circle(scene, (255, 255, 255), (end_x, end_y), 3)
                    
                    # Пульсирующий эффект для конечного кружочка
                    pulse = 0.5 + 0.5 * math.sin(now_ms * 0.01)
                    pulse_radius = int(end_circle_radius + pulse * 4)
                    pulse_col = (*col, int(100 * (1 - pulse)))
                    pygame.draw.circle(scene, pulse_col, (end_x, end_y), pulse_radius, 2)
                    
                    # Индикатор прогресса hold-ноты
                    if an.hold_started:
                        hold_progress = (now_ms - arr_t) / (end_t - arr_t)
                        hold_progress = max(0.0, min(1.0, hold_progress))
                        
                        # Рисуем полоску прогресса от центра к концу
                        progress_x = int(center_x - dx_norm * hold_length_pixels * hold_progress)
                        progress_y = int(center_y - dy_norm * hold_length_pixels * hold_progress)
                        
                        # Пройденная часть (яркая белая)
                        pygame.draw.line(scene, (255, 255, 255), (center_x, center_y), (progress_x, progress_y), 6)
                        pygame.draw.line(scene, bright_col, (center_x, center_y), (progress_x, progress_y), 4)
                        
                        # Оставшаяся часть (тусклая)
                        if hold_progress < 1.0:
                            dim_col = tuple(c // 3 for c in col)
                            pygame.draw.line(scene, dim_col, (progress_x, progress_y), (end_x, end_y), 4)
        # Ограничиваем количество частиц для производительности (больше для красоты)
        if len(state.particles) > 100:
            state.particles = state.particles[-100:]
        for p in state.particles:
            p.draw(scene)
        
        # Draw hit sparks (disabled during game over)
        if not state.failed:
            draw_hit_sparks(scene, state, (ox, oy))
        
        # Draw UI animations (disabled during game over)
        if not state.failed:
            draw_animated_labels(scene, state, (ox, oy), big_font)
            draw_combo_counter(scene, state, (ox, oy), big_font)
            draw_rank_animation(scene, state, (ox, oy), big_font)
        
        # Draw game over animation
        draw_game_over_animation(scene, state, (ox, oy), font, big_font)
        if state.failed and state.game_over_timer > 4000:
            game_over_buttons = draw_game_over_menu(scene, state, (ox, oy), font, big_font)
            game_over_menu_active = True
        else:
            game_over_buttons = []
            game_over_menu_active = False
        # Кешируем UI текст - обновляем только при изменении значений
        if not hasattr(state, 'cached_score') or state.cached_score != state.score:
            state.cached_score = state.score
            state.score_surf = font.render(f"Score: {state.score}", True, COLOR_TEXT)
        
        if not hasattr(state, 'cached_combo') or state.cached_combo != (state.combo, state.best_combo):
            state.cached_combo = (state.combo, state.best_combo)
            state.combo_surf = font.render(f"Combo: {state.combo} (Best {state.best_combo})", True, COLOR_TEXT)
        
        if not hasattr(state, 'cached_hp') or state.cached_hp != state.hp:
            state.cached_hp = state.hp
            state.hp_surf = font.render(f"HP: {state.hp}", True, COLOR_TEXT)
        
        score_surf = state.score_surf
        combo_surf = state.combo_surf  
        hp_surf = state.hp_surf
        scene.blit(score_surf, (20, 20))
        scene.blit(combo_surf, (20, 56))
        scene.blit(hp_surf, (20, 92))
        
        # Отображаем BPM множитель (сдвинут выше, чтобы не пересекаться с HP баром)
        if state.bpm_multiplier != 1.0:
            bpm_color = (255, 255, 0) if state.bpm_multiplier > 1.0 else (0, 255, 255)
            bpm_surf = font.render(f"Speed: {state.bpm_multiplier:.1f}x", True, bpm_color)
            scene.blit(bpm_surf, (20, 146))
        
        # Отображаем зажатые клавиши (сдвинут ниже)
        if state.keys_held:
            held_keys = [DISPLAY_FOR_KEY.get(key, str(key)) for key in state.keys_held]
            keys_text = "Held: " + ", ".join(held_keys[:5])  # Показываем максимум 5 клавиш
            keys_surf = font.render(keys_text, True, (150, 255, 150))
            scene.blit(keys_surf, (20, 176))
        
        # Выполняем хуки модов для отрисовки UI
        mod_system.execute_mod_hooks("on_draw_ui", scene, font, state)
        # HP bar
        hp_bar_bg = pygame.Rect(20, 126, 200, 14)
        pygame.draw.rect(scene, COLOR_HP_BG, hp_bar_bg, border_radius=7)
        hp_w = int(200 * max(0, min(1, state.hp / 100)))
        pygame.draw.rect(scene, COLOR_HP, pygame.Rect(20, 126, hp_w, 14), border_radius=7)

        state.judgements = [(t, ts) for (t, ts) in state.judgements if now_ms - ts < 800]
        for idx, (txt, ts) in enumerate(state.judgements):
            alpha = 1.0 - (now_ms - ts) / 800.0
            alpha = 0.0 if alpha < 0.0 else (1.0 if alpha > 1.0 else alpha)
            val = int(255 * alpha)
            val = 0 if val < 0 else (255 if val > 255 else val)
            col = (val, val, val)
            j = big_font.render(txt, True, col)
            jr = j.get_rect(center=(CENTER[0]+ox, CENTER[1] - 120 - idx * 40+oy))
            scene.blit(j, jr)
        # Guide lines toward center (removed global guides; tails are drawn per hold note only)
        # guide = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
        # gcol = (200, 200, 220, 40)
        # pygame.draw.line(guide, gcol, (0+10+ox, CENTER[1]+oy), (CENTER[0]+ox, CENTER[1]+oy), 2)
        # pygame.draw.line(guide, gcol, (WINDOW_SIZE[0]-10+ox, CENTER[1]+oy), (CENTER[0]+ox, CENTER[1]+oy), 2)
        # pygame.draw.line(guide, gcol, (CENTER[0]+ox, 0+10+oy), (CENTER[0]+ox, CENTER[1]+oy), 2)
        # pygame.draw.line(guide, gcol, (CENTER[0]+ox, WINDOW_SIZE[1]-10+oy), (CENTER[0]+ox, CENTER[1]+oy), 2)
        # scene.blit(guide, (0,0))
        # Progress bar (top)
        prog = 0.0 if duration_ms <= 0 else max(0.0, min(1.0, now_ms / duration_ms))
        pbg = pygame.Rect(0, 0, WINDOW_SIZE[0], 6)
        pygame.draw.rect(scene, COLOR_PROGRESS_BG, pbg)
        pygame.draw.rect(scene, COLOR_PROGRESS, pygame.Rect(0, 0, int(WINDOW_SIZE[0]*prog), 6))

        # Draw FPS counter (оптимизировано - обновляем только каждые 10 кадров)
        if frame_counter % 10 == 0:
            fps = int(clock.get_fps())
            state.fps_text = font.render(f"FPS: {fps}", True, (100, 100, 100))
        
        # Отображаем FPS если текст существует
        if hasattr(state, 'fps_text'):
            scene.blit(state.fps_text, (WINDOW_SIZE[0] - 100, 10))

        # Apply camera transforms (оптимизировано)
        total_zoom = state.cam_zoom
        # Используем более быстрые трансформации и кеширование
        if abs(state.cam_angle) > 0.01 or abs(total_zoom - 1.0) > 0.01:
            # Упрощенные трансформации для лучшей производительности
            if abs(state.cam_angle) > 0.01:
                transformed = pygame.transform.rotozoom(scene, -state.cam_angle, total_zoom)
            else:
                # Только масштабирование без поворота
                new_size = (int(scene.get_width() * total_zoom), int(scene.get_height() * total_zoom))
                transformed = pygame.transform.scale(scene, new_size)
            
            tx = (WINDOW_SIZE[0] - transformed.get_width()) // 2
            ty = (WINDOW_SIZE[1] - transformed.get_height()) // 2
            screen.fill(COLOR_BG)
            screen.blit(transformed, (tx, ty))
        else:
            screen.blit(scene, (0, 0))
        try:
            effs = state.active_effects_override if state.active_effects_override is not None else level.effects
            if effects_enabled and effects_mode != "off":
                if effects_mode == "light" and effs:
                    effs = [e for e in effs if e in ("vignette","glow_boost","blur")]
                apply_effects(screen, effs, perf_mode=perf_mode, quality=quality, frame_counter=frame_counter)
        except Exception:
            pass

        # Failure overlay
        if not state.failed and state.hp <= 0:
            # Проверяем чит "Без проигрыша"
            no_fail_cheat = False
            try:
                for mod in mod_system.get_enabled_mods():
                    if mod.name == "Читы":
                        with open(mod.file_path + "/mod_info.json", 'r', encoding='utf-8') as f:
                            mod_data = json.load(f)
                            cheat_settings = mod_data.get('settings', {})
                            no_fail_cheat = cheat_settings.get('no_fail', False)
                        break
            except:
                pass
            
            if not no_fail_cheat:
                state.failed = True
                start_game_over_animation(state)
            else:
                state.hp = 1  # Оставляем минимальное HP
        
        # Update game over animation
        if state.failed:
            update_game_over_animation(state, dt)

        if state.audio_started and not state.finished and not state.failed:
            # Finish strictly 1.0s after the last note's center end based on level data
            last_end_center = getattr(state, 'level_last_note_end_center_ms', None)
            all_done = (last_end_center is not None) and (now_ms >= last_end_center + 1000)
            if all_done:
                state.finished = True
                # Calculate and start rank animation
                acc = 0.0 if state.total_notes == 0 else (state.hits / state.total_notes) * 100.0
                rank = calculate_rank(state.score, state.total_notes, acc / 100.0)
                start_rank_animation(state, rank)
                # Save highscore and check achievements
                from .settings import save_highscore, unlock_achievement, get_highscore
                
                level_name = getattr(level, 'title', 'Custom Level')
                is_new_record = save_highscore(level_name, state.score, state.best_combo, acc/100.0, settings.get("timing", {}).get("difficulty", "normal"))
                
                # Check achievements
                if state.best_combo >= 50 and unlock_achievement("combo_50"):
                    state.achievements_earned.append("Combo 50+")
                if state.all_judgements.count("PERFECT") >= max(1, int(0.8 * state.total_notes)) and unlock_achievement("perfect_80"):
                    state.achievements_earned.append("80% PERFECT")
                if acc >= 95.0 and unlock_achievement("accuracy_95"):
                    state.achievements_earned.append("95% Accuracy")
                if state.best_combo >= 100 and unlock_achievement("combo_100"):
                    state.achievements_earned.append("Combo 100+")
                
                # Get best score for display
                best_score = get_highscore(level_name)
                
                # Fade-in overlay
                overlay = pygame.Surface(WINDOW_SIZE, pygame.SRCALPHA)
                for a in range(0, 161, 20):
                    overlay.fill((0, 0, 0, a))
                    screen.blit(overlay, (0, 0))
                    pygame.display.flip()
                    pygame.time.delay(10)
                # compute extended stats
                total = max(1, state.total_notes)
                perfects = state.all_judgements.count("PERFECT")
                goods = state.all_judgements.count("GOOD") + state.all_judgements.count("GREAT")
                bads = state.all_judgements.count("BAD")
                misses = state.all_judgements.count("MISS")
                res1 = big_font.render("Level Complete!", True, COLOR_TEXT)
                res2 = font.render(f"Score: {state.score}", True, COLOR_TEXT)
                if is_new_record:
                    res2 = font.render(f"Score: {state.score} (NEW RECORD!)", True, (255, 215, 0))
                res3 = font.render(f"Best Combo: {state.best_combo}", True, COLOR_TEXT)
                res4 = font.render(f"Accuracy: {acc:.1f}%", True, COLOR_TEXT)
                res5 = font.render(f"Judgements: P {perfects}  G {goods}  B {bads}  M {misses}", True, COLOR_TEXT)
                
                # Show best score if exists
                if best_score:
                    res6 = font.render(f"Best: {best_score.get('score', 0)} (Combo: {best_score.get('combo', 0)})", True, (200, 200, 200))
                else:
                    res6 = None
                btn_font = pygame.font.Font(FONT_NAME, 36)
                def draw_btn(txt, y):
                    surf = btn_font.render(txt, True, (10, 10, 10))
                    pad = 16
                    rect = pygame.Rect(0, 0, surf.get_width()+pad*2, surf.get_height()+pad)
                    rect.center = (CENTER[0], y)
                    pygame.draw.rect(screen, (230, 230, 230), rect, border_radius=10)
                    screen.blit(surf, (rect.x+pad, rect.y+pad//2))
                    return rect
                sr1 = res1.get_rect(center=(CENTER[0], CENTER[1]-100))
                sr2 = res2.get_rect(center=(CENTER[0], CENTER[1]-40))
                sr3 = res3.get_rect(center=(CENTER[0], CENTER[1]-20))
                sr4 = res4.get_rect(center=(CENTER[0], CENTER[1]+0))
                sr5 = res5.get_rect(center=(CENTER[0], CENTER[1]+20))
                if res6:
                    sr6 = res6.get_rect(center=(CENTER[0], CENTER[1]+40))
                # staggered fade/slide-in
                items = [(res1, sr1), (res2, sr2), (res3, sr3), (res4, sr4), (res5, sr5)]
                for idx, (surf_i, rect_i) in enumerate(items):
                    for a in range(0, 181, 45):
                        tmp = surf_i.copy()
                        tmp.set_alpha(a)
                        jitter = 8 - int(a/22)
                        screen.blit(tmp, rect_i.move(0, jitter))
                        pygame.display.flip()
                        pygame.time.delay(8)
                if res6:
                    screen.blit(res6, sr6)
                # Difficulty label
                diff_label = font.render(f"Difficulty: {diff}", True, (180, 180, 180))
                screen.blit(diff_label, diff_label.get_rect(center=(CENTER[0], CENTER[1]+40)))
                
                # Achievements line
                if state.achievements_earned:
                    ach_text = font.render("Achievements: " + ", ".join(state.achievements_earned), True, (255, 215, 0))
                    screen.blit(ach_text, ach_text.get_rect(center=(CENTER[0], CENTER[1]+70)))
                b1 = draw_btn("Restart (R)", CENTER[1]+130)
                b2 = draw_btn("Return to Menu (Enter/Esc)", CENTER[1]+190)
                b3 = draw_btn("Exit Game", CENTER[1]+250)
                pygame.display.flip()
                waiting = True
                # success jingle (use combo sound if available)
                try:
                    if state.combo_snd:
                        state.combo_snd.play()
                except Exception:
                    pass
                while waiting:
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            waiting = False
                            running = False
                        elif e.type == pygame.KEYDOWN:
                            if e.key == pygame.K_r:
                                state.reset()
                                countdown_start = pygame.time.get_ticks()
                                pygame.mixer.music.stop()
                                waiting = False
                            elif e.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                                waiting = False
                                running = False
                        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                            mx, my = e.pos
                            if b1.collidepoint(mx, my):
                                state.reset()
                                countdown_start = pygame.time.get_ticks()
                                pygame.mixer.music.stop()
                                waiting = False
                            elif b2.collidepoint(mx, my):
                                waiting = False
                                running = False
                            elif b3.collidepoint(mx, my):
                                waiting = False
                                running = False
                    pygame.time.delay(10)

        pygame.display.flip()

    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


def find_side_for_key(key_code: int) -> Optional[str]:
    return KEY_TO_SIDE.get(key_code)


def handle_hit_input(state: GameState, key_code: int, now_ms: int, settings: Dict) -> None:
    side = find_side_for_key(key_code)
    if side is None:
        return

    level = state.level
    # Оптимизированный поиск лучшей ноты - фильтруем заранее
    candidate_notes = [an for an in state.notes 
                      if not (an.hit or an.missed) and an.note.side == side]
    
    best_note = None
    best_abs_diff = level.hit_window_ms + 1  # Используем hit_window вместо большого числа
    
    for an in candidate_notes:
        target_time = an.arrive_time()
        abs_diff = abs(now_ms - target_time)
        if abs_diff <= level.hit_window_ms and abs_diff < best_abs_diff:
            best_abs_diff = abs_diff
            best_note = an
    if best_note is None:
        state.combo = 0
        state.judgements.append(("BAD", now_ms))
        state.all_judgements.append("BAD")
        apply_hp_damage(state, 5)
        if state.miss_snd:
            state.miss_snd.play()
        state.shake_timer = 120
        state.shake_intensity = 0.2
        # Red spark for bad hit
        add_hit_spark(state, CENTER[0], CENTER[1], "BAD")
        # Trigger lowpass filter for bad hit
        trigger_lowpass_filter(state)
        return

    # If hold note, start it; else complete tap
    if best_note.is_hold:
        best_note.hold_started = True
        best_note.hold_side = side
        state.pulse_timer = 120
        # particles on hold start
        # Красивые частицы для hold нот
        state.particles.extend([Particle(*CENTER, COLOR_NOTE.get(side, (255,255,255))) for _ in range(12)])
        state.shake_timer = 120
        state.shake_intensity = 0.4
        state.judgements.append(("HOLD START", now_ms))
        state.all_judgements.append("HOLD START")
        
        # Звук начала hold-ноты (немного другой тон)
        if state.hit_snd:
            state.hit_snd.play()
        
        return

    # Slide follow-up: if a slide was primed and player hit target in time
    if state.pending_slide_target and now_ms <= state.pending_slide_expire_ms and side == state.pending_slide_target:
        state.pending_slide_target = None
        # configurable slide bonus
        slide_bonus = int(settings.get("gameplay", {}).get("slide_bonus_score", 150))
        state.score += slide_bonus
        state.combo += 1
        state.best_combo = max(state.best_combo, state.combo)
        state.judgements.append(("SLIDE", now_ms))
        state.all_judgements.append("SLIDE")
        play_layered_hit_sound(state, "GREAT", state.combo, settings)
        add_hit_spark(state, CENTER[0], CENTER[1], "GREAT")
        return

    # Проверяем фейковую ноту
    if getattr(best_note.note, 'is_fake', False):
        # Фейковая нота - наказываем игрока
        best_note.hit = True  # Помечаем как попавшую чтобы не обрабатывать повторно
        apply_hp_damage(state, 15)  # Снимаем 15 HP
        state.combo = 0  # Сбрасываем комбо
        state.judgements.append(("FAKE!", now_ms))
        state.all_judgements.append("FAKE")
        
        # Красные частицы для фейковой ноты
        state.particles.extend([Particle(*CENTER, (255, 0, 0)) for _ in range(20)])
        state.shake_timer = 200
        state.shake_intensity = 1.0
        
        # Звук ошибки
        if state.miss_snd:
            state.miss_snd.play()
        
        # Красная вспышка
        state.flash_timer = 300
        
        return

    # tap scoring
    best_note.hit = True
    state.hits += 1
    
    # Проверяем читы
    perfect_accuracy_cheat = False
    score_multiplier_cheat = 1.0
    
    try:
        # Ищем мод читов
        for mod in mod_system.get_enabled_mods():
            if mod.name == "Читы":
                with open(mod.file_path + "/mod_info.json", 'r', encoding='utf-8') as f:
                    mod_data = json.load(f)
                    cheat_settings = mod_data.get('settings', {})
                    perfect_accuracy_cheat = cheat_settings.get('perfect_accuracy', False)
                    score_multiplier_cheat = cheat_settings.get('score_multiplier', 1.0)
                break
    except:
        pass
    
    # Определяем суждение
    if perfect_accuracy_cheat:
        add = 300
        judge = "PERFECT"
    elif best_abs_diff <= level.hit_window_ms * 0.25:
        add = 300
        judge = "PERFECT"
    elif best_abs_diff <= level.hit_window_ms * 0.5:
        add = 200
        judge = "GREAT"
    else:
        add = 100
        judge = "GOOD"
    
    state.combo += 1
    state.best_combo = max(state.best_combo, state.combo)
    
    # Double note: small bonus to score/combo
    if getattr(best_note.note, 'note_type', 'tap') == 'double':
        add = int(add * 1.25)
        state.combo += 1
        state.best_combo = max(state.best_combo, state.combo)

    # Slide note: arm follow-up window toward target side
    if getattr(best_note.note, 'note_type', 'tap') == 'slide':
        tgt = getattr(best_note.note, 'slide_target', None)
        if tgt:
            state.pending_slide_target = tgt
            follow_ms = int(settings.get("gameplay", {}).get("slide_follow_ms", 160))
            state.pending_slide_expire_ms = now_ms + max(80, follow_ms)

    # Применяем множитель очков
    final_score = int((add + int(state.combo * 0.5)) * score_multiplier_cheat)
    state.score += final_score
    state.judgements.append((judge, now_ms))
    state.all_judgements.append(judge)
    
    # Play layered hit sound
    play_layered_hit_sound(state, judge, state.combo, settings)
    
    # Enhanced visual effects
    # Красивые частицы для попаданий
    state.particles.extend([Particle(*CENTER, COLOR_NOTE.get(side, (255,255,255))) for _ in range(18)])
    
    # Combo-based screen shake (stronger with higher combo)
    base_shake = 0.6
    combo_multiplier = min(2.0, 1.0 + (state.combo - 1) * 0.05)
    state.shake_timer = max(state.shake_timer, 140)
    state.shake_intensity = max(state.shake_intensity, base_shake * combo_multiplier)
    
    # Track glow on hit
    state.track_glow[side] = 1.0
    
    # Hit sparks based on judgment
    add_hit_spark(state, CENTER[0], CENTER[1], judge)
    
    # Animated label for judgment
    colors = {
        "PERFECT": (0, 255, 0),    # Green
        "GREAT": (0, 200, 255),    # Cyan
        "GOOD": (255, 255, 0),     # Yellow
        "BAD": (255, 100, 100),    # Light red
        "HOLD": (200, 100, 255),   # Purple
    }
    color = colors.get(judge, (255, 255, 255))
    add_animated_label(state, judge + "!", CENTER[0], CENTER[1] - 50, color, 1200)
    
    # Beat glow trigger on strong hits
    if judge in ["PERFECT", "GREAT"]:
        state.beat_glow_timer = 200



def main():
    parser = argparse.ArgumentParser(description="Rhythm game")
    parser.add_argument("--level", required=True, help="Path to level json")
    args = parser.parse_args()

    level = load_level(args.level)
    play_level(level)


if __name__ == "__main__":
    main()
