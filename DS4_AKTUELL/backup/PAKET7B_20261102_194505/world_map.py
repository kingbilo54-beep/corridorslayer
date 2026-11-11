# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | INTERAKTIVE GALAXIEKARTE (PAKET 7A)
========================================================
Die Weltkarte (bg_world.jpg) wird zur interaktiven Spieloberflaeche:

  * Objekte des Bildes (Planeten, Stationen, zentrale Struktur, Signale)
    werden zu antippbaren Zielen. Ihre Positionen/Groessen sind in
    BILD-Relativkoordinaten (uv, 0..1) definiert -> OBJECTS ist die
    EINZIGE Quelle fuer Zeichnen UND Hit-Testing.
  * Cover-Transformation ohne Verzerrung: Bild und Hitboxen verwenden
    exakt dieselbe Transformation (prepare/to_screen). Bei starker
    Randbeschnitt-Gefahr wird automatisch auf "contain" reduziert,
    damit wichtige Objekte nicht abgeschnitten werden.
  * Hervorhebungen passen zur Objektform: Kreise -> rotierende Bogen-
    segmente, Hexagon -> Doppel-Hexagon, Ring -> gegenlaufende Ringe,
    Diamant -> pulsierender Diamant. Keine generischen Kreise.
  * Kompaktes Info-Panel (dunkel-transparent, duenne Neon-Kontur) mit
    Name, Status, Fortschritt, Voraussetzungen und Aktions-Buttons.
  * Caching: Hintergrund-Fit, statische Overlay-Ebene (Ringe, Labels,
    Routen) und Panel-Flaeche werden pro Groesse/Zustand gecacht. Pro
    Frame entsteht KEINE Fullscreen-Surface; dynamisch sind nur wenige
    guenstige Vektor-Draws + additve Glow-Sprites.

