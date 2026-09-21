"""
Пример мода для демонстрации системы модов
"""

def on_game_start(state, level):
    """Вызывается при старте игры"""
    print("Пример мода: Игра началась!")

def on_note_hit(state, note, judgment):
    """Вызывается при попадании по ноте"""
    if judgment == "PERFECT":
        print(f"Пример мода: Отличное попадание!")

def on_game_end(state, level):
    """Вызывается при завершении игры"""
    print(f"Пример мода: Игра завершена! Счет: {state.score}")