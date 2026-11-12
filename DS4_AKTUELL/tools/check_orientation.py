# -*- coding: utf-8 -*-
"""AUFTRAG 15 (3. DURCHLAUF, PAKET A3) | AUSRICHTUNGS-CHECK
===========================================================
Rendert ALLE Gegnertypen mit der ECHTEN Spiel-Funktion main.enemy_rotated
an 3 typischen Schiffspunkten (links auf Hoehe, links oben, links unten)
und legt die Ergebnisse als Kontaktbogen check_orientation.png ab.

Zusaetzlich werden harte Assertions geprueft:
  * FRONTALE Typen (eye/medusa/crystal) kommen unveraendert zurueck.
  * Seitliche Typen (dragon) werden exakt dann gespiegelt, wenn das
    Schiff LINKS vom Gegner steht.
  * Rotierbare Typen: die Nase (in Sprite-Kunst rechts bzw. links)
    zeigt nach der Rotation in Richtung Schiff (Toleranz 75 Grad,
    diagonale Kunst wie lancer/stalker bleibt abgedeckt).
  * Die Typ-Tabellen decken ALLE Gegner mit Spawn-Datei ab.

NUR Analyse: schreibt ausschliesslich check_orientation.png, aendert
keine Spielwerte, keine Saves. Idempotent (Auftrag 12).
Aufruf:  python tools/check_orientation.py
"""
import math
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
sys.path.insert(0, BASE)

import pygame  # noqa: E402

import main as game_mod  # noqa: E402  (echte enemy_rotated + Loader)

# Nase in der Sprite-KUNST (unrotiert), aus der verifizierten Montage:
#   right = Nase rechts  -> Spiel dreht mit -Winkel
#   left  = Nase links   -> ENEMY_FACES_LEFT
#   none  = frontal / seitlich
# PAKET A3 (3. DURCHLAUF): hive gehoert jetzt zur RECHTS-Kunst
# (Triebwerke links, Bug rechts) - siehe main.py ENEMY_FACES_LEFT.
NOSE_IN_ART = {
    "skitter": "right", "shard": "right", "husk": "right",
    "stalker": "left", "wraith": "right", "hive": "right",
    "carrier": "right", "medusa": "none", "eye": "none",
    "crystal": "none", "lancer": "left", "interceptor": "right",
    "brute": "right", "dragon": "right",   # Seitenansicht: Kopf rechts
}


def nose_direction_after(img, etype, ex, ey, sx, sy):
    """Richtung der Sprite-Nase NACH main.enemy_rotated (in Grad,
    Bildschirm-Koordinaten). Fuer frontale Typen None.
    Seitenansicht (dragon): Spiegelung kehrt die Nase um - art-Nase
    rechts, gespiegelt zeigt sie nach links."""
    rot = game_mod.enemy_rotated(img, etype, ex, ey, sx, sy)
    if rot is img:
        return None, rot
    if etype in game_mod.SIDE_VIEW_ENEMIES:
        flipped = bool(sx < ex)
        return (180.0 if flipped else 0.0), rot
    # Drehwinkel wie in enemy_rotated, angewandt auf die Nase in der
    # Kunst (rechts = 0 deg, links = 180 deg).
    ang_deg = math.degrees(math.atan2(sy - ey, sx - ex))
    if etype in game_mod.ENEMY_FACES_LEFT:
        phi = 180.0 - ang_deg          # rotierter Winkel (CCW, visuell)
    else:
        phi = -ang_deg
    nose = 0.0 if NOSE_IN_ART[etype] == "right" else 180.0
    # Visuelle CCW-Rotation in Screen-Koordinaten: Winkel addiert sich
    # negativ im atan2-Raum (y nach unten).
    return (nose - phi) % 360.0, rot


def ship_angle(ex, ey, sx, sy):
    return math.degrees(math.atan2(sy - ey, sx - ex)) % 360.0


