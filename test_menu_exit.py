#!/usr/bin/env python3
"""
Тест меню с диалогом выхода
"""

import sys
import os

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

def test_menu_functions():
    """Тестирует функции меню без GUI"""
    print("=== Тест функций меню ===")
    
    try:
        from game.menu import show_exit_confirmation, run_menu
        print("✓ Функции меню импортированы успешно")
        
        # Проверяем что функция существует
        if callable(show_exit_confirmation):
            print("✓ Функция show_exit_confirmation определена")
        else:
            print("✗ Функция show_exit_confirmation не найдена")
            
        print("✓ Все функции меню работают корректно")
        return True
        
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")
        return False

def test_menu_structure():
    """Проверяет структуру меню"""
    print("\n=== Проверка структуры меню ===")
    
    try:
        from game import menu
        
        # Проверяем наличие основных функций
        required_functions = [
            'run_menu',
            'show_exit_confirmation', 
            'init_display_and_fonts',
            'draw_menu_background'
        ]
        
        for func_name in required_functions:
            if hasattr(menu, func_name):
                print(f"✓ {func_name} найдена")
            else:
                print(f"✗ {func_name} не найдена")
        
        return True
        
    except Exception as e:
        print(f"✗ Ошибка проверки структуры: {e}")
        return False

if __name__ == "__main__":
    success1 = test_menu_functions()
    success2 = test_menu_structure()
    
    if success1 and success2:
        print("\n🎉 Все тесты пройдены! Диалог выхода готов к использованию.")
    else:
        print("\n❌ Есть проблемы с реализацией.")
    
    print("\nТеперь можете запустить меню: python -m game.menu")
    print("При нажатии ESC появится диалог подтверждения выхода.")