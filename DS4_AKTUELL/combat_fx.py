# NUR TEST-STUB (nicht Teil des Pakets) - ersetzt die unveränderte
# Paket-6-Datei des Nutzers, damit main.py headless lauffähig ist.
import pygame


class CombatFX:
    def __init__(self):
        self.shake_x = 0.0
        self.shake_y = 0.0

    def update(self, dt, combat=None, center=(0, 0)):
        self.shake_x = 0.0
        self.shake_y = 0.0

    def draw(self, surface, combat, T, s, elapsed):
        pass
