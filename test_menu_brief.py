#!/usr/bin/env python3
"""
Краткий тест меню
"""

import pygame
import sys
import os
import threading
import time

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

def test_menu():
    """Тестирует меню в отдельном потоке"""
    try:
        from game.menu import run_menu
        
        # Инициализируем pygame в headless режиме
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        pygame.init()
        pygame.display.set_mode((800, 600))
        
        print("Запуск меню...")
        run_menu()
        print("Меню завершено")
        
    except Exception as e:
        print(f"Ошибка в меню: {e}")
    finally:
        pygame.quit()

def main():
    print("=== Тест меню ===")
    
    # Запускаем меню в отдельном потоке
    menu_thread = threading.Thread(target=test_menu)
    menu_thread.daemon = True
    menu_thread.start()
    
    # Ждем немного
    time.sleep(3)
    
    if menu_thread.is_alive():
        print("✓ Меню запустилось и работает")
    else:
        print("✗ Меню завершилось слишком быстро")
    
    print("=== Тест завершен ===")

if __name__ == "__main__":
    main()