# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | UI-KIT (PAKET 6, LANDSCAPE)
================================================
Skalierbare Touch-Oberflaechen-Bibliothek + Landscape-Rotations-Layer.

Grundprinzip: Keine hartcodierten Pixel-Rechtecke. Jede Groesse wird
aus der aktuellen Bildschirmmasse abgeleitet:
  - U = min(W,H)/540  ist der Design-Massstab (1.0 bei 540px Breite).
  - u(px) skaliert eine Distanz, fs(pt) skaliert eine Schriftgroesse.
  - Draw und Hit-Test benutzen dieselben Layout-Objekte.

NEU IN PAKET 6:
  - Landscape-Layer: Ist die reale Surface im Hochformat (z.B. Android,
    wenn Pydroid die Ausrichtung nicht freigibt), wird unsichtbar in eine
    virtuelle Querformat-Surface gerendert und pro Frame um 90 Grad
    gedreht ausgegeben. Alle Screens sind damit IMMER Landscape.
    map_pos() rechnet Touch-Koordinaten zurueck (schneller Pfad: 1:1).
  - radial_glow(): gecachte additive Glueh-Sprites (RGB->Schwarz),
    gedacht fuer blit(..., special_flags=pygame.BLEND_ADD).
  - Button-Ripple: mark_pressed(id) beim Antippen -> draw_btn zeichnet
    einen expandierenden Ring als Touch-Feedback.
