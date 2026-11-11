# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 8.8/8.8b: LEBENDIGER HINTERGRUND (BG-FX)
==============================================================
Nutzer-Feedback: "Koennest du das Background dynamisch machen? Das
aktuelle Bild verwenden und evtl. die Flammen bewegen sich o.Ae."
(8.8b: "Kannst du die Flammen im Hintergrund irgendwie animieren?")

Das Kapitel-Bild bleibt UNVERAENDERT als Basis. Darueber liegen fuenf
guenstige Animations-Ebenen, die die Szene lebendig machen:

  1. STERNENSTAUB (2 Ebenen, Parallax):
     zwei vorgerenderte Punktfelder ziehen langsam nach links,
     unterschiedliche Geschwindigkeiten -> Tiefengefuehl.
  2. NEBEL-LICHTER (3 Blobs):
     grosse, sehr dezente weiche Farblichter treiben langsam und
     "atmen" in der Helligkeit (3 vorgebaute Intensitaetsstufen).
  3. GLUT-/FUNKEN-PARTIKEL ("Flammen bewegen sich"):
     ~26 glimmende Funken steigen vom unteren Bildrand auf und schweben
     sinusfaermig seitlich - wie Feuerglut / Plasmaflocken. Farbe je
     Kapitel (1: Eis-Cyan, 2: Violett-Magenta, 3: Feuer-Orange).
  4. BODENSCHEIN:
     dezenter, pulsierender Lichtstreifen am unteren Arenarand.
  5. FEUERZUNGEN (NEU 8.8b - die gemalten Flammen "brennen" jetzt):
     ~12 Feuerstellen am unteren Bildrand pulsieren mit weichem
     Grundglow, darueber zuckt je eine Flammenzunge (3 Flackerstufen,
     leichtes Schwanken) - das brennende Kapitel-Bild lebt.

Technik (bewusst wie ui_kit.radial_glow):
  * Alle Lichtflaechen sind RGB-nach-Schwarz (Farbe Vorskaliert nach
    Intensitaet) und werden mit BLEND_ADD geblendet - BLEND_ADD ignoriert
    Alpha, deshalb KEINE Alpha-Kanaele in den Lichtern (keine harten
    Raender, kein Alpha-Stacking).
  * Puls/Atmen ueber je 3 vorgerenderte Helligkeitsstufen statt
    set_alpha pro Frame.
  * Alle Flaeche gecacht; pro Frame nur Blits. Partikelbudget fest
    (26 Funken + 12 Feuerstellen).
  * Sternenstaub-Felder auf 1280 px Breite gekappt und gekachelt.
  * update(dt) klemmt dt auf 0.1 s (kein Sprung nach Pause/Resume).

API:
    fx = BgFX()
    fx.set_stage(stage_id)          # Kapitelpalette 0/1/2 (Stufe 1-5/6-10/11-15)
    fx.update(dt)                   # im Spieltick
    fx.draw(surface, T, s, elapsed) # in _draw_world, direkt nach dem BG-Bild
                                    # T(x, y) = Welt->Screen, s = Welt->Screen
