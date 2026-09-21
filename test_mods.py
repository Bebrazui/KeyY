#!/usr/bin/env python3
"""
Простой тест системы модов
"""

from game.mod_system import mod_system

def test_mod_system():
    print("=== Тест системы модов ===")
    
    # Сканируем моды
    print("Сканирование модов...")
    mod_system.scan_mods()
    
    # Получаем все моды
    all_mods = mod_system.get_all_mods()
    print(f"Найдено модов: {len(all_mods)}")
    
    for mod in all_mods:
        status = "ВКЛ" if mod.enabled else "ВЫКЛ"
        print(f"  [{status}] {mod.name} v{mod.version} - {mod.description}")
    
    # Получаем включенные моды
    enabled_mods = mod_system.get_enabled_mods()
    print(f"\nВключенных модов: {len(enabled_mods)}")
    
    # Тестируем хуки
    print("\nТестирование хуков...")
    results = mod_system.execute_mod_hooks("on_test", "test_data")
    print(f"Результаты хуков: {results}")
    
    print("=== Тест завершен ===")

if __name__ == "__main__":
    test_mod_system()