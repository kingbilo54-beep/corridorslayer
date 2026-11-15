# =====================================================================
# CORRIDOR SLAYER - PAKET 8.3: DAMAGE-FX AM SCHIFF
# ---------------------------------------------------------------------
# Wenn das Schiff Schaden nimmt, wurde bisher nur eine Schadenszahl und
# ein Sound gezeigt. Diese Datei ergibt jeden Treffer eine sichtbare
# Reaktion AM SCHIFF:
#
#   * Einschlags-Explosion (Funken orange/rot/weiss + Rauch)
#   * expandierender Schockwellen-Ring
#   * kurzer Weiß-/Orange-Flash am Trefferpunkt
#   * dezenter Screen-Shake (staerke = Schaden)
#   * rote Vignette kurz nach Treffern + unter 30% Huelle
#   * Glut-/Rauchpartikel aus dem Schiff bei kritischer Huelle
#
# Bewusst EIGENhaendig (neue Datei + eigene Partikellisten), damit die
# combat_fx.py des Nutzers (Paket 6) unveraendert bleibt und sich nichts
# in die Quere kommt. main.py ruft nur:
#     damage_fx.update(dt, combat, ship_world_xy)
#     damage_fx.draw_world(...)   # in _draw_world, ueber self.fx.draw
#     damage_fx.draw_vignette(SCREEN)  # nach dem Welt-Rendering
#     ox += damage_fx.shake_x     # in draw_playing
# =====================================================================
import math
import random

import pygame

try:
    from ui_kit import radial_glow_k
except Exception:                                    # Fallback (headless)
    def radial_glow_k(color, radius, k=1.0):
        kb = round(max(0.05, min(1.0, k)) * 10) / 10.0
        c = (int(color[0] * kb), int(color[1] * kb), int(color[2] * kb))
        r = max(2, int(radius))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for i in range(r, 0, -2):
            a = int(255 * (1 - i / r) * 0.55)
            pygame.draw.circle(s, (*c, a), (r, r), i)
        return s


class _Spark:
    """Ein Funken/Rauch-Partikel in WELT-Koordinaten (wie die Gegner)."""
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size",
                 "color", "drag", "grav", "smoke")

    def __init__(self, x, y, vx, vy, life, size, color,
                 drag=1.8, grav=0.0, smoke=False):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.size = size
        self.color = color
        self.drag = drag
        self.grav = grav
        self.smoke = smoke


class _Ring:
    """Expandierender Schockwellen-Ring am Trefferpunkt."""
    __slots__ = ("x", "y", "life", "max_life", "r0", "r1", "color")

    def __init__(self, x, y, r0, r1, life, color):
        self.x, self.y = x, y
        self.r0, self.r1 = r0, r1
        self.life = self.max_life = life
        self.color = color


# Farben (passend zur Dark-Sci-Fi-Palette des Spiels)
FIRE_HOT = (255, 236, 170)
FIRE_MID = (255, 168, 64)
FIRE_DARK = (228, 78, 36)
SPARK_CYAN = (150, 240, 255)      # Schild-/Energieanteil
SMOKE_COL = (70, 66, 74)
EMBER_COL = (255, 120, 50)


