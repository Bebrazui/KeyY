import argparse
import os
from typing import List, Optional, Tuple, Dict
import pygame
import shutil
import uuid
try:
    import tkinter as tk
    from tkinter import filedialog
except Exception:
    tk = None
    filedialog = None

from .level import Level, Note, Event, save_level
from .main import KEY_TO_SIDE, DISPLAY_FOR_KEY

COLOR_BG = (16, 18, 28)
COLOR_TEXT = (230, 230, 230)
COLOR_ACCENT = (80, 150, 255)
COLOR_TIMELINE = (60, 70, 100)
COLOR_GRID = (60, 90, 140)
COLOR_PREVIEW_CENTER = (240, 240, 255)
COLOR_PREVIEW_NOTE = {
    "left": (120, 200, 255),
    "top": (120, 255, 160),
    "right": (255, 170, 120),
    "bottom": (255, 120, 200),
}

BUTTON_RADIUS = 10

SIDES = ["left", "top", "right", "bottom"]
DEFAULT_KEYS = ["A", "W", "D", "S"]

EFFECT_LIST = [
    "invert", "grayscale", "blur", "vignette", "chroma_shift",
    "pixelate", "desaturate", "contrast", "glow_boost"
]

# Minimum press duration to treat as hold when recording (ms)
HOLD_RECORD_THRESHOLD_MS = 120


def ms_to_time_str(ms: int) -> str:
    total_seconds = ms // 1000
    m = total_seconds // 60
    s = total_seconds % 60
    return f"{m:02d}:{s:02d}.{(ms%1000)//10:02d}"


def save_state_for_undo(notes: List[Note], undo_stack: List[List[Note]], redo_stack: List[List[Note]], max_steps: int):
    """Save current state for undo"""
    # Clear redo stack when new action is performed
    redo_stack.clear()
    
    # Save current state
    state_copy = [Note(n.time_ms, n.side, n.key, n.duration_ms, getattr(n, 'is_fake', False), getattr(n, 'note_type', 'tap'), getattr(n, 'slide_target', None)) for n in notes]
    undo_stack.append(state_copy)
    
    # Limit undo stack size
    if len(undo_stack) > max_steps:
        undo_stack.pop(0)


def perform_undo(notes: List[Note], undo_stack: List[List[Note]], redo_stack: List[List[Note]]) -> bool:
    """Perform undo operation"""
    if not undo_stack:
        return False
    
    # Save current state to redo
    current_state = [Note(n.time_ms, n.side, n.key, n.duration_ms, getattr(n, 'is_fake', False), getattr(n, 'note_type', 'tap'), getattr(n, 'slide_target', None)) for n in notes]
    redo_stack.append(current_state)
    
    # Restore previous state
    previous_state = undo_stack.pop()
    notes.clear()
    notes.extend(previous_state)
    
    return True


def perform_redo(notes: List[Note], undo_stack: List[List[Note]], redo_stack: List[List[Note]]) -> bool:
    """Perform redo operation"""
    if not redo_stack:
        return False
    
    # Save current state to undo
    current_state = [Note(n.time_ms, n.side, n.key, n.duration_ms) for n in notes]
    undo_stack.append(current_state)
    
    # Restore next state
    next_state = redo_stack.pop()
    notes.clear()
    notes.extend(next_state)
    
    return True


