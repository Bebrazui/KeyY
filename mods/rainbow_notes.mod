{
  "name": "Радужные ноты",
  "version": "1.0",
  "description": "Делает ноты разноцветными и переливающимися",
  "author": "Пример",
  "enabled": false,
  "hooks": {
    "on_draw_note": ["rainbow_effect"],
    "on_game_update": ["update_rainbow"]
  },
  "settings": {
    "rainbow_speed": 0.05,
    "brightness": 1.0,
    "saturation": 1.0
  }
}