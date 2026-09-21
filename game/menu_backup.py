import os
import pygame
from typing import List, Tuple
import glob

from .level import load_level
from .main import play_level
from .editor import run_editor
from .settings import load_settings, save_settings
from .mod_system import mod_system

def run_menu():
    pygame.init()
    screen = pygame.display.set_mode((900, 600))
    pygame.display.set_caption("Rhythm Game - Mods Test")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    
    running = True
    while running:
        dt = clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Выполняем хуки модов для обработки клавиш
                results = mod_system.execute_mod_hooks("on_key_press", event, None, {})
                
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Отрисовка
        screen.fill((20, 20, 30))
        
        title = font.render("Тест системы модов", True, (255, 255, 255))
        screen.blit(title, (50, 50))
        
        help_text = font.render("Нажмите ] для автопилота, Tab для читов", True, (200, 200, 200))
        screen.blit(help_text, (50, 100))
        
        # FPS
        fps = int(clock.get_fps())
        fps_text = font.render(f"FPS: {fps}", True, (150, 150, 150))
        screen.blit(fps_text, (800, 10))
        
        # Выполняем хуки модов для отрисовки UI
        mod_system.execute_mod_hooks("on_draw_ui", screen, font, None)
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    run_menu()