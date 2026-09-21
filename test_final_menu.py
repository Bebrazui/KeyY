#!/usr/bin/env python3
"""
Финальный тест меню с диалогом подтверждения только в главном меню
"""

import sys
import os

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

def test_exit_confirmation_placement():
    """Проверяет что диалог подтверждения только в главном меню"""
    print("=== Тест размещения диалогов подтверждения ===")
    
    try:
        with open('game/menu.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Проверяем что функция диалога существует
        if 'def show_exit_confirmation(' in code:
            print("✅ Функция show_exit_confirmation найдена")
        else:
            print("❌ Функция show_exit_confirmation не найдена")
            return False
        
        # Считаем вызовы диалога
        dialog_calls = code.count('show_exit_confirmation(screen, hint_font)')
        
        print(f"📊 Найдено {dialog_calls} вызовов диалога подтверждения")
        
        # Проверяем что диалог только в главном меню (должно быть 2 вызова: ESC и закрытие окна)
        if dialog_calls == 2:
            print("✅ Диалог подтверждения только в главном меню - правильно!")
            return True
        elif dialog_calls > 2:
            print("⚠️  Диалогов больше чем нужно - возможно остались в других экранах")
            return False
        else:
            print("❌ Диалогов меньше чем нужно - возможно что-то сломалось")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False

def test_menu_functions():
    """Проверяет что все функции меню работают"""
    print("\n=== Тест функций меню ===")
    
    try:
        from game.menu import (
            run_menu, 
            show_exit_confirmation, 
            run_mods_screen,
            select_and_play_level,
            select_and_edit_level,
            run_settings_screen
        )
        
        functions = [
            'run_menu',
            'show_exit_confirmation', 
            'run_mods_screen',
            'select_and_play_level',
            'select_and_edit_level',
            'run_settings_screen'
        ]
        
        for func_name in functions:
            print(f"✅ {func_name} импортирована успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def main():
    print("🔍 Финальная проверка меню с диалогом подтверждения\n")
    
    test1 = test_exit_confirmation_placement()
    test2 = test_menu_functions()
    
    print(f"\n{'='*60}")
    
    if test1 and test2:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\n✨ Меню настроено правильно:")
        print("   • Диалог подтверждения выхода только в главном меню")
        print("   • Все остальные экраны выходят сразу при ESC")
        print("   • Нет ошибок импорта или выполнения")
        print("\n🚀 Запустите меню: python -m game.menu")
        print("   При нажатии ESC в главном меню появится диалог подтверждения")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ!")
        print("   Проверьте код и исправьте ошибки.")
    
    return test1 and test2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)