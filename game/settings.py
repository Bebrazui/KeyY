import json
import os
from typing import Dict, Any

DEFAULTS = {
    "graphics": {
        "quality": "high",   # high для лучшего качества
        "effects_enabled": False,  # Отключаем эффекты по умолчанию для производительности
        "effects_mode": "off",  # off | light | full
        "fullscreen": True,
        "parallax_circles": False  # Отключаем параллакс для производительности
    },
    "timing": {
        "linger_ms": 500,       # how long note stays at center after arrival (if not hit)
        "visible_lead_ms": 500,  # how long before arrival the note becomes visible
        "hit_window_ms": 120,
        "difficulty": "normal"  # easy|normal|hard|insane
    },
    "audio": {
        "music_volume": 0.8,
        "sfx_volume": 0.9,
        "layered_hitsounds": True,
        "pitch_shift_combo": True,
        "lowpass_on_bad": True
    },
    "ui": {
        "language": "en"  # en | ru
    },
    "gameplay": {
        "slide_follow_ms": 160,
        "slide_bonus_score": 150
    },
    "progress": {
        "highscores": {},  # level_name -> {"score": int, "combo": int, "accuracy": float, "difficulty": str}
        "achievements": []  # List of earned achievement IDs
    }
}

SETTINGS_PATH = os.path.join("config", "settings.json")


def ensure_dir():
    d = os.path.dirname(SETTINGS_PATH)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def load_settings() -> Dict[str, Any]:
    ensure_dir()
    if not os.path.exists(SETTINGS_PATH):
        save_settings(DEFAULTS)
        return json.loads(json.dumps(DEFAULTS))
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    merged = json.loads(json.dumps(DEFAULTS))
    _deep_update(merged, data)
    return merged


def save_settings(data: Dict[str, Any]) -> None:
    ensure_dir()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _deep_update(base: Dict[str, Any], upd: Dict[str, Any]) -> None:
    for k, v in upd.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v


def save_highscore(level_name: str, score: int, combo: int, accuracy: float, difficulty: str) -> bool:
    """Save a highscore if it's better than the current one. Returns True if saved."""
    settings = load_settings()
    current = settings["progress"]["highscores"].get(level_name, {})
    
    if not current or score > current.get("score", 0):
        settings["progress"]["highscores"][level_name] = {
            "score": score,
            "combo": combo,
            "accuracy": accuracy,
            "difficulty": difficulty
        }
        save_settings(settings)
        return True
    return False


def get_highscore(level_name: str) -> Dict[str, Any]:
    """Get the highscore for a level."""
    settings = load_settings()
    return settings["progress"]["highscores"].get(level_name, {})


def unlock_achievement(achievement_id: str) -> bool:
    """Unlock an achievement if not already unlocked. Returns True if newly unlocked."""
    settings = load_settings()
    achievements = settings["progress"]["achievements"]
    
    if achievement_id not in achievements:
        achievements.append(achievement_id)
        save_settings(settings)
        return True
    return False


def get_achievements() -> list:
    """Get list of unlocked achievements."""
    settings = load_settings()
    return settings["progress"]["achievements"]