"""
import math
import random

import pygame

WORLD_W = 960.0
WORLD_H = 540.0

# Kapitel-Paletten (Index = Kapitel: Stufe 1-5 / 6-10 / 11-15)
PALETTES = [
    # Kapitel 1: kaltes Eis-Cyan
    {"embers": ((120, 210, 235), (95, 150, 235), (150, 230, 220)),
     "nebula": ((30, 95, 130), (55, 65, 150), (35, 115, 115)),
     "floor": (40, 130, 175)},
    # Kapitel 2: Violett / Magenta
    {"embers": ((205, 120, 230), (145, 95, 230), (225, 165, 220)),
     "nebula": ((115, 45, 145), (75, 40, 160), (140, 45, 120)),
     "floor": (145, 65, 180)},
    # Kapitel 3: Feuer / Glut
    {"embers": ((230, 145, 65), (225, 95, 45), (235, 195, 135)),
     "nebula": ((160, 65, 30), (130, 40, 55), (180, 95, 35)),
     "floor": (205, 100, 45)},
]

EMBER_N = 26
FIRE_N = 12                # PAKET 8.8b: Feuerstellen unten (Flammenzungen)
DUST_MAX_W = 1280          # Sternenstaub-Feld-Breitenlimit (gekachelt)
BLOB_MAX = 300             # Nebel-Blob-Radius-Limit (px)

# PAKET 8.8b: Flammen-Farben (warm, in jedem Kapitel passend - Feuer ist
# Feuer). Von aussen (dunkelrot) nach innen (gelb-weiss).
FIRE_COLS = ((150, 40, 15), (235, 95, 30), (255, 190, 90), (255, 240, 200))


def _flame_sprite(k=1.0):
    """Eine Flammenzunge als RGB-nach-Schwarz-Sprite (BLEND_ADD).
    Klassische Zungenform: 4 gestapelte Kreise, nach oben schmaler und
    heller. k = Helligkeit (Flackerstufe 0..2 -> 0.55/0.80/1.05)."""
    w, h = 30, 52
    surf = pygame.Surface((w, h))
    surf.fill((0, 0, 0))
    cx = w // 2
    stack = ((h - 11, 11, 0), (h - 20, 8, 1), (h - 28, 5.5, 2), (h - 34, 3, 3))
    for i, (yy, rr, ci) in enumerate(stack):
        col = FIRE_COLS[ci]
        f = k * (1.0 - 0.13 * i)
        pygame.draw.circle(surf, (int(col[0] * f), int(col[1] * f),
                                  int(col[2] * f)),
                           (int(cx + (i % 2 - 0.5) * 1.2), yy), max(1, int(rr)))
    return pygame.transform.smoothscale(surf, (w, int(h * 1.25)))


def _glow_surf(color, radius, k=1.0):
    """Weiches Glueh-Sprite, RGB nach Schwarz (wie ui_kit.radial_glow).
    k = Intensitaet 0..1 - Farbe ist Vorskaliert, Flaeche opak."""
    r = max(6, int(radius))
    surf = pygame.Surface((r * 2, r * 2))
    surf.fill((0, 0, 0))
    steps = max(8, r // 2)
    for i in range(steps, 0, -1):
        rr = max(1, int(r * i / steps))
        f = (1.0 - i / steps) ** 2.4 * k
        if f <= 0.004:
            continue
        pygame.draw.circle(surf, (int(color[0] * f), int(color[1] * f),
                                  int(color[2] * f)), (r, r), rr)
    return surf


class BgFX:
    def __init__(self):
        self.t = 0.0
        self._pidx = -1
        self._pal = PALETTES[0]
        self._size_key = None      # (aw, ah) der letzten Flaechen-Gen
        self._dust = []            # [(surf, speed_world_px_s)]
        self._blobs = []           # [(surf, gx, gy (Anteil Welt), amp, phase)]
        self._floor_variants = []  # 3 Helligkeitsstufen (RGB-nach-Schwarz)
        self._ember_gfx = []       # 3 Toene x 3 Helligkeitsstufen
        self.fires = []            # PAKET 8.8b: Feuerstellen unten
        self._fire_gfx = []        # je Feuerstelle: 3 Flackerstufen
        self._fire_glow = None     # Grundglow (warm, pulsierend)
        self.embers = []           # [x, y, vy, sway, phase, size, tone]
        self._rnd = random.Random(88)
        for _ in range(EMBER_N):
            self.embers.append([
                self._rnd.uniform(0.0, WORLD_W),
                self._rnd.uniform(0.0, WORLD_H),
                self._rnd.uniform(-34.0, -13.0),
                self._rnd.uniform(8.0, 26.0),
                self._rnd.uniform(0.0, math.tau),
                self._rnd.uniform(0.55, 1.5),
                self._rnd.randrange(3),
            ])
        # PAKET 8.8b: Feuerstellen gleichmaessig ueber die Bildbreite
        # streuen (leicht verrutscht), im unteren Band - dort liegen in
        # den Kapitel-Bildern die brennenden Truemmer/Feuer.
        for i in range(FIRE_N):
            self.fires.append({
                "x": (i + 0.5) * WORLD_W / FIRE_N
                     + self._rnd.uniform(-26.0, 26.0),
                "y": WORLD_H * self._rnd.uniform(0.80, 0.94),
                "ph": self._rnd.uniform(0.0, math.tau),
                "spd": self._rnd.uniform(4.5, 8.5),     # Flacker-Tempo
                "sz": self._rnd.uniform(0.75, 1.45),    # Zungen-Groesse
                "sway": self._rnd.uniform(1.5, 4.0),    # seitliches Schwanken
            })

    # ---------------- Palette ----------------
    def set_stage(self, stage_id):
        """Kapitelpalette waehlen (gleiches Mapping wie das Kapitel-Bild)."""
        st = max(1, int(stage_id or 1))
        idx = 0 if st <= 5 else (1 if st <= 10 else 2)
        if idx != self._pidx:
            self._pidx = idx
            self._pal = PALETTES[idx]
            self._size_key = None            # Flaechen neu faerben

    # ---------------- Update ----------------
    def update(self, dt):
        if dt <= 0.0:
            return
        dt = min(0.1, dt)                    # Pause/Resume-Spruenge klemmen
        self.t += dt
        for e in self.embers:
            e[1] += e[2] * dt                # aufsteigen
            e[4] += dt                       # Phase
            if e[1] < -24.0:
                e[0] = self._rnd.uniform(0.0, WORLD_W)
                e[1] = WORLD_H + self._rnd.uniform(6.0, 42.0)
                e[2] = self._rnd.uniform(-34.0, -13.0)
                e[3] = self._rnd.uniform(8.0, 26.0)
                e[5] = self._rnd.uniform(0.55, 1.5)
                e[6] = self._rnd.randrange(3)

    # ---------------- Flaechen (lazy, gecacht) ----------------
    def _build(self, aw, ah, s):
        pal = self._pal
        self._size_key = (aw, ah, self._pidx)

        # 1) Sternenstaub: 2 gekachelte Punktfelder (SRCALPHA, Normal-Blit)
        self._dust = []
        for layer, (n_dots, speed, a_hi) in enumerate(((110, 7.0, 70),
                                                       (70, 17.0, 105))):
            tw = max(320, min(DUST_MAX_W, aw))
            th = max(220, ah)
            field = pygame.Surface((tw, th), pygame.SRCALPHA)
            rnd = random.Random(411 + layer)
            for _ in range(n_dots):
                x = rnd.uniform(0, tw)
                y = rnd.uniform(0, th)
                r = rnd.choice((1, 1, 1, 2))
                a = rnd.randint(max(18, a_hi // 3), a_hi)
                shade = rnd.choice((200, 225, 255))
                pygame.draw.circle(field, (shade, shade, min(255, shade + 12), a),
                                   (int(x), int(y)), r)
            self._dust.append((field, speed))

        # 2) Nebel-Lichter: 3 dezente Blobs (RGB nach Schwarz, BLEND_ADD)
        self._blobs = []
        br = int(max(110, min(BLOB_MAX, ah * 0.55)))
        for i, col in enumerate(pal["nebula"]):
            self._blobs.append((_glow_surf(col, br, 0.26),
                                0.12 + 0.38 * i,            # Grund-x (Welt)
                                0.22 + 0.24 * ((i + 1) % 2),  # Grund-y
                                70.0 + 34.0 * i,            # Drift (Welt-px)
                                i * 2.1))                   # Phase

        # 3) Bodenschein: Streifen unten hell -> oben weich auslaufend.
        #    3 Intensitaetsstufen = Puls ohne set_alpha (BLEND_ADD).
        fh = max(24, int(54 * s))
        self._floor_variants = []
        for k in (0.72, 1.0, 1.26):
            floor = pygame.Surface((max(320, int(aw)), fh))
            floor.fill((0, 0, 0))
            fc = pal["floor"]
            for y in range(fh):
                row = (y / max(1, fh - 1)) ** 2 * (0.175 * k)   # unten hell
                if row > 0.004:
                    pygame.draw.line(floor,
                                     (int(fc[0] * row), int(fc[1] * row),
                                      int(fc[2] * row)),
                                     (0, y), (floor.get_width() - 1, y))
            self._floor_variants.append(floor)

        # 4) Funken-Glow: 3 Farbtone x 3 Helligkeitsstufen (RGB nach Schwarz)
        self._ember_gfx = []
        for col in pal["embers"]:
            trio = tuple(_glow_surf(col, 7, k) for k in (0.36, 0.64, 1.0))
            self._ember_gfx.append(trio)

        # 5) PAKET 8.8b: FEUERZUNGEN - je Feuerstelle 3 Flackerstufen
        #    (vor-skaliert auf die Zungen-Groesse) + ein gemeinsamer
        #    warmer Grundglow. Alles RGB-nach-Schwarz (BLEND_ADD).
        self._fire_gfx = []
        flick = (0.55, 0.80, 1.05)
        for fr in self.fires:
            base_w = max(10, int(30 * fr["sz"] * s))
            base_h = max(16, int(65 * fr["sz"] * s))
            trio = []
            for k in flick:
                sp = _flame_sprite(k)
                trio.append(pygame.transform.smoothscale(sp, (base_w, base_h)))
            self._fire_gfx.append(trio)
        self._fire_glow = _glow_surf((255, 110, 30), max(40, int(70 * s)), 0.30)

    # ---------------- Draw ----------------
    def draw(self, surface, T, s, elapsed):
        x0, y0 = T(0.0, 0.0)
        x1, y1 = T(WORLD_W, WORLD_H)
        aw, ah = int(x1 - x0), int(y1 - y0)
        if aw <= 8 or ah <= 8:
            return
        if self._size_key != (aw, ah, self._pidx):
            self._build(aw, ah, s)

        clip = surface.get_clip()
        if clip:
            surface.set_clip(clip.clip(pygame.Rect(int(x0), int(y0), aw, ah)))

        # 1) Nebel-Lichter (langsam treibend; Atmen ueber Blit-Faktor):
        #    dezent - grosse weiche Farbe oben "unter" dem Staub.
        for i, (surf, gx, gy, amp, ph) in enumerate(self._blobs):
            bx = x0 + gx * aw + math.sin(self.t * 0.11 + ph) * amp * s
            by = y0 + gy * ah + math.cos(self.t * 0.09 + ph * 1.7) * (amp * 0.5) * s
            surface.blit(surf, surf.get_rect(center=(int(bx), int(by))),
                         special_flags=pygame.BLEND_ADD)

        # 2) Sternenstaub (2 Ebenen, gekachelt nach links driftend)
        for field, speed in self._dust:
            tw, th = field.get_size()
            ty = int(y0) + (ah - th) // 2
            off = (self.t * speed * s) % tw
            tx = int(x0) - int(off)
            while tx < int(x0) + aw:
                surface.blit(field, (tx, ty))
                tx += tw

        # 3) Bodenschein (pulsierend via 3 Stufen, additiv)
        if self._floor_variants:
            pulse = 0.5 + 0.5 * math.sin(self.t * 0.8)
            idx = 0 if pulse < 0.38 else (1 if pulse < 0.76 else 2)
            floor = self._floor_variants[idx]
            fw = floor.get_width()
            fy = int(y1) - floor.get_height()
            fx = int(x0)
            while fx < int(x1):
                surface.blit(floor, (fx, fy), special_flags=pygame.BLEND_ADD)
                fx += fw

        # 4) Glut-/Funken-Partikel (aufsteigend, schwebend, flackernd)
        for e in self.embers:
            ex = e[0] + math.sin(e[4] * e[3] * 0.14) * e[3]
            ey = e[1]
            flick = 0.5 + 0.5 * math.sin(self.t * (3.0 + e[5] * 2.4) + e[4])
            lvl = 0 if flick < 0.38 else (1 if flick < 0.76 else 2)
            gfx = self._ember_gfx[e[6]][lvl]
            gx, gy = T(ex, ey)
            surface.blit(gfx, gfx.get_rect(center=(int(gx), int(gy))),
                         special_flags=pygame.BLEND_ADD)

        # 5) PAKET 8.8b: FEUERZUNGEN - die gemalten Flammen unten
        #    "brennen" jetzt: die Zunge zuckt zwischen 3 Flackerstufen
        #    und schwankt seitlich, der Grundglow atmet langsam.
        if self._fire_gfx and self._fire_glow:
            glow_on = math.sin(self.t * 1.15) > 0.25   # Grundglow pulsiert
            glow = self._fire_glow
            for i, fr in enumerate(self.fires):
                gx, gy = T(fr["x"], fr["y"])
                flick = 0.5 + 0.5 * math.sin(self.t * fr["spd"] + fr["ph"])
                lvl = 0 if flick < 0.42 else (1 if flick < 0.80 else 2)
                spr = self._fire_gfx[i][lvl]
                wob = math.sin(self.t * fr["spd"] * 0.63 + fr["ph"] * 1.7) \
                    * fr["sway"] * s
                if glow_on:
                    surface.blit(glow, glow.get_rect(
                        center=(int(gx), int(gy - 4 * s))),
                        special_flags=pygame.BLEND_ADD)
                surface.blit(spr, spr.get_rect(
                    center=(int(gx + wob), int(gy))),
                    special_flags=pygame.BLEND_ADD)

        if clip:
            surface.set_clip(clip)
