import json
import os
import importlib.util
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class Mod:
    name: str
    version: str
    description: str
    author: str
    enabled: bool
    file_path: str
    mod_type: str  # "file" or "folder"
    
class ModSystem:
    def __init__(self):
        self.mods: Dict[str, Mod] = {}
        self.loaded_modules: Dict[str, Any] = {}  # Кеш загруженных модулей
        self.mods_dir = "mods"
        self.config_file = os.path.join(self.mods_dir, "mods_config.json")
        self.ensure_mods_dir()
        self.load_config()
        self.scan_mods()
    
    def ensure_mods_dir(self):
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir, exist_ok=True)
    
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for mod_id, mod_data in config.items():
                        if os.path.exists(mod_data.get('file_path', '')):
                            self.mods[mod_id] = Mod(**mod_data)
            except Exception as e:
                print(f"Ошибка загрузки конфига модов: {e}")
    
    def save_config(self):
        config = {}
        for mod_id, mod in self.mods.items():
            config[mod_id] = {
                'name': mod.name,
                'version': mod.version,
                'description': mod.description,
                'author': mod.author,
                'enabled': mod.enabled,
                'file_path': mod.file_path,
                'mod_type': mod.mod_type
            }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфига модов: {e}")
    
    def scan_mods(self):
        """Сканирует папку mods на наличие новых модов"""
        if not os.path.exists(self.mods_dir):
            return
        
        for item in os.listdir(self.mods_dir):
            item_path = os.path.join(self.mods_dir, item)
            
            # Проверяем .mod файлы
            if item.endswith('.mod') and os.path.isfile(item_path):
                mod_id = item[:-4]  # убираем .mod
                if mod_id not in self.mods:
                    self.load_mod_file(item_path, mod_id)
            
            # Проверяем папки с модами
            elif os.path.isdir(item_path) and item != "__pycache__":
                mod_info_path = os.path.join(item_path, "mod_info.json")
                if os.path.exists(mod_info_path) and item not in self.mods:
                    self.load_mod_folder(item_path, item)
    
    def load_mod_file(self, file_path: str, mod_id: str):
        """Загружает .mod файл"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                mod_data = json.load(f)
            
            mod = Mod(
                name=mod_data.get('name', mod_id),
                version=mod_data.get('version', '1.0'),
                description=mod_data.get('description', 'Нет описания'),
                author=mod_data.get('author', 'Неизвестно'),
                enabled=mod_data.get('enabled', True),
                file_path=file_path,
                mod_type='file'
            )
            
            self.mods[mod_id] = mod
            
        except Exception as e:
            print(f"Ошибка загрузки мода {file_path}: {e}")
    
    def load_mod_folder(self, folder_path: str, mod_id: str):
        """Загружает мод из папки"""
        try:
            mod_info_path = os.path.join(folder_path, "mod_info.json")
            with open(mod_info_path, 'r', encoding='utf-8') as f:
                mod_data = json.load(f)
            
            mod = Mod(
                name=mod_data.get('name', mod_id),
                version=mod_data.get('version', '1.0'),
                description=mod_data.get('description', 'Нет описания'),
                author=mod_data.get('author', 'Неизвестно'),
                enabled=mod_data.get('enabled', True),
                file_path=folder_path,
                mod_type='folder'
            )
            
            self.mods[mod_id] = mod
            
        except Exception as e:
            print(f"Ошибка загрузки мода из папки {folder_path}: {e}")
    
    def toggle_mod(self, mod_id: str):
        """Включает/выключает мод"""
        if mod_id in self.mods:
            self.mods[mod_id].enabled = not self.mods[mod_id].enabled
            self.save_config()
    
    def get_enabled_mods(self) -> List[Mod]:
        """Возвращает список включенных модов"""
        return [mod for mod in self.mods.values() if mod.enabled]
    
    def get_all_mods(self) -> List[Mod]:
        """Возвращает список всех модов"""
        return list(self.mods.values())
    
    def execute_mod_hooks(self, hook_name: str, *args, **kwargs):
        """Выполняет хуки модов"""
        results = []
        for mod in self.get_enabled_mods():
            try:
                if mod.mod_type == 'folder':
                    # Загружаем Python модуль из папки с кешированием
                    main_py = os.path.join(mod.file_path, "main.py")
                    if os.path.exists(main_py):
                        mod_key = f"{mod.name}_{mod.file_path}"
                        
                        # Проверяем кеш
                        if mod_key not in self.loaded_modules:
                            spec = importlib.util.spec_from_file_location(f"mod_{mod.name}", main_py)
                            if spec and spec.loader:
                                module = importlib.util.module_from_spec(spec)
                                spec.loader.exec_module(module)
                                self.loaded_modules[mod_key] = module
                        
                        module = self.loaded_modules[mod_key]
                        
                        # Вызываем хук если он есть
                        if hasattr(module, hook_name):
                            result = getattr(module, hook_name)(*args, **kwargs)
                            if result is not None:
                                results.append(result)
                
                elif mod.mod_type == 'file':
                    # Для .mod файлов можем выполнять простые команды
                    with open(mod.file_path, 'r', encoding='utf-8') as f:
                        mod_data = json.load(f)
                    
                    hooks = mod_data.get('hooks', {})
                    if hook_name in hooks:
                        # Выполняем простые команды из JSON
                        commands = hooks[hook_name]
                        if isinstance(commands, list):
                            for cmd in commands:
                                result = self.execute_simple_command(cmd, *args, **kwargs)
                                if result is not None:
                                    results.append(result)
                        
            except Exception as e:
                print(f"Ошибка выполнения хука {hook_name} в моде {mod.name}: {e}")
        
        return results
    
    def execute_simple_command(self, command: str, *args, **kwargs):
        """Выполняет простые команды из .mod файлов"""
        # Здесь можно добавить обработку простых команд
        if command == "print_debug":
            print(f"Мод выполнил команду: {command}")

# Глобальный экземпляр системы модов
mod_system = ModSystem()