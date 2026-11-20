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
  * AUSWAHL MIT TIEFE (Nutzerwunsch "die GANZE Erde soll sich hervor-
    woelben, nicht der Zirkel auf der Erde"): Das gewaehlte Gebiet loest
    sich KOMPLETT aus dem Kartenbild - nicht nur ein runder Ausschnitt.
    Eine per Objekt gross genug gewaehlte, weiche runde Region (Maske
    deckt den ganzen Planeten/die ganze Station) wird zentral ~16 %
    aufgeschaumt (WOELBUNG): voller Kern, weiches Verfliesen zur Kante
    -> KEINE sichtbare Kreis-Kante mehr, der ganze Planet woelbt sich.
    Dazu schwebende Hebung ueber eigenem Schatten + Akzent-Glow. Die
    Umgebung dunkelt dezent ab (radiales Fokus-Loch) - die Karte bleibt
    dabei VOLL ersichtlich. Das Prinzip gilt JEDEM Kartenobjekt (alle
    Kampagnen-Etappen + Signale), nur Radius/Kernstimme sind pro Objekt
    in OBJECTS["lift"] feinjustiert. Ein pulsierender Hinweis-Chip
    ('Nochmal antippen ...') erklaert den Zwei-Klick-Flow: 1. Klick =
    anwaehlen, 2. Klick = oeffnen.
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
# PAKET 7D: NUR NOCH KAMPAGNE - Hangar/Werft/Nexus-Symbole (hub, Res-
# und Nexus-Station) sind von der Karte entfernt. Jedes Objekt hat einen
# Story-Bezug: Kampfgebiete (Sektoren), ein aktives Feindsignal und das
# Boss-Signal am Ende jedes Sektors.
# uv  : Position relativ zur BILD-Groesse (0..1) - an bg_world.jpg angelehnt.
# rad : Radius relativ zur BILD-HOEHE (bleibt beim Skalieren formgetreu).
# shape: circle | hex | ring | diamond  (Highlight + Hit-Test passen sich an)
# Hinweis: Werte hier feinjustieren, falls Objekte im echten Bild leicht
#          anders liegen (Debug-Modus F1 zeigt Hitboxen auf der Karte an).
SECTOR_UV = {1: (0.50, 0.78), 2: (0.22, 0.55), 3: (0.78, 0.52),
             4: (0.28, 0.30), 5: (0.75, 0.17),
             # AUFTRAG 19 (PUNKT 2): Sektoren 6-8 hinter dem Dunklen
             # Sektor - der Weg fuehrt weiter in den Feindraum (oben
             # Mitte -> oben links -> Zentrum rechts, alle Positionen
             # kollisionsfrei zu Objekt-Radien + Touch-Puffer, geprueft
             # in tools/check_campaign.py). Route baut sich automatisch
             # aus sorted(SECTOR_UV.keys()).
             6: (0.46, 0.13), 7: (0.19, 0.14), 8: (0.66, 0.38)}

OBJECTS = [
    # AUFTRAG 17: Planeten/Signale ~25 % groesser (rad relativ zur Bildhoehe)
    # und Labels groesser - Karte und Ziele besser erkennbar. Hitboxen
    # (hit_r) und Highlights skalieren automatisch mit.
    # AUFTRAG GANZE-WOELBUNG: "lift" steuert die Auswahl-Woelbung JEDES
    # Objekts (gilt fuer ALLE Kampagnen-Etappen + Signale). Am ECHTEN
    # bg_world.jpg vermessen (scripts/measure_map_objects.py + Raster-
    # Crops):
    #   mask  -> Radius der weichen Woelb-Region in x objekt-rad. Muss
    #            GROSS genug sein, dass das ganze Objekt/Ensemble
    #            hineinliegt (vorher hob die alte 1.16r-Maske nur einen
    #            Kreis IN der Erde -> Nutzer sah "Zirkel auf der Erde").
    #   rr    -> Alternative zu mask: Radius direkt als Anteil der
    #            Screen-HOEHE (fuer Riesen-Objekte wie die Erde, deren
    #            sichtbare Scheibe ~4x objekt-r ist).
    #   core  -> Anteil der Region, der VOLL vergroessert ist, bevor
    #            der Effekt weich zur Kante verfliesst (soll knapp
    #            UEBER der Objekt-Kante liegen -> keine Geister-Kanten).
    #   dx/dy -> optionale Verschiebung des Woelb-Zentrums in Bild-UV
    #            (wenn der Anker nicht exakt auf der Objekt-Mitte sitzt,
    #            z. B. Erde: echte Planeten-Mitte liegt UNTERHALB des
    #            Bildrandes; Nebelkern/Kernwelt: Planeten-Mitte neben
    #            dem Anker). Hitbox/Label/Ringe bleiben unveraendert.
    {"id": "sector_1", "kind": "sector", "sector": 1, "shape": "circle",
     "uv": SECTOR_UV[1], "rad": 0.096, "name": "ERDE",
     # Vermessen: Erde ist eine RIESENSCHEIBE (Radius ~0.39 Bildhoehen),
     # deren Mitte knapp UNTER dem Bildrand liegt -> ganze sichtbare
     # Scheibe mit eigenem Zentrum woelben (kein Zirkel mehr).
     "lift": {"rr": 0.47, "core": 0.85, "dy": 0.348}},
    {"id": "sector_2", "kind": "sector", "sector": 2, "shape": "hex",
     "uv": SECTOR_UV[2], "rad": 0.077, "name": "RAUMSTATION",
     "lift": {"mask": 3.0, "core": 0.52}},    # Truemmerfeld + Mond ringum
    {"id": "sector_3", "kind": "sector", "sector": 3, "shape": "circle",
     "uv": SECTOR_UV[3], "rad": 0.090, "name": "ASTEROIDENGÜRTEL",
     "lift": {"mask": 2.4, "core": 0.55}},    # Station + Asteroiden-Kranz
    {"id": "sector_4", "kind": "sector", "sector": 4, "shape": "circle",
     "uv": SECTOR_UV[4], "rad": 0.074, "name": "MARS",
     "lift": {"mask": 3.5, "core": 0.55}},    # Festung zieht nach unten-links
    {"id": "sector_5", "kind": "sector", "sector": 5, "shape": "circle",
     "uv": SECTOR_UV[5], "rad": 0.084, "name": "DUNKLER SEKTOR",
     "lift": {"mask": 3.1, "core": 0.55}},    # Schlachtkreuzer ist breit
    # AUFTRAG 19: die drei neuen Kampagnen-Abschnitte (keine neuen
    # Grafiken - dieselben Formen/Farben wie die alten Sektoren).
    {"id": "sector_6", "kind": "sector", "sector": 6, "shape": "ring",
     "uv": SECTOR_UV[6], "rad": 0.078, "name": "DER RISS",
     "lift": {"mask": 2.8, "core": 0.55}},    # Portal + Leucht-Ring
    {"id": "sector_7", "kind": "sector", "sector": 7, "shape": "hex",
     "uv": SECTOR_UV[7], "rad": 0.080, "name": "NEBELKERN",
     "lift": {"mask": 2.7, "core": 0.60, "dx": -0.052, "dy": 0.018}},
    {"id": "sector_8", "kind": "sector", "sector": 8, "shape": "circle",
     "uv": SECTOR_UV[8], "rad": 0.094, "name": "KERNWELT",
     "lift": {"mask": 2.1, "core": 0.55, "dx": -0.031, "dy": 0.037}},
    {"id": "signal_a", "kind": "signal", "shape": "diamond",
     "uv": (0.115, 0.335), "rad": 0.047, "name": "FEINDSIGNALE",
     "lift": {"mask": 2.4, "core": 0.60}},
    {"id": "signal_b", "kind": "signal", "shape": "diamond",
     "uv": (0.895, 0.335), "rad": 0.047, "name": "BOSS-SIGNAL",
     "lift": {"mask": 2.6, "core": 0.60}},
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
        self._sel_geo = None       # Geometrie des ANGEBHOBENEN Gebiets
        self._dim = None           # Fokus-Abdunkelung (gecacht)
        self._dim_key = None
        self._lift = None          # angehobener Planet (gecacht)
        self._lift_key = None

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
        _s, _ox, _oy, iw, ih = self._tr
        sc = self._tr[0]
        H = ui_kit.H
        for o in OBJECTS:
            cx, cy = self.to_screen(o["uv"])
            r = max(6, int(o["rad"] * ih * sc))
            hit_r = max(u(26), int(r + u(12)))   # fingerfreundliche Touch-Flaeche
            # AUFTRAG GANZE-FLAECHE (Nutzer: "ich muss immer noch auf
            # den Zirkel druecken"): Die Hit-Flaeche deckt jetzt die
            # GESAMTE Woelb-Region ab - also den ganzen Planeten/das
            # ganze Ensemble, nicht nur den kleinen Anker-Zirkel.
            # Gleiche Quelle wie die Auswahl-Woelbung: "rr" = Anteil
            # der Screen-Hoehe (Erde), "mask" = x Objekt-Radius. Sitzt
            # das Woelb-Zentrum versetzt (dx/dy - z. B. Erde: die
            # Planeten-Mitte liegt UNTER dem Anker), wandert auch die
            # Hit-Mitte mit (hcx/hcy) - sonst bleibt die Unterkante
            # der Erde unantippbar.
            lift = o.get("lift") or {}
            hcx, hcy = cx, cy
            if "rr" in lift:
                lift_r = lift["rr"] * H
            elif "mask" in lift:
                lift_r = lift["mask"] * r
            else:
                lift_r = r
            if lift_r > hit_r:
                hit_r = int(min(lift_r, u(360)))
            if "dx" in lift or "dy" in lift:
                hcx = int(cx + lift.get("dx", 0.0) * iw * sc)
                hcy = int(cy + lift.get("dy", 0.0) * ih * sc)
            self._geo[o["id"]] = {"cx": cx, "cy": cy, "r": r,
                                  "hit_r": hit_r,
                                  "hcx": hcx, "hcy": hcy}
        return self._geo

    # ---------------- Interaktion ----------------
    def hit(self, pos):
        """Objekt unter dem Punkt (formnah, mit Touch-Puffer) oder None.
        AUFTRAG GANZE-FLAECHE: Hit-Mitte = Woelb-Zentrum (hcx/hcy) und
        Hit-Radius = gesamte Woelb-Region -> der ganze Planet antwortet,
        nicht nur der Zirkel am Anker. Ueberlappen sich grosse Hit-
        Flaeachen, gewinnt das naechstgelegene Objekt (best_d)."""
        if self._tr is None:
            return None
        best, best_d = None, 1e18
        px, py = pos
        for o in OBJECTS:
            g = self._geometry()[o["id"]]
            dx, dy = px - g["hcx"], py - g["hcy"]
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
        # Karte leicht abdunkeln -> Objekte/Labels bleiben lesbar (einmalig
        # gecacht). AUFTRAG 17: Abdunkelung reduziert (60 -> 45), die Karte
        # wirkt heller und die Planeten klarer erkennbar.
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 45))
        surf.blit(dim, (0, 0))
        self._bg, self._bg_key = surf, key
        return surf

    # ---------------- statische Ebene ----------------
    def _static_layer(self, states):
        """Ringe, Routen, Labels, Status-Pips - EINMAL pro (Groesse, Zustand)."""
        W, H = ui_kit.W, ui_kit.H
        sig = tuple(sorted((oid, st.get("status", ""), st.get("name", ""))
                           for oid, st in states.items()))
        # Auswahl im Cache-Key: das gewaehlte Objekt bekommt keinen
        # statischen Statusring mehr - der formpassende Highlight sitzt
        # am ANGEBHOBENEN Planeten (siehe _draw_lift).
        key = (W, H, self._tr_key, sig, self.selected)
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
            if o["id"] == self.selected:
                pass                   # Auswahl: statischer Ring entfaellt
            elif o["kind"] == "sector":
                pass                   # Planet-Auswahl: animierter Aussenring in draw()
            # feiner Statusring (immer sichtbar, sehr zurueckhaltend)
            elif o["shape"] == "circle":
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
            # AUFTRAG 17: Label groesser (F(9) -> F(11)) - bessere Lesbarkeit
            f = F(11)
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

    # ---------------- AUSWAHL: Fokus + WOELBUNG ----------------
    FOCUS_ALPHA = 86            # Abdunkelung der Umgebung (0..255)
    # AUFTRAG GANZE-WOELBUNG (Nutzer: "was ich will, ist das die ganze
    # Erde sich hervorwoelbt. Nicht der Zirkel auf der Erde."):
    # Die alte Maske (1.16r, hart) hob nur einen runden AUSSCHNITT aus
    # der Erde an - der Planet blieb groesstenteils am Boden und der
    # Nutzer sah einen Kreis IN der Erde. Jetzt:
    #   BULGE_MAG      : Zentrale Aufwoelung der Region (+16 %) - der
    #                    ganze Planet schwillt sichtbar Richtung Betrachter.
    #   LIFT_MASK_DEF  : Radius der weichen Woelb-Region (x objekt-rad).
    #                    Pro Objekt in OBJECTS["lift"]["mask"] ueber-
    #                    schrieben (am echten Bild vermessen).
    #   LIFT_CORE_DEF  : Voller Magnifikations-Kern (Anteil der Region),
    #                    danach weiches Verfliesen auf Alpha 0 -> keine
    #                    sichtbare Kreis-Kante. Auch pro Objekt ueber-
    #                    schreibbar (OBJECTS["lift"]["core"]).
    #   LIFT_UP        : Schwebende Hebung ueber der Karte (wie vorher).
    BULGE_MAG = 1.16
    LIFT_MASK_DEF = 2.05
    LIFT_CORE_DEF = 0.52
    LIFT_UP = 0.14

    def _focus_surface(self, oid):
        """Weiche Abdunkelung MIT radialem 'Loch' um das gewaehlte
        Objekt. Die Karte bleibt voll ersichtlich - nur die Umgebung
        tritt zurueck (Nutzer: 'Die Map ist immernoch ersichtlich, aber
        man sieht visuell, dass die Erde angewaehlt wurde'). Gecacht
        pro (Groesse, Transformation, Objekt). Das Loch folgt jetzt der
        WOELB-Region (nicht mehr 2.4r Pauschale), damit das ganze
        gewoelbte Objekt hell bleibt und nur die Umgebung abdunkelt."""
        W, H = ui_kit.W, ui_kit.H
        key = (W, H, self._tr_key, oid)
        if key == self._dim_key:
            return self._dim
        g = self._geometry()[oid]
        o = BY_ID.get(oid, {})
        R = self._lift_radius(o, g)
        R = int(R * self.BULGE_MAG) + u(34)
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, self.FOCUS_ALPHA))
        hole = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
        steps = 16
        for i in range(steps, 0, -1):
            rr = max(1, int(R * i / steps))
            a = int(self.FOCUS_ALPHA * (1.0 - (i / steps) ** 1.7))
            pygame.draw.circle(hole, (255, 255, 255, a), (R, R), rr)
        # Kern voll freistellen (die Ringe liessen 1-2 Alpha zurueck)
        pygame.draw.circle(hole, (255, 255, 255, self.FOCUS_ALPHA),
                           (R, R), max(1, R // steps))
        # Loch folgt dem WOELB-ZENTRUM (bei Erde unter dem Bildrand),
        # nicht dem Anker - sonst dunkelt die Umgebung IM Planeten ab.
        wx, wy = self._lift_center(o, g)
        dim.blit(hole, (int(wx) - R, int(wy) - R),
                 special_flags=pygame.BLEND_RGBA_SUB)
        self._dim, self._dim_key = dim, key
        return dim

    def _lift_radius(self, o, g):
        """Radius der Woelb-Region in Screen-px: Entweder explizit als
        Anteil der Screen-Hoehe (lift["rr"] - fuer Riesen wie die Erde)
        oder als Vielfaches des Objekt-Radius (lift["mask"], Default
        LIFT_MASK_DEF)."""
        lift = o.get("lift", {})
        if "rr" in lift:
            return max(8.0, lift["rr"] * ui_kit.H)
        return max(8.0, g["r"] * lift.get("mask", self.LIFT_MASK_DEF))

    def _lift_center(self, o, g):
        """Zentrum der Woelb-Region (Screen-px). Ohne dx/dy exakt der
        Objekt-Anker; sonst um den gemessenen UV-Versatz verschoben
        (z. B. Erde: echte Planeten-Mitte unter dem Bildrand)."""
        lift = o.get("lift", {})
        _s, _ox, _oy, iw, ih = self._tr
        dx = lift.get("dx", 0.0) * iw * _s
        dy = lift.get("dy", 0.0) * ih * _s
        return (g["cx"] + dx, g["cy"] + dy)

    def _bulge_surface(self, o, g):
        """NUTZERWUNSCH ("die GANZE Erde soll sich hervorwoelben, nicht
        der Zirkel auf der Erde"): Das gewaehlte Gebiet loest sich
        KOMPLETT aus dem Kartenbild und WOELBT sich zum Betrachter.

        Technik: eine pro Objekt GROSS genug gewaehlte Region (lift:
        "rr" als Anteil der Screen-Hoehe oder "mask" x objekt-rad -
        am echten bg_world.jpg vermessen, damit wirklich das ganze
        Objekt drin liegt) wird zentral um BULGE_MAG vergroessert und
        ueber eine weiche radiale Alpha-Maske gelegt: voller Kern bis
        zur Objekt-Kante, danach verfliesst der Effekt kontinuierlich
        auf Alpha 0. Radiale Vergroesserung bildet Kreise auf Kreise
        ab - Planeten bleiben formgetreu, nur eben GESCHAUMT. Kein
        harter Rand, kein Kreis mehr im Bild. Gecacht pro (Groesse,
        Transformation, Objekt, Bild) - Kosten nur EINMAL je Auswahl."""
        W, H = ui_kit.W, ui_kit.H
        key = (W, H, self._tr_key, o["id"], id(self._bg))
        if key == self._lift_key:
            return self._lift
        lift = o.get("lift", {})
        core_f = lift.get("core", self.LIFT_CORE_DEF)
        cx, cy = self._lift_center(o, g)
        R = int(self._lift_radius(o, g))     # Region deckt das GANZE Objekt
        S = R * 2
        crop = pygame.Surface((S, S), pygame.SRCALPHA)
        if self._bg is not None:
            area = pygame.Rect(cx - R, cy - R, S, S).clip(self._bg.get_rect())
            if area.w > 0 and area.h > 0:
                crop.blit(self._bg, (area.x - (cx - R), area.y - (cy - R)),
                          area)
        # WOELBUNG: Region zentral aufschaeumen ...
        Ms = max(2, int(S * self.BULGE_MAG))
        bulge = pygame.transform.smoothscale(crop, (Ms, Ms))
        # ... und per weicher radialer Maske einfuegen: voller Kern,
        # kontinuierlicher Alpha-Verlauf auf 0 an der Aussenkante ->
        # der Uebergang liegt im Weltraum UM den Planeten, nicht IM
        # Planeten (kein Zirkel mehr sichtbar).
        mask = pygame.Surface((Ms, Ms), pygame.SRCALPHA)
        steps = 40
        rm = Ms / 2.0
        for i in range(steps, 0, -1):        # aussen (a=0) -> innen (a=255)
            f = i / steps
            if f <= core_f:
                a = 255
            else:
                t = (f - core_f) / max(0.0001, 1.0 - core_f)
                a = int(255 * (1.0 - t) ** 1.45)
            pygame.draw.circle(mask, (255, 255, 255, a),
                               (Ms // 2, Ms // 2), max(1, int(rm * f)))
        bulge.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self._lift, self._lift_key = bulge, key
        return bulge

    def _draw_lift(self, surface, o, g, col, elapsed):
        """Schatten + Akzent-Glow + das sich WOELBENDE GESAMTE Gebiet.
        Liefert die verschobene Geometrie (cx, cy - Hebung, r * Woelb-
        faktor), damit Highlight, Verbindungslinie und Hinweis-Chip am
        gewoelbten Planeten sitzen statt auf der alten Stelle."""
        cx, cy, r = g["cx"], g["cy"], g["r"]
        lift = int(r * self.LIFT_UP) + int(u(3) * pulse(elapsed, 2.6, 0.0))
        # Woelb-Zentrum (bei Erde/Nebelkern/Kernwelt vom Anker versetzt)
        wx, wy = self._lift_center(o, g)
        R = self._lift_radius(o, g)
        # weicher Schatten UNTER dem schwebenden Objekt (gibt die Tiefe;
        # Breite folgt der Woelb-Region, nicht mehr dem alten 1.1x-Kreis)
        sw, sh_h = max(4, int(R * 1.06)), max(4, int(r * 0.62))
        sh = pygame.Surface((sw, sh_h), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 115), sh.get_rect())
        pygame.draw.ellipse(sh, (0, 0, 0, 75), sh.get_rect().inflate(
            -int(sw * 0.16), -int(sh_h * 0.24)))
        surface.blit(sh, sh.get_rect(center=(int(wx), int(g["cy"] + int(R * 0.72)))))
        # Akzent-Glow hinter dem gewoelbten Gebiet
        glow = radial_glow(_mix(col, WHITE, 0.30), int(R * 0.98))
        surface.blit(glow, glow.get_rect(center=(int(wx), int(wy - lift))),
                     special_flags=pygame.BLEND_ADD)
        spr = self._bulge_surface(o, g)
        surface.blit(spr, spr.get_rect(center=(int(wx), int(wy - lift))))
        # Highlight-Radius: bei grossen Woelb-Regionen folgt der Bogen
        # der OBJEKT-KANTE (Region * Kernanteil), nicht mehr dem kleinen
        # objekt-r - sonst schwebt der Bogen als Mini-Zirkel IM Planeten.
        lift_d = o.get("lift", {})
        if "hr" in lift_d:
            r_sel = max(4, int(lift_d["hr"] * ui_kit.H))
        else:
            r_sel = max(4, int(r * self.BULGE_MAG),
                        int(R * lift_d.get("core", self.LIFT_CORE_DEF) * 0.95))
        return {"cx": cx, "cy": cy - lift,
                "r": r_sel,
                "hit_r": g["hit_r"]}

    def _draw_hint(self, surface, g2, hint, col, elapsed):
        """Kleiner pulsierender Hinweis-Chip am gewaehlten Gebiet
        ('NOCHMAL ANTIPPEN · ...') - macht den Zwei-Klick-Flow sofort
        verstaendlich. Weicht dem Info-Panel aus (Positionen: ueber dem
        Planeten, unter dem Label, links vom Planeten)."""
        f = F(9)
        tw = f.size(hint)[0]
        w, h = tw + u(16), u(18)
        k = pulse(elapsed, 2.2, 0.0)
        W, H = ui_kit.W, ui_kit.H
        base_x = g2["cx"] - w // 2
        cands = [(base_x, max(u(46), g2["cy"] - g2["r"] - h - u(10))),
                 (base_x, g2["cy"] + g2["r"] + u(22)),
                 (g2["cx"] - g2["r"] - w - u(12), g2["cy"] - h // 2)]
        pan = self._panel_rect
        pos = cands[0]
        for px, py in cands:
            rr = pygame.Rect(px, py, w, h)
            if not (rr.right < W - u(4) and rr.top >= u(40)
                    and rr.bottom < H - u(4)):
                continue
            if pan is not None and rr.colliderect(pan.inflate(u(8), u(8))):
                continue
            pos = (px, py)
            break
        x, y = pos
        chip = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(chip, (4, 9, 18, 196), chip.get_rect(),
                         border_radius=u(7))
        pygame.draw.rect(chip, (*col, int(120 + 120 * k)), chip.get_rect(),
                         1, border_radius=u(7))
        surface.blit(chip, (x, y))
        surface.blit(f.render(hint, True, _mix(col, WHITE, 0.40)),
                     (x + u(8), y + (h - f.get_height()) // 2))

    # ---------------- Info-Panel ----------------
    def _draw_panel(self, surface, info):
        """Kompaktes Info-Panel unten rechts. Liefert/aktualisiert Button-Rects.
        PAKET 7D: Info-Zeilen werden auf Panelbreite umgebrochen (Story-Texte
        passen immer ins Panel) und bis zu 4 Zeilen beruecksichtigt."""
        W, H = ui_kit.W, ui_kit.H
        m = u(10)
        pw = min(int(W * 0.46), u(430))
        f_info = F(9)
        # Zeilen umbrechen (max. 4 Logikzeilen)
        wrapped = []
        for ln in info.get("lines", [])[:4]:
            wrapped += ui_kit.wrap_text(ln, f_info, pw - u(24))[:2]   # je Logikzeile max. 2 Screenzeilen
        # dynamische Hoehe: Titel+Status+Basis vs. Fortschritt + Infozeilen
        ph = u(96) + (u(16) if info.get("progress") is not None else 0) \
            + u(13) * len(wrapped) + u(30)
        ph = min(ph, int(H * 0.46))
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
        # Info-Zeilen (umgebrochen)
        for ln in wrapped:
            text(surface, ln, f_info, MUTED, (rect.x + pad, y))
            y += int(f_info.get_height() * 1.25)
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
        # Close-X (PAKET 7D: getoente Glasflaeche statt Schwarz)
        cxr = self._btn_rects["map_close"]
        _sh = pygame.Surface((max(2, cxr.w), max(2, cxr.h)), pygame.SRCALPHA)
        _sh.fill((30, 60, 88, 110))
        surface.blit(_sh, cxr.topleft)
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
            # PAKET 7D: transparent-getoente Flaeche (Glas), klare Kontur
            tint = (int(col[0] * 0.14), int(col[1] * 0.14), int(col[2] * 0.14))
            fill = (*tint, 120 if en else 46)
            sh = pygame.Surface((max(2, rr.w), max(2, rr.h)), pygame.SRCALPHA)
            sh.fill(fill)
            surface.blit(sh, rr.topleft)
            pygame.draw.rect(surface, col if en else _scaled_c(DIM, 0.9), rr,
                             2 if en else 1, border_radius=u(6))
            f = ui_kit.fit_font(lbl, 9, rr.w - u(10))
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
            g = self._sel_geo or self._geometry()[oid]
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
            col = GREEN if self.hit((g["hcx"], g["hcy"])) == o["id"] else RED
            # Objekt-Kreis + GESAMTE Hit-Flaeche um das Woelb-Zentrum
            pygame.draw.circle(surface, col, (g["cx"], g["cy"]), g["r"], 1)
            pygame.draw.circle(surface, (255, 90, 90),
                               (g["hcx"], g["hcy"]), g["hit_r"], 1)
            pygame.draw.line(surface, col, (g["hcx"] - 4, g["hcy"]),
                             (g["hcx"] + 4, g["hcy"]), 1)
            pygame.draw.line(surface, col, (g["hcx"], g["hcy"] - 4),
                             (g["hcx"], g["hcy"] + 4), 1)
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
        self._sel_geo = None
        surface.blit(self._bg_surface(img), (0, 0))
        geo = self._geometry()

        # NUTZER-FLOW (Kampagnenkarte): Das gewaehlte Gebiet HEBT SICH
        # HERVOR. Schritt 1: weiche Fokus-Abdunkelung um das Objekt -
        # die Karte bleibt voll ersichtlich, die Umgebung tritt nur
        # leicht zurueck ("man sieht visuell, dass die Erde angewaehlt
        # wurde").
        if self.selected and self.selected in geo:
            surface.blit(self._focus_surface(self.selected), (0, 0))

        surface.blit(self._static_layer(states), (0, 0))

        # Schritt 2: das Gebiet selbst loest sich aus dem Bild (weiche
        # runde Maske) und schwebt leicht vergroessert ueber der Karte -
        # eigener Schatten, Akzent-Glow, pulsierende Hebung. Highlight
        # + Hinweis-Chip folgen der neuen Position.
        if self.selected and self.selected in geo:
            o = BY_ID[self.selected]
            st = states.get(self.selected, {})
            col = st.get("col") or DEFAULT_COLOR[o["kind"]]
            self._sel_geo = self._draw_lift(surface, o, geo[self.selected],
                                            col, elapsed)

        # Planet states use broken outer-rim arcs around the planet image;
        # no center marker or small selection dot covers the clickable world.
        for index, o in enumerate(OBJECTS):
            if o["kind"] != "sector" or o["id"] == self.selected:
                continue
            g = geo[o["id"]]
            st = states.get(o["id"], {})
            status = st.get("status", "GESPERRT")
            col = st.get("col") or DEFAULT_COLOR[o["kind"]]
            rr = max(g["r"] + u(5), int(min(self._lift_radius(o, g) * .9,
                                             ui_kit.H * .44)))
            rect = pygame.Rect(g["hcx"] - rr, g["hcy"] - rr, rr * 2, rr * 2)
            active = status in ("AKTIV", "SCHIFFSMISSION")
            done = status == "ABGESCHLOSSEN"
            k = pulse(elapsed, 3.2, index * .43) if active else 0.0
            ring_col = (_scaled_c(col, .38 + .34 * k) if active else
                        _scaled_c(GREEN, .72) if done else _scaled_c(MUTED, .42))
            width = max(1, u(2) if active else 1)
            phase = elapsed * (.22 if active else 0.0) + index * .73
            for seg in range(4):
                start = phase + seg * math.pi / 2
                pygame.draw.arc(surface, ring_col, rect, start, start + .72, width)
            if active and k > .78:
                glow = radial_glow(_scaled_c(col, .28), max(6, int(rr * .42)))
                surface.blit(glow, glow.get_rect(center=(g["hcx"], g["hcy"])),
                             special_flags=pygame.BLEND_ADD)

        # Auswahl-Highlight (formfitting, folgt der ANGEBHOBENEN Flaeche)
        if self.selected and self.selected in geo:
            o = BY_ID[self.selected]
            st = states.get(self.selected, {})
            col = st.get("col") or DEFAULT_COLOR[o["kind"]]
            gsel = self._sel_geo or geo[self.selected]
            self._draw_highlight(surface, o, gsel, col, elapsed)

        # Panel
        self._panel_rect = None
        self._btn_rects = {}
        if info:
            self._draw_panel(surface, info)

        # Hinweis-Chip NACH dem Panel: er kann dem Panel ausweichen
        if self.selected and self.selected in geo and info \
                and info.get("hint"):
            o = BY_ID[self.selected]
            st = states.get(self.selected, {})
            col = st.get("col") or DEFAULT_COLOR[o["kind"]]
            self._draw_hint(surface, self._sel_geo or geo[self.selected],
                            info["hint"], col, elapsed)
