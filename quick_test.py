#!/usr/bin/env python3
"""
Быстрый тест меню без GUI
"""

import sys
import os

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

from game.mod_system import mod_system

def test_menu_initialization():
    print("=== Тест инициализации меню ===")
    
    # Тестируем загрузку модов
    print("1. Загрузка модов...")
    mod_system.scan_mods()
    mods = mod_system.get_all_mods()
    print(f"   Найдено модов: {len(mods)}")
    
    # Тестируем хуки несколько раз
    print("2. Тестирование хуков (5 раз)...")
    for i in range(5):
        results = mod_system.execute_mod_hooks("on_test", f"test_{i}")
        print(f"   Итерация {i+1}: хуки выполнены")
    
    print("3. Проверка что моды не загружаются повторно...")
    initial_count = len(mod_system.loaded_modules)
    
    # Выполняем хуки еще раз
    mod_system.execute_mod_hooks("on_test", "final_test")
    final_count = len(mod_system.loaded_modules)
    
    if initial_count == final_count:
        print("   ✓ Модули не перезагружаются - отлично!")
    else:
        print("   ✗ Модули перезагружаются - есть проблема")
    
    print("=== Тест завершен ===")

if __name__ == "__main__":
    test_menu_initialization()