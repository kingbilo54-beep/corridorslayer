# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | campaign star chart.

All configured campaign destinations are interactive. Their
image-relative positions drive map focus and hit testing; all
other bodies in the retained panorama remain artwork. Campaign state and
mission actions are supplied by main.py, while this module owns chart
layout, status tags and the compact destination panel.
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
# Nur die acht konfigurierten Kampagnenziele sind interaktive Kartenobjekte.
# Planeten, Stationen, Schiffe und Signale im Bild bleiben Dekoration.
# uv  : Position relativ zur BILD-Groesse (0..1) - an bg_world.jpg angelehnt.
# rad : Radius relativ zur BILD-HOEHE (bleibt beim Skalieren formgetreu).
# shape: hit-test geometry; the artwork itself supplies the visible target.
# Hinweis: Werte hier feinjustieren, falls Objekte im echten Bild leicht
#          anders liegen (Debug-Modus F1 zeigt Hitboxen auf der Karte an).
SECTOR_UV = {
    # Auf sichtbare Himmelskoerper/Zielregionen im Panorama gelegt. Die
    # Bildkoordinaten bleiben die gemeinsame Quelle fuer Orbit und Hitbox.
    1: (0.87, 0.18),   # blauer Heimatwelt-Kandidat, ganz im Bild
    2: (0.77, 0.52),   # Orbitalstation
    3: (0.51, 0.66),   # Asteroidenguertel / Vorposten
    4: (0.08, 0.62),   # roter Planet
    5: (0.90, 0.67),   # Vulkanwelt am Rand des Feindsektors
    6: (0.50, 0.21),   # Risszentrum
    7: (0.70, 0.33),   # Nebelmond
    8: (0.50, 0.49),   # Gasriese im Kernsystem
    9: (0.12, 0.16),   # Karthax / brauner Planet links oben
    10: (0.06, 0.34),  # Nyx-Mond links
    11: (0.80, 0.06),  # Ashen Array / Vulkanposten
    12: (0.92, 0.40),  # Vesper am rechten Kartenrand
    13: (0.61, 0.44),  # Cinder Ring / Ringwelt
    14: (0.26, 0.30),  # Orpheus-Forschungsaußenposten
    15: (0.67, 0.75),  # Thronmond, vollständig sichtbarer Mond im unteren Bild
}

