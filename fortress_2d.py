"""CORRIDOR SLAYER | 2D Ship Renderer."""
import pygame
import os

class Fortress:
    def __init__(self, x, y, level=1):
        self.x = x
        self.y = y
        self.level = level
        self._base_image = None
        
        self.image_folder = "fortress" 
        # Für 960x540 Querformat
        self.target_width = 160 
        
        self._load_image()

    def _load_image(self):
        image_name = f"ship_lvl_{self.level}.png"
        image_path = os.path.join(self.image_folder, image_name)
        
        try:
            raw_image = pygame.image.load(image_path).convert_alpha()
            bounding_rect = raw_image.get_bounding_rect()
            cropped_image = pygame.Surface((bounding_rect.width, bounding_rect.height), pygame.SRCALPHA)
            cropped_image.blit(raw_image, (0, 0), bounding_rect)
            
            base_w, base_h = cropped_image.get_size()
            target_h = int(base_h * (self.target_width / base_w))
            
            self._base_image = pygame.transform.smoothscale(cropped_image, (self.target_width, target_h))
            
        except Exception as e:
            print(f"Fehler beim Laden von {image_path}: {e}")
            self._base_image = pygame.Surface((160, 80), pygame.SRCALPHA)
            pygame.draw.ellipse(self._base_image, (40, 50, 70), (0, 0, 160, 80))

    def update(self, dt):
        pass

    def draw(self, screen):
        if not self._base_image:
            return
        rect = self._base_image.get_rect(center=(self.x, self.y))
        screen.blit(self._base_image, rect)