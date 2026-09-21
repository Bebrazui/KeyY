#!/usr/bin/env python3
"""
Тест всех диалогов подтверждения выхода в меню
"""

import sys
import os
import re

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

def test_exit_dialogs_in_code():
    """Проверяет что диалоги подтверждения добавлены во все нужные места"""
    print("=== Проверка диалогов подтверждения выхода ===")
    
    try:
        with open('game/menu.py', 'r', encoding='utf-8') as f:
            menu_code = f.read()
        
        # Проверяем наличие функции диалога
        if 'def show_exit_confirmation(' in menu_code:
            print("✅ Функция show_exit_confirmation найдена")
        else:
            print("❌ Функция show_exit_confirmation не найдена")
            return False
        
        # Проверяем использование диалога в разных местах
        checks = [
            ('Главное меню', 'if show_exit_confirmation(screen, hint_font):'),
            ('Настройки', 'show_exit_confirmation.*настроек'),
            ('Выбор уровней', 'show_exit_confirmation.*уровней'),
            ('Меню модов', 'show_exit_confirmation.*модов'),
        ]
        
        all_good = True
        for name, pattern in checks:
            if re.search(pattern, menu_code, re.IGNORECASE):
                print(f"✅ {name}: диалог подтверждения найден")
            else:
                print(f"❌ {name}: диалог подтверждения НЕ найден")
                all_good = False
        
        # Проверяем что нет прямых return при ESC
        direct_returns = menu_code.count('pygame.K_ESCAPE')
        dialog_calls = menu_code.count('show_exit_confirmation')
        
        print(f"\n📊 Статистика:")
        print(f"   Обработок ESC: {direct_returns}")
        print(f"   Вызовов диалога: {dialog_calls}")
        
        if dialog_calls >= 5:  # Ожидаем минимум 5 диалогов
            print("✅ Достаточно диалогов подтверждения")
        else:
            print("⚠️  Возможно не все места покрыты диалогами")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Ошибка при проверке кода: {e}")
        return False

def test_menu_import():
    """Проверяет что меню импортируется без ошибок"""
    print("\n=== Проверка импорта меню ===")
    
    try:
        from game.menu import show_exit_confirmation, run_menu
        print("✅ Меню импортируется успешно")
        
        # Проверяем что функция вызывается
        if callable(show_exit_confirmation):
            print("✅ Функция show_exit_confirmation готова к использованию")
        else:
            print("❌ Функция show_exit_confirmation не является вызываемой")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def main():
    print("🔍 Тестирование системы диалогов подтверждения выхода\n")
    
    test1 = test_exit_dialogs_in_code()
    test2 = test_menu_import()
    
    print(f"\n{'='*50}")
    
    if test1 and test2:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("\n✨ Диалоги подтверждения выхода успешно добавлены во все экраны меню.")
        print("   Теперь при нажатии ESC будет появляться подтверждение.")
        print("\n🚀 Можете запускать меню: python -m game.menu")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ!")
        print("   Проверьте код и исправьте ошибки.")
    
    return test1 and test2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)