"""
import os
import pygame

# ---------------- Palette (Sci-Fi Neon) ----------------
VOID = (3, 6, 14)
PANEL = (8, 15, 29)
LINE = (25, 48, 70)
CYAN = (0, 255, 255)
CYAN_SOFT = (23, 145, 177)
ICE = (203, 247, 255)
WHITE = (232, 242, 250)
MUTED = (91, 119, 145)
DIM = (46, 68, 91)
VIOLET = (153, 94, 255)
MAGENTA = (255, 62, 177)
GREEN = (77, 255, 181)
RED = (255, 77, 100)
AMBER = (255, 190, 76)

# ---------------- Skalierung ----------------
U = 1.0
W = 540
H = 960
_MAX_FONT_CACHE = {}


def set_screen(w, h):
    """Wird 1x pro Frame aufgerufen; berechnet den Design-Massstab."""
    global W, H, U
    if (w, h) != (W, H):
        _MAX_FONT_CACHE.clear()   # Pixelgroessen ändern sich -> Fontcache leeren
    W, H = w, h
    U = max(0.62, min(w, h) / 540.0)


def u(px):
    """Skaliert eine Distanz in Bildschirmpixel."""
    return max(1, int(round(px * U)))


def fs(pt):
    """Skaliert eine Schriftgroesse (Designpunkt -> Pixel)."""
    return max(10, int(round(pt * U)))


def margin():
    return u(18)


def btn_h():
    """Standard-Touchhoehe: mind. 48 reale Pixel (Daumen-freundlich)."""
    return max(48, u(46))


# ---------------- Landscape-Rotations-Layer ----------------
# Android/Pydroid erlaubt es pygame nicht, die Bildschirmausrichtung zu
# setzen. Strategie: gerendert wird IMMER im Querformat. Passt die reale
# Surface nicht (Hochformat), landet der Frame in einer virtuellen
# Querformat-Surface und wird um 90 Grad gedreht ausgegeben.
# CS_ROTATE = 90 (Standard, entspricht Android-Landscape "Top nach rechts")
# oder -90 (Ger&auml;t andersherum gedreht).
_ROTATE = 90
try:
    _ROTATE = int(os.environ.get("CS_ROTATE", "90"))
    if _ROTATE not in (90, -90):
        _ROTATE = 90
except Exception:
    _ROTATE = 90

_real_w = 540
_real_h = 960
_vsurf = None
ROTATED = False          # True, wenn dieser Frame rotiert ausgegeben wird


def real_size():
    """Reale (physische) Surface-Groesse - fuer Touch-Events."""
    return (_real_w, _real_h)


def begin_frame():
    """Liefert die Surface, in die dieser Frame gezeichnet wird.
    Setzt W/H/U auf die VIRTUELLEN (Landscape-)Masse."""
    global _real_w, _real_h, _vsurf, ROTATED
    surf = pygame.display.get_surface()
    rw, rh = surf.get_size()
    _real_w, _real_h = rw, rh
    if rw >= rh:                          # Querformat: direkter Pfad
        ROTATED = False
        set_screen(rw, rh)
        return surf
    # Hochformat: virtuelle Querformat-Surface (exakt gespiegelt getauscht)
    ROTATED = True
    vw, vh = rh, rw
    vs = _vsurf
    if vs is None or vs.get_size() != (vw, vh):
        vs = pygame.Surface((vw, vh))
        _vsurf = vs
    set_screen(vw, vh)
    return vs


def end_frame():
    """Rotiert den virtuellen Frame auf die reale Surface (nur Hochformat-Pfad)."""
    if _vsurf is None or not ROTATED:
        return
    surf = pygame.display.get_surface()
    rot = pygame.transform.rotate(_vsurf, _ROTATE)
    if rot.get_size() != (_real_w, _real_h):
        rot = pygame.transform.scale(rot, (_real_w, _real_h))
    surf.blit(rot, (0, 0))


def map_pos(pos):
    """Reale Touch-/Maus-Koordinate -> virtuelle Zeichen-Koordinate."""
    if not ROTATED:
        return (int(pos[0]), int(pos[1]))
    # rotate(90, CCW): Quelle (x, y) -> Ziel (y, VW-1-x); rueckwaerts:
    lx = _vsurf.get_width() - 1 - int(pos[1])
    ly = int(pos[0])
    return (lx, ly)


def rotated():
    return ROTATED


# ---------------- Additive Glueh-Sprites (Cache) ----------------
_GLOW = {}


def radial_glow(color, radius):
    """Gecachtes weiches Glueh-Sprite (RGB nach Schwarz), r in Designpx.
    Einsatz: surface.blit(spr, pos, special_flags=pygame.BLEND_ADD)."""
    r = max(3, u(radius))
    key = (color, r)
    spr = _GLOW.get(key)
    if spr is None:
        size = r * 2
        spr = pygame.Surface((size, size))
        steps = max(6, r // 2)
        for i in range(steps, 0, -1):
            rr = int(r * i / steps)
            k = (1.0 - i / steps) ** 2.2
            c = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
            pygame.draw.circle(spr, c, (r, r), rr)
        if len(_GLOW) > 80:
            _GLOW.clear()
        _GLOW[key] = spr
    return spr


# ---------------- Schriften ----------------
_FAMILY = ["roboto", "segoeui", "helvetica", "arial"]


def set_family(names):
    global _FAMILY
    _FAMILY = list(names)
    _MAX_FONT_CACHE.clear()


def F(pt, bold=True):
    """Font-Cache: pt = Designpunkt (wird auf Screen skaliert)."""
    px = fs(pt)
    key = (px, bold)
    f = _MAX_FONT_CACHE.get(key)
    if f is None:
        f = pygame.font.SysFont(_FAMILY, px, bold=bold)
        _MAX_FONT_CACHE[key] = f
    return f


# PAKET 7D: Schrift-Fitting (kleiner Cache)
_FIT_CACHE = {}


def _F_px(px, bold=True):
    """Font-Cache auf Pixel-Basis (fuer sehr kleine Schrift im Fitting)."""
    key = (int(px), bold)
    f = _MAX_FONT_CACHE.get(key)
    if f is None:
        f = pygame.font.SysFont(_FAMILY, max(6, int(px)), bold=bold)
        _MAX_FONT_CACHE[key] = f
    return f


def fit_font(value, base_pt, max_w, bold=True):
    """Groesste Font, deren Text in max_w passt (Start: base_pt, Untergrenze
    7 reale Pixel). Garantiert: Beschriftungen bleiben INNERHALB des Buttons
    - kein Anschneiden, kein Kleben am Rand."""
    value = str(value)
    limit = max(u(10), int(max_w))
    key = (value, fs(base_pt), limit, bold)
    hit = _FIT_CACHE.get(key)
    if hit is not None:
        return hit
    px = fs(base_pt)
    while px > 7 and _F_px(px, bold).size(value)[0] > limit:
        px -= 1
    f = _F_px(px, bold)
    if len(_FIT_CACHE) > 400:
        _FIT_CACHE.clear()
    _FIT_CACHE[key] = f
    return f


# ---------------- Grund-Draw ----------------
def text(surface, value, font, color, pos, anchor="topleft"):
    img = font.render(str(value), True, color)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(img, rect)
    return rect


def _ring_pts(k):
    pts = []
    for d in range(1, k + 1):
        pts += [(d, 0), (-d, 0), (0, d), (0, -d), (d, d), (d, -d), (-d, d), (-d, -d)]
    return pts


def neon_text(surface, value, font, color, pos, anchor="topleft", glow_strength=2):
    """Neon-Text (8er-Ring-Glow, performant genug fuer Headlines)."""
    glow_img = font.render(str(value), True, color)
    base = glow_img.get_rect()
    setattr(base, anchor, pos)
    for alpha in (90, 45):
        glow_img.set_alpha(alpha)
        for dx, dy in _ring_pts(max(1, min(3, glow_strength))):
            surface.blit(glow_img, (base.x + dx, base.y + dy))
    img = font.render(str(value), True, WHITE)
    surface.blit(img, base)
    return base


def panel(surface, rect, fill=PANEL, border=LINE, radius=12, width=2):
    if fill:
        pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border, rect, width, border_radius=radius)


def wrap_text(value, font, max_w):
    """Bricht Text an realer Pixelbreite um (kein Abschneiden mehr)."""
    words = str(value).split()
    lines, cur = [], ""
    for w0 in words:
        cand = (cur + " " + w0).strip()
        if not cur or font.size(cand)[0] <= max_w:
            cur = cand
        else:
            lines.append(cur)
            cur = w0
    if cur:
        lines.append(cur)
    return lines or [""]


def draw_wrapped(surface, value, font, color, pos, max_w, line_h=None, anchor="topleft"):
    """Zeichnet umgebrochenen Text, liefert die benutzte Hoehe zurueck."""
    line_h = line_h or int(font.get_height() * 1.25)
    x, y = pos
    for i, ln in enumerate(wrap_text(value, font, max_w)):
        text(surface, ln, font, color, (x, y + i * line_h), anchor)
    return line_h * len(wrap_text(value, font, max_w))


# ---------------- Vollflaechen-Caches (Performance) ----------------
_OV = {}
_GRID = {}


def overlay(surface, alpha=160):
    """Verdunkelungsebene, pro (Groesse, Alpha) gecacht."""
    key = (W, H, alpha)
    s = _OV.get(key)
    if s is None:
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha))
        if len(_OV) > 24:
            _OV.clear()
        _OV[key] = s
    surface.blit(s, (0, 0))


def grid_bg(surface, elapsed):
    """Hologitter + Scanline, Gitterflaeche gecacht."""
    key = (W, H)
    s = _GRID.get(key)
    if s is None:
        s = pygame.Surface((W, H))
        s.fill(VOID)
        spacing = u(40)
        col = (8, 17, 30)
        for x in range(0, W, spacing):
            pygame.draw.line(s, col, (x, 0), (x, H))
        for y in range(0, H, spacing):
            pygame.draw.line(s, col, (0, y), (W, y))
        if len(_GRID) > 6:
            _GRID.clear()
        _GRID[key] = s
    surface.blit(s, (0, 0))
    y = int((elapsed * 38) % (H + u(80))) - u(40)
    if 0 <= y < H:
        pygame.draw.rect(surface, (12, 35, 50), (0, y, W, u(4)))


# ---------------- Buttons ----------------
class Btn:
    """Ein Touch-Element: Rechteck + Beschriftung + Aktion-ID.
    PAKET 7B: 'active' markiert dauerhaft-aktive Buttons (dezent pulsierende
    Kontur) - z.B. gewaehlte Module in der Werft."""
    __slots__ = ("id", "rect", "label", "sub", "accent", "enabled", "icon",
                 "active")

    def __init__(self, bid, rect, label="", sub="", accent=CYAN, enabled=True,
                 icon="", active=False):
        self.id = bid
        self.rect = rect
        self.label = label
        self.sub = sub
        self.accent = accent
        self.enabled = enabled
        self.icon = icon
        self.active = active

    def hit(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


def _mix_col(c, other, k):
    return (int(c[0] + (other[0] - c[0]) * k),
            int(c[1] + (other[1] - c[1]) * k),
            int(c[2] + (other[2] - c[2]) * k))


def draw_btn(surface, b, pressed=False):
    """PAKET 7B: Neon-Button mit Tiefe (Verlauf + Kantenlicht + Eckwinkel),
    klar unterscheidbaren Zustaenden (idle / hover / pressed / disabled /
    active) und Touch-Ripple. bleibt abwaertskompatibel."""
    rect = b.rect
    accent = b.accent if b.enabled else DIM
    if getattr(b, "icon", ""):
        icon_button(surface, rect, b.icon, accent if b.enabled else DIM, pressed, b.enabled)
        _draw_ripple(surface, b, rect)
        return
    hovered = (not pressed) and b.enabled and rect.collidepoint(
        map_pos(pygame.mouse.get_pos()))
    state = ("disabled" if not b.enabled else
             "pressed" if pressed else "hover" if hovered else "idle")
    surface.blit(_btn_base(rect, b.accent, state), rect.topleft)
    if state == "pressed":
        glow = radial_glow_k(b.accent, int(max(rect.w, rect.h) * 0.75), 0.24)
        surface.blit(glow, glow.get_rect(center=rect.center),
                     special_flags=pygame.BLEND_ADD)
    if state == "disabled":
        border = DIM
    elif state == "idle":
        border = tuple(max(30, int(c * 0.80)) for c in b.accent)
    else:
        border = accent
    pygame.draw.rect(surface, border, rect, 2 if pressed else 1, border_radius=u(10))
    _corner_brackets(surface, rect.inflate(-u(8), -u(8)),
                     DIM if state == "disabled" else accent, u(7))
    if getattr(b, "active", False) and state != "disabled":
        # PAKET 7C: Aktiv/Ausgewaehlt - gefuellte Flaeche + linke Akzentkante,
        # plus pulsierende Aussenkontur (dezent, nicht mehr der einzige Hinweis)
        _active_overlay(surface, rect, b.accent, u(10))
        if state != "pressed":
            k = pulse(pygame.time.get_ticks() * 0.001, 3.4)
            pygame.draw.rect(surface, _mix_col(b.accent, WHITE, 0.25 + 0.35 * k),
                             rect.inflate(2, 2), 1, border_radius=u(11))
    # PAKET 7D: Schrift passt IMMER in den Button (kein Abschneiden)
    lab_f = fit_font(b.label or " ", 15, rect.w - u(16))
    sub_f = fit_font(b.sub or " ", 10, rect.w - u(12))
    if b.sub:
        if pressed or hovered:
            neon_text(surface, b.label, lab_f, accent, (rect.centerx, rect.centery - u(9)), "center", 1)
        else:
            text(surface, b.label, lab_f, WHITE if b.enabled else DIM, (rect.centerx, rect.centery - u(9)), "center")
        text(surface, b.sub, sub_f, accent if b.enabled else DIM, (rect.centerx, rect.centery + u(10)), "center")
    else:
        if pressed or hovered:
            neon_text(surface, b.label, fit_font(b.label, 16, rect.w - u(16)), accent, rect.center, "center", 1)
        else:
            text(surface, b.label, lab_f, WHITE if b.enabled else DIM, rect.center, "center")
    _draw_ripple(surface, b, rect)


# ---------------- Touch-Ripple ----------------
_PULSES = {}


def mark_pressed(bid, now=None):
    """Beim Antippen aufrufen: loest den Ripple in draw_btn aus."""
    _PULSES[bid] = now if now is not None else pygame.time.get_ticks()
    if len(_PULSES) > 24:
        for k in list(_PULSES.keys())[:12]:
            del _PULSES[k]


def _draw_ripple(surface, b, rect):
    t0 = _PULSES.get(b.id)
    if t0 is None:
        return
    t = (pygame.time.get_ticks() - t0) / 260.0
    if t >= 1.0:
        del _PULSES[b.id]
        return
    rr = int(max(rect.w, rect.h) * (0.35 + 0.65 * t))
    a = int(150 * (1.0 - t))
    c = tuple(min(255, int(ch * a / 255 + 8)) for ch in b.accent)
    cx, cy = rect.center
    pygame.draw.circle(surface, c, (cx, cy), rr, max(2, u(2)))
    if rr < min(rect.w, rect.h) // 2:
        pygame.draw.circle(surface, c, (cx, cy), rr + u(3), 1)


def draw_btns(surface, btns, pressed_id=None):
    for b in btns.values():
        if b.rect.width > 0 and b.rect.height > 0:
            draw_btn(surface, b, pressed=(pressed_id == b.id))


def first_hit(btns, pos):
    for b in btns.values():
        if b.hit(pos):
            return b
    return None


# ---------------- Schalter (Toggle) ----------------
def draw_toggle(surface, rect, on, accent=GREEN):
    pygame.draw.rect(surface, (26, 32, 44), rect, border_radius=rect.h // 2)
    pygame.draw.rect(surface, accent if on else DIM, rect, 2, border_radius=rect.h // 2)
    r = max(8, int(rect.h * 0.36))
    kx = rect.right - r - u(5) if on else rect.x + r + u(5)
    pygame.draw.circle(surface, accent if on else MUTED, (kx, rect.centery), r)


def icon_button(surface, rect, kind, accent=CYAN, pressed=False, enabled=True):
    """PAKET 7B: Icon-Flaeche im Button-Skin (Tiefe + klare Kontur)."""
    state = "pressed" if pressed else ("idle" if enabled else "disabled")
    surface.blit(_btn_base(rect, accent, state), rect.topleft)
    border = DIM if not enabled else (accent if pressed else tuple(max(30, int(c * 0.80)) for c in accent))
    pygame.draw.rect(surface, border, rect, 2 if pressed else 1, border_radius=u(10))
    _corner_brackets(surface, rect.inflate(-u(8), -u(8)),
                     DIM if not enabled else accent, u(6))
    cx, cy = rect.center
    col = WHITE if enabled else DIM
    s = max(2, u(2))
    if kind == "pause":
        bw = u(5)
        pygame.draw.rect(surface, col, (cx - bw * 2, cy - u(8), bw, u(16)), border_radius=s)
        pygame.draw.rect(surface, col, (cx + bw, cy - u(8), bw, u(16)), border_radius=s)
    elif kind in ("sound_on", "sound_off"):
        pygame.draw.polygon(surface, col, [(cx - u(9), cy - u(4)), (cx - u(3), cy - u(4)),
                                           (cx + u(3), cy - u(9)), (cx + u(3), cy + u(9)),
                                           (cx - u(3), cy + u(4)), (cx - u(9), cy + u(4))])
        if kind == "sound_on":
            pygame.draw.arc(surface, col, (cx + u(2), cy - u(8), u(9), u(16)), -1.0, 1.0, s)
            pygame.draw.arc(surface, col, (cx + u(4), cy - u(11), u(12), u(22)), -0.9, 0.9, s)
        else:
            pygame.draw.line(surface, RED, (cx + u(4), cy - u(6)), (cx + u(12), cy + u(6)), s + 1)
            pygame.draw.line(surface, RED, (cx + u(12), cy - u(6)), (cx + u(4), cy + u(6)), s + 1)
    elif kind == "close":
        pygame.draw.line(surface, col, (cx - u(7), cy - u(7)), (cx + u(7), cy + u(7)), s + 1)
        pygame.draw.line(surface, col, (cx + u(7), cy - u(7)), (cx - u(7), cy + u(7)), s + 1)
    elif kind == "back":
        pygame.draw.polygon(surface, col, [(cx + u(6), cy - u(9)), (cx + u(6), cy + u(9)),
                                           (cx - u(8), cy)])
        pygame.draw.line(surface, col, (cx - u(8), cy), (cx + u(9), cy), s)
    elif kind == "play":
        pygame.draw.polygon(surface, col, [(cx - u(6), cy - u(9)), (cx - u(6), cy + u(9)),
                                           (cx + u(9), cy)])


# ======================================================================
# PAKET 7A: COMPACT SCI-FI RPG LAYER
# PAKET 7B: BUTTON-SKIN MIT TIEFE UND ZUSTAENDEN
# ======================================================================
# Ziel: hochwertige, zurueckhaltende Optik statt Mobile-Game-Look.
#  - Buttons heben sich klar vom Hintergrund ab: dunkles Halbtransparent-
#    Glas + Verlauf + Kantenlicht + Eckwinkel (Tiefe), Akzent-Kontur.
#  - Zustaende: idle / hover / pressed / disabled (+ active = Puls).
#  - Kompakte Buttons: kleines sichtbares Element IM grossen Touch-Rect.
#  - Schmale Aktionsleiste am unteren Bildschirmrand.
#  - Vector-Icons (keine Assets noetig) + langsame, gestaffelte Glow-Pulse.
# Alle bisherigen Funktionen/Konstanten bleiben unveraendert nutzbar.

import math as _math

_BAR_BG = {}
_GLASS = {}
_GLOWK = {}
_BTN_SKIN = {}


def _btn_base(rect, accent, state):
    """PAKET 7B: Gecachte Button-Grundflaeche (Verlauf + Kantenlicht).
    PAKET 7D: KEINE schwarzen Flaeche mehr - transparente, leicht akzent-
    getoente Glasflaeche (der Hintergrund schimmert bewusst durch) mit
    klarer Kontur. state: 'idle'|'hover'|'pressed'|'disabled'."""
    w, h = max(4, int(rect.w)), max(4, int(rect.h))
    key = (w, h, accent, state)
    s = _BTN_SKIN.get(key)
    if s is None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        # Grundtoenung: Anteil der Akzentfarbe auf dunklem Glas
        tint_k = {"disabled": 0.05, "pressed": 0.26, "hover": 0.20}.get(state, 0.14)
        tint = tuple(int(c * tint_k) for c in accent)
        # Deckkraft: deutlich transparenter als 7B (7B: 184-248)
        alpha = {"disabled": 52, "pressed": 158, "hover": 128}.get(state, 100)
        s.fill((*tint, alpha))
        # Vertikaler Verlauf: oben etwas heller getoent -> Tiefe ohne Schwarz
        grad = {"disabled": 10, "pressed": 54, "hover": 46}.get(state, 38)
        rows = max(4, h // 2)
        for i in range(rows):
            row_alpha = int((1.0 - i / rows) * grad)
            if row_alpha <= 0:
                continue
            pygame.draw.line(s, (*tint, row_alpha), (0, i), (w, i))
        # Kantenlicht oben + weicher Sockel unten (Plastizitaet)
        light_a = {"disabled": 6, "pressed": 46, "hover": 34}.get(state, 24)
        pygame.draw.line(s, (255, 255, 255, light_a), (0, 0), (w, 0))
        pygame.draw.line(s, (0, 0, 0, 60), (0, h - 1), (w, h - 1))
        if len(_BTN_SKIN) > 140:
            _BTN_SKIN.clear()
        _BTN_SKIN[key] = s
    return s


def _active_overlay(surface, rect, accent, radius):
    """PAKET 7C: Aktiv/Ausgewaehlt-Flaeche - gefuellte Akzentflaeche +
    Akzentkante links. Macht den Zustand UNABHAENGIG von Hover/Puls klar
    erkennbar (Bedienkonsole: 'dieses System ist gewaehlt')."""
    s = pygame.Surface((max(4, rect.w), max(4, rect.h)), pygame.SRCALPHA)
    s.fill((int(accent[0] * 0.30), int(accent[1] * 0.30), int(accent[2] * 0.30), 46))
    pygame.draw.rect(s, (*accent, 120), (0, 0, u(3), rect.h))
    surface.blit(s, rect.topleft)


def _corner_brackets(surface, rect, color, length, lw=1):
    """Vier Eckwinkel im Sci-Fi-Stil (dezent, kein Vollrahmen)."""
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    length = max(2, length)
    ln = pygame.draw.line
    ln(surface, color, (x, y), (x + length, y), lw)
    ln(surface, color, (x, y), (x, y + length), lw)
    ln(surface, color, (x + w, y), (x + w - length, y), lw)
    ln(surface, color, (x + w, y), (x + w, y + length), lw)
    ln(surface, color, (x, y + h), (x + length, y + h), lw)
    ln(surface, color, (x, y + h), (x, y + h - length), lw)
    ln(surface, color, (x + w, y + h), (x + w - length, y + h), lw)
    ln(surface, color, (x + w, y + h), (x + w, y + h - length), lw)


def bar_h():
    """Hoehe der schlanken Aktionsleiste (Touch-Streifen)."""
    return max(44, u(46))


def compact_btn_h():
    """Sichtbare Hoehe kompakter Buttons (Touch-Rect bleibt groesser)."""
    return u(28)


def icon_touch():
    """Touch-Kantenlaenge fuer Icon-Buttons (visuell kleiner gezeichnet)."""
    return max(38, u(38))


def pulse(elapsed, period=3.6, phase=0.0, lo=0.0, hi=1.0):
    """Langsamer Sinus-Puls 0..1. Ueber 'phase' gestaffelt (nicht alle
    Elemente gleichzeitig)."""
    k = 0.5 + 0.5 * _math.sin(_math.tau * elapsed / period + phase)
    return lo + (hi - lo) * k


def radial_glow_k(color, radius, k=1.0):
    """radial_glow mit Intensitaetskaler k (0..1), k in 0.1-Stufen gecacht."""
    kb = round(max(0.05, min(1.0, k)) * 10) / 10.0
    c = (int(color[0] * kb), int(color[1] * kb), int(color[2] * kb))
    return radial_glow(c, radius)


def action_bar_rect(h=None):
    """Schmale Leiste am unteren Bildschirmrand (voll breit)."""
    return pygame.Rect(0, H - (h or bar_h()), W, (h or bar_h()))


def draw_action_bar(surface, rect, accent=CYAN, elapsed=0.0):
    """Dunkles, transparentes Leisten-Panel mit duenner Neon-Oberkante
    (Flaeche gecacht, Linie dezenter Puls)."""
    key = (rect.w, rect.h)
    s = _BAR_BG.get(key)
    if s is None:
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        s.fill((4, 9, 18, 200))
        pygame.draw.line(s, (255, 255, 255, 10), (0, 1), (rect.w, 1), 1)
        _BAR_BG[key] = s
    surface.blit(s, rect.topleft)
    a = 70 + int(50 * pulse(elapsed, 4.2))
    line = pygame.Surface((rect.w, 2), pygame.SRCALPHA)
    line.fill((accent[0], accent[1], accent[2], a))
    surface.blit(line, (rect.x, rect.y))


def glass_panel(surface, rect, accent=CYAN, radius=None, alpha=210, width=None):
    """Dunkles, transparentes Panel mit duenner Neon-Kontur (gecacht).
    PAKET 7B: Kontur etwas kraeftiger. PAKET 7C: zusaetzliche Akzent-
    Oberkante (Konsole: 'Bedienpanel'), hebt Panels klarer vom Hintergrund ab."""
    radius = u(radius) if radius else u(12)
    width = width or max(1, u(1.5))
    key = (rect.w, rect.h, accent, radius, alpha)
    s = _GLASS.get(key)
    if s is None:
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        s.fill((4, 9, 18, alpha))
        pygame.draw.rect(s, (accent[0], accent[1], accent[2], 130),
                         (0, 0, rect.w, rect.h), 2, border_radius=radius)
        pygame.draw.rect(s, (255, 255, 255, 20),
                         (u(4), u(4), rect.w - u(8), rect.h - u(8)), 1,
                         border_radius=max(2, radius - u(4)))
        # PAKET 7C: Akzent-Oberkante (Konsolen-Look)
        pygame.draw.line(s, (accent[0], accent[1], accent[2], 88),
                         (u(10), 1), (rect.w - u(10), 1), 2)
        if len(_GLASS) > 40:
            _GLASS.clear()
        _GLASS[key] = s
    surface.blit(s, rect.topleft)
    pygame.draw.rect(surface, accent, rect, width, border_radius=radius)


def draw_icon(surface, kind, cx, cy, s, color):
    """Kleine Vector-Icons fuer kompakte Buttons (s skaliert, ~Design-px)."""
    def U(v):
        return max(1, int(round(v * s / 16.0)))
    lw = max(1, U(2))
    if kind == "flask":                     # Forschung
        pygame.draw.polygon(surface, color,
                            [(cx - U(3), cy - U(8)), (cx + U(3), cy - U(8)),
                             (cx + U(7), cy + U(7)), (cx - U(7), cy + U(7))], lw)
        pygame.draw.line(surface, color, (cx - U(4), cy), (cx + U(4), cy), lw)
    elif kind == "hex":                     # Skill-Nexus
        pts = [(cx + _math.cos(_math.radians(60 * i - 30)) * U(8),
                cy + _math.sin(_math.radians(60 * i - 30)) * U(8)) for i in range(6)]
        pygame.draw.polygon(surface, color, pts, lw)
        pygame.draw.circle(surface, color, (cx, cy), max(1, U(2)))
    elif kind == "map":                     # Galaxie
        pygame.draw.circle(surface, color, (cx - U(3), cy - U(2)), U(4), lw)
        pygame.draw.circle(surface, color, (cx + U(4), cy + U(3)), U(3), lw)
        pygame.draw.line(surface, color, (cx - U(6), cy + U(6)), (cx + U(6), cy - U(6)), lw)
    elif kind == "gear":                    # System
        pygame.draw.circle(surface, color, (cx, cy), U(6), lw)
        for a in (0, 60, 120):
            ar = _math.radians(a)
            pygame.draw.line(surface, color,
                             (cx + _math.cos(ar) * U(6), cy + _math.sin(ar) * U(6)),
                             (cx + _math.cos(ar) * U(9), cy + _math.sin(ar) * U(9)), lw)
    elif kind == "power":                   # Beenden
        pygame.draw.arc(surface, color, (cx - U(6), cy - U(6), U(12), U(12)), 0.6, 5.7, lw)
        pygame.draw.line(surface, color, (cx, cy - U(9)), (cx, cy - U(2)), lw)
    elif kind == "shield":                  # Idle/Verteidigung
        pygame.draw.polygon(surface, color,
                            [(cx, cy - U(8)), (cx + U(6), cy - U(4)),
                             (cx + U(4), cy + U(5)), (cx, cy + U(8)),
                             (cx - U(4), cy + U(5)), (cx - U(6), cy - U(4))], lw)
    elif kind == "bolt":
        pygame.draw.polygon(surface, color,
                            [(cx + U(2), cy - U(8)), (cx - U(4), cy + U(1)),
                             (cx - U(0), cy + U(1)), (cx - U(2), cy + U(8)),
                             (cx + U(4), cy - U(1)), (cx + U(0), cy - U(1))])
    elif kind == "pause":
        bw = U(2)
        pygame.draw.rect(surface, color, (cx - bw * 2 - U(1), cy - U(6), bw, U(12)), border_radius=1)
        pygame.draw.rect(surface, color, (cx + bw + U(1), cy - U(6), bw, U(12)), border_radius=1)
    elif kind in ("sound_on", "sound_off"):
        pygame.draw.polygon(surface, color, [(cx - U(6), cy - U(3)), (cx - U(2), cy - U(3)),
                                             (cx + U(2), cy - U(6)), (cx + U(2), cy + U(6)),
                                             (cx - U(2), cy + U(3)), (cx - U(6), cy + U(3))])
        if kind == "sound_on":
            pygame.draw.arc(surface, color, (cx + U(1), cy - U(5), U(6), U(10)), -1.0, 1.0, lw)
        else:
            pygame.draw.line(surface, RED, (cx + U(3), cy - U(4)), (cx + U(8), cy + U(4)), lw)
            pygame.draw.line(surface, RED, (cx + U(8), cy - U(4)), (cx + U(3), cy + U(4)), lw)
    elif kind == "close":
        pygame.draw.line(surface, color, (cx - U(5), cy - U(5)), (cx + U(5), cy + U(5)), lw + 1)
        pygame.draw.line(surface, color, (cx + U(5), cy - U(5)), (cx - U(5), cy + U(5)), lw + 1)
    elif kind == "back":
        pygame.draw.polygon(surface, color, [(cx + U(4), cy - U(6)), (cx + U(4), cy + U(6)),
                                             (cx - U(6), cy)])
    elif kind == "play":
        pygame.draw.polygon(surface, color, [(cx - U(4), cy - U(6)), (cx - U(4), cy + U(6)),
                                             (cx + U(6), cy)])
    elif kind == "forward":                 # PAKET 8: Leisten-Scroll rechts
        pygame.draw.polygon(surface, color, [(cx - U(4), cy - U(6)), (cx - U(4), cy + U(6)),
                                             (cx + U(6), cy)])
    elif kind == "list":                    # PAKET 8: Quests
        for yy in (-4, 0, 4):
            pygame.draw.line(surface, color, (cx - U(3), cy + U(yy)),
                             (cx + U(7), cy + U(yy)), lw)
            pygame.draw.circle(surface, color, (cx - U(6), cy + U(yy)), U(1))
    elif kind == "calendar":                # PAKET 8: Weekly-Quests
        pygame.draw.rect(surface, color, (cx - U(7), cy - U(5), U(14), U(12)), lw)
        pygame.draw.line(surface, color, (cx - U(7), cy - U(1)), (cx + U(7), cy - U(1)), lw)
        pygame.draw.line(surface, color, (cx - U(4), cy - U(8)), (cx - U(4), cy - U(4)), lw)
        pygame.draw.line(surface, color, (cx + U(4), cy - U(8)), (cx + U(4), cy - U(4)), lw)
    elif kind == "star":                    # PAKET 8: Beschwörung
        pts = []
        for i in range(10):
            ang = -_math.pi / 2 + i * _math.pi / 5
            rr = U(8) if i % 2 == 0 else U(3.5)
            pts.append((cx + _math.cos(ang) * rr, cy + _math.sin(ang) * rr))
        pygame.draw.polygon(surface, color, pts, lw)


def draw_compact_btn(surface, b, pressed=False, pulse_k=None, layout="h"):
    """PAKET 7B: Kompakter Button im neuen Skin - sichtbares Element bewusst
    klein, zentriert im (grossen) Touch-Rect; Zustaende klar unterscheidbar.
      layout 'h': Icon + Label nebeneinander (Aktionsleiste HUD)
      layout 'v': Icon ueber Label (Menue-Leiste)
      b.icon    : nur Icon (Icon-Button)
      b.active  : dauerhaft-aktiv -> sanft pulsierende Kontur
    pulse_k: optionaler langsamer Glow 0..1 (nur fuer EINZELNE Elemente).
    """
    r = b.rect
    accent = b.accent if b.enabled else DIM
    icon_only = bool(getattr(b, "icon", "")) and not b.label
    # --- sichtbarer Innen-Rect ---
    if icon_only:
        vs = min(r.w, r.h) - u(10)              # quadratisch, mit Luft
        vr = pygame.Rect(0, 0, max(u(22), vs), max(u(22), vs))
        vr.center = r.center
    else:
        vh = min(r.h - u(8), compact_btn_h() + (u(8) if b.sub else 0))
        vh = max(u(20), vh)
        vr = pygame.Rect(r.x + u(6), r.centery - vh // 2, r.w - u(12), vh)
    hovered = (not pressed) and b.enabled and r.collidepoint(map_pos(pygame.mouse.get_pos()))
    state = ("disabled" if not b.enabled else
             "pressed" if pressed else "hover" if hovered else "idle")
    surface.blit(_btn_base(vr, b.accent, state), vr.topleft)
    if pulse_k is not None and not pressed:
        glow = radial_glow_k(accent, int(max(vr.w, vr.h) * 0.9), 0.10 + 0.12 * pulse_k)
        surface.blit(glow, glow.get_rect(center=vr.center), special_flags=pygame.BLEND_ADD)
    if pressed:
        glow = radial_glow_k(accent, int(max(vr.w, vr.h) * 0.8), 0.28)
        surface.blit(glow, glow.get_rect(center=vr.center), special_flags=pygame.BLEND_ADD)
    if state == "disabled":
        border = DIM
    elif state == "idle":
        border = tuple(max(30, int(c * 0.80)) for c in b.accent)
    else:
        border = accent
    pygame.draw.rect(surface, border, vr, 2 if pressed else 1, border_radius=u(7))
    _corner_brackets(surface, vr.inflate(-u(6), -u(6)),
                     DIM if state == "disabled" else accent, max(3, u(4)))
    if getattr(b, "active", False) and state != "disabled":
        # PAKET 7C: Aktiv/Ausgewaehlt (z.B. Werft-Modulchips): gefuellte
        # Flaeche + Akzentkante - klar von Hover/Kontur unterscheidbar
        _active_overlay(surface, vr, b.accent, u(7))
        if state != "pressed":
            k = pulse(pygame.time.get_ticks() * 0.001, 3.4)
            pygame.draw.rect(surface, _mix_col(b.accent, WHITE, 0.25 + 0.35 * k),
                             vr.inflate(2, 2), 1, border_radius=u(8))
    # --- Inhalt ---
    if icon_only:
        col = WHITE if b.enabled else DIM
        draw_icon(surface, b.icon, vr.centerx, vr.centery, u(15), col)
    elif layout == "v":
        if b.icon:
            draw_icon(surface, b.icon, vr.centerx, vr.top + u(9), u(13),
                      accent if b.enabled else DIM)
        # PAKET 7D: Label immer innerhalb des sichtbaren Buttons
        f = fit_font(b.label, 9, vr.w - u(8))
        img = f.render(b.label, True, WHITE if b.enabled else DIM)
        surface.blit(img, img.get_rect(midtop=(vr.centerx, vr.top + u(17))))
    else:
        tx = vr.centerx
        if b.icon:
            draw_icon(surface, b.icon, vr.x + u(13), vr.centery, u(13),
                      accent if b.enabled else DIM)
            tx = vr.x + u(26) + (vr.w - u(26)) // 2
        f = fit_font(b.label, 11, (vr.w - u(30)) if b.icon else (vr.w - u(10)))
        img = f.render(b.label, True, WHITE if b.enabled else DIM)
        surface.blit(img, img.get_rect(center=(tx, vr.centery - (u(6) if b.sub else 0))))
        if b.sub:
            f2 = fit_font(str(b.sub), 8, vr.w - u(10))
            img2 = f2.render(str(b.sub), True, accent if b.enabled else DIM)
            surface.blit(img2, img2.get_rect(midtop=(tx, vr.centery + u(4))))
    _draw_ripple(surface, b, r)


def draw_compact_icon_btn(surface, b, pressed=False):
    """PAKET 7B: Icon-Button im neuen Skin (visuell ~28px im grossen Touch-Feld)."""
    r = b.rect
    accent = b.accent if b.enabled else DIM
    vs = max(u(22), min(r.w, r.h) - u(10))
    vr = pygame.Rect(0, 0, vs, vs)
    vr.center = r.center
    hovered = (not pressed) and b.enabled and r.collidepoint(map_pos(pygame.mouse.get_pos()))
    state = ("disabled" if not b.enabled else
             "pressed" if pressed else "hover" if hovered else "idle")
    surface.blit(_btn_base(vr, b.accent, state), vr.topleft)
    if pressed:
        glow = radial_glow_k(accent, int(vs * 0.9), 0.30)
        surface.blit(glow, glow.get_rect(center=vr.center), special_flags=pygame.BLEND_ADD)
    if state == "disabled":
        border = DIM
    elif state == "idle":
        border = tuple(max(30, int(c * 0.80)) for c in b.accent)
    else:
        border = accent
    pygame.draw.rect(surface, border, vr, 2 if pressed else 1, border_radius=u(7))
    _corner_brackets(surface, vr.inflate(-u(6), -u(6)),
                     DIM if state == "disabled" else accent, max(3, u(4)))
    draw_icon(surface, b.icon, vr.centerx, vr.centery, u(15),
              WHITE if b.enabled else DIM)
    _draw_ripple(surface, b, r)


# ======================================================================
# PAKET 8: MINI-BUTTONS (kompakte Menueleiste)
# ======================================================================
# Rechteckige Buttons mit maximal leicht gerundeten Ecken, deutlich
# geringerer Hoehe/Breite, kleiner Schrift und einheitlichen Massen.
# Alle Zustaende bleiben erhalten (idle/hover/pressed/disabled/active),
# Leuchteffekte sind bewusst minimal. Bestehende draw_btn/draw_compact_btn
# bleiben unveraendert im Einsatz (Werft, Karten etc.).

MINI_PT = 12          # Basisschriftgroesse (Designpunkt)
MINI_RADIUS = 4       # leicht gerundete Ecken (Designpixel)

_MINI_BG = {}


def mini_btn_h():
    """Einheitliche Hoehe der Mini-Buttons."""
    return max(24, u(30))


def _mini_base(rect, accent, state):
    key = (rect.w, rect.h, accent, state)
    s = _MINI_BG.get(key)
    if s is None:
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        if state == "pressed":
            s.fill((accent[0], accent[1], accent[2], 52))
        elif state == "hover":
            s.fill((accent[0], accent[1], accent[2], 26))
        elif state == "active":
            s.fill((accent[0], accent[1], accent[2], 34))
        elif state == "disabled":
            s.fill((18, 24, 34, 160))
        else:
            s.fill((10, 18, 30, 190))
        _MINI_BG[key] = s
    return s


def draw_mini_btn(surface, b, pressed=False, pulse_k=None):
    """PAKET 8: kompakter Rechteck-Button (Icon links, kurze Beschriftung).
    Fuer 10-12 Buttons in einer Leiste ausgelegt; kein grosser Glow."""
    rect = b.rect
    accent = b.accent if b.enabled else DIM
    hovered = (not pressed) and b.enabled and rect.collidepoint(
        map_pos(pygame.mouse.get_pos()))
    active = getattr(b, "active", False) and not pressed
    if pressed:
        state = "pressed"
    elif not b.enabled:
        state = "disabled"
    elif hovered:
        state = "hover"
    elif active:
        state = "active"
    else:
        state = "idle"
    surface.blit(_mini_base(rect, b.accent, state), rect.topleft)
    if state == "pressed" or active:
        g = radial_glow_k(b.accent, int(max(rect.w, rect.h) * 0.6),
                          0.10 if pressed else 0.06)
        surface.blit(g, g.get_rect(center=rect.center),
                     special_flags=pygame.BLEND_ADD)
    if state == "disabled":
        border = DIM
    elif state == "idle":
        border = tuple(max(40, int(c * 0.72)) for c in b.accent)
    else:
        border = accent
    pygame.draw.rect(surface, border, rect, 2 if pressed else 1,
                     border_radius=u(MINI_RADIUS))
    if active and pulse_k is not None:
        pygame.draw.rect(surface, _mix_col(b.accent, WHITE, 0.2 + 0.3 * pulse_k),
                         rect.inflate(2, 2), 1, border_radius=u(MINI_RADIUS))
    # Beschriftung: passt IMMER in den Button (kein Abschneiden)
    pad = u(6)
    label = b.label or ""
    icon_w = 0
    if getattr(b, "icon", ""):
        icon_w = u(13)
        col = WHITE if b.enabled else DIM
        draw_icon(surface, b.icon, rect.x + pad + icon_w // 2,
                  rect.centery, u(11), col)
    if label:
        f = fit_font(label, MINI_PT, rect.w - 2 * pad - icon_w - (u(2) if icon_w else 0))
        col = WHITE if b.enabled else DIM
        tx = rect.x + pad + icon_w + (u(2) if icon_w else 0)
        if icon_w:
            text(surface, label, f, col, (tx, rect.centery), "midleft")
        else:
            text(surface, label, f, col, rect.center, "center")
    _draw_ripple(surface, b, rect)


def mini_bar_layout(items, y=None, bar_h=None, pad=None, gap=None):
    """PAKET 8.1: untere Navigationsleiste mit FESTEN Button-Massen.
    Die Buttons werden NICHT mehr ueber die Bildschirmbreite gestreckt:
    je ~65x34 Design-px, gleichmassige Abstaende, Gruppe zentriert und
    insgesamt nur ~55-65 % der Bildschirmbreite breit. Ist die Gruppe
    breiter als der Screen (sehr schmale Screens), startet sie am linken
    Rand - den Overflow regelt main.py wie bisher per Scroll-Pfeilen.
    Liefert (bar_rect, [Btn...]); bar bleibt die volle schmale Leiste."""
    n = max(1, len(items))
    bw = u(NAV_BTN_W)
    bh = u(NAV_BTN_H)
    gap = u(NAV_GAP) if gap is None else gap
    pad = u(5) if pad is None else pad
    th = bar_h or nav_bar_h()
    bar = pygame.Rect(0, (H - th) if y is None else y, W, th)
    group = n * bw + (n - 1) * gap
    x0 = (W - group) // 2                 # zentriert, keine Streckung
    if x0 < pad:
        x0 = pad                          # Overflow -> Scroll uebernimmt
    by = bar.y + max(u(2), (bar.h - bh) // 2)
    btns = []
    for i, (bid, label, icon, acc) in enumerate(items):
        r = pygame.Rect(x0 + i * (bw + gap), by, bw, bh)
        btns.append(Btn(bid, r, label, "", acc, icon=icon))
    return bar, btns


# ======================================================================
# PAKET 8.1: NAV-LEISTE (eigener Renderer der unteren Navigation)
# ======================================================================
# Kompakte rechteckige Buttons im Dark-Sci-Fi-RPG-Stil:
#   - Feste Groesse ~65x34 Design-px (keine Streckung, einheitlich).
#   - Dunkler, leicht transparenter Metallhintergrund (Verlauf +
#     Kantenlicht, gecacht).
#   - Dezente cyanfarbene Umrandung; Hover/Druck heller; aktiver
#     Menuepunkt mit deutlichem Cyan-Akzent (Kontur + Unterkante +
#     cyan Beschriftung/Icon).
#   - Kleine Vector-Icons + gut lesbare Beschriftung, EINE geteilte
#     Font fuer alle Buttons (einheitliche Schriftgroesse).
#   - Keine uebergrossen Glow-Effekte; Ripple als Touch-Feedback.
# draw_mini_btn bleibt NICHT veraendert im Einsatz (Quest-/Beschwoe-
# rungs-Screens), damit andere Menues unberuehrt bleiben.

NAV_BTN_W = 80         # PAKET 8.7 MOBILE: 65 -> 80 (groessere Touchflaeche)
NAV_BTN_H = 44         # PAKET 8.7 MOBILE: 34 -> 44 (Daumen-freundlich)
NAV_GAP = 4            # gleichmassiger Abstand zwischen den Buttons
NAV_RADIUS = 4         # maximal leicht gerundete Ecken
NAV_PAD_X = 4          # horizontaler Innenrand je Seite
NAV_ICON_W = 11        # Kante der kleinen Icons
NAV_IGAP = 2           # Luecke zwischen Icon und Beschriftung

NAV_BORDER_IDLE = (30, 108, 132)     # dezente Cyan-Umrandung (Normal)
NAV_BORDER_ON = CYAN                 # Hover / Druck / Aktiv

_NAV_BG = {}


def nav_bar_h():
    """Hoehe der Nav-Leiste: Buttonhoehe + gleichmassiger Rand."""
    return u(NAV_BTN_H) + 2 * u(4)


def nav_label_font(labels=("GALAXIE", "SUMMON", "WEEKLY", "SYSTEM")):
    """EINE Font fuer alle Nav-Beschriftungen: die groesste Font, in der
    jedes Label (gemessen am breitesten, z. B. "SUMMON") in den Button
    passt. Vorhandene Schriftanpassung (fit_font/_F_px) wird weiterverwendet."""
    max_w = u(NAV_BTN_W) - 2 * u(NAV_PAD_X) - u(NAV_ICON_W) - u(NAV_IGAP)
    px = fs(MINI_PT)
    while px > 7 and any(_F_px(px).size(s)[0] > max_w for s in labels):
        px -= 1
    return _F_px(px)


def _nav_base(rect, state):
    """Gecachte Metall-Grundflaeche: dunkel, leicht transparent,
    Vertikal-Verlauf + Kantenlicht; Zustand toent dezent cyan."""
    w, h = max(4, int(rect.w)), max(4, int(rect.h))
    key = (w, h, state)
    s = _NAV_BG.get(key)
    if s is None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        tint_k = {"pressed": 0.22, "hover": 0.10, "active": 0.14,
                  "disabled": 0.0}.get(state, 0.0)
        alpha = 150 if state == "disabled" else 198
        top, bot, tint = (54, 66, 84), (13, 19, 29), (0, 176, 206)
        rows = max(2, h)
        for i in range(rows):
            k = i / (rows - 1)
            col = tuple(int(top[j] + (bot[j] - top[j]) * k
                            + (tint[j] - (top[j] + (bot[j] - top[j]) * k))
                            * tint_k) for j in range(3))
            pygame.draw.line(s, (*col, alpha), (0, i), (w, i))
        light = {"disabled": 8, "active": 40}.get(state, 26)
        pygame.draw.line(s, (255, 255, 255, light), (0, 0), (w, 0))
        pygame.draw.line(s, (0, 0, 0, 70), (0, h - 1), (w, h - 1))
        if len(_NAV_BG) > 60:
            _NAV_BG.clear()
        _NAV_BG[key] = s
    return s


def draw_nav_btn(surface, b, pressed=False, pulse_k=None, font=None):
    """PAKET 8.1: Button der unteren Navigationsleiste.
    Zustaende: idle / hover / pressed / active (aktueller Menuepunkt) /
    disabled - klar unterscheidbar, ohne ueberdimensionierte Effekte.
    font: geteilte Nav-Font (einheitliche Schriftgroesse); ohne Angabe
    passt sich die Schrift wie bisher per fit_font an."""
    rect = b.rect
    hovered = (not pressed) and b.enabled and rect.collidepoint(
        map_pos(pygame.mouse.get_pos()))
    active = getattr(b, "active", False) and not pressed
    if pressed:
        state = "pressed"
    elif not b.enabled:
        state = "disabled"
    elif hovered:
        state = "hover"
    else:
        state = "active" if active else "idle"
    surface.blit(_nav_base(rect, state), rect.topleft)
    if state == "disabled":
        border = DIM
    elif state == "idle":
        border = NAV_BORDER_IDLE
    else:
        border = NAV_BORDER_ON
    pygame.draw.rect(surface, border, rect, 2 if pressed else 1,
                     border_radius=u(NAV_RADIUS))
    if active and not pressed:
        # Deutlicher Cyan-Akzent: Unterkante + sanfte Puls-Aussenkontur
        pygame.draw.line(surface, CYAN, (rect.x + u(4), rect.bottom - u(3)),
                         (rect.right - u(4), rect.bottom - u(3)), max(1, u(1)))
        if pulse_k is not None:
            pygame.draw.rect(surface, _mix_col(CYAN, WHITE, 0.2 + 0.3 * pulse_k),
                             rect.inflate(2, 2), 1, border_radius=u(NAV_RADIUS))
    # Inhalt: kleines Icon + Beschriftung als zentrierte Einheit
    pad = u(NAV_PAD_X)
    icon_w = u(NAV_ICON_W) if getattr(b, "icon", "") else 0
    igap = u(NAV_IGAP) if icon_w else 0
    label = b.label or ""
    if font is not None:
        f = font
    elif label:
        f = fit_font(label, MINI_PT, rect.w - 2 * pad - icon_w - igap)
    else:
        f = None
    lw = f.size(label)[0] if (label and f) else 0
    x0 = rect.centerx - (icon_w + igap + lw) // 2
    col_txt = (CYAN if active else WHITE) if b.enabled else DIM
    col_ico = (CYAN if active else (233, 244, 252)) if b.enabled else DIM
    if icon_w:
        draw_icon(surface, b.icon, x0 + icon_w // 2, rect.centery, u(12), col_ico)
    if label and f:
        text(surface, label, f, col_txt, (x0 + icon_w + igap, rect.centery),
             "midleft")
    _draw_ripple(surface, b, rect)
