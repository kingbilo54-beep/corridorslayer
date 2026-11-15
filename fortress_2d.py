"""CORRIDOR SLAYER | 2D Ship Renderer.

PAKET 7E:
  * set_level(level): Schiffsbild NACH einem Schiffs-Upgrade neu laden
    (fortress/ship_lvl_<Stufe>.png, Bilder 1-12).
  * ROBUSTER FALLBACK: Fehlt ein Bild (z. B. nur Stufe 1 vorhanden oder
    eine Luecke im Ordner), wird automatisch die naechstniedrigere
    VORHANDENE Stufe geladen - der Turm/das Schiff verschwindet nie.
"""
import pygame
import os

class Fortress:
    def __init__(self, x, y, level=1):
        self.x = x
        self.y = y
        self.level = 1
        self._base_image = None

        self.image_folder = "fortress"
        # Für 960x540 Querformat
        self.target_width = 160

        self.set_level(level)

    def _available_levels(self):
        """Stufen, fuer die im Ordner ein ship_lvl_x.png liegt."""
        try:
            files = os.listdir(self.image_folder)
        except OSError:
            return set()
        out = set()
        for f in files:
            n = f.lower()
            if n.startswith("ship_lvl_") and n.endswith(".png"):
                try:
                    out.add(int(n[len("ship_lvl_"):-4]))
                except ValueError:
                    pass
        return out

    def _resolve_level(self, level):
        """Naechstniedrigere VORHANDENE Stufe (mind. 1) - kein leeres Bild.
        Liegt gar kein Bild im Ordner, wird Stufe 1 gemeldet (laeuft auf
        den gezeichneten Notfall-Rumpf hinaus)."""
        level = max(1, int(level))
        avail = self._available_levels()
        if not avail:
            return 1
        while level > 1 and level not in avail:
            level -= 1
        return level

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

    def set_level(self, level):
        """PAKET 7E: Neue Schiffs-Stufe anwenden (Bild neu laden).
        Fehlt das Bild der Stufe, wird automatisch die naechstniedrigere
        vorhandene Stufe verwendet (Stufe 1 als Untergrenze)."""
        lvl = self._resolve_level(level)
        if lvl == self.level and self._base_image is not None:
            return
        self.level = lvl
        self._load_image()

    def update(self, dt):
        pass

    def draw(self, screen):
        if not self._base_image:
            return
        rect = self._base_image.get_rect(center=(self.x, self.y))
        screen.blit(self._base_image, rect)
