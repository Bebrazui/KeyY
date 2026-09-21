#!/usr/bin/env python3
"""
Финальный тест системы модов
"""

import sys
import os
import io
from contextlib import redirect_stdout

# Добавляем путь к игре
sys.path.insert(0, os.path.dirname(__file__))

from game.mod_system import mod_system

def test_no_infinite_loading():
    """Тестирует что нет бесконечной загрузки модов"""
    print("=== Финальный тест системы модов ===")
    
    # Перехватываем вывод
    output_buffer = io.StringIO()
    
    print("1. Первая загрузка модов...")
    with redirect_stdout(output_buffer):
        mod_system.scan_mods()
        # Выполняем хуки несколько раз
        for i in range(3):
            mod_system.execute_mod_hooks("on_test", f"test_{i}")
    
    first_output = output_buffer.getvalue()
    
    print("2. Повторные вызовы хуков...")
    output_buffer = io.StringIO()
    
    with redirect_stdout(output_buffer):
        # Выполняем хуки еще несколько раз
        for i in range(5):
            mod_system.execute_mod_hooks("on_test", f"repeat_test_{i}")
    
    second_output = output_buffer.getvalue()
    
    # Анализируем результаты
    first_load_messages = first_output.count("загружен")
    second_load_messages = second_output.count("загружен")
    
    print(f"3. Результаты:")
    print(f"   Сообщений о загрузке при первом запуске: {first_load_messages}")
    print(f"   Сообщений о загрузке при повторных вызовах: {second_load_messages}")
    
    if second_load_messages == 0:
        print("   ✅ УСПЕХ: Моды не перезагружаются!")
    else:
        print("   ❌ ОШИБКА: Моды все еще перезагружаются")
    
    print(f"4. Статистика:")
    print(f"   Всего модов: {len(mod_system.get_all_mods())}")
    print(f"   Включенных модов: {len(mod_system.get_enabled_mods())}")
    print(f"   Кешированных модулей: {len(mod_system.loaded_modules)}")
    
    print("=== Тест завершен ===")
    
    return second_load_messages == 0

if __name__ == "__main__":
    success = test_no_infinite_loading()
    sys.exit(0 if success else 1)