"""CORRIDOR SLAYER | Combat FX: Sichtbare Gefechts-Effekte.

PAKET A2 (WIEDERHERSTELLUNG): Diese Datei wurde im Paket A1 versehentlich
als Test-Stub (ohne Zeichnung) ausgeliefert - dadurch waren Schuesse,
Partikel, Treffer-Optiken und Schadenszahlen unsichtbar (Nutzer:
"Die Schuesse vom Schiff sind komplett verschwunden"). Diese Version
zeichnet ALLES wieder und behaelt dabei die unveraenderte Schnittstelle:

    fx = CombatFX()
    fx.update(dt, combat, center)     # combat darf None sein (kein Gefecht)
    fx.draw(surface, combat, T, s, elapsed)
    fx.shake_x / fx.shake_y           # Screen-Shake auf der Arena

Gezeichnet werden (Daten liegen unveraendert in pve_system.PvECombat):
    * combat.particles        - Explosionen/Glut/Funken (bewegt pve_system)
    * combat.projectiles      - Kanonen-/Gegner-/Drohnen-Schuesse mit
                                Leuchtspur, Glow-Kern und Farbkennung
                                (Spieler = p.color, Gegner = p.color)
    * combat.muzzle_flashes   - Muendungsfeuer der Kanonen [x, y, winkel, t]
Schadenszahlen zeichnet main.py SELBST (_draw_world, seit Paket 4) -
hier NICHT nochmal, sonst erscheinen sie doppelt. Die Bewegung/Lebenszeit
aller Objekte bleibt in pve_system - hier steht nur die Darstellung
(keine Logik, keine Werte).
"""
import math
import random

import pygame

# Versions-Kennung: main.py prueft diese Konstante. Fehlt sie (alter
# Stand, Test-Stub wie in Paket A1 oder beschaedigte Datei), schaltet
# main.py automatisch auf den eingebauten Notfall-Renderer um - Schuesse
# und Partikel bleiben so IMMER sichtbar, egal was in dieser Datei steht.
FX_VERSION = "A2"

# Kleiner Glow-Cache (additive Leuchtflecken). Begrenzt, damit der
# Speicher auf Android ruhig bleibt.
_GLOW_CACHE = {}


def _glow(color, radius):
    """Weiches, additive-faehiges Leuchtfleck-Surface (gecacht)."""
    key = (color, radius)
    g = _GLOW_CACHE.get(key)
    if g is None:
        g = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        stufen = ((0.30, 1.00), (0.55, 0.62), (0.85, 0.30))
        for k, a in stufen:
            r = max(1, int(radius * k))
            pygame.draw.circle(g, (*color, int(90 * a)), (radius, radius), r)
        pygame.draw.circle(g, (*color, 150), (radius, radius),
                           max(1, int(radius * 0.42)))
        if len(_GLOW_CACHE) > 48:
            _GLOW_CACHE.clear()
        _GLOW_CACHE[key] = g
    return g


def _fade(color, k):
    """Farbe Richtung Schwarz abdunkeln (k = 0..1)."""
    return (int(color[0] * k), int(color[1] * k), int(color[2] * k))


