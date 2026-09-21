#!/usr/bin/env python3
"""
Тест диалога подтверждения выхода
"""

import pygame
import sys
import os
import threading
import time

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

def test_exit_dialog():
    """Тестирует диалог подтверждения выхода"""
    try:
        # Инициализируем pygame
        pygame.init()
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Test Exit Dialog")
        
        from game.menu import show_exit_confirmation
        
        # Создаем шрифт
        font = pygame.font.Font(None, 24)
        
        # Заполняем экран
        screen.fill((50, 50, 70))
        
        # Показываем диалог
        print("Показываю диалог подтверждения выхода...")
        print("Нажмите Enter чтобы выйти или Esc чтобы остаться")
        
        result = show_exit_confirmation(screen, font)
        
        if result:
            print("Пользователь выбрал: ВЫЙТИ")
        else:
            print("Пользователь выбрал: ОСТАТЬСЯ")
        
        return result
        
    except Exception as e:
        print(f"Ошибка в тесте: {e}")
        return False
    finally:
        pygame.quit()

if __name__ == "__main__":
    print("=== Тест диалога подтверждения выхода ===")
    print("Запускаю диалог...")
    
    # Запускаем тест только если есть дисплей
    try:
        result = test_exit_dialog()
        print(f"Результат теста: {'Выход' if result else 'Остаться'}")
    except Exception as e:
        print(f"Не удалось запустить тест (возможно нет дисплея): {e}")
    
    print("=== Тест завершен ===")