def run_editor(audio_path: str, title: str, artist: str, bpm: Optional[float], out_path: Optional[str], screen: Optional[pygame.Surface]=None):
    if not pygame.get_init():
        pygame.init()
    if screen is None:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    w, h = screen.get_size()
    pygame.display.set_caption("KeyY — Editor")
    font = pygame.font.Font(None, 30)
    big_font = pygame.font.Font(None, 40)

    # ensure default local time var to avoid UnboundLocalError in rare branches
    t = 0

    if not os.path.isabs(audio_path):
        audio_path = os.path.join(os.getcwd(), audio_path)
    if not os.path.exists(audio_path):
        print(f"Audio not found: {audio_path}")
        # allow continue; user may set audio via toolbar

    if not pygame.mixer.get_init():
        pygame.mixer.init()
    try:
        if os.path.exists(audio_path):
            pygame.mixer.music.load(audio_path)
    except Exception:
        pass

    notes: List[Note] = []
    events: List[Event] = []  # События эффектов по времени
    approach_ms = 1000
    hit_window_ms = 120

    # Effects active dictionary initialized here
    active_effects: Dict[str, bool] = {effect: False for effect in EFFECT_LIST}

    playing = False
    recording = False
    start_ticks = pygame.time.get_ticks()
    base_offset_ms = 0

    zoom = 0.08
    grid_div = 4
    metronome = False
    last_beat_play = -1

    timeline_h = int(h * 0.25)

    # Selection/drag state
    selected_idx: Optional[int] = None
    dragging = False
    drag_offset_ms = 0
    # Note dragging/resizing state
    dragging_note_idx: Optional[int] = None
    dragging_mode: Optional[str] = None  # 'move' | 'resize'
    drag_start_mouse_x = 0
    drag_orig_time = 0
    drag_orig_duration = 0
    # Scrub state for LMB on timeline
    scrubbing = False
    scrub_start_x = 0
    scrub_start_base = 0
    # Effect insert modal state
    effect_insert_mode: Dict[str, any] = {
        "active": False,
        "start_time": 0,
        "duration_ms": 1000,
        "effect_idx": 0,
        "pos": (0, 0)
    }
    
    # Undo/Redo system
    undo_stack: List[List[Note]] = []
    redo_stack: List[List[Note]] = []
    max_undo_steps = 50

    # Preview pane geometry
    preview_rect = pygame.Rect(0, 0, int(w * 0.32), int(h * 0.32))
    preview_rect.center = (int(w * 0.83), int(h * 0.22))

    # Toolbar with tabs
    toolbar_rects: List[Tuple[str, pygame.Rect]] = []
    tab_rects: List[Tuple[str, pygame.Rect]] = []
    toolbar_page = 'main'  # 'main' | 'controls' | 'effects'
    current_note_type = 'tap'  # tap | double | slide
    current_slide_target: Optional[str] = None
    show_help = True

    def layout_toolbar():
        toolbar_rects.clear()
        tab_rects.clear()

        # Tabs
        tabs = [("Main", 'main'), ("Controls", 'controls'), ("Effects", 'effects')]
        tx = 16
        ty = 50
        for caption, page in tabs:
            surf = font.render(caption, True, (20,20,30))
            wbtn = max(110, surf.get_width()+24)
            r = pygame.Rect(tx, ty, wbtn, 28)
            tab_rects.append((page, r))
            tx += wbtn + 8

        x = 16
        y = 86

        if toolbar_page == 'main':
            main_labels = ["Open Audio", "Open Level", "Set Title", "Set Artist", "Save", "Export"]
            for lbl in main_labels:
                surf = font.render(lbl, True, (20,20,30))
                wbtn = max(140, surf.get_width()+24)
                r = pygame.Rect(x, y, wbtn, 36)
                toolbar_rects.append((lbl, r))
                x += wbtn + 12
                if x > w - 200:
                    x = 16
                    y += 44
        elif toolbar_page == 'controls':
            control_labels = ["Play", "Rec", "Stop", "BPM+", "BPM-", "Reset BPM", "Zoom+", "Zoom-", "Grid+", "Grid-", "Metro", "App+", "App-", "Hit+", "Hit-",
                              "Type:Tap(1)", "Type:Double(2)", "Type:Slide(3)", "Slide Target:WASD"]
            for lbl in control_labels:
                surf = font.render(lbl, True, (20,20,30))
                wbtn = max(90, surf.get_width()+16)
                r = pygame.Rect(x, y, wbtn, 32)
                toolbar_rects.append((lbl, r))
                x += wbtn + 8
                if x > w - 200:
                    x = 16
                    y += 38
        else:  # effects
            row_limit = w - 100
            for i, effect in enumerate(EFFECT_LIST):
                effect_label = f"{i+1}:{effect[:4]}"
                surf = font.render(effect_label, True, (20,20,30))
                wbtn = max(60, surf.get_width()+12)
                r = pygame.Rect(x, y, wbtn, 28)
                toolbar_rects.append((effect_label, r))
                x += wbtn + 6
                if x > row_limit:
                    x = 16
                    y += 32
    layout_toolbar()

    # Text input overlay state
    input_mode: Optional[str] = None  # 'title' | 'artist' | 'audio'
    input_text: str = ""
    message: str = ""
    message_timer = 0

    def get_now_ms() -> int:
        if not playing:
            return base_offset_ms
        else:
            return base_offset_ms + (pygame.time.get_ticks() - start_ticks)

    def play(rec: bool):
        nonlocal playing, start_ticks, recording
        if not playing and os.path.exists(audio_path):
            start_ticks = pygame.time.get_ticks()
            pygame.mixer.music.play(start=base_offset_ms / 1000.0)
            playing = True
            recording = rec

    def pause():
        nonlocal playing, recording
        pygame.mixer.music.pause()
        playing = False
        recording = False

    def stop_audio():
        nonlocal playing, recording
        pygame.mixer.music.stop()
        playing = False
        recording = False

    def time_to_x(t: float, center: float) -> int:
        return int((t - get_now_ms()) * zoom + center)

    def x_to_time(x: int, center: float) -> int:
        return int((x - center) / zoom + get_now_ms())

    def find_note_at_time(t: int, tolerance_ms: int = 80) -> Optional[int]:
        if not notes:
            return None
        lo, hi = 0, len(notes) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            dt2 = notes[mid].time_ms - t
            if dt2 < 0:
                lo = mid + 1
            elif dt2 > 0:
                hi = mid - 1
            else:
                lo = hi = mid
                break
        candidates = set()
        for i in (hi, lo):
            if 0 <= i < len(notes):
                candidates.add(i)
        best = None
        best_diff = 10**9
        for i in candidates:
            diff = abs(notes[i].time_ms - t)
            if diff < best_diff and diff <= tolerance_ms:
                best = i
                best_diff = diff
        return best

    def hit_test_note(mx: int, my: int, center_x: int) -> Tuple[Optional[int], Optional[str]]:
        # Returns (index, mode) where mode 'move' or 'resize' (hold tail)
        by = h - timeline_h + 40
        bw = 44
        bh = 28
        if not (h - timeline_h <= my <= h):
            return None, None
        for i, n in enumerate(notes):
            x = time_to_x(n.time_ms, center_x)
            rect = pygame.Rect(x - bw//2, by - bh//2, bw, bh)
            if rect.collidepoint(mx, my):
                return i, 'move'
            if n.duration_ms > 0:
                end_x = time_to_x(n.time_ms + n.duration_ms, center_x)
                # tail handle area: small square at end
                handle = pygame.Rect(end_x - 6, by - 10, 12, 20)
                if handle.collidepoint(mx, my):
                    return i, 'resize'
        return None, None

    clock = pygame.time.Clock()

    # Hold recording state
    active_holds: Dict[int, int] = {}

    # Safety: ensure defined
    if 'active_holds' not in locals() or active_holds is None:
        active_holds = {}

    # Allow recording without audio loaded (just time from base_offset)

    while True:
        dt = clock.tick(60)
        w, h = screen.get_size()
        center_x = w // 2
        timeline_h = int(h * 0.25)

        # Message timer
        if message_timer > 0:
            message_timer -= dt
            if message_timer <= 0:
                message = ""

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                break
            elif event.type == pygame.KEYDOWN:
                if input_mode:
                    # text input mode
                    if event.key == pygame.K_ESCAPE:
                        input_mode = None
                    elif event.key == pygame.K_RETURN:
                        if input_mode == 'title':
                            title = input_text.strip() or title
                            input_mode = None
                        elif input_mode == 'artist':
                            artist = input_text.strip() or artist
                            input_mode = None
                        elif input_mode == 'audio':
                            p = input_text.strip()
                            if p and not os.path.isabs(p):
                                p = os.path.join(os.getcwd(), p)
                            if p and os.path.exists(p):
                                audio_path = p
                                try:
                                    pygame.mixer.music.load(audio_path)
                                    message = "Audio loaded"
                                    message_timer = 2000
                                except Exception as e:
                                    message = f"Audio load error"
                                    message_timer = 2000
                                input_mode = None
                            else:
                                message = "File not found"
                                message_timer = 2000
                                input_mode = None
                        input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        ch = event.unicode
                        if ch:
                            input_text += ch
                    continue
                # normal controls
                if event.key == pygame.K_ESCAPE:
                    if effect_insert_mode["active"]:
                        effect_insert_mode["active"] = False
                    else:
                        return
                # Effect insert modal controls
                if effect_insert_mode["active"]:
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        effect_insert_mode["effect_idx"] = (effect_insert_mode["effect_idx"] - 1) % len(EFFECT_LIST)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        effect_insert_mode["effect_idx"] = (effect_insert_mode["effect_idx"] + 1) % len(EFFECT_LIST)
                    elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                        effect_insert_mode["duration_ms"] = max(100, effect_insert_mode["duration_ms"] - 100)
                    elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                        effect_insert_mode["duration_ms"] = min(30000, effect_insert_mode["duration_ms"] + 100)
                    elif event.key == pygame.K_RETURN:
                        start_t = int(effect_insert_mode["start_time"])
                        dur = int(effect_insert_mode["duration_ms"])
                        eff = EFFECT_LIST[effect_insert_mode["effect_idx"]]
                        events.append(Event(time_ms=start_t, type="effect_on", name=eff))
                        events.append(Event(time_ms=start_t + dur, type="effect_off", name=eff))
                        events.sort(key=lambda e: e.time_ms)
                        message = f"Added {eff} {dur}ms @ {start_t}"
                        message_timer = 2000
                        effect_insert_mode["active"] = False
                    # Do not fall-through to other controls when modal
                    continue
                elif event.key == pygame.K_SPACE:
                    mods = pygame.key.get_mods()
                    rec = not (mods & pygame.KMOD_SHIFT)
                    if playing:
                        pause()
                    else:
                        play(rec)
                elif event.key == pygame.K_r:
                    if playing:
                        recording = not recording
                    else:
                        play(True)
                # Start hold on supported keys (exclude SPACE used for transport)
                if recording and event.key in KEY_TO_SIDE and event.key != pygame.K_SPACE:
                    if event.key not in active_holds:
                        active_holds[event.key] = get_now_ms()
                        # also place a tap immediately so on quick taps it exists
                        side = KEY_TO_SIDE.get(event.key)
                        label = DISPLAY_FOR_KEY.get(event.key, pygame.key.name(event.key).upper())
                        
                        # Проверяем фейковые клавиши (Win или Alt)
                        is_fake = event.key in (pygame.K_LMETA, pygame.K_RMETA, pygame.K_LALT, pygame.K_RALT)
                        
                        n = Note(time_ms=int(active_holds[event.key]), side=side, key=label, duration_ms=0, is_fake=is_fake)
                        try:
                            n.note_type = current_note_type
                            if current_note_type == 'slide':
                                n.slide_target = current_slide_target or 'right'
                        except Exception:
                            pass
                        notes.append(n)
                        notes.sort(key=lambda n: n.time_ms)
                        
                        if is_fake:
                            message = f"Added FAKE note at {int(active_holds[event.key])}ms"
                            message_timer = 2000
                elif event.key == pygame.K_LEFT:
                    base_offset_ms = max(0, get_now_ms() - 1000)
                    stop_audio()
                elif event.key == pygame.K_RIGHT:
                    base_offset_ms = get_now_ms() + 1000
                    stop_audio()
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    zoom = min(0.5, zoom * 1.25)
                elif event.key == pygame.K_MINUS:
                    zoom = max(0.02, zoom / 1.25)
                elif event.key == pygame.K_LEFTBRACKET:
                    grid_div = max(1, grid_div - 1)
                elif event.key == pygame.K_RIGHTBRACKET:
                    grid_div = min(16, grid_div + 1)
                elif event.key == pygame.K_m:
                    metronome = not metronome
                elif event.key == pygame.K_t:
                    if not hasattr(run_editor, "tap_times"):
                        run_editor.tap_times = []
                    run_editor.tap_times.append(pygame.time.get_ticks())
                    if len(run_editor.tap_times) > 5:
                        run_editor.tap_times.pop(0)
                    if len(run_editor.tap_times) >= 2:
                        intervals = [run_editor.tap_times[i+1]-run_editor.tap_times[i] for i in range(len(run_editor.tap_times)-1)]
                        avg = sum(intervals) / len(intervals)
                        bpm = 60000.0 / avg
                elif event.key == pygame.K_F1:
                    show_help = not show_help
                # Quick type change for selected note
                elif event.key == pygame.K_q and selected_idx is not None and 0 <= selected_idx < len(notes):
                    nt = getattr(notes[selected_idx], 'note_type', 'tap')
                    seq = ['tap','double','slide']
                    idx = (seq.index(nt) - 1) % len(seq) if nt in seq else 0
                    notes[selected_idx].note_type = seq[idx]
                    if notes[selected_idx].note_type != 'slide':
                        notes[selected_idx].slide_target = None
                elif event.key == pygame.K_e and selected_idx is not None and 0 <= selected_idx < len(notes):
                    nt = getattr(notes[selected_idx], 'note_type', 'tap')
                    seq = ['tap','double','slide']
                    idx = (seq.index(nt) + 1) % len(seq) if nt in seq else 0
                    notes[selected_idx].note_type = seq[idx]
                    if notes[selected_idx].note_type != 'slide':
                        notes[selected_idx].slide_target = None
                elif event.key == pygame.K_r and selected_idx is not None and 0 <= selected_idx < len(notes):
                    if getattr(notes[selected_idx], 'note_type', 'tap') == 'slide':
                        order = ['left','top','right','bottom']
                        cur = getattr(notes[selected_idx], 'slide_target', None)
                        nxt = order[(order.index(cur)+1) % len(order)] if cur in order else 'right'
                        notes[selected_idx].slide_target = nxt
                # Note type hotkeys
                elif event.key == pygame.K_1:
                    current_note_type = 'tap'
                    current_slide_target = None
                    message = "Note type: TAP"; message_timer = 1200
                elif event.key == pygame.K_2:
                    current_note_type = 'double'
                    current_slide_target = None
                    message = "Note type: DOUBLE"; message_timer = 1200
                elif event.key == pygame.K_3:
                    current_note_type = 'slide'
                    message = "Note type: SLIDE (set target WASD)"; message_timer = 1800
                elif current_note_type == 'slide' and event.key in (pygame.K_a, pygame.K_w, pygame.K_d, pygame.K_s):
                    st = KEY_TO_SIDE.get(event.key)
                    if st:
                        current_slide_target = st
                        message = f"Slide target: {st.upper()}"; message_timer = 1200
                # Undo/Redo
                elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        # Ctrl+Shift+Z = Redo
                        if perform_redo(notes, undo_stack, redo_stack):
                            message = "Redo"
                            message_timer = 1000
                    else:
                        # Ctrl+Z = Undo
                        if perform_undo(notes, undo_stack, redo_stack):
                            message = "Undo"
                            message_timer = 1000
                elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    # Ctrl+Y = Redo
                    if perform_redo(notes, undo_stack, redo_stack):
                        message = "Redo"
                        message_timer = 1000
                elif event.key == pygame.K_COMMA:
                    approach_ms = max(200, approach_ms - 50)
                elif event.key == pygame.K_PERIOD:
                    approach_ms = min(2000, approach_ms + 50)
                elif event.key == pygame.K_SEMICOLON:
                    hit_window_ms = max(40, hit_window_ms - 5)
                elif event.key == pygame.K_QUOTE:
                    hit_window_ms = min(250, hit_window_ms + 5)
                # Effect toggles (1-9)
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, 
                                 pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9):
                    effect_idx = event.key - pygame.K_1
                    if 0 <= effect_idx < len(EFFECT_LIST):
                        effect = EFFECT_LIST[effect_idx]
                        
                        # Если зажат Shift - добавляем эффект по времени
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            current_time = get_now_ms()
                            # Добавляем событие включения эффекта
                            events.append(Event(time_ms=current_time, type="effect_on", name=effect))
                            events.sort(key=lambda e: e.time_ms)
                            message = f"Added {effect} ON at {current_time}ms"
                            message_timer = 2000
                        # Если зажат Ctrl - добавляем выключение эффекта
                        elif pygame.key.get_mods() & pygame.KMOD_CTRL:
                            current_time = get_now_ms()
                            events.append(Event(time_ms=current_time, type="effect_off", name=effect))
                            events.sort(key=lambda e: e.time_ms)
                            message = f"Added {effect} OFF at {current_time}ms"
                            message_timer = 2000
                        else:
                            # Обычное переключение эффекта
                            active_effects[effect] = not active_effects[effect]
                            message = f"Effect {effect}: {'ON' if active_effects[effect] else 'OFF'}"
                            message_timer = 1000
                elif event.key == pygame.K_s and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    os.makedirs("assets", exist_ok=True)
                    ext = os.path.splitext(audio_path)[1].lower() or ".ogg"
                    new_audio_name = f"song_{uuid.uuid4().hex[:8]}{ext}"
                    new_audio_path = os.path.join("assets", new_audio_name)
                    try:
                        if os.path.exists(audio_path):
                            shutil.copy2(audio_path, new_audio_path)
                        audio_rel = new_audio_path
                    except Exception:
                        audio_rel = os.path.relpath(audio_path, os.getcwd())
                    level = Level(title=title, artist=artist, audio=audio_rel,
                                  approach_ms=approach_ms, hit_window_ms=hit_window_ms, notes=notes, 
                                  effects=[effect for effect, enabled in active_effects.items() if enabled],
                                  events=events)
                    os.makedirs("levels", exist_ok=True)
                    out_path2 = os.path.join("levels", f"{title.replace(' ', '_')}_{uuid.uuid4().hex[:6]}.json")
                    save_level(level, out_path2)
                    out_path = out_path2
                    message = f"Exported: {out_path2}"
                    message_timer = 3000
                elif event.key == pygame.K_s:
                    level = Level(title=title, artist=artist, audio=os.path.relpath(audio_path, os.getcwd()) if audio_path else "",
                                  approach_ms=approach_ms, hit_window_ms=hit_window_ms, notes=notes, 
                                  effects=[effect for effect, enabled in active_effects.items() if enabled],
                                  events=events)
                    if out_path is None:
                        os.makedirs("levels", exist_ok=True)
                        out_path = os.path.join("levels", f"{title.replace(' ', '_')}.json")
                    save_level(level, out_path)
                    message = f"Saved: {out_path}"
                    message_timer = 2000
                elif event.key in (pygame.K_a, pygame.K_w, pygame.K_s, pygame.K_d, pygame.K_LEFT, pygame.K_UP, pygame.K_DOWN, pygame.K_RIGHT,
                                   pygame.K_j, pygame.K_i, pygame.K_k, pygame.K_l, pygame.K_f, pygame.K_t, pygame.K_g, pygame.K_h,
                                   pygame.K_KP4, pygame.K_KP8, pygame.K_KP5, pygame.K_KP6):
                    if recording:
                        side = KEY_TO_SIDE.get(event.key)
                        if side:
                            label = DISPLAY_FOR_KEY.get(event.key, pygame.key.name(event.key).upper())
                            tcur = get_now_ms()
                            n2 = Note(time_ms=int(tcur), side=side, key=label)
                            try:
                                n2.note_type = current_note_type
                                if current_note_type == 'slide':
                                    n2.slide_target = current_slide_target or 'right'
                            except Exception:
                                pass
                            notes.append(n2)
                            notes.sort(key=lambda n: n.time_ms)
                            continue
                    if selected_idx is not None and 0 <= selected_idx < len(notes):
                        side = KEY_TO_SIDE.get(event.key)
                        if side:
                            notes[selected_idx].side = side
                            label = DISPLAY_FOR_KEY.get(event.key, pygame.key.name(event.key).upper())
                            notes[selected_idx].key = label
                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    if selected_idx is not None and 0 <= selected_idx < len(notes):
                        save_state_for_undo(notes, undo_stack, redo_stack, max_undo_steps)
                        notes.pop(selected_idx)
                        selected_idx = None
                elif event.key == pygame.K_HOME:
                    if selected_idx is not None and bpm and bpm > 0:
                        beat_ms = 60000.0 / bpm
                        div_ms = beat_ms / grid_div
                        t2 = notes[selected_idx].time_ms
                        notes[selected_idx].time_ms = int(round(t2 / div_ms) * div_ms)
                        notes.sort(key=lambda n: n.time_ms)
                        selected_idx = find_note_at_time(notes[selected_idx].time_ms)
                elif event.key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                    if selected_idx is not None:
                        step = 50 if (pygame.key.get_mods() & pygame.KMOD_SHIFT) else 10
                        delta = -step if event.key == pygame.K_PAGEUP else step
                        notes[selected_idx].time_ms = max(0, notes[selected_idx].time_ms + delta)
                        notes.sort(key=lambda n: n.time_ms)
                        selected_idx = find_note_at_time(notes[selected_idx].time_ms)
            elif event.type == pygame.KEYUP:
                # End hold
                if recording and event.key in active_holds:
                    start_t = active_holds.pop(event.key)
                    end_t = get_now_ms()
                    dur = max(0, int(end_t - start_t))
                    # find the last note at start_t for this side/key and set duration
                    side = KEY_TO_SIDE.get(event.key)
                    label = DISPLAY_FOR_KEY.get(event.key, pygame.key.name(event.key).upper())
                    # find candidate note by exact time match (within 10ms)
                    idx = None
                    for i in range(len(notes)-1, -1, -1):
                        n = notes[i]
                        if n.side == side and n.key == label and abs(n.time_ms - int(start_t)) <= 10 and n.duration_ms == 0:
                            idx = i
                            break
                    if idx is not None:
                        # Ставим hold только если длительность не меньше порога
                        if dur >= HOLD_RECORD_THRESHOLD_MS:
                            notes[idx].duration_ms = dur
                        else:
                            notes[idx].duration_ms = 0  # оставить как tap
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if input_mode:
                    continue
                if event.button == 1:
                    # Note drag start
                    idx_hit, mode = hit_test_note(mx, my, center_x)
                    if idx_hit is not None:
                        dragging_note_idx = idx_hit
                        dragging_mode = mode
                        drag_start_mouse_x = mx
                        drag_orig_time = notes[idx_hit].time_ms
                        drag_orig_duration = notes[idx_hit].duration_ms
                        selected_idx = idx_hit
                        continue
                    # Toolbar click
                    for lbl, r in toolbar_rects:
                        if r.collidepoint(mx, my):
                            if lbl == "Open Audio":
                                # Try native file dialog
                                if tk and filedialog:
                                    try:
                                        root = tk.Tk(); root.withdraw()
                                        path = filedialog.askopenfilename(title='Select audio', filetypes=[('Audio','*.ogg *.wav *.mp3'),('All Files','*.*')])
                                        root.destroy()
                                        if path:
                                            p = path
                                            if p and not os.path.isabs(p):
                                                p = os.path.join(os.getcwd(), p)
                                            if p and os.path.exists(p):
                                                audio_path = p
                                                try:
                                                    pygame.mixer.music.load(audio_path)
                                                    message = "Audio loaded"
                                                    message_timer = 2000
                                                except Exception:
                                                    message = "Audio load error"; message_timer = 2000
                                            else:
                                                message = "File not found"; message_timer = 2000
                                        else:
                                            # user cancelled
                                            pass
                                    except Exception:
                                        input_mode = 'audio'; input_text = ""; message = "Enter audio path and press Enter"; message_timer = 4000
                                else:
                                    input_mode = 'audio'; input_text = ""; message = "Enter audio path and press Enter"; message_timer = 4000
                            elif lbl == "Open Level":
                                # choose json level and load
                                level_path = None
                                if tk and filedialog:
                                    try:
                                        root = tk.Tk(); root.withdraw()
                                        level_path = filedialog.askopenfilename(title='Select level json', filetypes=[('JSON','*.json')])
                                        root.destroy()
                                    except Exception:
                                        level_path = None
                                if not level_path:
                                    input_mode = None
                                else:
                                    try:
                                        from .level import load_level
                                        lvl = load_level(level_path)
                                        notes.clear()
                                        for nd in (lvl.notes or []):
                                            notes.append(nd)
                                        events.clear()
                                        for ev in (lvl.events or []):
                                            events.append(ev)
                                        title = lvl.title
                                        artist = lvl.artist
                                        audio_path = os.path.join(os.getcwd(), lvl.audio) if not os.path.isabs(lvl.audio) else lvl.audio
                                        try:
                                            if os.path.exists(audio_path):
                                                pygame.mixer.music.load(audio_path)
                                        except Exception:
                                            pass
                                        # Reset effects and load from level
                                        active_effects = {effect: False for effect in EFFECT_LIST}
                                        if lvl.effects:
                                            for effect in lvl.effects:
                                                if effect in active_effects:
                                                    active_effects[effect] = True
                                        out_path = level_path
                                        message = f"Loaded: {os.path.basename(level_path)}"; message_timer = 3000
                                    except Exception as e:
                                        message = "Load error"; message_timer = 2000
                            elif lbl == "Set Title":
                                input_mode = 'title'; input_text = title; message = "Type title and press Enter"; message_timer = 4000
                            elif lbl == "Set Artist":
                                input_mode = 'artist'; input_text = artist; message = "Type artist and press Enter"; message_timer = 4000
                            elif lbl == "Save":
                                level = Level(title=title, artist=artist, audio=os.path.relpath(audio_path, os.getcwd()) if audio_path else "",
                                              approach_ms=approach_ms, hit_window_ms=hit_window_ms, notes=notes, 
                                              effects=[effect for effect, enabled in active_effects.items() if enabled],
                                              events=events)
                                if out_path is None:
                                    os.makedirs("levels", exist_ok=True)
                                    out_path = os.path.join("levels", f"{title.replace(' ', '_')}.json")
                                save_level(level, out_path)
                                message = f"Saved: {out_path}"; message_timer = 2000
                            elif lbl == "Export":
                                os.makedirs("assets", exist_ok=True)
                                ext = os.path.splitext(audio_path)[1].lower() or ".ogg"
                                new_audio_name = f"song_{uuid.uuid4().hex[:8]}{ext}"
                                new_audio_path = os.path.join("assets", new_audio_name)
                                try:
                                    if os.path.exists(audio_path):
                                        shutil.copy2(audio_path, new_audio_path)
                                    audio_rel = new_audio_path
                                except Exception:
                                    audio_rel = os.path.relpath(audio_path, os.getcwd())
                                level = Level(title=title, artist=artist, audio=audio_rel,
                                              approach_ms=approach_ms, hit_window_ms=hit_window_ms, notes=notes, 
                                              effects=[effect for effect, enabled in active_effects.items() if enabled],
                                              events=events)
                                os.makedirs("levels", exist_ok=True)
                                out_path2 = os.path.join("levels", f"{title.replace(' ', '_')}_{uuid.uuid4().hex[:6]}.json")
                                save_level(level, out_path2)
                                out_path = out_path2
                                message = f"Exported: {out_path2}"; message_timer = 3000
                            elif lbl == "Play":
                                if playing:
                                    pause()
                                else:
                                    play(False)  # Play without recording
                                message = f"{'Paused' if not playing else 'Playing'}"; message_timer = 1000
                            elif lbl == "Rec":
                                if playing:
                                    recording = not recording
                                    message = f"Recording: {'ON' if recording else 'OFF'}"; message_timer = 1000
                                else:
                                    play(True)  # Play with recording
                                    message = "Recording started"; message_timer = 1000
                            elif lbl == "Stop":
                                if playing:
                                    pause()
                                    message = "Stopped"; message_timer = 1000
                            elif lbl == "BPM+":
                                if bpm:
                                    bpm = min(300, bpm + 5)
                                    message = f"BPM: {bpm:.1f}"; message_timer = 1000
                            elif lbl == "BPM-":
                                if bpm:
                                    bpm = max(60, bpm - 5)
                                    message = f"BPM: {bpm:.1f}"; message_timer = 1000
                            elif lbl == "Reset BPM":
                                bpm = 120.0
                                message = f"BPM reset to {bpm:.1f}"; message_timer = 1000
                            elif lbl == "Zoom+":
                                zoom = min(0.5, zoom * 1.25)
                                message = f"Zoom: {zoom:.2f}"; message_timer = 1000
                            elif lbl == "Zoom-":
                                zoom = max(0.02, zoom / 1.25)
                                message = f"Zoom: {zoom:.2f}"; message_timer = 1000
                            elif lbl == "Grid+":
                                grid_div = min(16, grid_div + 1)
                                message = f"Grid: {grid_div}"; message_timer = 1000
                            elif lbl == "Grid-":
                                grid_div = max(1, grid_div - 1)
                                message = f"Grid: {grid_div}"; message_timer = 1000
                            elif lbl == "Metro":
                                metronome = not metronome
                                message = f"Metronome: {'ON' if metronome else 'OFF'}"; message_timer = 1000
                            elif lbl == "App+":
                                approach_ms = min(2000, approach_ms + 50)
                                message = f"Approach: {approach_ms}ms"; message_timer = 1000
                            elif lbl == "App-":
                                approach_ms = max(200, approach_ms - 50)
                                message = f"Approach: {approach_ms}ms"; message_timer = 1000
                            elif lbl == "Hit+":
                                hit_window_ms = min(250, hit_window_ms + 5)
                                message = f"Hit Window: {hit_window_ms}ms"; message_timer = 1000
                            elif lbl == "Hit-":
                                hit_window_ms = max(40, hit_window_ms - 5)
                                message = f"Hit Window: {hit_window_ms}ms"; message_timer = 1000
                            # Обработка кнопок эффектов
                            elif ":" in lbl and lbl.split(":")[1] in [effect[:4] for effect in EFFECT_LIST]:
                                effect_short = lbl.split(":")[1]
                                # Находим полное название эффекта
                                effect = next((e for e in EFFECT_LIST if e.startswith(effect_short)), None)
                                if effect:
                                    mods = pygame.key.get_mods()
                                    current_time = get_now_ms()
                                    
                                    if mods & pygame.KMOD_SHIFT:
                                        # Shift + клик = добавить включение эффекта
                                        events.append(Event(time_ms=current_time, type="effect_on", name=effect))
                                        events.sort(key=lambda e: e.time_ms)
                                        message = f"Added {effect} ON at {current_time}ms"
                                        message_timer = 2000
                                    elif mods & pygame.KMOD_CTRL:
                                        # Ctrl + клик = добавить выключение эффекта
                                        events.append(Event(time_ms=current_time, type="effect_off", name=effect))
                                        events.sort(key=lambda e: e.time_ms)
                                        message = f"Added {effect} OFF at {current_time}ms"
                                        message_timer = 2000
                                    else:
                                        # Обычный клик = переключить эффект
                                        active_effects[effect] = not active_effects[effect]
                                        message = f"Effect {effect}: {'ON' if active_effects[effect] else 'OFF'}"
                                        message_timer = 1000
                            break
                    # Timeline scrubbing by left-click in timeline area
                    timeline_rect = pygame.Rect(0, h - timeline_h, w, timeline_h)
                    if timeline_rect.collidepoint(mx, my):
                        # set base_offset_ms to clicked time and start scrubbing
                        clicked_time = x_to_time(mx, center_x)
                        base_offset_ms = max(0, int(clicked_time))
                        scrubbing = True
                        scrub_start_x = mx
                        scrub_start_base = base_offset_ms
                        # stop audio while scrubbing
                        stop_audio()
                        continue
                    # Select/drag or add note handled elsewhere
                elif event.button == 3:
                    # RMB on note deletes it; otherwise timeline opens effect insert modal
                    timeline_rect = pygame.Rect(0, h - timeline_h, w, timeline_h)
                    idx_hit, mode = hit_test_note(mx, my, center_x)
                    if idx_hit is not None:
                        save_state_for_undo(notes, undo_stack, redo_stack, max_undo_steps)
                        notes.pop(idx_hit)
                        selected_idx = None
                    elif timeline_rect.collidepoint(mx, my):
                        start_t = int(x_to_time(mx, center_x))
                        effect_insert_mode["active"] = True
                        effect_insert_mode["start_time"] = max(0, start_t)
                        effect_insert_mode["pos"] = (mx, my)
                        # close any playback while editing
                        stop_audio()
                    else:
                        # Else: delete nearest note as before
                        if notes:
                            t_clicked = x_to_time(mx, center_x)
                            idx = find_note_at_time(t_clicked, tolerance_ms=int(120/zoom))
                            if idx is not None:
                                notes.pop(idx)
                                selected_idx = None
                elif event.button == 2:
                    dragging = True
                    drag_offset_ms = 0
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:
                    dragging = False
                if event.button == 1 and scrubbing:
                    scrubbing = False
                if event.button == 1 and dragging_note_idx is not None:
                    dragging_note_idx = None
                    dragging_mode = None
            elif event.type == pygame.MOUSEMOTION and dragging and pygame.mouse.get_pressed(num_buttons=3)[1]:
                dx, dy = event.rel
                base_offset_ms = max(0, base_offset_ms - int(dx / max(0.02, zoom)))
            elif event.type == pygame.MOUSEMOTION and scrubbing and pygame.mouse.get_pressed(num_buttons=3)[0]:
                dx, dy = event.rel
                # adjust base offset by pixel delta mapped to time via zoom
                base_offset_ms = max(0, int(scrub_start_base + (mx - scrub_start_x) / max(0.02, zoom)))
            elif event.type == pygame.MOUSEMOTION and dragging_note_idx is not None and pygame.mouse.get_pressed(num_buttons=3)[0]:
                # Dragging note move/resize
                idx = dragging_note_idx
                n = notes[idx]
                if dragging_mode == 'move':
                    new_time = int(x_to_time(event.pos[0], center_x))
                    # Optional snap to BPM grid when BPM set
                    if bpm and bpm > 0:
                        beat_ms = 60000.0 / bpm
                        div_ms = beat_ms / grid_div
                        new_time = int(round(new_time / div_ms) * div_ms)
                    n.time_ms = max(0, new_time)
                    notes.sort(key=lambda nn: nn.time_ms)
                    # keep dragging the same note after reorder
                    selected_idx = notes.index(n)
                    dragging_note_idx = selected_idx
                elif dragging_mode == 'resize':
                    end_time = int(x_to_time(event.pos[0], center_x))
                    dur = max(0, end_time - n.time_ms)
                    n.duration_ms = dur

        # Metronome
        if metronome and bpm and bpm > 0 and playing:
            beat_ms = 60000.0 / bpm
            now = get_now_ms()
            beat_idx = int(now // beat_ms)
            if beat_idx != last_beat_play:
                last_beat_play = beat_idx
                try:
                    snd = pygame.mixer.Sound(os.path.join("assets", "hit.wav"))
                    snd.play()
                except Exception:
                    pass

        screen.fill(COLOR_BG)

        now_ms = get_now_ms()
        rec_flag = "REC" if recording else ("PLAY" if playing else "STOP")
        info = "F1:Help  SPACE:Play/Rec  R:Rec  +/-:Zoom  []:Grid  m:Metro  t:BPM  1-9:Effects  Shift/CTRL+Effect:Add  S:Save  ESC:Back  Q/E:Type  R:Slide target"
        txt = font.render(info, True, COLOR_TEXT)
        screen.blit(txt, (16, 12))

        eff = ", ".join([effect for effect, enabled in active_effects.items() if enabled]) or "none"
        params = f"{rec_flag}  Time {ms_to_time_str(int(now_ms))}  BPM:{bpm or 0:.1f}  Grid:{grid_div}  Zoom:{zoom:.2f}  Approach:{approach_ms}  HitWin:{hit_window_ms}  Effects:[{eff}]  Notes:{len(notes)}  Events:{len(events)}  Title:{title}  Artist:{artist}"
        st = big_font.render(params, True, COLOR_TEXT)
        screen.blit(st, (16, 42))

        # Toolbar tabs draw
        for page, r in tab_rects:
            is_active = (page == toolbar_page)
            col = (120, 200, 255) if is_active else (80, 150, 255)
            pygame.draw.rect(screen, col, r, border_radius=8)
            cap = font.render(page.capitalize(), True, (20,20,30))
            screen.blit(cap, cap.get_rect(center=r.center))

        # Toolbar draw
        for lbl, r in toolbar_rects:
            # Определяем цвет кнопки
            button_color = COLOR_ACCENT
            text_color = (20,20,30)
            
            # Особая обработка для кнопок эффектов
            if ":" in lbl and lbl.split(":")[1] in [effect[:4] for effect in EFFECT_LIST]:
                effect_short = lbl.split(":")[1]
                effect = next((e for e in EFFECT_LIST if e.startswith(effect_short)), None)
                if effect and active_effects.get(effect, False):
                    button_color = (100, 255, 100)  # Зеленый для активных эффектов
                    text_color = (0, 0, 0)
            # Особая обработка для метронома
            elif lbl == "Metro" and metronome:
                button_color = (255, 200, 100)  # Оранжевый для активного метронома
                text_color = (0, 0, 0)
            # Особая обработка для кнопок воспроизведения
            elif lbl == "Play" and playing:
                button_color = (100, 255, 100)  # Зеленый для воспроизведения
                text_color = (0, 0, 0)
            elif lbl == "Rec" and recording:
                button_color = (255, 100, 100)  # Красный для записи
                text_color = (255, 255, 255)
            
            pygame.draw.rect(screen, button_color, r, border_radius=8)
            cap = font.render(lbl, True, text_color)
            screen.blit(cap, cap.get_rect(center=r.center))

        # Help overlay
        if show_help:
            ov = pygame.Surface((w, 170), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 150))
            help_lines = [
                "F1 — toggle help",
                "SPACE — Play/Pause (hold Shift for Play only)",
                "R — toggle recording",
                "1/2/3 — note type (Tap/Double/Slide), WASD — slide target",
                "Q/E — change type of selected note; R — cycle slide target",
                "Mouse LMB — drag note; tail — resize hold; RMB — delete or open effects",
                "Arrow LEFT/RIGHT — scrub; MMB — drag timeline; HOME — snap to grid",
                "S — Save; Shift+S — Export (copy audio)"
            ]
            for i, line in enumerate(help_lines):
                s = font.render(line, True, (230, 230, 240))
                ov.blit(s, (20, 16 + i * 18))
            screen.blit(ov, (0, h - timeline_h - ov.get_height() - 8))

        # Show prompt overlay if input mode
        if input_mode:
            ov = pygame.Surface((w, 120), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 180))
            screen.blit(ov, (0, h//2 - 60))
            prompt = { 'title': 'Enter Title:', 'artist': 'Enter Artist:', 'audio': 'Enter Audio Path:' }[input_mode]
            p1 = big_font.render(prompt, True, COLOR_TEXT)
            p2 = big_font.render(input_text, True, (220, 240, 255))
            screen.blit(p1, p1.get_rect(center=(w//2, h//2 - 16)))
            screen.blit(p2, p2.get_rect(center=(w//2, h//2 + 20)))

        # Live preview
        # Get active effects
        active_effects_list = [effect for effect, enabled in active_effects.items() if enabled]
        draw_preview(screen, preview_rect, now_ms, notes, approach_ms, active_effects_list)

        # Timeline background
        timeline_rect = pygame.Rect(0, h - timeline_h, w, timeline_h)
        pygame.draw.rect(screen, COLOR_TIMELINE, timeline_rect)

        # Enhanced Grid by BPM with beat highlighting
        if bpm and bpm > 0:
            beat_ms = 60000.0 / bpm
            left_time = now_ms - (w / zoom) / 2
            right_time = now_ms + (w / zoom) / 2
            k = int(left_time // (beat_ms / grid_div)) - 4
            end_k = int(right_time // (beat_ms / grid_div)) + 8
            
            # Draw beat lines with different intensities
            for j in range(k, end_k+1):
                tmark = j * (beat_ms / grid_div)
                x = time_to_x(tmark, w//2)
                if 0 <= x < w:
                    # Different colors and thickness for different beat divisions
                    if (j % grid_div) == 0:  # Main beats
                        color = (255, 255, 100)  # Bright yellow
                        thickness = 3
                        height = timeline_h
                    elif (j % (grid_div // 2)) == 0:  # Half beats
                        color = (200, 200, 255)  # Light blue
                        thickness = 2
                        height = timeline_h // 2
                    else:  # Subdivisions
                        color = (100, 150, 200)  # Muted blue
                        thickness = 1
                        height = timeline_h // 4
                    
                    # Draw vertical line
                    pygame.draw.line(screen, color, (x, h - timeline_h), (x, h - timeline_h + height), thickness)
                    
                    # Add glow effect for main beats
                    if (j % grid_div) == 0:
                        glow_surf = pygame.Surface((thickness + 4, height), pygame.SRCALPHA)
                        glow_color = (*color, 50)
                        pygame.draw.line(glow_surf, glow_color, (2, 0), (2, height), thickness + 2)
                        screen.blit(glow_surf, (x - 2, h - timeline_h))

        # Notes as buttons on timeline with hold length and type badges
        for i, n in enumerate(notes):
            x = time_to_x(n.time_ms, w//2)
            if 0 <= x < w:
                by = h - timeline_h + 40
                bw = 44
                bh = 28
                rect = pygame.Rect(x - bw//2, by - bh//2, bw, bh)
                col = COLOR_PREVIEW_NOTE.get(n.side, COLOR_ACCENT)
                if i == selected_idx:
                    pygame.draw.rect(screen, (255,255,255), rect.inflate(6,6), border_radius=BUTTON_RADIUS)
                pygame.draw.rect(screen, col, rect, border_radius=BUTTON_RADIUS)
                label = font.render(n.key, True, (20, 20, 30))
                screen.blit(label, label.get_rect(center=rect.center))
                # draw hold bar if duration
                if n.duration_ms > 0:
                    end_x = time_to_x(n.time_ms + n.duration_ms, w//2)
                    pygame.draw.line(screen, col, (x + bw//2, by), (end_x, by), 4)
                # type badge
                nt = getattr(n, 'note_type', 'tap')
                if nt != 'tap':
                    badge = 'D' if nt == 'double' else 'SL'
                    bs = font.render(badge, True, (255,255,255))
                    tag = pygame.Surface((bs.get_width()+10, bs.get_height()+4), pygame.SRCALPHA)
                    pygame.draw.rect(tag, (0,0,0,160), tag.get_rect(), border_radius=6)
                    tag.blit(bs, (5, 2))
                    screen.blit(tag, (rect.right - tag.get_width(), rect.top - tag.get_height()))
        # Live hold preview lines
        if recording and active_holds:
            for kcode, start_t in active_holds.items():
                x0 = time_to_x(int(start_t), w//2)
                x1 = time_to_x(get_now_ms(), w//2)
                by = h - timeline_h + 40
                col = (200,200,220)
                pygame.draw.line(screen, col, (x0, by-8), (x1, by-8), 2)

        # Current marker
        pygame.draw.line(screen, (255, 255, 255), (w//2, h - timeline_h), (w//2, h), 2)

        # Effect insert overlay
        if effect_insert_mode["active"]:
            px, py = effect_insert_mode["pos"]
            box_w, box_h = 320, 120
            bx = max(10, min(w - box_w - 10, px - box_w//2))
            by = max(h - timeline_h + 10, min(h - box_h - 10, py - box_h//2))
            overlay = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            pygame.draw.rect(overlay, (100, 120, 160), overlay.get_rect(), 2, border_radius=8)
            screen.blit(overlay, (bx, by))
            eff_name = EFFECT_LIST[effect_insert_mode["effect_idx"]]
            line1 = big_font.render(f"Effect: {eff_name}  (1-9 to pick)", True, COLOR_TEXT)
            line2 = font.render(f"Start: {ms_to_time_str(effect_insert_mode['start_time'])}", True, COLOR_TEXT)
            line3 = font.render(f"Duration: {effect_insert_mode['duration_ms']} ms  (+/-)  Enter=OK  Esc=Cancel", True, (200, 220, 255))
            screen.blit(line1, (bx + 12, by + 10))
            screen.blit(line2, (bx + 12, by + 46))
            screen.blit(line3, (bx + 12, by + 76))

        # Bottom control pad
        pad_h = 90
        pad_rect = pygame.Rect(0, h - pad_h, w, pad_h)
        pygame.draw.rect(screen, (30, 32, 44), pad_rect)
        keys = [("A","left"), ("W","top"), ("D","right"), ("S","bottom")]
        pad_btns: List[Tuple[pygame.Rect,str,str]] = []
        gap = 20
        btn_w = 80
        btn_h = 44
        total_w = len(keys)*btn_w + (len(keys)-1)*gap
        start_x = (w - total_w)//2
        y = h - pad_h//2
        for idx2, (klabel, side) in enumerate(keys):
            r = pygame.Rect(start_x + idx2*(btn_w+gap), y - btn_h//2, btn_w, btn_h)
            pygame.draw.rect(screen, COLOR_PREVIEW_NOTE.get(side,(120,160,220)), r, border_radius=10)
            txt2 = big_font.render(klabel, True, (20,20,30))
            screen.blit(txt2, txt2.get_rect(center=r.center))
            pad_btns.append((r, side, klabel))

        # Message
        if message:
            m = font.render(message, True, COLOR_TEXT)
            screen.blit(m, (16, 120))

        pygame.display.flip()

        # Handle pad and toolbar tab clicks after flip
        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if event.button == 1:
                mx, my = event.pos
                # Tabs
                for page, r in tab_rects:
                    if r.collidepoint(mx, my):
                        toolbar_page = page
                        layout_toolbar()
                        break
                for r, side, klabel in pad_btns:
                    if r.collidepoint(mx, my):
                        tnew = get_now_ms()
                        if bpm and bpm > 0:
                            beat_ms = 60000.0 / bpm
                            div_ms = beat_ms / grid_div
                            tnew = int(round(tnew / div_ms) * div_ms)
                        notes.append(Note(time_ms=int(tnew), side=side, key=klabel))
                        notes.sort(key=lambda n: n.time_ms)
                        selected_idx = find_note_at_time(int(tnew))
                        break
        for event in pygame.event.get(pygame.MOUSEMOTION):
            if dragging and pygame.mouse.get_pressed(num_buttons=3)[1]:
                dx, dy = event.rel
                base_offset_ms = max(0, base_offset_ms - int(dx / max(0.02, zoom)))
        for event in pygame.event.get(pygame.MOUSEBUTTONUP):
            if event.button == 2:
                dragging = False


def draw_preview(screen: pygame.Surface, rect: pygame.Rect, now_ms: int, notes: List[Note], approach_ms: int, effects: List[str] = None) -> None:
    # Enhanced preview with effects
    preview_surf = pygame.Surface(rect.size, pygame.SRCALPHA)
    preview_surf.fill((24, 26, 36))
    
    cx, cy = rect.width // 2, rect.height // 2
    center_r = int(min(rect.width, rect.height) * 0.08)
    
    # Draw background grid
    step = 20
    for x in range(0, rect.width, step):
        pygame.draw.line(preview_surf, (40, 45, 60), (x, 0), (x, rect.height), 1)
    for y in range(0, rect.height, step):
        pygame.draw.line(preview_surf, (40, 45, 60), (0, y), (rect.width, y), 1)
    
    # Draw center with glow
    glow_surf = pygame.Surface((center_r*4, center_r*4), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (200, 220, 255, 40), (center_r*2, center_r*2), center_r+8)
    preview_surf.blit(glow_surf, (cx-center_r*2, cy-center_r*2))
    pygame.draw.circle(preview_surf, COLOR_PREVIEW_CENTER, (cx, cy), center_r, 2)
    
    # Guide lines with glow
    gcol = (200, 200, 220)
    pygame.draw.line(preview_surf, gcol, (10, cy), (rect.width-10, cy), 2)
    pygame.draw.line(preview_surf, gcol, (cx, 10), (cx, rect.height-10), 2)
    
    # Draw notes with enhanced visuals
    for n in notes:
        t = (now_ms - (n.time_ms - approach_ms)) / max(1, approach_ms)
        t = max(0.0, min(1.0, t))
        
        if n.side == "left":
            sx, sy = 10, cy
        elif n.side == "right":
            sx, sy = rect.width-10, cy
        elif n.side == "top":
            sx, sy = cx, 10
        else:
            sx, sy = cx, rect.height-10
            
        x = int(sx + (cx - sx) * t)
        y = int(sy + (cy - sy) * t)
        col = COLOR_PREVIEW_NOTE.get(n.side, (200, 200, 200))
        
        # Draw note with glow
        note_radius = 8
        glow_surf = pygame.Surface((note_radius*3, note_radius*3), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*col, 60), (note_radius*1.5, note_radius*1.5), note_radius+2)
        preview_surf.blit(glow_surf, (x-note_radius*1.5, y-note_radius*1.5))
        
        # Draw note
        pygame.draw.circle(preview_surf, col, (x, y), note_radius)
        
        # Draw hold tail if applicable
        if n.duration_ms > 0:
            end_t = (now_ms - (n.time_ms + n.duration_ms - approach_ms)) / max(1, approach_ms)
            end_t = max(0.0, min(1.0, end_t))
            if end_t < 1.0:
                end_x = int(sx + (cx - sx) * end_t)
                end_y = int(sy + (cy - sy) * end_t)
                pygame.draw.line(preview_surf, col, (x, y), (end_x, end_y), 3)
    
    # Apply effects if any
    if effects:
        # Simple effect simulation
        if "blur" in effects:
            small = pygame.transform.scale(preview_surf, (rect.width//2, rect.height//2))
            preview_surf = pygame.transform.scale(small, (rect.width, rect.height))
        # Исправляем блокировку поверхности - используем копию массива
        if "invert" in effects:
            try:
                arr = pygame.surfarray.pixels3d(preview_surf).copy()
                arr[:] = 255 - arr
                preview_surf = pygame.surfarray.make_surface(arr)
            except Exception:
                pass  # Пропускаем эффект если ошибка
                
        if "grayscale" in effects:
            try:
                arr = pygame.surfarray.pixels3d(preview_surf).copy()
                gray = (arr[:,:,0]*0.3 + arr[:,:,1]*0.59 + arr[:,:,2]*0.11).astype('uint8')
                arr[:,:,0] = gray; arr[:,:,1] = gray; arr[:,:,2] = gray
                preview_surf = pygame.surfarray.make_surface(arr)
            except Exception:
                pass  # Пропускаем эффект если ошибка
    
    # Draw border
    pygame.draw.rect(preview_surf, (100, 120, 160), preview_surf.get_rect(), 2, border_radius=10)
    
    # Blit to main screen
    screen.blit(preview_surf, rect)


def side_to_default_key(side: str) -> str:
    return {
        "left": "A",
        "top": "W",
        "right": "D",
        "bottom": "S",
    }.get(side, "W")


def main():
    parser = argparse.ArgumentParser(description="Beat map editor")
    parser.add_argument("--audio", required=True, help="Path to audio file (ogg/wav/mp3)")
    parser.add_argument("--title", required=True, help="Level title")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--bpm", type=float, default=0.0, help="Grid BPM for timeline")
    parser.add_argument("--out", default=None, help="Output level json path")
    args = parser.parse_args()

    run_editor(args.audio, args.title, args.artist, args.bpm, args.out)


if __name__ == "__main__":
    main()
