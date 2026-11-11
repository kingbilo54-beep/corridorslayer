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
    """Ein Touch-Element: Rechteck + Beschriftung + Aktion-ID."""
    __slots__ = ("id", "rect", "label", "sub", "accent", "enabled", "icon")

    def __init__(self, bid, rect, label="", sub="", accent=CYAN, enabled=True, icon=""):
        self.id = bid
        self.rect = rect
        self.label = label
        self.sub = sub
        self.accent = accent
        self.enabled = enabled
        self.icon = icon

    def hit(self, pos):
        return self.enabled and self.rect.collidepoint(pos)


def draw_btn(surface, b, pressed=False):
    """Neon-Button mit Press-Feedback (Touch-Ripple) und Hover (Maus)."""
    rect = b.rect
    accent = b.accent if b.enabled else DIM
    if getattr(b, "icon", ""):
        icon_button(surface, rect, b.icon, accent if b.enabled else DIM, pressed, b.enabled)
        _draw_ripple(surface, b, rect)
        return
    hovered = (not pressed) and b.enabled and rect.collidepoint(
        map_pos(pygame.mouse.get_pos()))
    fill = (10, 26, 42) if pressed else ((6, 20, 33) if hovered else (4, 12, 24))
    pygame.draw.rect(surface, fill, rect, border_radius=u(10))
    border = accent if (pressed or hovered) else tuple(max(18, int(c * 0.55)) for c in accent)
    pygame.draw.rect(surface, border, rect, 3 if pressed else 2, border_radius=u(10))
    lab_f = F(15)
    sub_f = F(10)
    if b.sub:
        if pressed or hovered:
            neon_text(surface, b.label, lab_f, accent, (rect.centerx, rect.centery - u(9)), "center", 1)
        else:
            text(surface, b.label, lab_f, WHITE, (rect.centerx, rect.centery - u(9)), "center")
        text(surface, b.sub, sub_f, accent if b.enabled else DIM, (rect.centerx, rect.centery + u(10)), "center")
    else:
        if pressed or hovered:
            neon_text(surface, b.label, F(16), accent, rect.center, "center", 1)
        else:
            text(surface, b.label, F(16), WHITE if b.enabled else DIM, rect.center, "center")
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
    """Kleine Icon-Touchflaeche: kind in {'pause','sound_on','sound_off','close','back'}."""
    fill = (10, 26, 42) if pressed else (4, 12, 24)
    pygame.draw.rect(surface, fill, rect, border_radius=u(10))
    pygame.draw.rect(surface, accent if pressed else tuple(max(18, int(c * 0.6)) for c in accent),
                     rect, 2, border_radius=u(10))
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
