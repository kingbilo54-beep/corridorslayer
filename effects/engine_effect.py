# =====================================================================
# CORRIDOR SLAYER | PAKET 7E: TRIEBWERKS-FX (WIEDERHERSTELLUNG)
# ---------------------------------------------------------------------
# Diese Datei wurde im Paket 6/7 als Test-Stub mitgeliefert (18 Zeilen,
# nur ein statischer 6-px-Kreis). Folge: Das Schiff hatte keinen
# sichtbaren Triebwerkseffekt mehr (Nutzer: "Verschwundene Triebwerks-
# effekte wiederherstellen"). Diese Version stellt den Effekt wieder
# her und behaelt dabei DIE UNVERAENDERTE Schnittstelle aus main.py:
#
#     engine = EngineEffect(x, y)
#     engine.set_position(x, y)     # Screen-Punkt des Duesen (je Frame)
#     engine.update(dt, level)      # level = Stufe des Moduls "antrieb"
#     engine.draw(surface)          # zeichnet am gesetzten Punkt
#
# Dargestellt wird der Abwindstrahl am Heck (Duese zeigt nach links,
# das Schiff fliegt nach rechts):
#   * weicher, additiver Glutkern an der Duese (flackert)
#   * nach hinten auslaufende Abwindfahne (5 Segmente)
#   * kleine Glutpartikel, die nach links abziehen und verblassen
# Die Stärke skaliert mit der Antriebsstufe (Funktionsanzeige wie der
# Schildring - keine Hulenaenderung). Keine Spiellogik, keine Werte:
# diese Datei zeichnet NUR und kann das Gefecht nicht beeinflussen.
# =====================================================================
import math
import random

import pygame

try:                                      # ui_kit-Glow, wenn verfuegbar
    from ui_kit import radial_glow_k
except Exception:                         # Fallback (headless/flat copy)
    radial_glow_k = None

# Glow-Cache (begrenzt, damit der Speicher auf Android ruhig bleibt)
_GLOW_CACHE = {}


def _glow(color, radius):
    """Weiches, additive-faehiges Leuchtfleck-Surface (gecacht).
    KRÄFTIG abgestuft: der Strahl muss auch dann lesbar bleiben, wenn
    spaeter gezeichnete Ebenen (Schild-Grafik, Vignette) abdunkeln -
    der alte Stub war deshalb sichtbar, weil er OPAK malte."""
    key = (color, radius)
    g = _GLOW_CACHE.get(key)
    if g is None:
        g = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        stufen = ((0.30, 1.00), (0.55, 0.62), (0.85, 0.30))
        for k, a in stufen:
            r = max(1, int(radius * k))
            pygame.draw.circle(g, (*color, int(190 * a)), (radius, radius), r)
        pygame.draw.circle(g, (*color, 235), (radius, radius),
                           max(1, int(radius * 0.42)))
        if len(_GLOW_CACHE) > 48:
            _GLOW_CACHE.clear()
        _GLOW_CACHE[key] = g
    return g


def _add_glow(surface, color, radius, x, y):
    """Glow additiv an (x, y) malen - ueber ui_kit wenn importierbar."""
    if radial_glow_k is not None:
        try:
            g = radial_glow_k(color, radius, 1.0)
            surface.blit(g, g.get_rect(center=(int(x), int(y))),
                         special_flags=pygame.BLEND_ADD)
            return
        except Exception:
            pass
    g = _glow(color, max(2, int(radius)))
    surface.blit(g, g.get_rect(center=(int(x), int(y))),
                 special_flags=pygame.BLEND_ADD)


class EngineEffect:
    """Triebwerks-FX am Heck des Schiffs (PAKET 7E, wiederhergestellt)."""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.level = 1
        self.t = 0.0                       # Animationszeit (Flackern)
        self._emit = 0.0                   # Partikel-Emissions-Rest
        self._embers = []                  # [x, y, vx, vy, life, max, size]
        self._rng = random.Random(70411)

    # ---------------- Schnittstelle (unveraendert) ----------------
    def set_position(self, x, y):
        self.x, self.y = x, y

    def update(self, dt, level=1):
        dt = max(0.0, min(0.1, dt))        # gegen Zeit-Spruenke (Tab-Wechsel)
        self.level = max(1, int(level))
        self.t += dt

        # Glutpartikel emittieren (Rate je Antriebsstufe)
        rate = 14.0 + 5.0 * self.level
        self._emit += dt * rate
        while self._emit >= 1.0 and len(self._embers) < 80:
            self._emit -= 1.0
            self._embers.append([
                self.x - self._rng.uniform(0.0, 6.0),
                self.y + self._rng.uniform(-3.0, 3.0),
                -(55.0 + self._rng.uniform(0.0, 70.0)) - 3.0 * self.level,
                self._rng.uniform(-9.0, 9.0),
                self._rng.uniform(0.30, 0.60), 0.60,
                self._rng.uniform(1.5, 3.2),
            ])

        # Partikel bewegen + abklingen lassen
        for e in self._embers:
            e[0] += e[2] * dt
            e[1] += e[3] * dt
            e[4] -= dt
        self._embers = [e for e in self._embers if e[4] > 0.0]

    def draw(self, surface):
        lvl = self.level
        # Flackerfaktor: weiches Fremdlicht-Blinken, nie stillstehend
        flick = 0.80 + 0.14 * math.sin(self.t * 11.0) \
                     + 0.06 * math.sin(self.t * 23.0)
        flick = max(0.55, min(1.10, flick))

        kern_r = (4.0 + 1.0 * lvl) * flick          # Glutkern an der Duese
        seg = (4.5 + 1.0 * lvl) * flick             # Segment-Abstand Fahne
        # Farben: heisser Kern -> kuehlerer Abwindstrahl (wie Stub-Farbe)
        # 1) OPAKER Leuchtkern (guaranteed visibility, wie der Stub, nur
        #    schoener): verdraengt dunkle Overlays an der Duese selbst.
        pygame.draw.circle(surface, (150, 225, 250),
                           (int(self.x), int(self.y)), max(2, int(kern_r * 0.5)))
        pygame.draw.circle(surface, (210, 245, 255),
                           (int(self.x), int(self.y)),
                           max(1, int(kern_r * 0.28)))
        # 2) additive Glutschichten darueber
        _add_glow(surface, (190, 240, 255), kern_r * 1.5, self.x, self.y)
        _add_glow(surface, (110, 210, 240), kern_r * 2.1, self.x, self.y)
        for i in range(1, 6):                       # Abwindfahne nach links
            px = self.x - i * seg
            py = self.y + (i * 0.6) * math.sin(self.t * 9.0 + i)
            r = kern_r * (1.15 - 0.15 * i)
            if r < 1.5:
                break
            _add_glow(surface, (70, 175, 220), r, px, py)
        # Glutpartikel (klein, blau-cyan, verblassend)
        for e in self._embers:
            k = e[4] / e[5] if e[5] > 0.0 else 0.0
            c = (int(110 + 100 * k), int(175 + 70 * k), 255)
            r = max(1, int(e[6] * (0.6 + 0.6 * k)))
            pygame.draw.circle(surface, c, (int(e[0]), int(e[1])), r)
