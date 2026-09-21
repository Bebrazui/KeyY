{
  "name": "Отладочная информация",
  "version": "1.0",
  "description": "Показывает дополнительную информацию на экране. Нажмите F1 для переключения.",
  "author": "Система",
  "enabled": false,
  "hooks": {
    "on_key_press": ["toggle_debug"],
    "on_draw_ui": ["draw_debug_info"]
  },
  "settings": {
    "show_debug": false,
    "show_note_count": true,
    "show_timing": true,
    "show_performance": true
  }
}