class DamageFX:
    """Sammelt Treffer-Ereignisse des Kampfes und spielt die Schiff-
    Einschlags-Optik ab (siehe Dateikopf)."""

    def __init__(self):
        self.sparks = []
        self.rings = []
        self.flashes = []            # (x, y, life, max_life, radius)
        self.shake_x = 0.0
        self.shake_y = 0.0
        self._shake_amp = 0.0
        self.hurt_vignette = 0.0     # 0..1 Sichtbarkeit der roten Vignette
        self._ember_timer = 0.0
        self._vig_vignette = None    # gecachte Vignette-Surface
        self._rng = random.Random(8304)

    # ---------------- Ereignisse aus dem Kampf ----------------
    def collect(self, combat):
        """Nimmt hit_events aus dem Kampf entgegen (Welt-Koordinaten).
        Die Liste im Kampf wird geleert, damit nichts doppelt kommt."""
        ev = getattr(combat, "hit_events", None)
        if not ev:
            return
        for (hx, hy, dmg) in ev[-16:]:
            self.impact(hx, hy, float(dmg))
        del ev[:]

    def impact(self, wx, wy, dmg=10.0):
        """Einschlag am Punkt (Welt-Koordinaten). dmg steuert Groesse."""
        rng = self._rng
        power = max(0.35, min(2.2, dmg / 14.0))
        n_spark = int(14 + 10 * power)
        for _ in range(n_spark):
            a = rng.uniform(0, math.tau)
            sp = rng.uniform(40, 210) * power
            col = rng.choice((FIRE_HOT, FIRE_MID, FIRE_MID,
                              FIRE_DARK, SPARK_CYAN))
            self.sparks.append(_Spark(
                wx, wy, math.cos(a) * sp, math.sin(a) * sp,
                rng.uniform(0.22, 0.5), rng.uniform(1.5, 3.4) * power,
                col, drag=2.2))
        for _ in range(3 + int(2 * power)):          # Rauch
            a = rng.uniform(0, math.tau)
            sp = rng.uniform(10, 46)
            self.sparks.append(_Spark(
                wx, wy, math.cos(a) * sp, math.sin(a) * sp - 12.0,
                rng.uniform(0.5, 0.95), rng.uniform(4, 9) * power,
                SMOKE_COL, drag=1.1, grav=-26.0, smoke=True))
        rad = 26 + 16 * power
        self.rings.append(_Ring(wx, wy, 4.0, rad * 2.4, 0.32,
                                (255, 190, 120)))
        self.rings.append(_Ring(wx, wy, 2.0, rad * 1.4, 0.22,
                                (160, 235, 255)))
        self.flashes.append((wx, wy, 0.16, 0.16, rad))
        self._shake_amp = min(7.0, self._shake_amp + 1.6 + 1.3 * power)
        self.hurt_vignette = min(1.0, self.hurt_vignette + 0.55)

    # ---------------- Update ----------------
    def update(self, dt, combat=None, ship_world=(0.0, 0.0)):
        self.collect(combat)

        # Screen-Shake abklingen lassen
        self._shake_amp = max(0.0, self._shake_amp - dt * 14.0)
        if self._shake_amp > 0.05:
            a = self._shake_amp
            self.shake_x = self._rng.uniform(-a, a)
            self.shake_y = self._rng.uniform(-a, a) * 0.7
        else:
            self.shake_x = self.shake_y = 0.0

        # Vignette abklingen
        self.hurt_vignette = max(0.0, self.hurt_vignette - dt * 1.6)

        # Kritische Huelle: Glut + Rauch aus dem Schiff
        if combat is not None and not getattr(combat, "is_idle", False):
            hp = getattr(combat, "player_hp", 1.0)
            mx = max(1.0, getattr(combat, "max_player_hp", 1.0))
            crit = hp / mx <= 0.30 and hp > 0
            if crit:
                self.hurt_vignette = max(self.hurt_vignette,
                                         0.22 + 0.10 * math.sin(hp * 0.0))
                self._ember_timer -= dt
                if self._ember_timer <= 0:
                    self._ember_timer = self._rng.uniform(0.05, 0.16)
                    sx, sy = ship_world
                    wx = sx + self._rng.uniform(-16, 20)
                    wy = sy + self._rng.uniform(-10, 12)
                    col = self._rng.choice((EMBER_COL, (255, 190, 90),
                                            SMOKE_COL))
                    self.sparks.append(_Spark(
                        wx, wy,
                        self._rng.uniform(-14, 14), self._rng.uniform(-52, -20),
                        self._rng.uniform(0.4, 0.9),
                        self._rng.uniform(2, 4.5), col,
                        drag=0.6, grav=-14.0,
                        smoke=(col is SMOKE_COL)))

        # Partikel integrieren
        for p in self.sparks:
            p.life -= dt
            d = max(0.0, 1.0 - p.drag * dt)
            p.vx *= d
            p.vy = p.vy * d + p.grav * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
        self.sparks = [p for p in self.sparks if p.life > 0]
        for r in self.rings:
            r.life -= dt
        self.rings = [r for r in self.rings if r.life > 0]
        self.flashes = [(x, y, l - dt, ml, rad)
                        for (x, y, l, ml, rad) in self.flashes if l - dt > 0]

    # ---------------- Zeichnen (Welt-Ebene) ----------------
    def draw_world(self, surface, T, elapsed=0.0):
        """Partikel/Ringe/Flash in Welt-Koordinaten zeichnen (T = Mapper)."""
        for r in self.rings:
            k = 1.0 - r.life / max(0.001, r.max_life)
            rad = (r.r0 + (r.r1 - r.r0) * k)
            x, y = T(r.x, r.y)
            a = int(190 * (1.0 - k))
            if a <= 4 or rad < 1:
                continue
            pygame.draw.circle(surface, r.color, (int(x), int(y)),
                               int(rad), max(1, int(3 * (1 - k))))
        for p in self.sparks:
            k = p.life / max(0.001, p.max_life)
            x, y = T(p.x, p.y)
            if p.smoke:
                a = int(90 * k)
                rad = max(1, int(p.size * (1.6 - 0.6 * k)))
                s = pygame.Surface((rad * 2, rad * 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*p.color, a), (rad, rad), rad)
                surface.blit(s, (int(x) - rad, int(y) - rad))
            else:
                c = tuple(int(ch * (0.45 + 0.55 * k)) for ch in p.color)
                pygame.draw.circle(surface, c, (int(x), int(y)),
                                   max(1, int(p.size * (0.5 + 0.5 * k))))
        for (x, y, life, ml, rad) in self.flashes:
            k = life / max(0.001, ml)
            g = radial_glow_k((255, 200, 120), int(rad * 2.2), 0.25 + 0.65 * k)
            gx, gy = T(x, y)
            surface.blit(g, g.get_rect(center=(int(gx), int(gy))),
                         special_flags=pygame.BLEND_ADD)

    # ---------------- Zeichnen (Bildschirm-Ebene) ----------------
    def draw_vignette(self, surface):
        """Rote Rand-Vignette nach Treffern / bei kritischer Huelle."""
        v = self.hurt_vignette
        if v <= 0.02:
            return
        w, h = surface.get_size()
        key = (w, h)
        if self._vig_vignette is None or self._vig_vignette[0] != key:
            base = pygame.Surface((w, h), pygame.SRCALPHA)
            # Rahmen-Glow: vier weiche Kanten (Billig-Vignette via Ringe)
            cx, cy = w // 2, h // 2
            maxr = math.hypot(cx, cy)
            steps = 26
            for i in range(steps, 0, -1):
                k = i / steps                      # 1=Rand, 0=Zentrum
                rad = int(maxr * k)
                a = int(120 * (k ** 2.2))
                pygame.draw.circle(base, (255, 30, 44, a), (cx, cy), rad)
            self._vig_vignette = (key, base)
        vig = self._vig_vignette[1].copy()
        vig.fill((255, 40, 50, int(255 * min(0.5, v * 0.5))),
                 special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(vig, (0, 0))
