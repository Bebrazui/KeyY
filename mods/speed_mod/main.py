"""
Мод ускорителя - изменяет скорость игры
"""
import pygame
import json
import os

# Глобальные переменные мода
speed_multiplier = 1.0
settings = {}

def load_settings():
    """Загружает настройки мода"""
    global settings, speed_multiplier
    try:
        mod_path = os.path.dirname(__file__)
        with open(os.path.join(mod_path, "mod_info.json"), 'r', encoding='utf-8') as f:
            data = json.load(f)
            settings = data.get('settings', {})
            speed_multiplier = settings.get('speed_multiplier', 1.0)
    except Exception as e:
        print(f"Ошибка загрузки настроек мода ускорителя: {e}")
        settings = {
            "speed_multiplier": 1.0,
            "min_speed": 0.5,
            "max_speed": 2.0,
            "speed_step": 0.1
        }

def save_settings():
    """Сохраняет настройки мода"""
    global settings, speed_multiplier
    try:
        mod_path = os.path.dirname(__file__)
        mod_info_path = os.path.join(mod_path, "mod_info.json")
        
        with open(mod_info_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        settings['speed_multiplier'] = speed_multiplier
        data['settings'] = settings
        
        with open(mod_info_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Ошибка сохранения настроек мода ускорителя: {e}")

def on_key_press(event, state, settings_game):
    """Обработка нажатий клавиш"""
    global speed_multiplier
    
    if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
        # Увеличиваем скорость
        max_speed = settings.get('max_speed', 2.0)
        step = settings.get('speed_step', 0.1)
        speed_multiplier = min(max_speed, speed_multiplier + step)
        save_settings()
        print(f"Скорость: {speed_multiplier:.1f}x")
        
    elif event.key == pygame.K_MINUS:
        # Уменьшаем скорость
        min_speed = settings.get('min_speed', 0.5)
        step = settings.get('speed_step', 0.1)
        speed_multiplier = max(min_speed, speed_multiplier - step)
        save_settings()
        print(f"Скорость: {speed_multiplier:.1f}x")

def on_game_update(state, dt, now_ms):
    """Обновление игры - изменяем скорость времени"""
    global speed_multiplier
    
    # Изменяем скорость времени для нот
    if hasattr(state, 'notes'):
        for note in state.notes:
            if hasattr(note, 'approach_ms'):
                # Корректируем время подхода ноты
                note.approach_ms = int(note.approach_ms / speed_multiplier)

def on_draw_ui(screen, font, state):
    """Отрисовка UI мода"""
    global speed_multiplier
    
    if speed_multiplier != 1.0:
        speed_text = font.render(f"Скорость: {speed_multiplier:.1f}x", True, (255, 255, 0))
        screen.blit(speed_text, (20, 180))

# Инициализация мода
load_settings()
print(f"Мод ускорителя загружен. Скорость: {speed_multiplier:.1f}x")