"""
Мод автопилота - автоматически играет за игрока
"""
import pygame
import json
import os
import random

# Глобальные переменные мода
settings = {}

def load_settings():
    """Загружает настройки мода"""
    global settings
    try:
        mod_path = os.path.dirname(__file__)
        with open(os.path.join(mod_path, "mod_info.json"), 'r', encoding='utf-8') as f:
            data = json.load(f)
            settings = data.get('settings', {})
    except Exception as e:
        print(f"Ошибка загрузки настроек автопилота: {e}")
        settings = {
            "enabled": False,
            "accuracy": 0.95,
            "reaction_time_ms": 50
        }

def save_settings():
    """Сохраняет настройки мода"""
    global settings
    try:
        mod_path = os.path.dirname(__file__)
        mod_info_path = os.path.join(mod_path, "mod_info.json")
        
        with open(mod_info_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data['settings'] = settings
        
        with open(mod_info_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения настроек автопилота: {e}")

def on_key_press(event, state, game_settings):
    """Обработка нажатий клавиш"""
    global settings
    
    if event.key == pygame.K_RIGHTBRACKET:  # ] key
        settings["enabled"] = not settings.get("enabled", False)
        save_settings()
        print(f"Автопилот {'включен' if settings['enabled'] else 'выключен'}")
        return True  # Сообщаем что мод обработал клавишу
    
    return False

def on_game_update(state, dt, now_ms):
    """Обновление игры - автопилот"""
    global settings
    
    if not settings.get("enabled", False):
        return
    
    if not hasattr(state, 'audio_started') or not state.audio_started:
        return
    
    if hasattr(state, 'finished') and state.finished:
        return
        
    if hasattr(state, 'failed') and state.failed:
        return
    
    if not hasattr(state, 'notes'):
        return
    
    # Получаем настройки
    accuracy = settings.get("accuracy", 0.95)
    reaction_time = settings.get("reaction_time_ms", 50)
    
    # Автоматически играем ноты
    for note in state.notes:
        if note.hit or note.missed:
            continue
            
        arrive_time = note.spawn_time_ms + state.level.approach_ms
        hit_window = state.level.hit_window_ms
        
        # Проверяем попадание в окно с учетом точности
        if abs(now_ms - arrive_time) <= hit_window:
            # Случайная точность
            if random.random() < accuracy:
                # Имитируем нажатие клавиши
                side = note.note.side
                
                # Импортируем функции из основной игры
                try:
                    import sys
                    import os
                    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
                    from game.main import handle_hit_input, KEY_TO_SIDE
                    
                    # Находим подходящую клавишу
                    key = None
                    for k, s in KEY_TO_SIDE.items():
                        if s == side:
                            key = k
                            break
                    
                    if key:
                        handle_hit_input(state, key, now_ms, {})
                except Exception as e:
                    print(f"Ошибка автопилота: {e}")

def on_draw_ui(screen, font, state):
    """Отрисовка UI мода"""
    global settings
    
    if settings.get("enabled", False):
        autopilot_text = font.render("АВТОПИЛОТ [ВКЛЮЧЕН]", True, (0, 255, 0))
        screen.blit(autopilot_text, (10, 10))

def on_mod_init():
    """Инициализация мода"""
    load_settings()
    print("Мод автопилота загружен. Нажмите ] для включения/выключения.")

# Инициализация при первом импорте
if 'autopilot_mod_initialized' not in globals():
    globals()['autopilot_mod_initialized'] = True
    on_mod_init()