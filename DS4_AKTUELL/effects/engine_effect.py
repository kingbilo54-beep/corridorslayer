# NUR TEST-STUB (nicht Teil des Pakets) - ersetzt die unveränderte
# Paket-6-Datei des Nutzers, damit main.py headless lauffähig ist.
import pygame


class EngineEffect:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.level = 1

    def set_position(self, x, y):
        self.x, self.y = x, y

    def update(self, dt, level=1):
        self.level = level

    def draw(self, surface):
        pygame.draw.circle(surface, (0, 130, 170), (int(self.x), int(self.y)), 6)
