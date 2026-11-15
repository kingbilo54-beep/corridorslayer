# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | ORTS-SZENEN & ZOOM-NAVIGATION (PAKET 7F)
==============================================================
Die Kampagnen-Weltkarte wird zur interaktiven Navigation ausgebaut:

  * Jeder Planet / jede Station / jedes Kampagnen-Signal der Karte
    (world_map.OBJECTS) ist anklickbar und hat GENAU EINEN Eintrag in
    LOCATIONS (datengetrieben -> neue Orte = neuer Dict-Eintrag, keine
    neue Logik).
  * Antippen startet eine fluessige Zoom-Animation (easeInOut) direkt
    zum Objekt; die Kamera faehrt von der Vollansicht in den Ort. Die
    Zoom-Quelle (Weltkarte + Rand-Sternfeld) wird einmalig gecacht,
    pro Animationsframe entsteht nur EIN smoothscale.
  * Danach blendet eine EIGENE Szenerie ein (separates Hintergrundbild
    pro Ort aus scenes/<scene>), die per Konfiguration lebendig wirkt:
    Staub-Partikel, Nebel-Glows, Blinklichter, Radar-Sweep, Patrouillen-
    schiffe, Funken und Blitze - alles prozedural, keine Extra-Assets.
    Fehlt ein Bild, entsteht ein prozeduraler Ort in der Akzentfarbe.
  * Nach dem Einschwenken erscheint das Orts-Panel: Typ, Status,
    Story, VERFUEGBARE KAEMPFE (naechster Einsatz / Elite / Boss) und
    Buttons KAMPF STARTEN / STUFEN / Zurueck. Der Kampfstart laeuft
    ueber die BEKANNTEN main.py-Pfade (_map_action -> _try_enter_stage);
    "STUFEN" oeffnet das vorhandene Stufen-Sheet. Das Kampagnensystem
    bleibt unveraendert, Hangar/Werft/Nexus tauchen nicht auf.
  * "Zurueck" (X, ESC oder leerer Tap) spielt den Zoom rueckwaerts zur
    Karte (weiche Uebergaenge in beide Richtungen).

