# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 7C: UPGRADE-FX - sichtbares Upgrade-Feedback.

Kurze, hochwertige Animation (~1.1 s, NICHT blockierend), wenn ein
Schiffs-Modul aufgewertet wird:

  1. Modul-Hotspot wird hervorgehoben (expandierender Doppelring).
  2. Eine Energie-/Scan-Linie laeuft ueber die Schiffs-/Karten-Flaeche.
  3. Beim "Treffer" des Moduls: Lichtimpuls (additiver Glow) + Funken.
  4. Neue Stufe wird als aufsteigender Text "LVL X" angezeigt.
  5. Dezenter Kameraimpuls (shake() liefert Offsets fuer die Werft).

Alles prozedural (pygame-Primitives + gecachte Glows), keine Assets.
Farbe pro Modul kommt aus main.HOTSPOT_COL (Sci-Fi-Palette).
"""
import math
import random

import pygame

import ui_kit
from ui_kit import (u, F, text, neon_text, radial_glow_k, _mix_col,
                    WHITE, CYAN)

_DUR = 1.1          # Gesamtdauer in Sekunden
_SCAN_T0 = 0.10     # Scan-Start
_SCAN_T1 = 0.62     # Scan-Ende (Impuls-Fenster)


class UpgradeFX:
    """Verwaltet alle laufenden Upgrade-Animationen (mehrere gleichzeitig
    moeglich, praktisch immer nur eine). update() pro Frame, draw() NACH dem
    Schiff/Panel zeichnen."""

    def __init__(self):
        self.fx = []          # Liste von aktiven Animationen (dicts)

    # ---------------- Start ----------------
    def start(self, key, level, x, y, color, rect=None):
        """Neue Animation starten.
        key    : Modul-Schluessel (nur zur Info/Debug)
        level  : NEUE Stufe (wird als Text angezeigt)
        x, y   : Hotspot-Position auf der Surface
        color  : Akzentfarbe des Moduls
        rect   : Flaeche fuer den Scan-Sweep (Schiffsbild-Rect oder
                 Modul-Karten-Rect); None = nur Ring/Impuls am Hotspot."""
        rnd = random.Random(hash((key, level, int(x), int(y))) & 0xFFFF)
        sparks = []
        for _ in range(14):
            ang = rnd.uniform(0, math.tau)
            sp = rnd.uniform(70, 210)
            sparks.append([math.cos(ang) * sp, math.sin(ang) * sp,
                           rnd.uniform(0.35, 0.7)])
        self.fx.append({
            "key": key, "level": int(level), "x": x, "y": y, "color": color,
            "rect": pygame.Rect(rect) if rect is not None else None,
            "t": 0.0, "sparks": sparks, "seed": rnd.random(),
        })

    def busy(self):
        return bool(self.fx)

    # ---------------- Update ----------------
    def update(self, dt):
        for f in list(self.fx):
            f["t"] += dt
            for s in f["sparks"]:
                s[0] *= (1.0 - 2.2 * dt)
                s[1] = s[1] * (1.0 - 2.2 * dt) + 60.0 * dt   # leichte Aufwaerts
                s[2] -= dt
            if f["t"] >= _DUR:
                self.fx.remove(f)

    def shake(self):
        """Dezenter Kameraimpuls 0..~3 px (nur in der Werft anwenden)."""
        if not self.fx:
            return (0, 0)
        f = max(self.fx, key=lambda e: e["t"])
        t = f["t"]
        if t >= 0.45:
            return (0, 0)
        k = (1.0 - t / 0.45)
        a = self.elapsed_phase(f)
        dx = math.sin(a * 46.0) * 3.0 * k
        dy = math.cos(a * 39.0) * 2.2 * k
        return (int(dx), int(dy))

    @staticmethod
    def elapsed_phase(f):
        return f["t"] * 7.0 + f["seed"] * 10.0

    # ---------------- Zeichnen ----------------
    def draw(self, surface):
        for f in self.fx:
            t = f["t"] / _DUR
            x, y, col = f["x"], f["y"], f["color"]
            # --- 1) Highlight-Ring am Modul (erste Haelfte) ---
            if t < 0.5:
                k = t / 0.5
                r1 = int(u(10) + k * u(26))
                pygame.draw.circle(surface, col, (int(x), int(y)), r1,
                                   max(1, u(2) - (1 if k > 0.7 else 0)))
                if k > 0.25:
                    pygame.draw.circle(surface, _mix_col(col, WHITE, 0.5),
                                       (int(x), int(y)), int(r1 * 0.66), 1)
            # --- 2) Energie-/Scan-Sweep ueber die Flaeche ---
            if f["rect"] is not None and _SCAN_T0 <= t <= _SCAN_T1:
                r = f["rect"]
                sk = (t - _SCAN_T0) / (_SCAN_T1 - _SCAN_T0)
                sx = int(r.x + sk * (r.w - 2))
                alpha = math.sin(min(1.0, sk) * math.pi)          # 0..1..0
                line = pygame.Surface((max(2, u(3)), r.h), pygame.SRCALPHA)
                line.fill((int(col[0]), int(col[1]), int(col[2]),
                           int(120 * alpha)))
                surface.blit(line, (sx, r.y))
                # heller Kern der Scanlinie + schwanz nach links
                core = pygame.Surface((max(1, u(1)), r.h), pygame.SRCALPHA)
                core.fill((255, 255, 255, int(180 * alpha)))
                surface.blit(core, (sx + u(1), r.y))
                trail = pygame.Surface((int(r.w * 0.16) + 1, r.h), pygame.SRCALPHA)
                for i in range(trail.get_width()):
                    a = int(46 * alpha * (1.0 - i / trail.get_width()))
                    pygame.draw.line(trail, (*col, a), (i, 0), (i, r.h))
                surface.blit(trail, (max(r.x, sx - trail.get_width()), r.y))
                # Energie-Flusspunkte entlang der Scanlinie
                for pj in range(3):
                    pt = (self.elapsed_phase(f) * 0.31 + pj / 3.0) % 1.0
                    py = r.y + int(pt * (r.h - 2))
                    g = radial_glow_k(col, u(5), 0.5 * alpha)
                    surface.blit(g, g.get_rect(center=(sx + u(1), py)),
                                 special_flags=pygame.BLEND_ADD)
            # --- 3) Lichtimpuls + Funken (Mitte) ---
            if 0.30 <= t <= 0.75:
                k = (t - 0.30) / 0.45
                g = radial_glow_k(_mix_col(col, WHITE, 0.35),
                                  int(u(26) + u(30) * k), 0.55 * (1.0 - k))
                surface.blit(g, g.get_rect(center=(int(x), int(y))),
                             special_flags=pygame.BLEND_ADD)
                pr = int(u(6) + u(40) * k)
                pygame.draw.circle(surface, col, (int(x), int(y)), pr,
                                   max(1, u(2) - (1 if k > 0.6 else 0)))
            if t <= 0.75:
                for s in f["sparks"]:
                    if s[2] <= 0:
                        continue
                    px = x + s[0] * f["t"]
                    py = y + s[1] * f["t"]
                    c = _mix_col(col, WHITE, 0.35) if s[2] > 0.25 else col
                    pygame.draw.circle(surface, c, (int(px), int(py)),
                                       max(1, u(1.6)))
            # --- 4) Neue Stufe als aufsteigender Text ---
            if 0.35 <= t:
                k = (t - 0.35) / 0.65
                a = max(0.0, 1.0 - k)
                fnt = F(13)
                img = fnt.render(f"LVL {f['level']}", True, WHITE)
                img.set_alpha(int(255 * a))
                ty = y - u(18) - int(k * u(26))
                surface.blit(img, img.get_rect(midbottom=(int(x), int(ty))))
                sub = fnt.render(f"{f['key'].upper()} AUFGERUESTET", True, col)
                sub.set_alpha(int(200 * a))
                surface.blit(sub, sub.get_rect(midtop=(int(x), int(ty))))
