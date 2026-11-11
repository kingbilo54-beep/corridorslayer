# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 8.7: FEUER-BESCHAEDIGUNG AM SCHIFF
============================================================
Nutzer-Feedback: "Das Schiff soll etwas brennen, sobald es unter der
Haelfte des Lebens hat."

BurnFX ist ein Partikel-Overlay, das im aktiven Gefecht an zufaelligen
Rumpfpunkten Flammen, Funken und Rauch erzeugt:

  HP > 50 %  : aus (kein Partikel)
  50-25 %    : kleine Flammen, wenige (Schwoelen)
  25-10 %    : deutliche Flammen + erste Funken (Brand)
  < 10 %     : Vollbrand - grosse Flammen, Funken, dunkler Rauch

update() bekommt die Schiffsposition in Weltkoordinaten und haelt alle
Partikel ABSOLUT in Weltkoordinaten (neu entstehende Partikel kleben am
aktuellen Rumpfpunkt). draw() transformiert sie ueber T(x, y) auf den
Screen - genau wie Gegner/Projektile in main._draw_world. Das Partikel-
Budget ist klein gehalten (< 120 Partikel), damit es auf dem Handy
performt.
"""
import math
import random

import pygame


class BurnFX:
    START = 0.50          # HP-Anteil: ab hier schwoelt das Schiff
    HEAVY = 0.25          # ab hier brennt es deutlich
    CRIT = 0.10           # ab hier Vollbrand (Funken + Rauch)

    MAX_FLAMES = 64
    MAX_SPARKS = 40
    MAX_SMOKE = 26

    def __init__(self):
        self.flames = []   # [x, y, vx, vy, age, life, size, flicker]
        self.sparks = []   # [x, y, vx, vy, life, max_life]
        self.smoke = []    # [x, y, vx, vy, life, max_life, r0]
        self.ratio = 1.0
        self._acc = 0.0
        self._rnd = random.Random()

    # ---------------- Update ----------------
    def update(self, dt, hp_ratio, ship_xy, angle=0.0):
        """hp_ratio: 0..1 - ship_xy: Weltposition des Schiffs."""
        self.ratio = max(0.0, min(1.0, float(hp_ratio)))
        sx, sy = float(ship_xy[0]), float(ship_xy[1])
        r = self.ratio

        # Spawnrate (Partikel/s) je Schweregrad
        if r >= self.START:
            rate = 0.0
        elif r < self.CRIT:
            rate = 24.0
        elif r < self.HEAVY:
            rate = 14.0
        else:
            rate = 9.0

        self._acc += rate * dt
        while self._acc >= 1.0:
            self._acc -= 1.0
            if len(self.flames) < self.MAX_FLAMES:
                # Rumpfpunkt (Schiffsrumpf ~ 64x36 Weltpixel, Ellipse)
                ang = self._rnd.uniform(0.0, math.tau)
                rr = math.sqrt(self._rnd.random())
                ox = math.cos(ang) * 30.0 * rr
                oy = math.sin(ang) * 17.0 * rr - 2.0
                if r < self.CRIT:
                    size = self._rnd.uniform(7.0, 13.0)
                    life = self._rnd.uniform(0.45, 0.75)
                elif r < self.HEAVY:
                    size = self._rnd.uniform(5.0, 9.0)
                    life = self._rnd.uniform(0.40, 0.65)
                else:
                    size = self._rnd.uniform(3.5, 6.5)
                    life = self._rnd.uniform(0.35, 0.55)
                self.flames.append([sx + ox, sy + oy,
                                    self._rnd.uniform(-6, 6),
                                    -(14.0 + self._rnd.uniform(0, 16)),
                                    0.0, life, size,
                                    self._rnd.uniform(0.0, math.tau)])

        cos_a, sin_a = math.cos(angle), math.sin(angle)
        for f in list(self.flames):
            f[4] += dt                       # age
            f[0] += f[2] * dt
            f[1] += f[3] * dt
            f[2] += math.sin(f[4] * 9.0 + f[7]) * 22.0 * dt   # Flackern
            if f[4] >= f[5]:
                self.flames.remove(f)
                ex, ey = f[0], f[1]
                # Funken (ab "Brand") und Rauch (nur Vollbrand)
                if r < self.HEAVY and len(self.sparks) < self.MAX_SPARKS \
                        and self._rnd.random() < 0.30:
                    self.sparks.append([ex, ey,
                                        self._rnd.uniform(-34, 34),
                                        self._rnd.uniform(-95, -45),
                                        self._rnd.uniform(0.25, 0.5), 0.5])
                if r < self.CRIT and len(self.smoke) < self.MAX_SMOKE \
                        and self._rnd.random() < 0.35:
                    self.smoke.append([ex, ey,
                                       self._rnd.uniform(-12, 12),
                                       self._rnd.uniform(-44, -26),
                                       self._rnd.uniform(0.7, 1.2), 1.2,
                                       self._rnd.uniform(4, 8)])

        for p in list(self.sparks):
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 130.0 * dt               # Gravitation
            p[4] -= dt
            if p[4] <= 0:
                self.sparks.remove(p)

        for p in list(self.smoke):
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
            if p[4] <= 0:
                self.smoke.remove(p)

    # ---------------- Draw ----------------
    def draw(self, surface, T, s, elapsed):
        """T(x, y) = Welt->Screen-Transformation, s = Welt->Screen-Faktor."""
        if self.ratio >= self.START or (not self.flames and not self.sparks
                                        and not self.smoke):
            return

        # 1) Rauch (hinter allem)
        for p in self.smoke:
            x, y = T(p[0], p[1])
            k = 1.0 - max(0.0, p[4]) / p[5]
            rad = max(1, int((p[6] + 11.0 * k) * s))
            a = int(44 * (1.0 - k))
            if a > 4:
                puff = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                pygame.draw.circle(puff, (30, 28, 32, a), (rad, rad), rad)
                surface.blit(puff, (int(x) - rad, int(y) - rad))

        # 2) Flammen (additiv wirken sie wie echtes Feuer)
        for f in self.flames:
            x, y = T(f[0], f[1])
            k = f[4] / f[5]
            flick = 0.84 + 0.16 * math.sin(elapsed * 21.0 + f[7])
            rad = max(1, int(f[6] * (0.55 + 0.75 * k) * flick * s))
            if k < 0.35:
                col = (255, int(216 + 39 * (1.0 - k / 0.35)), 96)
            elif k < 0.7:
                kk = (k - 0.35) / 0.35
                col = (255, int(170 - 70 * kk), int(96 - 60 * kk))
            else:
                kk = (k - 0.7) / 0.3
                col = (int(200 - 80 * kk), 62, 32)
            flame = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(flame, (*col, 205), (rad, rad), rad)
            core = max(1, int(rad * 0.42))
            pygame.draw.circle(flame, (255, 244, 198, 230),
                               (rad, rad + core // 2), core)
            surface.blit(flame, (int(x) - rad, int(y) - rad))

        # 3) Funken
        for p in self.sparks:
            x, y = T(p[0], p[1])
            k = max(0.0, p[4]) / p[5]
            rad = max(1, int(2.3 * s * (0.5 + 0.5 * k)))
            sp = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
            pygame.draw.circle(sp, (255, 202, 92, int(235 * k)),
                               (rad, rad), rad)
            surface.blit(sp, (int(x) - rad, int(y) - rad))