Diese Datei kennt KEINE Spielmechanik: main.py liefert Statusdaten und
das gefuellte info-Dict (battles/primary/second), hier passieren nur
Kamera, Szenerie, Effekte, Panel und Hit-Testing.
"""
import math
import os
import random
import pygame
import ui_kit
from ui_kit import (u, F, text, neon_text, radial_glow, glass_panel,
                    fit_font, wrap_text, pulse,
                    VOID, WHITE, MUTED, DIM, CYAN, GREEN, AMBER, VIOLET)

# ---------------------------------------------------------------------
# ORTE DER KAMPAGNE  (eine Quelle: Szenenbild + Effekte + Panel-Tags)
# ---------------------------------------------------------------------
# id    : identisch zu world_map.OBJECTS -> main.py verbindet beides.
# kind  : Panel-Tag ueber dem Titel (PLANET / STATION / REGION / SIGNAL).
# scene : separates Hintergrundbild in scenes/ (Fallback: prozedural).
# accent: Akzentfarbe von Glow, Konturen und Panel.
# fx    : Effekt-Konfiguration der Szenerie (dezent, siehe _draw_fx).
LOCATIONS = {
    "sector_1": {
        "kind": "PLANET", "sector": 1, "name": "ERDE",
        "scene": "loc_erde.jpg", "accent": CYAN,
        "fx": {"dust": (70, (170, 210, 255)), "fog": ((0, 150, 210), 3, 0.30),
               "lights": [(0.16, 0.82), (0.24, 0.88), (0.33, 0.80), (0.44, 0.86),
                          (0.55, 0.92), (0.63, 0.84), (0.74, 0.90), (0.85, 0.86)],
               "movers": (2, (120, 220, 255))},
    },
    "sector_2": {
        "kind": "STATION", "sector": 2, "name": "RAUMSTATION",
        "scene": "loc_raumstation.jpg", "accent": (255, 70, 160),
        "fx": {"dust": (55, (220, 180, 230)), "fog": ((190, 40, 140), 3, 0.26),
               "sweep": ((255, 90, 180), 0.5, 0.42),
               "lights": [(0.30, 0.38), (0.44, 0.30), (0.58, 0.36), (0.68, 0.46),
                          (0.38, 0.52), (0.62, 0.56)]},
    },
    "sector_3": {
        "kind": "REGION", "sector": 3, "name": "ASTEROIDENGÜRTEL",
        "scene": "loc_asteroiden.jpg", "accent": (70, 220, 150),
        "fx": {"dust": (80, (190, 230, 200)), "fog": ((40, 170, 110), 3, 0.24),
               "rocks": 5,
               "lights": [(0.46, 0.52), (0.52, 0.46), (0.58, 0.55), (0.50, 0.62)]},
    },
    "sector_4": {
        "kind": "PLANET", "sector": 4, "name": "MARS",
        "scene": "loc_mars.jpg", "accent": (255, 140, 60),
        "fx": {"dust": (45, (255, 200, 150)), "fog": ((220, 90, 30), 3, 0.30),
               "embers": 42,
               "lights": [(0.22, 0.68), (0.36, 0.74), (0.52, 0.70), (0.66, 0.78),
                          (0.78, 0.72)]},
    },
    "sector_5": {
        "kind": "REGION", "sector": 5, "name": "DUNKLER SEKTOR",
        "scene": "loc_dunkler.jpg", "accent": VIOLET,
        "fx": {"dust": (34, (200, 180, 255)), "fog": ((120, 50, 220), 5, 0.42),
               "lightning": (2.6, 3), "movers": (2, (170, 120, 255))},
    },
    "signal_a": {
        "kind": "SIGNAL", "sector": 0, "name": "FEINDSIGNALE",
        "scene": "loc_feindsignale.jpg", "accent": (70, 230, 140),
        "fx": {"dust": (60, (180, 240, 200)), "fog": ((30, 170, 100), 2, 0.22),
               "sweep": ((70, 230, 140), 0.5, 0.44), "movers": (3, (120, 240, 160))},
    },
    "signal_b": {
        "kind": "SIGNAL", "sector": 0, "name": "BOSS-SIGNAL",
        "scene": "loc_boss.jpg", "accent": AMBER,
        "fx": {"dust": (40, (255, 210, 150)), "fog": ((200, 110, 30), 4, 0.38),
               "lightning": (3.4, 2), "embers": 30},
    },
}

# ------------------------------- Timing -------------------------------
ZOOM_IN_TIME = 0.95       # Karte -> Objekt
ZOOM_OUT_TIME = 0.80      # Szene -> Karte
SCENE_FADE = 0.55         # Ueberblendung Zoom -> Szenenbild
SCENE_SETTLE = 1.60       # sanftes Nachschwenken des Szenenbilds
PANEL_DELAY = 0.45        # Panel erscheint nach dem Einschwenken
ZOOM_TARGET = 2.9         # Endzoom auf das Kartenobjekt

_NONE, _ZOOM_IN, _SCENE, _ZOOM_OUT = 0, 1, 2, 3


def _ease_io(t):
    """easeInOutCubic - weicher Start, weiches Ankommen."""
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1.0 - ((-2 * t + 2) ** 3) / 2.0


def _ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def _sc(c, k):
    return (max(0, min(255, int(c[0] * k))),
            max(0, min(255, int(c[1] * k))),
            max(0, min(255, int(c[2] * k))))


class SceneView:
    """Zoom-Kamera + Orts-Szenerie + Kampf-Panel der Weltkarte.

    Ablauf: open() -> ZOOM_IN (Karte zoomt zum Objekt) -> SCENE (Szenen-
    bild blendet ein, Effekte, Panel mit Kaempfen) -> close() ->
    ZOOM_OUT (rueckwaerts zur Karte) -> on_closed-Callback (main.py).
    """

    def __init__(self, scenes_dir):
        self.scenes_dir = scenes_dir
        self.phase = _NONE
        self.loc_id = None
        self.t = 0.0                       # Zeit in der aktuellen Phase
        self.on_closed = None              # Callback main.py (Map-Deselect)
        self._uv = (0.5, 0.5)              # Kartenobjekt (Bild-UV)
        self._cam_to = (0.5, 0.5)          # Kameraziel (leicht ueber Mitte)
        self._zo_from = None               # Zoom-Out-Startpunkt (bei ESC mitten im Zoom)
        self._info = None
        self._btn_rects = {}
        self._panel_rect = None
        self._scene_imgs = {}              # oid -> Surface | None
        self._zoom_base = None             # gecachte Zoom-Quelle (Weltkarte)
        self._zoom_key = None
        self._fallbacks = {}               # oid -> prozedurale Szene
        self._settled = {}                 # (oid, W, H) -> eingefahrenes Bild
        self._dim = None                   # Lesbarkeits-Verlauf (gecacht)
        self._dim_key = None
        self._vign = None                  # Vignette (gecacht)
        self._vign_key = None
        self._fx = {}                      # pro Ort initialisierte Partikel

    # ------------------------- Zustand / API -------------------------
    @property
    def active(self):
        """Zoom oder Szene sichtbar (main.py darf dann die Karte nicht zeichnen)."""
        return self.phase != _NONE

    @property
    def in_scene(self):
        return self.phase == _SCENE

    def blocks_map(self):
        """Wahr, solange Kartenobjekte nicht klickbar sein sollen
        (Zoom hinein, Szene, Zoom zurueck - die Karte ist 'in Bewegung')."""
        return self.phase in (_ZOOM_IN, _SCENE, _ZOOM_OUT)

    def open(self, oid, uv):
        """Zoom zum Kartenobjekt starten (main.py nach _map_select)."""
        if oid not in LOCATIONS:
            return
        if self.loc_id != oid or self.phase in (_NONE, _ZOOM_OUT):
            self.phase = _ZOOM_IN
            self.t = 0.0
        self.loc_id = oid
        self._uv = uv
        # Kameraziel minimal unter dem Objekt -> Objekt sitzt ueber dem Panel
        self._cam_to = (uv[0], min(0.94, uv[1] + 0.05))
        self._fx_init(oid)
        self._btn_rects = {}
        self._panel_rect = None

    def close(self):
        """Szene schliessen -> Zoom zurueck zur Karte (Animation).
        Funktioniert aus der Szene UND aus einem laufenden Zoom: Der
        Rueckweg startet weich ab der aktuellen Kameraposition."""
        if self.phase == _ZOOM_IN:
            k = _ease_io(min(1.0, self.t / ZOOM_IN_TIME))
            self._zo_from = (1.0 + (ZOOM_TARGET - 1.0) * k,
                             (0.5 + (self._cam_to[0] - 0.5) * k,
                              0.5 + (self._cam_to[1] - 0.5) * k))
            self.phase = _ZOOM_OUT
            self.t = 0.0
            self._btn_rects = {}
            self._panel_rect = None
        elif self.phase == _SCENE:
            self._zo_from = None
            self.phase = _ZOOM_OUT
            self.t = 0.0
            self._btn_rects = {}
            self._panel_rect = None

    def abort(self):
        """Sofort schliessen (Zustandswechsel, z. B. Kampfstart)."""
        self.phase = _NONE
        self.loc_id = None
        self._zo_from = None
        self._btn_rects = {}
        self._panel_rect = None

    def update(self, dt):
        if self.phase == _NONE:
            return
        self.t += dt
        if self.phase == _ZOOM_IN and self.t >= ZOOM_IN_TIME:
            self.phase, self.t = _SCENE, 0.0
        elif self.phase == _ZOOM_OUT and self.t >= ZOOM_OUT_TIME:
            cb = self.on_closed
            self.abort()
            if cb:
                cb()

    def button_rects(self):
        """Panel-Buttons fuer main.py _layout_stages (leer, wenn versteckt)."""
        return dict(self._btn_rects) if self.phase == _SCENE else {}

    def panel_rect(self):
        return self._panel_rect

    # --------------------------- Aktualisierung ---------------------------
    def _zoom_base_surf(self, img):
        """Zoom-Quelle: Weltkarte in Cover-Groesse + Sternfeld-Rand (gecacht).
        Damit bleibt der Zoom auch an Bildraendern weich (kein hartes Void)."""
        W, H = ui_kit.W, ui_kit.H
        key = (W, H, id(img))
        if key == self._zoom_key:
            return self._zoom_base
        rnd = random.Random(2077)
        if img is None:
            pad = pygame.Surface((int(W * 1.4), int(H * 1.4)))
            pad.fill(VOID)
            for _ in range(260):
                b = rnd.randrange(40, 160)
                pygame.draw.circle(pad, (b, b, min(255, b + 25)),
                                   (rnd.randrange(pad.get_width()),
                                    rnd.randrange(pad.get_height())),
                                   rnd.choice((1, 1, 1, 2)))
        else:
            iw, ih = img.get_size()
            s = max(W / iw, H / ih)              # Cover wie die Karte selbst
            P = 1.32                             # Rand fuer Rand-Objekte
            pw, ph = int(iw * s * P), int(ih * s * P)
            pad = pygame.Surface((pw, ph))
            pad.fill(VOID)
            scaled = pygame.transform.smoothscale(img, (int(iw * s * P), int(ih * s * P)))
            pad.blit(scaled, ((pw - scaled.get_width()) // 2,
                              (ph - scaled.get_height()) // 2))
            # Sternfeld ueber Rand + Karte (weiche Uebergaenge, Weltraum-Feel)
            inner = pygame.Rect((pw - scaled.get_width()) // 2,
                                (ph - scaled.get_height()) // 2,
                                scaled.get_width(), scaled.get_height())
            for _ in range(200):
                x, y = rnd.randrange(pw), rnd.randrange(ph)
                if inner.collidepoint((x, y)) and rnd.random() < 0.55:
                    continue                     # Karte bleibt stubenrein
                b = rnd.randrange(35, 130)
                pygame.draw.circle(pad, (b, b, min(255, b + 20)), (x, y),
                                   rnd.choice((1, 1, 2)))
            dim = pygame.Surface((pw, ph), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 55))
            pad.blit(dim, (0, 0))
        self._zoom_base, self._zoom_key = pad, key
        return pad

    def _scene_img(self, oid):
        """Separates Szenenbild des Ortes (lazy geladen, None -> Fallback).
        PAKET 7F: Bilder werden beim Laden leicht aufgehellt (+16 RGB),
        damit die Szenerie trotz dunkler Motive lesbar bleibt."""
        if oid in self._scene_imgs:
            return self._scene_imgs[oid]
        img = None
        fn = LOCATIONS[oid].get("scene")
        if fn:
            try:
                img = pygame.image.load(os.path.join(self.scenes_dir, fn)).convert()
                lift = pygame.Surface(img.get_size())
                lift.fill((16, 16, 20))
                img.blit(lift, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
            except Exception:
                img = None
        self._scene_imgs[oid] = img
        return img

    def _fallback_scene(self, oid):
        """Prozedurale Szenerie, falls das Bild fehlt (Ort bleibt besuchbar)."""
        W, H = ui_kit.W, ui_kit.H
        key = (oid, W, H)
        if key in self._fallbacks:
            return self._fallbacks[key]
        acc = LOCATIONS[oid]["accent"]
        rnd = random.Random(hash(oid) & 0xffff)
        surf = pygame.Surface((W, H))
        surf.fill(VOID)
        for _ in range(5):
            gx, gy = rnd.randrange(W), rnd.randrange(H)
            gr = rnd.randrange(int(min(W, H) * 0.22), int(min(W, H) * 0.55))
            glow = radial_glow(_sc(acc, rnd.uniform(0.10, 0.30)), gr)
            surf.blit(glow, glow.get_rect(center=(gx, gy)),
                      special_flags=pygame.BLEND_ADD)
        for _ in range(220):
            b = rnd.randrange(35, 150)
            pygame.draw.circle(surf, (b, b, min(255, b + 22)),
                               (rnd.randrange(W), rnd.randrange(H)),
                               rnd.choice((1, 1, 1, 2)))
        self._fallbacks[key] = surf
        return surf

    def _dim_overlay(self):
        """Verlauf unten (Panel-Lesbarkeit) + leichte Daemmerung (gecacht)."""
        W, H = ui_kit.W, ui_kit.H
        key = (W, H)
        if key == self._dim_key:
            return self._dim
        lay = pygame.Surface((W, H), pygame.SRCALPHA)
        lay.fill((0, 0, 0, 26))
        grad = max(1, int(H * 0.42))
        for i in range(grad):
            a = int(95 * (i / grad) ** 1.7)
            pygame.draw.line(lay, (0, 0, 0, a), (0, H - grad + i), (W, H - grad + i))
        self._dim, self._dim_key = lay, key
        return lay

    def _vignette(self):
        W, H = ui_kit.W, ui_kit.H
        key = (W, H)
        if key == self._vign_key:
            return self._vign
        lay = pygame.Surface((W, H), pygame.SRCALPHA)
        r = int(math.hypot(W, H) * 0.66)
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (0, 0, 0, 105), (r, r), r)
        pygame.draw.circle(glow, (0, 0, 0, 0), (r, r), int(r * 0.70))
        lay.blit(glow, (W // 2 - r, H // 2 - r))
        self._vign, self._vign_key = lay, key
        return lay

    # ------------------------------ Effekte ------------------------------
    def _fx_init(self, oid):
        """Partikel/Beweger einmalig pro Ort anlegen (deterministisch)."""
        if self._fx.get("oid") == oid:
            return
        cfg = LOCATIONS[oid].get("fx", {})
        rnd = random.Random(hash(oid) & 0xffff)
        fx = {"oid": oid}
        if "dust" in cfg:
            n, col = cfg["dust"]
            fx["dust"] = [(rnd.random(), rnd.random(),
                           rnd.uniform(0.004, 0.016), rnd.uniform(0.003, 0.010),
                           rnd.uniform(1.0, 2.4), rnd.uniform(0, math.tau), col)
                          for _ in range(n)]
        if "embers" in cfg:
            fx["embers"] = [(rnd.random(), rnd.random(),
                             rnd.uniform(0.05, 0.13), rnd.uniform(0.6, 1.6),
                             rnd.uniform(0, math.tau))
                            for _ in range(cfg["embers"])]
        if "movers" in cfg:
            n, col = cfg["movers"]
            fx["movers"] = [{"off": rnd.random(), "per": rnd.uniform(9.0, 15.0),
                             "y": rnd.uniform(0.16, 0.62), "amp": rnd.uniform(0.01, 0.035),
                             "sp": rnd.uniform(0.5, 1.1), "s": rnd.uniform(0.8, 1.4),
                             "col": col} for _ in range(n)]
        if "rocks" in cfg:
            fx["rocks"] = [{"off": rnd.random(), "per": rnd.uniform(22.0, 34.0),
                            "y": rnd.uniform(0.2, 0.8), "r": rnd.uniform(5, 14),
                            "pts": [(rnd.uniform(0.7, 1.3), rnd.uniform(0.7, 1.3))
                                    for _ in range(7)]}
                           for _ in range(cfg["rocks"])]
        if "lightning" in cfg:
            every, n = cfg["lightning"]
            fx["lightning"] = {"every": every, "pts": [(rnd.uniform(0.15, 0.85),
                                                        rnd.uniform(0.12, 0.55))
                                                       for _ in range(n)]}
        self._fx = fx

    def _draw_fx(self, surface, t, alpha):
        """Dezente Szenen-Effekte: Staub, Nebel, Lichter, Sweep, Bewegung."""
        if alpha <= 0.02:
            return
        cfg = LOCATIONS[self.loc_id].get("fx", {})
        W, H = ui_kit.W, ui_kit.H
        fx = self._fx

        # Nebel: langsam driftende, additive Weichzeichner
        if "fog" in cfg:
            col, n, inten = cfg["fog"]
            acc = LOCATIONS[self.loc_id]["accent"]
            base = _sc(acc, 0.55)
            for i in range(n):
                ph = i * math.tau / n
                x = W * (0.5 + 0.34 * math.sin(t * 0.05 + ph))
                y = H * (0.42 + 0.20 * math.cos(t * 0.04 + ph * 1.7))
                r = int(min(W, H) * 0.42)
                glow = radial_glow(_sc(base, 0.45), r)
                glow.set_alpha(int(255 * inten * alpha))
                surface.blit(glow, glow.get_rect(center=(int(x), int(y))),
                             special_flags=pygame.BLEND_ADD)

        # Staub-Partikel: langsames Drift + Funkeln
        for (x, y, sx, sy, sz, ph, col) in fx.get("dust", ()):
            px = (x + t * sx) % 1.02 - 0.01
            py = (y + t * sy) % 1.02 - 0.01
            tw = 0.55 + 0.45 * math.sin(t * 1.7 + ph)
            c = _sc(col, (0.35 + 0.5 * tw) * alpha)
            pygame.draw.circle(surface, c, (int(px * W), int(py * H)),
                               max(1, int(sz * u(1.1))))

        # Funken (Mars / Boss): steigen auf, flackern
        for (x, y, sp, sz, ph) in fx.get("embers", ()):
            py = (y - t * sp) % 1.08
            px = x + 0.015 * math.sin(t * 0.8 + ph)
            tw = 0.5 + 0.5 * math.sin(t * 3.1 + ph * 2.0)
            col = (255, int(120 + 80 * tw), 40)
            pygame.draw.circle(surface, _sc(col, alpha * (0.45 + 0.5 * tw)),
                               (int(px * W), int((1.08 - py) * H)),
                               max(1, int(sz * u(1.2))))

        # Patrouillen / Verbaende: ziehen ruhig von links nach rechts
        for m in fx.get("movers", ()):
            k = ((t + m["off"] * m["per"]) % m["per"]) / m["per"]
            px = (-0.08 + 1.16 * k) * W
            py = H * (m["y"] + m["amp"] * math.sin(t * m["sp"] * math.tau))
            s = u(7) * m["s"]
            col = _sc(m["col"], 0.9 * alpha)
            dirx = 1.0
            pts = [(px + dirx * s * 1.6, py),
                   (px - dirx * s * 0.9, py - s * 0.75),
                   (px - dirx * s * 0.35, py),
                   (px - dirx * s * 0.9, py + s * 0.75)]
            pygame.draw.polygon(surface, (10, 16, 26), pts)
            pygame.draw.polygon(surface, col, pts, 1)
            tr = _sc(col, 0.5)
            pygame.draw.line(surface, tr, (px - dirx * s * 0.9, py),
                             (px - dirx * s * 2.4, py), 1)

        # Treibende Felsen (Asteroidenguertel)
        for rk in fx.get("rocks", ()):
            k = ((t + rk["off"] * rk["per"]) % rk["per"]) / rk["per"]
            px = (-0.06 + 1.12 * k) * W
            py = H * rk["y"]
            r = u(rk["r"])
            pts = []
            for i, (a, b) in enumerate(rk["pts"]):
                ang = math.tau * i / len(rk["pts"])
                pts.append((px + math.cos(ang) * r * a, py + math.sin(ang) * r * b))
            pygame.draw.polygon(surface, (22, 24, 32), pts)
            pygame.draw.polygon(surface, _sc((150, 160, 180), 0.5 * alpha), pts, 1)

        # Radar-Sweep (Station / Signale)
        if "sweep" in cfg:
            col, ux, uy = cfg["sweep"]
            cx, cy = ux * W, uy * H
            rad = min(W, H) * 0.24
            a0 = (t * 55.0) % 360.0
            for i, (rr, bright) in enumerate(((rad, 0.85), (rad * 0.68, 0.5),
                                              (rad * 0.36, 0.35))):
                ar = pygame.Rect(cx - rr, cy - rr, rr * 2, rr * 2)
                pygame.draw.arc(surface, _sc(col, bright * alpha), ar,
                                math.radians(a0 + i * 40),
                                math.radians(a0 + i * 40 + 80), 1)
            pygame.draw.circle(surface, _sc(col, 0.4 * alpha), (int(cx), int(cy)),
                               max(1, int(rad)), 1)

        # Blinklichter (Stadtlichter, Station, Lagerfeuer)
        for i, (lx, ly) in enumerate(cfg.get("lights", ())):
            ph = i * 1.31
            tw = 0.5 + 0.5 * math.sin(t * 2.1 + ph)
            r = max(1, int(u(2) * (0.7 + 0.6 * tw)))
            col = _sc(LOCATIONS[self.loc_id]["accent"], (0.5 + 0.5 * tw) * alpha)
            pygame.draw.circle(surface, col, (int(lx * W), int(ly * H)), r)
            if tw > 0.8:
                g = radial_glow(col, u(14))
                surface.blit(g, g.get_rect(center=(int(lx * W), int(ly * H))),
                             special_flags=pygame.BLEND_ADD)

        # Blitze (Dunkler Sektor / Boss): kurze, seltene Aufhellung
        ln = fx.get("lightning")
        if ln:
            cyc = t % ln["every"]
            if cyc < 0.28:
                k = max(0.0, 1.0 - abs(cyc - 0.10) / 0.16)
                idx = int(t / ln["every"]) % max(1, len(ln["pts"]))
                lx, ly = ln["pts"][idx]
                g = radial_glow(_sc(LOCATIONS[self.loc_id]["accent"], 0.9),
                                int(min(W, H) * 0.34))
                g.set_alpha(int(190 * k * alpha))
                surface.blit(g, g.get_rect(center=(int(lx * W), int(ly * H))),
                             special_flags=pygame.BLEND_ADD)

    # ------------------------------ Panel ------------------------------
    def _draw_panel(self, surface, info, appear):
        """Orts-Panel: Typ, Name, Status, Story, KAEMPFE, Aktionen.
        Erscheint nach dem Einschwenken (slide-up); Buttons sind erst
        klickbar, wenn das Panel steht (appear >= 0.95)."""
        W, H = ui_kit.W, ui_kit.H
        acc = info.get("accent", CYAN)
        pw = max(u(300), min(int(W * 0.58), u(620)))
        pad = u(12)
        f_info = F(9)
        f_bat = F(10)

        story = info.get("story", "")
        wrapped = wrap_text(story, f_info, pw - pad * 2)[:2] if story else []
        battles = (info.get("battles") or [])[:4]
        has_prog = info.get("progress") is not None
        prim, sec = info.get("primary"), info.get("second")

        ph = (u(10) + u(14) + int(F(14).get_height() * 1.15) + u(4)
              + int(F(10).get_height() * 1.2) + u(6)
              + int(f_info.get_height() * 1.3) * len(wrapped)
              + (u(6) if battles else 0)
              + int(f_bat.get_height() * 1.55) * len(battles)
              + (u(16) if has_prog else u(4))
              + u(34) + u(10))
        ph = min(ph, int(H * 0.60))
        x, y = u(12), H - u(12) - ph
        self._panel_rect = pygame.Rect(x, y, pw, ph)
        self._btn_rects = {}

        slide = int((1.0 - appear) * u(26))
        rect = self._panel_rect.move(0, slide)
        glass_panel(surface, rect, accent=acc, radius=u(10), alpha=214, width=1)

        # Close-X (immer vorhanden)
        cxr = pygame.Rect(rect.right - u(28) - u(7), rect.y + u(7), u(28), u(28))
        if appear > 0.9:
            self._btn_rects["scene_close"] = cxr
        sh = pygame.Surface((cxr.w, cxr.h), pygame.SRCALPHA)
        sh.fill((40, 30, 60, 110))
        surface.blit(sh, cxr.topleft)
        pygame.draw.rect(surface, MUTED, cxr, 1, border_radius=u(6))
        ccx, ccy = cxr.center
        cs = max(2, u(4))
        pygame.draw.line(surface, WHITE, (ccx - cs, ccy - cs), (ccx + cs, ccy + cs), 2)
        pygame.draw.line(surface, WHITE, (ccx + cs, ccy - cs), (ccx - cs, ccy + cs), 2)

        cy = rect.y + u(9)
        # Typ-Tag + Titel
        tag = info.get("tag", "")
        if tag:
            text(surface, tag, F(8), _sc(acc, 0.85), (rect.x + pad, cy), "topleft")
        cy += u(13)
        neon_text(surface, info["title"], F(14), acc, (rect.x + pad, cy), "topleft", 1)
        cy += int(F(14).get_height() * 1.15) + u(3)
        # Status
        text(surface, info.get("status", ""), F(10),
             info.get("status_col", WHITE), (rect.x + pad, cy), "topleft")
        cy += int(F(10).get_height() * 1.2) + u(5)
        # Story
        for ln in wrapped:
            text(surface, ln, f_info, MUTED, (rect.x + pad, cy), "topleft")
            cy += int(f_info.get_height() * 1.3)
        # Verfuegbare Kaempfe
        if battles:
            cy += u(5)
            text(surface, "VERFÜGBARE KÄMPFE", F(8), _sc(acc, 0.75),
                 (rect.x + pad, cy), "topleft")
            cy += u(13)
            for b in battles:
                col = b.get("col", CYAN)
                pygame.draw.circle(surface, col, (rect.x + pad + u(3), int(cy + f_bat.get_height() / 2)), max(2, u(2)))
                text(surface, b.get("label", ""), f_bat, col,
                     (rect.x + pad + u(10), cy), "topleft")
                if b.get("note"):
                    img = f_info.render(b["note"], True, _sc(MUTED, 1.0))
                    surface.blit(img, img.get_rect(midright=(rect.right - pad - u(2), int(cy + f_bat.get_height() / 2))))
                cy += int(f_bat.get_height() * 1.55)
        # Fortschritt
        if has_prog:
            cy += u(8)
            bw = pw - pad * 2
            bh = max(3, u(5))
            pygame.draw.rect(surface, (14, 22, 34), (rect.x + pad, cy, bw, bh),
                             border_radius=u(3))
            prog = max(0.0, min(1.0, info["progress"]))
            if prog > 0:
                pygame.draw.rect(surface, acc, (rect.x + pad, cy, int(bw * prog), bh),
                                 border_radius=u(3))
            pygame.draw.rect(surface, _sc(acc, 0.45), (rect.x + pad, cy, bw, bh),
                             1, border_radius=u(3))
            if info.get("progress_text"):
                text(surface, info["progress_text"], F(8), MUTED,
                     (rect.x + pad, cy + bh + u(2)), "topleft")
            cy += bh + u(14)
        else:
            cy += u(6)
        # Aktions-Buttons (Glasflaeche + Kontur, Schrift via fit_font)
        by = rect.bottom - u(34)
        bh2 = u(27)
        bw_p, bw_s = u(168), u(104)
        actions = []
        if sec:
            r_s = pygame.Rect(rect.right - bw_p - bw_s - u(22), by, bw_s, bh2)
            if appear > 0.9:
                self._btn_rects["scene_second"] = r_s
            actions.append(("scene_second", r_s, sec))
        if prim:
            r_p = pygame.Rect(rect.right - bw_p - u(12), by, bw_p, bh2)
            if appear > 0.9:
                self._btn_rects["scene_primary"] = r_p
            actions.append(("scene_primary", r_p, prim))
        for rid, rr, act in actions:
            lbl, col, en = act
            tint = (int(col[0] * 0.15), int(col[1] * 0.15), int(col[2] * 0.15))
            fill = (*tint, 125 if en else 45)
            shb = pygame.Surface((max(2, rr.w), max(2, rr.h)), pygame.SRCALPHA)
            shb.fill(fill)
            surface.blit(shb, rr.topleft)
            pygame.draw.rect(surface, col if en else _sc(DIM, 0.95), rr,
                             2 if en else 1, border_radius=u(6))
            f = fit_font(lbl, 9, rr.w - u(10))
            img = f.render(lbl, True, WHITE if en else MUTED)
            surface.blit(img, img.get_rect(center=rr.center))
            if en and rid == "scene_primary":
                k = pulse(pygame.time.get_ticks() * 0.001, 2.6)
                pygame.draw.rect(surface, _sc(col, 0.3 + 0.3 * k),
                                 rr.inflate(int(u(3) + u(2) * k), int(u(3) + u(2) * k)),
                                 1, border_radius=u(7))

    # ------------------------------ Zeichnen ------------------------------
    def _draw_zoom(self, surface, img, z, cam):
        """Aktueller Kamera-Ausschnitt der Weltkarte (vollflaechig)."""
        W, H = ui_kit.W, ui_kit.H
        base = self._zoom_base_surf(img)
        bw, bh = base.get_size()
        vw, vh = W / z, H / z
        cx = min(max(cam[0] * bw, vw / 2), bw - vw / 2)
        cy = min(max(cam[1] * bh, vh / 2), bh - vh / 2)
        crop = pygame.Rect(int(cx - vw / 2), int(cy - vh / 2),
                           int(vw), int(vh))
        crop.clip(base.get_rect())
        frame = pygame.transform.smoothscale(base.subsurface(crop), (W, H))
        surface.blit(frame, (0, 0))

    def _draw_scene_bg(self, surface, oid, alpha, settle):
        """Szenenbild (Cover) mit sanftem Nachschwenken + Lesbarkeits-Verlauf."""
        W, H = ui_kit.W, ui_kit.H
        img = self._scene_img(oid)
        if img is not None:
            if settle >= 0.999:
                key = (oid, W, H)
                scaled = self._settled.get(key)
                if scaled is None:
                    iw, ih = img.get_size()
                    s = max(W / iw, H / ih)
                    scaled = pygame.transform.smoothscale(
                        img, (int(iw * s) + 1, int(ih * s) + 1))
                    self._settled[key] = scaled
            else:
                iw, ih = img.get_size()
                s = max(W / iw, H / ih) * (1.0 + 0.13 * (1.0 - settle))
                scaled = pygame.transform.smoothscale(
                    img, (int(iw * s) + 1, int(ih * s) + 1))
            if alpha < 0.999:
                scaled = scaled.copy()
                scaled.set_alpha(int(255 * alpha))
            surface.blit(scaled, scaled.get_rect(center=(W // 2, H // 2)))
        else:
            fb = self._fallback_scene(oid)
            if alpha < 0.999:
                fb = fb.copy()
                fb.set_alpha(int(255 * alpha))
            surface.blit(fb, (0, 0))
        surface.blit(self._dim_overlay(), (0, 0))

    def draw(self, surface, map_img, elapsed, info=None):
        """Zeichnet Zoom/Kamera, Szenerie, Effekte und Panel je Phase."""
        if self.phase == _NONE or not self.loc_id:
            return
        W, H = ui_kit.W, ui_kit.H
        oid = self.loc_id
        acc = LOCATIONS[oid]["accent"]

        if self.phase == _ZOOM_IN:
            k = _ease_io(self.t / ZOOM_IN_TIME)
            z = 1.0 + (ZOOM_TARGET - 1.0) * k
            cam = (0.5 + (self._cam_to[0] - 0.5) * k,
                   0.5 + (self._cam_to[1] - 0.5) * k)
            self._draw_zoom(surface, map_img, z, cam)
            # Ziel-Reticle: faellt mit dem Zoom ein, zeigt das Ziel
            r = int(u(10) + u(16) * (1.0 - k))
            px, py = W * self._cam_to[0], H * self._cam_to[1]
            pygame.draw.circle(surface, _sc(acc, 0.5 + 0.4 * k), (int(px), int(py)), r, 1)
            pygame.draw.circle(surface, _sc(acc, 0.3), (int(px), int(py)), r + u(5), 1)
        elif self.phase == _SCENE:
            t = self.t
            fade = _ease_out(t / SCENE_FADE)
            settle = _ease_out(t / SCENE_SETTLE)
            self._draw_zoom(surface, map_img, ZOOM_TARGET, self._cam_to)
            self._draw_scene_bg(surface, oid, fade, settle)
            fx_alpha = max(0.0, min(1.0, (t - 0.25) / 0.9))
            self._draw_fx(surface, t, fx_alpha)
            surface.blit(self._vignette(), (0, 0))
            if t >= PANEL_DELAY and info:
                appear = _ease_out((t - PANEL_DELAY) / 0.35)
                self._draw_panel(surface, info, appear)
        elif self.phase == _ZOOM_OUT:
            k = _ease_io(self.t / ZOOM_OUT_TIME)
            from_z, from_cam = self._zo_from if self._zo_from else (
                ZOOM_TARGET, self._cam_to)
            z = from_z + (1.0 - from_z) * k
            cam = (from_cam[0] + (0.5 - from_cam[0]) * k,
                   from_cam[1] + (0.5 - from_cam[1]) * k)
            # Karte zuerst (liegt drunter), Szene blendet darueber ab
            self._draw_zoom(surface, map_img, z, cam)
            if self.t < 0.30:
                fade = 1.0 - self.t / 0.30
                self._draw_scene_bg(surface, oid, fade, 1.0)
                self._draw_fx(surface, self.t + 2.0, fade)
                surface.blit(self._vignette(), (0, 0))

    # ------------------------------ Debug ------------------------------
    def debug_state(self):
        """Kurzinfo fuer Tests/F1-Overlay."""
        return {"phase": self.phase, "loc": self.loc_id, "t": round(self.t, 2)}