class CombatFX:
    """Zeichnet Projektile/Partikel/Muzzle/Schadenszahlen + Arena-Shake."""

    def __init__(self):
        self.shake_x = 0.0
        self.shake_y = 0.0
        self._amp = 0.0                       # aktuelle Shake-Amplitude
        self._trails = {}                     # id(proj) -> letzte Welt-Punkte
        self._rng = random.Random(20477)

    # ---------------- Update (kein Zeichnen) ----------------
    def update(self, dt, combat=None, center=(0, 0)):
        # Arena-Shake abklingen lassen (Eigenschwingung der Kanonen bleibt
        # dezent - der harte Treffer-Shake am Schiff liegt in damage_fx).
        self._amp = max(0.0, self._amp - dt * 10.0)
        if self._amp > 0.05:
            self.shake_x = self._rng.uniform(-self._amp, self._amp)
            self.shake_y = self._rng.uniform(-self._amp, self._amp) * 0.7
        else:
            self.shake_x = 0.0
            self.shake_y = 0.0

        if combat is None:
            # Kein Gefecht (Menue/Pause): Spuren verwerfen.
            self._trails.clear()
            return

        # Leuchtschlangen je Projektil mitfuehren (nur Positionspuffer -
        # Bewegung bleibt in pve_system).
        alive = set()
        for p in combat.projectiles:
            alive.add(id(p))
            pts = self._trails.get(id(p))
            if pts is None:
                pts = []
                self._trails[id(p)] = pts
            pts.append((p.x, p.y))
            while len(pts) > 7:
                pts.pop(0)
        for k in list(self._trails.keys()):
            if k not in alive:
                del self._trails[k]

        # Eigenes Feuer regt den Shake ganz leicht an (Gefuehl der Wucht).
        if getattr(combat, "muzzle_flashes", None):
            self._amp = min(2.0, self._amp + dt * 5.0)

    # ---------------- Zeichnen ----------------
    def draw(self, surface, combat, T, s, elapsed):
        # ---- 1) Partikel (Explosionen, Glut, Funken) ----
        for pt in combat.particles:
            k = pt.life / pt.max_life if pt.max_life > 0 else 0.0
            if k <= 0.0:
                continue
            x, y = T(pt.x, pt.y)
            r = max(1, int(pt.size * s * (0.5 + 0.5 * k)))
            col = _fade(pt.color, 0.35 + 0.65 * k)
            pygame.draw.circle(surface, col, (int(x), int(y)), r)
            if r >= 3 and k > 0.45:
                # heisser Kern bei frischen Partikeln (kurz heller)
                pygame.draw.circle(surface, _fade(pt.color, 1.0),
                                   (int(x), int(y)), max(1, r // 2))

        # ---- 2) Projektile mit Leuchtspur ----
        for p in combat.projectiles:
            col = p.color if isinstance(p.color, tuple) else (255, 255, 255)
            pts = self._trails.get(id(p))
            if pts and len(pts) >= 2:
                # Spur von hinten (dunkel) zur aktuellen Position (hell)
                n = len(pts)
                for i in range(n - 1):
                    kk = (i + 1) / n
                    a = T(*pts[i])
                    b = T(*pts[i + 1])
                    pygame.draw.line(surface, _fade(col, 0.25 + 0.55 * kk),
                                     (int(a[0]), int(a[1])),
                                     (int(b[0]), int(b[1])),
                                     max(1, int(p.size * s * 0.55)))
            x, y = T(p.x, p.y)
            r = max(1, int(p.size * s))
            # Glow (additiv) + Kern
            g = _glow(col, max(4, r * 3))
            surface.blit(g, g.get_rect(center=(int(x), int(y))),
                         special_flags=pygame.BLEND_ADD)
            pygame.draw.circle(surface, col, (int(x), int(y)), r)
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(x), int(y)), max(1, r // 2))

        # ---- 3) Muendungsfeuer der Kanonen ----
        for mf in getattr(combat, "muzzle_flashes", []):
            mx, my, ang, t = mf[0], mf[1], mf[2], mf[3]
            if t <= 0:
                continue
            k = max(0.0, min(1.0, t / 0.08))
            x, y = T(mx, my)
            laenge = (10 + 26 * k) * s
            breite = max(1, int(3.2 * s * (0.5 + k)))
            dx = math.cos(ang)
            dy = math.sin(ang)           # Welt-/Screen-Y zeigt nach unten
            sp = (int(x + dx * laenge), int(y + dy * laenge))
            # Strahlkeil + heller Kern + Glow
            pygame.draw.line(surface, (255, 210, 120),
                             (int(x), int(y)), sp, breite)
            pygame.draw.line(surface, (255, 255, 220),
                             (int(x), int(y)),
                             (int(x + dx * laenge * 0.55),
                              int(y + dy * laenge * 0.55)),
                             max(1, breite // 2))
            g = _glow((255, 200, 110), max(4, int(9 * s * (0.5 + k))))
            surface.blit(g, g.get_rect(center=(int(x), int(y))),
                         special_flags=pygame.BLEND_ADD)
        # Schadenszahlen: zeichnet main._draw_world selbst -> hier bewusst
        # NICHT (sonst doppelt).
