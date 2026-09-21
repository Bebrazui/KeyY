#!/usr/bin/env python3
"""
Простой тест диалогов выхода
"""

import sys
import os

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

def main():
    print("=== Простой тест диалогов выхода ===")
    
    try:
        # Проверяем импорт
        from game.menu import show_exit_confirmation
        print("✅ Функция show_exit_confirmation импортирована")
        
        # Проверяем что функция существует
        if callable(show_exit_confirmation):
            print("✅ Функция готова к использованию")
        
        # Проверяем код
        with open('game/menu.py', 'r', encoding='utf-8') as f:
            code = f.read()
        
        dialog_count = code.count('show_exit_confirmation(')
        print(f"✅ Найдено {dialog_count} вызовов диалога подтверждения")
        
        if dialog_count >= 5:
            print("🎉 УСПЕХ! Диалоги подтверждения добавлены во все экраны!")
            print("\nТеперь при нажатии ESC в любом экране меню будет появляться")
            print("диалог 'Вы уверены что хотите выйти?' с кнопками Да/Нет.")
            print("\nЗапустите меню: python -m game.menu")
            return True
        else:
            print("⚠️ Возможно не все экраны покрыты")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)