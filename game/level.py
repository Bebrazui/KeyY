import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class Note:
    time_ms: int
    side: str  # "left" | "top" | "right" | "bottom"
    key: str   # display key, e.g., "A", "W", "S", "D"
    duration_ms: int = 0  # 0 for tap; >0 for hold notes
    is_fake: bool = False  # True для фейковых нот
    note_type: str = "tap"  # "tap" | "hold" | "double" | "slide"
    slide_target: Optional[str] = None  # For slide notes: target side


@dataclass
class Event:
    time_ms: int
    type: str  # 'zoom','rotate','effect_on','effect_off'
    value: Optional[float] = None
    name: Optional[str] = None


@dataclass
class Level:
    title: str
    artist: str
    audio: str  # relative path to audio file
    approach_ms: int = 1000
    hit_window_ms: int = 120
    difficulty: str = ""  # optional per-level override: easy|normal|hard|insane
    notes: List[Note] = None
    effects: List[str] = None  # post-processing effects identifiers
    events: List[Event] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "artist": self.artist,
            "audio": self.audio,
            "approach_ms": self.approach_ms,
            "hit_window_ms": self.hit_window_ms,
            "notes": [asdict(n) for n in (self.notes or [])],
            "effects": list(self.effects or []),
            "events": [asdict(e) for e in (self.events or [])],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Level":
        notes = []
        for nd in data.get("notes", []):
            if "duration_ms" not in nd:
                nd["duration_ms"] = 0
            notes.append(Note(**nd))
        events = [Event(**ev) for ev in data.get("events", [])]
        return Level(
            title=data.get("title", "Untitled"),
            artist=data.get("artist", "Unknown"),
            audio=data.get("audio", ""),
            approach_ms=int(data.get("approach_ms", 1000)),
            hit_window_ms=int(data.get("hit_window_ms", 120)),
            difficulty=str(data.get("difficulty", "")),
            notes=notes,
            effects=list(data.get("effects", [])),
            events=events,
        )


def load_level(path: str) -> Level:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Level.from_dict(data)


def save_level(level: Level, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(level.to_dict(), f, ensure_ascii=False, indent=2)