OBJECTS = [
    {"id": "sector_1", "kind": "sector", "sector": 1, "shape": "circle",
     "uv": SECTOR_UV[1], "rad": 0.060, "name": "ERDE"},
    {"id": "sector_2", "kind": "sector", "sector": 2, "shape": "circle",
     "uv": SECTOR_UV[2], "rad": 0.048, "name": "RAUMSTATION"},
    {"id": "sector_3", "kind": "sector", "sector": 3, "shape": "circle",
     "uv": SECTOR_UV[3], "rad": 0.040, "name": "ASTEROIDENGÜRTEL"},
    {"id": "sector_4", "kind": "sector", "sector": 4, "shape": "circle",
     "uv": SECTOR_UV[4], "rad": 0.078, "name": "MARS"},
    {"id": "sector_5", "kind": "sector", "sector": 5, "shape": "circle",
     "uv": SECTOR_UV[5], "rad": 0.070, "name": "DUNKLER SEKTOR"},
    {"id": "sector_6", "kind": "sector", "sector": 6, "shape": "circle",
     "uv": SECTOR_UV[6], "rad": 0.034, "name": "DER RISS"},
    {"id": "sector_7", "kind": "sector", "sector": 7, "shape": "circle",
     "uv": SECTOR_UV[7], "rad": 0.028, "name": "NEBELKERN"},
    {"id": "sector_8", "kind": "sector", "sector": 8, "shape": "circle",
     "uv": SECTOR_UV[8], "rad": 0.082, "name": "KERNWELT"},
    {"id": "sector_9", "kind": "sector", "sector": 9, "shape": "circle",
     "uv": SECTOR_UV[9], "rad": 0.066, "name": "KARTHAX"},
    {"id": "sector_10", "kind": "sector", "sector": 10, "shape": "circle",
     "uv": SECTOR_UV[10], "rad": 0.035, "name": "NYX-MOND"},
    {"id": "sector_11", "kind": "sector", "sector": 11, "shape": "circle",
     "uv": SECTOR_UV[11], "rad": 0.040, "name": "ASHEN ARRAY"},
    {"id": "sector_12", "kind": "sector", "sector": 12, "shape": "circle",
     "uv": SECTOR_UV[12], "rad": 0.047, "name": "VESPER"},
    {"id": "sector_13", "kind": "sector", "sector": 13, "shape": "circle",
     "uv": SECTOR_UV[13], "rad": 0.060, "name": "CINDER RING"},
    {"id": "sector_14", "kind": "sector", "sector": 14, "shape": "circle",
     "uv": SECTOR_UV[14], "rad": 0.030, "name": "ORPHEUS LABOR"},
    {"id": "sector_15", "kind": "sector", "sector": 15, "shape": "circle",
     "uv": SECTOR_UV[15], "rad": 0.048, "name": "THRONMOND"},
]
BY_ID = {o["id"]: o for o in OBJECTS}
DEFAULT_COLOR = {"sector": CYAN}
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
        self.hovered = None
        self._tr = None            # (s, ox, oy, iw, ih)
        self._tr_key = None
        self._geo = {}             # id -> dict(cx, cy, r, hit_r)
        self._bg = None            # gecachtes, eingepasstes Bild
        self._bg_key = None
        self._camera_bg = None
        self._camera_bg_key = None
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
        x, y = ox + uv[0] * iw * s, oy + uv[1] * ih * s
        if self.selected in BY_ID and self.selected in SECTOR_UV:
            ax, ay = (ox + SECTOR_UV[BY_ID[self.selected]["sector"]][0] * iw * s,
                      oy + SECTOR_UV[BY_ID[self.selected]["sector"]][1] * ih * s)
            zoom = 1.06
            x, y = ax + (x - ax) * zoom, ay + (y - ay) * zoom
        return (int(x), int(y))

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
            # Campaign nodes sit directly on destination artwork. Keep the
            # touch margin modest so decorative image areas stay inert.
            hit_r = max(u(28), int(r + u(8)))
            hcx, hcy = cx, cy
            self._geo[o["id"]] = {"cx": cx, "cy": cy, "r": r,
                                  "hit_r": hit_r,
                                  "hcx": hcx, "hcy": hcy}
        return self._geo

    # ---------------- Interaktion ----------------
    def hit(self, pos):
        """Kampagnenziel unter dem Punkt (mit begrenztem Touch-Puffer)."""
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
        if obj_id != self.selected:
            self.selected = obj_id
            self._geo = {}
            self._static_key = None
            self._camera_bg_key = None

    def set_hover(self, obj_id):
        if obj_id != self.hovered:
            self.hovered = obj_id
            self._static_key = None

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
        # Selection in the cache key keeps destination badges crisp.
        key = (W, H, self._tr_key, sig, self.selected, self.hovered)
        if key == self._static_key:
            return self._static
        lay = pygame.Surface((W, H), pygame.SRCALPHA)
        geo = self._geometry()

        for o in OBJECTS:
            g = geo[o["id"]]
            st = states.get(o["id"], {})
            col = st.get("col") or DEFAULT_COLOR[o["kind"]]
            locked = st.get("status", "").startswith("GESPERRT")
            name = st.get("name") or o["name"]
            # Compact numbered sector tags keep the artwork visible. Names
            # only appear for the focused or hovered destination.
            f = F(7)
            tag_col = col
            label = f.render(f'{o["sector"]:02d}', True, tag_col)
            tag = pygame.Rect(0, 0, u(20), u(15))
            tag.center = (g["cx"] + g["r"] // 2, g["cy"] - g["r"] // 2)
            pygame.draw.rect(lay, (3, 9, 20, 180), tag, border_radius=u(2))
            pygame.draw.line(lay, (*tag_col, 210 if not locked else 95),
                             (tag.left + u(3), tag.top + u(3)),
                             (tag.left + u(3), tag.bottom - u(3)), 1)
            lay.blit(label, label.get_rect(center=tag.center))
            if o["id"] in (self.hovered, self.selected):
                title = F(9).render(name, True, WHITE)
                badge = pygame.Rect(0, 0, title.get_width() + u(14),
                                    title.get_height() + u(6))
                badge.center = (g["cx"], max(u(52), g["cy"] - g["r"] - u(13)))
                pygame.draw.rect(lay, (3, 9, 20, 208), badge, border_radius=u(3))
                pygame.draw.line(lay, (*col, 225), badge.topleft,
                                 (badge.left + u(12), badge.top), max(1, u(2)))
                pygame.draw.line(lay, (*col, 225), badge.bottomleft,
                                 (badge.left + u(12), badge.bottom), max(1, u(2)))
                lay.blit(title, title.get_rect(center=badge.center))
        self._static, self._static_key = lay, key
        return lay

    def _draw_destination_lighting(self, surface, states, elapsed):
        """Soft contour lighting for the destination under hover or focus."""
        for index, o in enumerate(OBJECTS):
            g = self._geometry()[o["id"]]
            state = states.get(o["id"], {}).get("status", "GESPERRT")
            locked = state.startswith("GESPERRT")
            completed = state == "ABGESCHLOSSEN"
            selected = o["id"] == self.selected
            hovered = o["id"] == self.hovered
            if not selected and not hovered and not (state == "AKTIV"):
                continue
            base = GREEN if completed else (AMBER if selected else CYAN)
            if locked:
                base = MUTED
            k = pulse(elapsed, 2.4, index * .37)
            radius = max(u(24), int(g["r"] * (1.35 if hovered else 1.55)))
            strength = (.48 + .20 * k) if selected else (.34 + .14 * k)
            glow = radial_glow(_scaled_c(base, strength), radius)
            surface.blit(glow, glow.get_rect(center=(g["cx"], g["cy"])),
                         special_flags=pygame.BLEND_ADD)

    def _draw_hint(self, surface, g2, hint, col, elapsed):
        """Kleiner pulsierender Hinweis-Chip am gewaehlten Gebiet
        ('NOCHMAL ANTIPPEN · ...') - macht den Zwei-Klick-Flow sofort
        verstaendlich. Weicht dem Info-Panel aus (Positionen: ueber dem
        Planeten, unter dem Label, links vom Planeten)."""
        W, H = ui_kit.W, ui_kit.H
        f = ui_kit.fit_font(hint, 9, max(u(20), W - u(32)))
        tw = f.size(hint)[0]
        w, h = min(W - u(16), tw + u(16)), u(18)
        k = pulse(elapsed, 2.2, 0.0)
        base_x = min(max(u(8), g2["cx"] - w // 2), W - w - u(8))
        cands = [(base_x, max(u(46), g2["cy"] - g2["r"] - h - u(10))),
                 (base_x, g2["cy"] + g2["r"] + u(22)),
                 (max(u(8), g2["cx"] - g2["r"] - w - u(12)),
                  g2["cy"] - h // 2)]
        pan = self._panel_rect
        pos = (base_x, min(max(u(46), cands[0][1]), H - bar_h() - h - u(6)))
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
        bg = self._bg_surface(img)
        if self.selected in BY_ID:
            zoom = 1.06
            anchor = self.to_screen(BY_ID[self.selected]["uv"])
            key = (self._bg_key, self.selected, zoom)
            if key != self._camera_bg_key:
                self._camera_bg = pygame.transform.smoothscale(
                    bg, (int(ui_kit.W * zoom), int(ui_kit.H * zoom)))
                self._camera_bg_key = key
            surface.blit(self._camera_bg,
                         (int(anchor[0] * (1 - zoom)),
                          int(anchor[1] * (1 - zoom))))
        else:
            surface.blit(bg, (0, 0))
        geo = self._geometry()

        surface.blit(self._static_layer(states), (0, 0))
        self._draw_destination_lighting(surface, states, elapsed)

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
            self._draw_hint(surface, geo[self.selected],
                            info["hint"], col, elapsed)