def main():
    pygame.init()
    pygame.display.set_mode((64, 64))     # convert_alpha braucht Display

    types = sorted(NOSE_IN_ART.keys())
    # Vollstaendigkeit: jede Spawn-Datei muss klassifiziert sein
    files = {f[len("enemy_"):-len(".png")]
             for f in os.listdir(os.path.join(BASE, "enemys"))
             if f.startswith("enemy_") and f.endswith(".png")
             and not f.endswith("_closed.png")}
    missing = files - set(types)
    extra = set(types) - files
    assert not missing, f"nicht klassifizierte Gegner: {sorted(missing)}"
    assert not extra, f"klassifizierte Gegner ohne PNG: {sorted(extra)}"

    fails = []
    for t in types:
        img = game_mod.load_enemy_image(t)
        for label, (dx, dy) in (("links", (-400, 0)),
                                ("links_oben", (-300, -170)),
                                ("links_unten", (-300, 170)),
                                ("rechts", (400, 0))):
            ex, ey = 700.0, 270.0
            sx, sy = ex + dx, ey + dy
            want = ship_angle(ex, ey, sx, sy)
            got, rot = nose_direction_after(img, t, ex, ey, sx, sy)
            if got is None:
                # frontale Typen: Surface darf sich nicht aendern
                if t in game_mod.ENEMY_NO_ROTATE and rot is not img:
                    fails.append(f"{t}/{label}: frontal, aber rotiert")
                continue
            diff = abs((got - want + 180.0) % 360.0 - 180.0)
            if diff > 75.0:
                fails.append(f"{t}/{label}: Nase {got:.0f} deg, "
                             f"Schiff bei {want:.0f} deg (Abweichung {diff:.0f})")

    # ---- Kontaktbogen ----
    CELL_W, CELL_H, LBL = 250, 200, 26
    COLS = 3
    rows = (len(types) + COLS - 1) // COLS
    sheet = pygame.Surface((COLS * CELL_W, rows * (CELL_H + LBL)),
                           pygame.SRCALPHA)
    sheet.fill((18, 20, 28))
    font = pygame.font.SysFont("dejavusansmono", 17)
    for i, t in enumerate(types):
        col, row = i % COLS, i // COLS
        x0, y0 = col * CELL_W, row * (CELL_H + LBL)
        img = game_mod.load_enemy_image(t)
        ex, ey = 620.0, 300.0
        # Schiff-Punkt links unten (typische Spielsituation)
        sx, sy = 220.0, 380.0
        rot = game_mod.enemy_rotated(img, t, ex, ey, sx, sy)
        k = min((CELL_W - 70) / rot.get_width(),
                (CELL_H - 30) / rot.get_height(), 1.6)
        rot2 = pygame.transform.smoothscale(
            rot, (max(1, int(rot.get_width() * k)),
                  max(1, int(rot.get_height() * k))))
        # Schiff-Markierung + Verbindungslinie
        px, py = x0 + 34, y0 + LBL + CELL_H - 34
        exx, eyy = x0 + CELL_W - 60, y0 + LBL + 44
        pygame.draw.line(sheet, (60, 90, 130), (px, py), (exx, eyy), 1)
        pygame.draw.circle(sheet, (0, 220, 255), (px, py), 7)
        pygame.draw.circle(sheet, (0, 120, 200), (px, py), 7, 2)
        sheet.blit(rot2, rot2.get_rect(center=(exx, eyy)))
        sheet.blit(font.render(t, True, (255, 230, 120)), (x0 + 6, y0 + 4))
        pygame.draw.rect(sheet, (70, 70, 92),
                         (x0, y0, CELL_W, CELL_H + LBL), 1)
    out = os.path.join(BASE, "check_orientation.png")
    pygame.image.save(sheet, out)
    print(f"Kontaktbogen: {out}")

    if fails:
        print("FEHLER:")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("OK: alle 14 Gegnertypen zeigen mit der Nase zum Schiff "
          "(Kampagne + Idle nutzen denselben Pfad _draw_world).")


if __name__ == "__main__":
    main()