Spielmechanik bleibt komplett in main.py (bestehende Systeme): Diese
Datei kennt nur Geometrie, Statusdaten (die main.py uebergibt) und
Darstellung.
"""
import math
import random
import pygame
import ui_kit
from ui_kit import (u, F, text, neon_text, radial_glow, glass_panel, draw_icon,
                    bar_h, pulse, VOID, LINE, DIM, MUTED, WHITE, ICE, GREEN,
                    RED, AMBER, CYAN, CYAN_SOFT, MAGENTA, VIOLET)

# ---------------------------------------------------------------------
# OBJEKTE DER WELTKARTE  (eine Quelle fuer Zeichnen + Hit-Testing)
# ---------------------------------------------------------------------
# uv  : Position relativ zur BILD-Groesse (0..1) - an bg_world.jpg angelehnt.
# rad : Radius relativ zur BILD-HOEHE (bleibt beim Skalieren formgetreu).
# shape: circle | hex | ring | diamond  (Highlight + Hit-Test passen sich an)
# Hinweis: Werte hier feinjustieren, falls Objekte im echten Bild leicht
#          anders liegen (Debug-Modus F1 zeigt Hitboxen auf der Karte an).
SECTOR_UV = {1: (0.50, 0.78), 2: (0.22, 0.55), 3: (0.78, 0.52),
             4: (0.28, 0.30), 5: (0.75, 0.17)}

OBJECTS = [
    {"id": "sector_1", "kind": "sector", "sector": 1, "shape": "circle",
     "uv": SECTOR_UV[1], "rad": 0.075, "name": "ERDE"},
    {"id": "sector_2", "kind": "sector", "sector": 2, "shape": "hex",
     "uv": SECTOR_UV[2], "rad": 0.060, "name": "RAUMSTATION"},
    {"id": "sector_3", "kind": "sector", "sector": 3, "shape": "circle",
     "uv": SECTOR_UV[3], "rad": 0.070, "name": "ASTEROIDENGÜRTEL"},
    {"id": "sector_4", "kind": "sector", "sector": 4, "shape": "circle",
     "uv": SECTOR_UV[4], "rad": 0.058, "name": "MARS"},
    {"id": "sector_5", "kind": "sector", "sector": 5, "shape": "circle",
     "uv": SECTOR_UV[5], "rad": 0.066, "name": "DUNKLER SEKTOR"},
    {"id": "hub", "kind": "hub", "shape": "hex",
     "uv": (0.50, 0.44), "rad": 0.105, "name": "FLOTTENHUB PRIME"},
    {"id": "station_res", "kind": "station", "shape": "ring",
     "uv": (0.635, 0.635), "rad": 0.045, "name": "FORSCHUNGS-STATION"},
    {"id": "station_nex", "kind": "station", "shape": "ring",
     "uv": (0.345, 0.175), "rad": 0.042, "name": "NEXUS-RELAY"},
    {"id": "signal_a", "kind": "signal", "shape": "diamond",
     "uv": (0.115, 0.335), "rad": 0.038, "name": "SIGNAL ALPHA"},
    {"id": "signal_b", "kind": "signal", "shape": "diamond",
     "uv": (0.895, 0.335), "rad": 0.038, "name": "BOSS-SIGNAL"},
]
BY_ID = {o["id"]: o for o in OBJECTS}
DEFAULT_COLOR = {"sector": CYAN, "hub": VIOLET, "station": AMBER, "signal": GREEN}
VIRTSIZE = (1920, 1080)          # angenommen, falls bg_world.jpg fehlt


def _scaled_c(c, k):
    return (max(0, int(c[0] * k)), max(0, int(c[1] * k)), max(0, int(c[2] * k)))


def _mix(c, other, k):
    return (int(c[0] + (other[0] - c[0]) * k),
            int(c[1] + (other[1] - c[1]) * k),
            int(c[2] + (other[2] - c[2]) * k))


class GalaxyMap:
    """Zeichnung + Hit-Test der interaktiven Galaxiekarte."""

    def __init__(self):
        self.selected = None
        self._tr = None            # (s, ox, oy, iw, ih)
        self._tr_key = None
        self._geo = {}             # id -> dict(cx, cy, r, hit_r)
        self._bg = None            # gecachtes, eingepasstes Bild
        self._bg_key = None
        self._static = None        # gecachte statische Overlay-Ebene
        self._static_key = None
        self._panel_rect = None
        self._btn_rects = {}       # 'map_primary' / 'map_second' / 'map_close'
        self._last_states = {}

    # ---------------- Geometrie (Bild <-> Screen) ----------------
    def prepare(self, img):
        """Berechnet die Cover-Transformation Bild->Screen (gecacht).
        Das Bild wird NIE verzerrt; bei >15% Randbeschnitt wird automatisch
        auf 'contain' entlang der betroffenen Achse reduziert."""
        W, H = ui_kit.W, ui_kit.H
        iw, ih = img.get_size() if img is not None else VIRTSIZE
        key = (W, H, iw, ih)
        if key == self._tr_key:
            return self._tr
        s_cover = max(W / iw, H / ih)
        crop_x = (iw * s_cover - W) / (iw * s_cover)
        crop_y = (ih * s_cover - H) / (ih * s_cover)
        s = s_cover
        if crop_x > 0.15:
            s = min(s, W / iw)       # horiz. beschnittgefaehrdet -> Breite einpassen
        if crop_y > 0.15:
            s = min(s, H / ih)       # vertik. beschnittgefaehrdet -> Hoehe einpassen
        self._tr = (s, (W - iw * s) / 2.0, (H - ih * s) / 2.0, iw, ih)
        self._tr_key = key
        self._geo = {}
        self._bg = None
        return self._tr

    def to_screen(self, uv):
        """Bild-UV -> Screen-Position (DIESE Funktion nutzen Zeichnen UND
        Hit-Test -> Bild und Hitboxen bleiben beim Skalieren exakt vereint)."""
        s, ox, oy, iw, ih = self._tr
        return (int(ox + uv[0] * iw * s), int(oy + uv[1] * ih * s))

    def _geometry(self):
        """Screen-Geometrie aller Objekte (gecacht pro Transformation)."""
        if self._geo:
            return self._geo
        _s, _ox, _oy, _iw, ih = self._tr
        for o in OBJECTS:
            cx, cy = self.to_screen(o["uv"])
            r = max(6, int(o["rad"] * ih * self._tr[0]))
            hit_r = max(u(26), int(r + u(12)))   # fingerfreundliche Touch-Flaeche
            self._geo[o["id"]] = {"cx": cx, "cy": cy, "r": r, "hit_r": hit_r}
        return self._geo

    # ---------------- Interaktion ----------------
    def hit(self, pos):
        """Objekt unter dem Punkt (formnah, mit Touch-Puffer) oder None."""
        if self._tr is None:
            return None
        best, best_d = None, 1e18
        px, py = pos
        for o in OBJECTS:
            g = self._geometry()[o["id"]]
            dx, dy = px - g["cx"], py - g["cy"]
            shape = o["shape"]
            if shape == "diamond":
                inside = (abs(dx) + abs(dy)) <= g["hit_r"] * 1.05
            elif shape == "hex":
                inside = (abs(dx) <= g["hit_r"] * 0.92 and
                          abs(dy) <= g["hit_r"] * 0.92)
            else:
                inside = dx * dx + dy * dy <= g["hit_r"] * g["hit_r"]
            if inside:
                d = dx * dx + dy * dy
                if d < best_d:
                    best, best_d = o["id"], d
        return best

    def select(self, obj_id):
        self.selected = obj_id

    def button_rects(self):
        """Rechtecke der Panel-Buttons (0-2 Aktionen + Close), fuer Btns in main."""
        return dict(self._btn_rects)

    def panel_rect(self):
        """Rect des Info-Panels (oder None) - main.py respektiert diese Zone."""
        return self._panel_rect

    # ---------------- Hintergrund ----------------
    def _bg_surface(self, img):
        W, H = ui_kit.W, ui_kit.H
        s, ox, oy, iw, ih = self._tr
        key = (W, H, iw, ih, id(img) if img is not None else -1)
        if key == self._bg_key:
            return self._bg
        if img is None:
            # Prozeduraler Galaxie-Fallback (gecacht, nur Sternfeld + Nebel)
            surf = pygame.Surface((W, H))
            surf.fill(VOID)
            rnd = random.Random(20260)
            for _ in range(6):
                gx, gy = rnd.randrange(W), rnd.randrange(H)
                gr = rnd.randrange(int(min(W, H) * 0.2), int(min(W, H) * 0.5))
                col = _scaled_c(rnd.choice(((110, 60, 200), (0, 120, 160), (180, 50, 120))), 0.35)
                glow = radial_glow(col, gr)
                surf.blit(glow, glow.get_rect(center=(gx, gy)), special_flags=pygame.BLEND_ADD)
            for _ in range(240):
                b = rnd.randrange(40, 170)
                pygame.draw.circle(surf, (b, b, min(255, b + 25)),
                                   (rnd.randrange(W), rnd.randrange(H)), rnd.choice((1, 1, 1, 2)))
            self._bg, self._bg_key = surf, key
            return surf
        scaled = pygame.transform.smoothscale(
            img, (max(2, int(iw * s)), max(2, int(ih * s))))
        surf = pygame.Surface((W, H))
        surf.fill(VOID)
        surf.blit(scaled, (int(ox), int(oy)))
        # Karte leicht abdunkeln -> Objekte/Labels bleiben lesbar (einmalig gecacht)
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 60))
        surf.blit(dim, (0, 0))
        self._bg, self._bg_key = surf, key
        return surf

    # ---------------- statische Ebene ----------------
    def _static_layer(self, states):
        """Ringe, Routen, Labels, Status-Pips - EINMAL pro (Groesse, Zustand)."""
        W, H = ui_kit.W, ui_kit.H
        sig = tuple(sorted((oid, st.get("status", ""), st.get("name", ""))
                           for oid, st in states.items()))
        key = (W, H, self._tr_key, sig)
        if key == self._static_key:
            return self._static
        lay = pygame.Surface((W, H), pygame.SRCALPHA)
        geo = self._geometry()

        # dezente Handelsroute zwischen den Sektor-Planeten (statisch)
        route = [geo[f"sector_{i}"] for i in sorted(SECTOR_UV.keys())]
        pts = [(g["cx"], g["cy"]) for g in route]
        if len(pts) >= 2:
            pygame.draw.lines(lay, (*_scaled_c(CYAN, 0.35), 40), False, pts, 1)

        for o in OBJECTS:
            g = geo[o["id"]]
            st = states.get(o["id"], {})
            col = st.get("col") or DEFAULT_COLOR[o["kind"]]
            r = g["r"]
            # feiner Statusring (immer sichtbar, sehr zurueckhaltend)
            if o["shape"] == "circle":
                pygame.draw.circle(lay, (*_scaled_c(col, 0.65), 110), (g["cx"], g["cy"]), r, 1)
            elif o["shape"] == "hex":
                pts_h = [(g["cx"] + math.cos(math.radians(60 * i - 30)) * r,
                          g["cy"] + math.sin(math.radians(60 * i - 30)) * r) for i in range(6)]
                pygame.draw.polygon(lay, (*_scaled_c(col, 0.65), 110), pts_h, 1)
            elif o["shape"] == "ring":
                pygame.draw.circle(lay, (*_scaled_c(col, 0.6), 100), (g["cx"], g["cy"]), r, 1)
                pygame.draw.circle(lay, (*_scaled_c(col, 0.35), 60), (g["cx"], g["cy"]),
                                   max(3, int(r * 0.55)), 1)
            elif o["shape"] == "diamond":
                pts_d = [(g["cx"], g["cy"] - r), (g["cx"] + r, g["cy"]),
                         (g["cx"], g["cy"] + r), (g["cx"] - r, g["cy"])]
                pygame.draw.polygon(lay, (*_scaled_c(col, 0.65), 110), pts_d, 1)
            # Status-Pip + Label
            locked = st.get("status") in ("GESPERRT",)
            pip_c = _scaled_c(col, 0.25) if locked else col
            pygame.draw.circle(lay, (*pip_c, 220), (g["cx"] + int(r * 0.72), g["cy"] - int(r * 0.72)),
                               max(2, u(2.5)))
            name = st.get("name") or o["name"]
            f = F(9)
            img = f.render(name, True, _scaled_c(col, 0.9) if not locked else _scaled_c(MUTED, 0.9))
            lw2 = img.get_width()
            lx = min(max(g["cx"], lw2 // 2 + 3), W - lw2 // 2 - 3)
            ly = g["cy"] + r + u(6)
            if ly + img.get_height() > H - bar_h() - u(6):
                ly = g["cy"] - r - u(6) - img.get_height()
            lay.blit(img, img.get_rect(midtop=(lx, ly)))
        self._static, self._static_key = lay, key
        return lay

    # ---------------- Highlights (formfitting) ----------------
    def _draw_highlight(self, surface, o, g, col, elapsed):
        cx, cy, r = g["cx"], g["cy"], g["r"]
        k = pulse(elapsed, 2.8, 0.0)
        glow = radial_glow(_mix(col, WHITE, 0.35), int(r * 2.2))
        surface.blit(glow, glow.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_ADD)
        lw = max(2, u(2))
        shape = o["shape"]
        if shape == "circle":
            a0 = math.radians((elapsed * 90) % 360)
            for off in (0.0, math.pi):          # zwei gegenlaufende Bogensegmente
                pygame.draw.arc(surface, col, (cx - r - u(4), cy - r - u(4),
                                               (r + u(4)) * 2, (r + u(4)) * 2),
                                a0 + off, a0 + off + 1.5, lw)
            pygame.draw.circle(surface, _scaled_c(col, 0.8), (cx, cy), r + u(2), 1)
        elif shape == "hex":
            rot = math.radians((elapsed * 40) % 60)
            for scale, alpha_col in ((1.18, col), (1.34, _scaled_c(col, 0.5))):
                pts = [(cx + math.cos(rot + math.radians(60 * i)) * r * scale,
                        cy + math.sin(rot + math.radians(60 * i)) * r * scale)
                       for i in range(6)]
                pygame.draw.polygon(surface, alpha_col, pts, 1 if scale > 1.2 else lw)
        elif shape == "ring":
            rr = r + u(4)
            a0 = math.radians((elapsed * 80) % 360)
            pygame.draw.arc(surface, col, (cx - rr, cy - rr, rr * 2, rr * 2), a0, a0 + 2.2, lw)
            a1 = math.radians((-elapsed * 60) % 360)
            pygame.draw.arc(surface, _scaled_c(col, 0.6), (cx - rr, cy - rr, rr * 2, rr * 2),
                            a1 + math.pi, a1 + math.pi + 1.6, 1)
        elif shape == "diamond":
            rr = r + u(5) + int(2 * k)
            pts = [(cx, cy - rr), (cx + rr, cy), (cx, cy + rr), (cx - rr, cy)]
            pygame.draw.polygon(surface, col, pts, lw)
            pts2 = [(p[0] * 1.35 - cx * 0.35, p[1] * 1.35 - cy * 0.35) for p in pts]
            pygame.draw.polygon(surface, _scaled_c(col, 0.5), pts2, 1)

    # ---------------- Info-Panel ----------------
    def _draw_panel(self, surface, info):
        """Kompaktes Info-Panel unten rechts. Liefert/aktualisiert Button-Rects."""
        W, H = ui_kit.W, ui_kit.H
        m = u(10)
        pw = min(int(W * 0.46), u(430))
        lines = info.get("lines", [])[:2]
        # dynamische Hoehe: Titel+Status+Basis vs. Fortschritt + Infozeilen
        ph = u(96) + (u(16) if info.get("progress") is not None else 0) \
            + u(13) * len(lines) + u(30)
        ph = min(ph, int(H * 0.42))
        x = W - m - pw
        y = H - bar_h() - u(10) - ph
        rect = pygame.Rect(x, y, pw, ph)
        self._panel_rect = rect
        self._btn_rects = {}
        accent = info.get("accent", CYAN)
        glass_panel(surface, rect, accent=accent, radius=u(10), alpha=216, width=1)

        pad = u(12)
        # Titel
        neon_text(surface, info["title"], F(13), accent, (rect.x + pad, rect.y + u(8)),
                  "topleft", 1)
        # Status-Zeile
        f = F(10)
        text(surface, info["status"], f, info.get("status_col", WHITE),
             (rect.x + pad, rect.y + u(30)))
        y = rect.y + u(46)
        # Fortschrittsbalken (falls vorhanden)
        prog = info.get("progress")
        if prog is not None:
            bw = rect.w - pad * 2
            bh = max(3, u(6))
            pygame.draw.rect(surface, (14, 22, 34), (rect.x + pad, y, bw, bh),
                             border_radius=u(3))
            if prog > 0:
                pygame.draw.rect(surface, accent, (rect.x + pad, y, int(bw * min(1.0, prog)), bh),
                                 border_radius=u(3))
            pygame.draw.rect(surface, _scaled_c(accent, 0.5), (rect.x + pad, y, bw, bh),
                             1, border_radius=u(3))
            if info.get("progress_text"):
                text(surface, info["progress_text"], F(9), MUTED,
                     (rect.x + pad, y + bh + u(3)))
            y += bh + u(18)
        # Info-Zeilen
        for ln in info.get("lines", [])[:2]:
            text(surface, ln, F(9), MUTED, (rect.x + pad, y))
            y += int(F(9).get_height() * 1.25)
        # Buttons (Rechtecke fuer main.py-Btns, Zeichnung hier)
        by = rect.bottom - u(34)
        bh2 = u(26)
        self._btn_rects["map_close"] = pygame.Rect(rect.right - u(26) - u(8), rect.y + u(7),
                                                   u(26), u(26))
        prim = info.get("primary")
        sec = info.get("second")
        bw_prim = u(150)
        bw_sec = u(104)
        if sec:
            r_sec = pygame.Rect(rect.right - bw_prim - bw_sec - u(24), by, bw_sec, bh2)
            self._btn_rects["map_second"] = r_sec
        if prim:
            r_prim = pygame.Rect(rect.right - bw_prim - u(12), by, bw_prim, bh2)
            self._btn_rects["map_primary"] = r_prim
        # Close-X
        cxr = self._btn_rects["map_close"]
        pygame.draw.rect(surface, (10, 16, 28), cxr, border_radius=u(6))
        pygame.draw.rect(surface, MUTED, cxr, 1, border_radius=u(6))
        ccx, ccy = cxr.center
        cs = max(2, u(4))
        pygame.draw.line(surface, WHITE, (ccx - cs, ccy - cs), (ccx + cs, ccy + cs), 2)
        pygame.draw.line(surface, WHITE, (ccx + cs, ccy - cs), (ccx - cs, ccy + cs), 2)
        # Aktionsbuttons (nur definierte Aktionen zeichnen)
        action_defs = []
        if sec:
            action_defs.append(("map_second", self._btn_rects["map_second"],
                                sec[0], sec[1], sec[2]))
        if prim:
            action_defs.append(("map_primary", self._btn_rects["map_primary"],
                                prim[0], prim[1], prim[2]))
        for rid, rr, lbl, col, en in action_defs:
            fill = (12, 26, 42) if en else (6, 10, 18)
            pygame.draw.rect(surface, fill, rr, border_radius=u(6))
            pygame.draw.rect(surface, col if en else _scaled_c(DIM, 0.9), rr,
                             2 if en else 1, border_radius=u(6))
            f = F(9)
            img = f.render(lbl, True, WHITE if en else MUTED)
            surface.blit(img, img.get_rect(center=rr.center))
            if en and rid == "map_primary":
                k = pulse(0.0 + pygame.time.get_ticks() * 0.001, 2.6)
                pygame.draw.rect(surface, _scaled_c(col, 0.3 + 0.3 * k),
                                 rr.inflate(int(u(3) + u(2) * k), int(u(3) + u(2) * k)),
                                 1, border_radius=u(7))
        # Verbindungslinie Objekt -> Panel
        oid = self.selected
        if oid and oid in self._geometry():
            g = self._geometry()[oid]
            anchor = (g["cx"], g["cy"])
            target = rect.midleft if anchor[0] < rect.left else (
                (rect.left, min(max(anchor[1], rect.top + u(20)), rect.bottom - u(20))))
            pygame.draw.line(surface, _scaled_c(accent, 0.5), anchor, target, 1)
            pygame.draw.circle(surface, accent, anchor, max(2, u(2)))

    # ---------------- Debug ----------------
    def draw_debug(self, surface):
        """Hitboxen + UV-Koordinaten anzeigen (F1/Debug-Modus)."""
        f = F(8)
        for o in OBJECTS:
            g = self._geometry()[o["id"]]
            col = GREEN if self.hit((g["cx"], g["cy"])) == o["id"] else RED
            pygame.draw.circle(surface, col, (g["cx"], g["cy"]), g["hit_r"], 1)
            pygame.draw.line(surface, col, (g["cx"] - 4, g["cy"]), (g["cx"] + 4, g["cy"]), 1)
            pygame.draw.line(surface, col, (g["cx"], g["cy"] - 4), (g["cx"], g["cy"] + 4), 1)
            text(surface, f"{o['uv'][0]:.2f},{o['uv'][1]:.2f}", f, col,
                 (g["cx"], g["cy"] - g["hit_r"] - u(10)), "midtop")

    # ---------------- Rahmen-Zeichnung ----------------
    def draw(self, surface, img, elapsed, states, info=None):
        """Zeichnet Karte + Highlights + Panel.
        states: {obj_id: {'name': str, 'status': str, 'status_col': tuple,
                          'progress': float|None, 'lines': [str]}}
        info  : Panel-Inhalt oder None (kein Panel) - von main.py gebaut.
        """
        if img is not None or self._tr is None:
            self.prepare(img)
        self._last_states = states
        surface.blit(self._bg_surface(img), (0, 0))
        surface.blit(self._static_layer(states), (0, 0))
        geo = self._geometry()

        # langsamer Puls NUR fuer erreichbare Ziele (gestaffelte Phasen)
        for o in OBJECTS:
            st = states.get(o["id"], {})
            if st.get("pulse"):
                g = geo[o["id"]]
                k = pulse(elapsed, 3.4, hash(o["id"]) % 7 * 0.55)
                rr = g["r"] + u(3) + int(u(3) * k)
                col = st.get("col") or DEFAULT_COLOR[o["kind"]]
                pygame.draw.circle(surface, _scaled_c(col, 0.35 + 0.3 * k),
                                   (g["cx"], g["cy"]), rr, 1)
                if k > 0.72:
                    glow = radial_glow(_scaled_c(col, 0.4), int(g["r"] * 1.7))
                    surface.blit(glow, glow.get_rect(center=(g["cx"], g["cy"])),
                                 special_flags=pygame.BLEND_ADD)

        # Auswahl-Highlight (formfitting)
        if self.selected and self.selected in geo:
            o = BY_ID[self.selected]
            st = states.get(self.selected, {})
            col = st.get("col") or DEFAULT_COLOR[o["kind"]]
            self._draw_highlight(surface, o, geo[self.selected], col, elapsed)

        # Panel
        self._panel_rect = None
        self._btn_rects = {}
        if info:
            self._draw_panel(surface, info)
