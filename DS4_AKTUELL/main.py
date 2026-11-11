# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | LANDSCAPE EDITION (PAKET 8.6)
===============================================
PAKET 8.6 - ZEREMONIE-INSZENIERUNG + IDLE-OEKONOMIE:

  * BESCHWOERUNGS-ZEREMONIE NEU INSZENIERT: 5 Phasen (Konvergenz ->
    Materialisierung -> Aufladung -> Burst -> Offenbarung). Die Kapsel
    ist zu Beginn bewusst NICHT sichtbar: Die Kammer startet dunkel und
    LEER (retouchierte Kulisse), die geschlossene Kapsel materialisiert
    sich erst auf dem Podest (Flicker), laedt auf (glimmende Streifen,
    Zittern, Runenring), loest sich im Energie-Burst auf - und die beste
    gezogene Einheit steigt mit Seltenheits-Strahlen und Banner auf.
    Epic-Ziehungen laden stattdessen das Portal (Swirl-Wachstum +
    Blitzboegen) und die Einheit tritt aus dem Portal.
  * IDLE-OEKONOMIE: Offline-Einkommen mit Bericht beim Reinkommen
    (Abwesenheit seit letzter Sicherung, max. 8 h, 60 % Effizienz -
    Credits + Data Cores, ABHOLEN-Button). Im Idle-Betrieb wird das
    verdiente Geld jetzt alle 8 s automatisch in die Wallet ueberwiesen
    (mit Meldung) statt erst beim Beenden; Save-Heartbeat alle 30 s.
  * Alles von Paket 8.5 bleibt: 3 Helden-Champions (Ingenieur/Lyra/
    Nova), 15er-Pool, Duplikat-Credits, Ergebnis-/Sammlungs-Ansicht.

PAKET 8.1 - NAVIGATIONSLEISTE ÜBERARBEITET (nur Darstellung/Anordnung,
alle Funktionen und Klickaktionen unveraendert):

  * KOMPAKTE BUTTONS: die 9 Nav-Buttons haben feste Masse (~65x34
    Design-px, mindestens leicht gerundet) und werden NICHT mehr ueber
    die Bildschirmbreite gestreckt - die Gruppe sitzt zentriert und
    nimmt nur ~55-65 % der Breite ein, mit gleichmassigen Abstaenden.
  * HOCHWERTIGE OPTIK: dunkler, leicht transparenter Metallhintergrund,
    dezente cyanfarbene Umrandung; aktiver Menuepunkt mit deutlichem
    Cyan-Akzent; kleine Icons + kurze, gut lesbare Beschriftungen
    (IDLE/WERFT/NEXUS/GALAXIE/DAILY/WEEKLY/SUMMON/SYSTEM/ENDE) in
    EINHEITLICHER Schriftgroesse und Button-Hoehe.
  * Eigener Renderer ui_kit.draw_nav_btn - Quest-/Beschwoerungs-Screens
    und alle anderen Menues bleiben unveraendert. Bei sehr schmalen
    Screens weiterhin Scroll-Overflow mit Pfeilen.

PAKET 7E - SCHIFFS-UPGRADE ENDLICH NUTZBAR (auf Basis von Paket 7D):

  * SCHIFFSRUMPF STUFE 1-12: In der Werft gibt es jetzt den Button
    "SCHIFF AUFWERTEN" - das Schiff SELBST wird aufgewertet, gegen
    steigende Credit-Kosten. Wirkung ist ECHT (+80 max. Huelle und
    +3% Schaden je Stufe, wirkt sofort im Gefecht) und das Schiffsbild
    wechselt auf fortress/ship_lvl_<Stufe>.png (Bilder 1-12).
  * KANONEN-BILD FOLGT WAFFEN-STUFE: Der Geschuetzturm zeigt jetzt
    kanonen/kanonen_lvl_<Waffen-Stufe>.png (1-12; fehlt ein Bild, wird
    automatisch die naechstniedrigere vorhandene Stufe geladen).
  * Fallback: fortress_2d.set_level + Verzeichnis-Scan - das Schiff
    verschwindet nie, auch wenn Bilder fehlen.

PAKET 7D - UI- UND GAMEPLAY-KORREKTUREN (auf Basis von Paket 7C):

  * BUTTONS: keine schwarzen Flaeche mehr - transparente, leicht
    akzent-getoente Glasflaechen mit klarer Neon-Kontur (auch disabled);
    Schrift-Fitting (ui_kit.fit_font) haelt jede Beschriftung INNERHALB
    des Buttons (kein Anschneiden mehr, z. B. Werft-Chips).
  * WELTKARTE = KAMPAGNE: Flottenhub/Werft/Nexus-Symbole entfernt -
    nur noch die 5 Sektoren mit Story-Texten, FEINDSIGNALE (naechster
    Einsatz) und BOSS-SIGNAL. Kopfzeile "KAMPAGNE".
  * SCHIFFS-UPGRADES: Stufen-Gate entfernt (frueher 3 Stufen = +1 Level,
    was alle Upgrades sperrte) - Credits sind das Tor, alle 8 Module
    sind sofort bis Stufe 15 aufwertbar und wirken echt im Gefecht.

UI-REDESIGN + INTERAKTIVE GALAXIEKARTE (auf Basis der stabilen
Paket-6-Version; Kampfmechanik, Skill-System und Spielstaende
unveraendert):

  * COMPACT SCI-FI RPG UI: schmale Aktionsleiste am unteren Rand
    (Menue + Gefechts-HUD), deutlich kleinere Button-Optik bei
    erhaltenen Touch-Flaechen (kompakte Elemente sitzen zentriert im
    grossen Touch-Rect), dunkle transparente Panels mit duennen
    Neon-Konturen (ui_kit Compact-Layer + world_map.glass_panel).
  * STARTMENÜ-NEON-GLOW: Cyan/Magenta-Glows pulsieren langsam und
    gestaffelt, GALAXIE-Button als einziges UI-Element mit dezentem
    Puls, Touch-Ripple + Glow-Flash beim Antippen. Hintergrund bleibt
    dunkel, keine hektischen Effekte.
  * INTERAKTIVE WELTKARTE (world_map.py): bg_world.jpg wird zur
    Spieloberflaeche. Planeten = Sektoren, Stationen = Forschung /
    Skill-Nexus, zentrale Struktur = Flottenhub (Idle-Betrieb),
    Signale = Elite-/Boss-Einsatz. Hitboxen liegen als UV-Koordinaten
    RELATIV ZUM BILD vor; Zeichnen und Touch-Hit-Testing nutzen
dieselbe Transformation (cover, unverzerrt, mit Anti-Beschnitt).
    Formfitting-Highlights (Kreis/Hex/Ring/Diamant), kompaktes
    Info-Panel mit Status, Fortschritt, Voraussetzungen und Direkt-
    start verfuegbarer Missionen. Bild-, Overlay- und Panel-Caching.
  * DEBUG: F1 zeigt auf der Karte Hitboxen + UV-Koordinaten.
  * PAKET 7B - UI-POLISH: Button-Skin mit Tiefe (Verlauf, Kantenlicht,
    Eckwinkel), klar unterscheidbaren Zustaenden (idle/hover/pressed/
    disabled/active) und dezentem Puls aktiver Buttons; Panel-Konturen
    kraeftiger. Hintergrundbilder bleiben sichtbar.
  * PAKET 7B - WERFT (eigenstaendiges Schiffs-Upgrade-Menue, State
    RESEARCH): Schiff als interaktives Objekt - Modul-Hotspots direkt am
    Schiffwaehlbar, plus Chip-Leiste als Alternative. Detail-Panel mit
    aktuellen Werten, naechster Stufe, Kosten und echtem Upgrade-Button.
    Neues Modul "reaktor" (Reaktor / Energie); alle Module wirken wirklich
    aufs Gefecht (gear_mods -> pve_system).
  * PAKET 7B - OPTIK-STRIKT GETRENNT: Schiffskorpus und Geschützturm
    haengen NUR am kosmetischen Level (cosmetic_hull, Standard 1) und
    NIE an Modul-Stufen - keine automatische Gesamtaufwertung mehr.
    (Fix: der Turm verschwand frueher ab Kanonen-Stufe 2, da nur
    kanonen_lvl_1.png existiert.) Schildring/Triebwerks-Glow bleiben als
    System-Effekte (Funktionsanzeige, keine Huelenaenderung).
  * PAKET 7B - SKILL-NEXUS: 5 Spezialisierungen, 30 Knoten, echte
    Verzweigungen mit sichtbaren Voraussetzungs-Kanten; neue Effekte
    (LETZER WILLE, BOSS-JAEGER, SCHROTTBERGUNG, KONTRAKTE, TEMPFELD,
    KUEHLSYSTEM, NOTSTROMZELLEN, SYSTEM-SYNERGIE, SCHILDKONDENSATOR,
    DURCHSCHLAG) wirken wirklich im Spiel.
  * Alles Erhaltene (Paket 6): Landscape-Rotationsschicht, Orbital
    Energy Lattice, Kampfeffekte, Victory-Video + Ton, Damage Numbers,
    Idle-Modus + Data Cores, Balancing aus Paket 4.
"""
import math
import os
import sys
import json
import logging
import random
import time
import pygame

from module_system import (FortressModules, module_effect_values,
                           module_next_effect, SHIP_MAX_LEVEL,
                           SHIP_HP_PER_LVL, SHIP_DMG_PCT_PER_LVL)
from pve_system import PvECombat
import pve_system as pve_sys      # PAKET 8.8b: BREATH_*-Konstanten fürs Rendering
try:
    from effects.engine_effect import EngineEffect   # PAKET 7E: Triebwerks-FX
except ImportError:                       # SCHRITT 1d: Datei auch FLACH neben
    from engine_effect import EngineEffect   # main.py wird akzeptiert (Hotfix)
try:
    from effects.damage_fx import DamageFX   # PAKET 8.3: Einschlag-FX am Schiff
except ImportError:                          # SCHRITT 1d: Fallback wie bei burn_fx
    from damage_fx import DamageFX           # Dateien auch FLACH akzeptieren
try:
    from effects.burn_fx import BurnFX   # PAKET 8.7: Schiff brennt < 50 % HP
except ImportError:                      # PAKET 8.7a: Datei auch FLACH neben
    from burn_fx import BurnFX           # main.py wird akzeptiert (Hotfix)
import bg_fx                             # PAKET 8.8: lebendiger Hintergrund
import shield_gfx                        # PAKET 8.7: eigene Schild-Grafiken (DS4)
from fortress_2d import Fortress
from ship_movement import ShipMovement
from sound_system import SFX
from skill_tree import SkillTree, SKILL_TREE
import ui_kit
from ui_kit import (set_screen, u, fs, F, margin, btn_h, text, neon_text, panel,
                    overlay, grid_bg, draw_btn, draw_btns, first_hit, Btn,
                    draw_toggle, wrap_text, radial_glow,
                    VOID, PANEL, LINE, CYAN, CYAN_SOFT, ICE, WHITE, MUTED,
                    DIM, VIOLET, MAGENTA, GREEN, RED, AMBER,
                    bar_h, compact_btn_h, icon_touch, pulse, radial_glow_k,
                    action_bar_rect, draw_action_bar, glass_panel, draw_icon,
                    draw_compact_btn, draw_compact_icon_btn, _mix_col,
                    fit_font)
import skill_nexus
import combat_fx
import world_map
import map_locations   # PAKET 7F: Zoom-Navigation + Orts-Szenen
import upgrade_fx
from upgrade_fx import UpgradeFX
# PAKET 8: RPG-Progression, Quests, Beschwörung (Werte in rpg_config.py)
import datetime
import rpg_config
import rpg_progression
import quest_system
import summon_system

pygame.init()

# ---------- Anzeige: Landscape-Fenster (Desktop) / Vollbild (Handy) ----------
IS_ANDROID = any(k in os.environ for k in
                 ("ANDROID_ARGUMENT", "ANDROID_PRIVATE", "ANDROID_ENTRYPOINT",
                  "PYDROID3", "PYDROID"))
FORCE_FULLSCREEN = IS_ANDROID or os.environ.get("CS_FULLSCREEN") == "1"

if FORCE_FULLSCREEN:
    try:
        SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    except Exception:
        # Bewusst still: Vollbild ist auf manchen Geraeten nicht verfueg-
        # bar (Treiber/Rechte) - das normale Fenster ist der erwartete,
        # harmlose Rueckfall.
        SCREEN = pygame.display.set_mode((960, 540), pygame.RESIZABLE)
else:
    SCREEN = pygame.display.set_mode((960, 540), pygame.RESIZABLE)
pygame.display.set_caption("CORRIDOR SLAYER // LANDSCAPE EDITION")
CLOCK = pygame.time.Clock()
FPS = 60

# ---------- Weltkonstanten (unveraendert -> Gameplay-Balance bleibt) ----------
WORLD_W, WORLD_H = 960.0, 540.0
FORTRESS_POS = (120.0, 270.0)
CANNON_OFFSETS = [(4, -14)]

VERSION = "LANDSCAPE EDITION v8.7"
_BASE = os.path.dirname(os.path.abspath(__file__))
_PREFS_PATH = os.path.join(_BASE, "ui_prefs.json")

# ---------- Asset-Ordner: erst neben dieser Datei, dann alter Hartpfad ----------
def _folder(name, old_abs):
    p = os.path.join(_BASE, name)
    if os.path.isdir(p):
        return p
    if os.path.isdir(old_abs):
        return old_abs
    return p


# ---------- REFAKTOR SCHRITT 2: FEHLER-LOGGING ----------
# Alle bisher still verschluckten Fehler ("except: pass") landen ab jetzt
# in corridor_slayer.log (Level WARNING, mit Zeitstempel). Das Verhalten
# des Spiels aendert sich NICHT - es laeuft wie vorher weiter, der Fehler
# wird nur noch sichtbar.
_log = logging.getLogger("corridor_slayer")
_log.setLevel(logging.WARNING)
try:
    _log_fh = logging.FileHandler(os.path.join(_BASE, "corridor_slayer.log"),
                                  encoding="utf-8")
    _log_fh.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-7s %(message)s"))
    _log.addHandler(_log_fh)
except Exception:
    # Bewusst still: Ist keine Log-Datei schreibbar (z. B. schreibge-
    # schuetzter Ordner), laeuft das Spiel unveraendert weiter - es fehlt
    # nur die Protokolldatei. Kein anderer Rueckfall moeglich/nuetzlich.
    pass

ENEMY_FOLDER = _folder("enemys", r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\enemys")
MODULE_FOLDER = _folder("modules", r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\modules")
KANONEN_FOLDER = _folder("kanonen", r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\kanonen")

enemy_images = {}
module_images = {}
kanonen_images = {}
_enemy_scaled = {}
_module_scaled = {}
_kanonen_scaled = {}


def _scaled(cache, key, img, s):
    """Skaliert ein Image mit s (Viertel-Pixel-Buckets gecacht)."""
    b = max(1, int(round(s * 8)))
    k = (key, b)
    out = cache.get(k)
    if out is None:
        nw = max(2, int(img.get_width() * b / 8))
        nh = max(2, int(img.get_height() * b / 8))
        out = pygame.transform.smoothscale(img, (nw, nh))
        if len(cache) > 60:
            cache.clear()
        cache[k] = out
    return out


# PAKET 8.2/8.8: In-Game-Breite je Gegnertyp (Weltkoordinaten 960x540).
# 8.8: Die neuen Nutzer-Grafiken - Bosse bewusst deutlich groesser;
# unbekannte Typen fallen auf 70 zurueck (alter Standard).
# 8.8a: BOSSE MIT PRAESENZ (Nutzerwunsch) - TARNJAEGER/SCHLACHTSCHIFF/
# EISDRACHE nochmal ~1.6x groesser (150/195/235 statt 96/124/148).
ENEMY_IMG_W = {"skitter": 46, "shard": 50, "husk": 62, "wraith": 52,
               "hive": 78, "lancer": 112,
               "stalker": 68, "medusa": 64, "carrier": 110,
               "eye": 66, "crystal": 58,
               "interceptor": 150, "brute": 195, "dragon": 235}

# PAKET 8.8b: SEITENANSICHT-SPRITES. Diese Gegner sind seitlich gezeichnet
# (Drache: Kopf rechts, Beine unten) und dürfen NICHT gedreht werden -
# bei 180° zum Schiff lagen sie auf dem Rücken (Nutzer-Screenshot). Sie
# werden stattdessen nur horizontal gespiegelt (Blick zum Schiff).
SIDE_VIEW_ENEMIES = {"dragon"}

# AUFTRAG 15 (2. DURCHLAUF): GEGNER-AUSRICHTUNG. Jedes enemys/*.png wurde
# einzeln in Original-Ausrichtung verifiziert (Montage + Enden-Zoom je
# Sprite, siehe scripts/orientation_*.png). Gegner spawnen bei x=1000 und
# fliegen NACH LINKS zum Schiff - die Nase muss also zum Schiff zeigen.
#   ENEMY_FACES_LEFT : Nase zeigt im KUNSTWERK nach LINKS. Der Winkel
#     zum Schiff wird mit (180° - Winkel) gedreht, damit die Nase
#     wirklich zum Schiff zeigt (nicht das Heck).
#   ENEMY_NO_ROTATE  : FRONTAL/vertikal aufgebaute Sprites (Auge, Qualle,
#     Kristall) - jede Rotation kippt sie auf die Seite/auf den Kopf.
#     Sie bleiben aufrecht stehen.
#   SIDE_VIEW_ENEMIES: Seitlich gezeichnet (Drache) - nur spiegeln.
#   Alles andere     : Nase zeigt nach RECHTS -> Rotation -Winkel.
# Korrigiert gegenueber dem 1. Durchlauf (Nutzer: "Gegner erscheinen
# weiterhin überwiegend falsch herum", auch im Idle):
#   * husk     : Nase zeigt RECHTS (runde Düse links, gepanzerte Bugkannte
#                rechts) - war irrtuemlich als LINKS markiert.
#   * carrier  : Nase zeigt RECHTS (Geschütztürme + konvergierende
#                Bugflossen rechts) - war irrtuemlich als LINKS markiert.
#   * stalker  : Nase zeigt LINKS (Mandibeln + Augencluster links,
#                Hinterleib rechts) - war ohne Eintrag (RECHTS).
ENEMY_FACES_LEFT = {"hive", "lancer", "stalker"}
ENEMY_NO_ROTATE = {"eye", "medusa", "crystal"}


def enemy_rotated(img, enemy_type, enemy_x, enemy_y, ship_x, ship_y):
    """AUFTRAG 15 (2. DURCHLAUF): Liefert das kampfbereit gedrehte Sprite.
    Die Nase jedes Gegners zeigt zum Schiff - je Spritetyp nach der
    Klassifizierung oben (LINKS-Kunst / frontal / seitlich / RECHTS).
    Gilt EINHEITLICH fuer Kampagne UND Idle (beide zeichnen über
    _draw_world -> diese Funktion). Zentral ausgelagert, damit der
    Ausrichtungs-Test (tools/check_orientation.py) die ECHTE Spiellogik
    prueft und nicht eine Kopie."""
    if enemy_type in SIDE_VIEW_ENEMIES:
        # Seitlich gezeichnet: nur spiegeln, NICHT kippen.
        return pygame.transform.flip(img, ship_x < enemy_x, False)
    if enemy_type in ENEMY_NO_ROTATE:
        return img
    ang_deg = math.degrees(math.atan2(ship_y - enemy_y, ship_x - enemy_x))
    if enemy_type in ENEMY_FACES_LEFT:
        # LINKS-Kunst: Nase um 180° versetzt zum Zielwinkel drehen.
        return pygame.transform.rotate(img, 180.0 - ang_deg)
    # Nase rechts: bisheriges Verhalten (-Winkel).
    return pygame.transform.rotate(img, -ang_deg)

# PAKET 8.8b: IDLE-OEKONOMIE GEBREMST (Nutzerfeedback: "Im idle Modus
# sollte es auch ca. 1h dauern bis der idle reward generiert wird.
# Ansonsten macht der afkler zu viel Profit. Es sollte auch ein Limit
# geben, dass nach 8h das Maximum erreicht worden ist.")
#   IDLE_PAYOUT_S      : Beute sammelt sich an, Auszahlung alle 60 min
#   IDLE_SESSION_CAP_S : nach 8 h Idle in EINER Sitzung ist das Maximum
#                        erreicht -> Einkommen wird eingefroren (HUD zeigt
#                        "MAXIMUM ERREICHT"). Der Offline-Bericht bleibt
#                        separat bei 60 % Effizienz / 8 h Deckel.
IDLE_PAYOUT_S = 3600
IDLE_SESSION_CAP_S = 8 * 3600


def load_enemy_image(enemy_type):
    if enemy_type in enemy_images:
        return enemy_images[enemy_type]
    path = os.path.join(ENEMY_FOLDER, f"enemy_{enemy_type}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), rect)
        target_w = ENEMY_IMG_W.get(enemy_type, 70)
        target_h = int(cropped.get_height() * (target_w / cropped.get_width()))
        scaled = pygame.transform.smoothscale(cropped, (target_w, target_h))
        enemy_images[enemy_type] = scaled
        return scaled
    except Exception:
        # Bewusst still: Fehlendes Gegner-Bild ist erwartet (nicht jeder
        # Typ hat eine eigene Datei) -> Magenta-Platzhalter als Rueckfall.
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(surf, MAGENTA, (20, 20), 20)
        enemy_images[enemy_type] = surf
        return surf


# PAKET 8.8c: DRACHEN-MAUL-ZUSTAND. Der Eisdrache hat jetzt ZWEI Sprites:
#   enemy_dragon.png          = Maul OFFEN   (nur waehrend Angriffen)
#   enemy_dragon_closed.png   = Maul ZU      (Normalflug) - vorher "blieb
#     die Schnauze permanent offen", was ungewollt dumm aussah.
# pve_system setzt enemy.mouth_open; die Zeichnung waehlt das passende
#   Sprite (gleiche Zielhoehe -> kein Groessen-Sprung beim Wechsel).
_enemy_variant_images = {}


def load_enemy_variant(enemy_type, suffix):
    """Laedt enemy_<typ><suffix>.png als ZUSTANDS-Variante (z. B. Drachen-
    maul zu). Skaliert auf DIESELBE HOEHE wie das Haupt-Sprite (ENEMY_IMG_W
    auf den Haupt-Sprite angewandt) - so springt beim Wechsel nichts.
    Gecacht je (Typ, Suffix); fehlt die Datei, greift das Haupt-Sprite
    zurueck."""
    key = (enemy_type, suffix)
    if key in _enemy_variant_images:
        return _enemy_variant_images[key]
    path = os.path.join(ENEMY_FOLDER, f"enemy_{enemy_type}{suffix}.png")
    try:
        ref = load_enemy_image(enemy_type)          # Referenz-Hoehe
        ref_h = ref.get_height()
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), rect)
        target_w = max(8, int(cropped.get_width() * ref_h / cropped.get_height()))
        scaled = pygame.transform.smoothscale(cropped, (target_w, ref_h))
        _enemy_variant_images[key] = scaled
        return scaled
    except Exception:
        # Bewusst still: Die Zustands-Variante (z. B. Drachen-Maul zu) darf
        # fehlen -> Haupt-Sprite bleibt gueltiger Rueckfall.
        return load_enemy_image(enemy_type)


# PAKET 8.8a: BOSS-PRAESENZ - vorgerenderte Aura in Boss-Farbe (radialer
# Schein). Wird 1x je Farbe gebaut und 1x je Groesse skaliert (gecacht);
# im Gefecht nur geblittet, der Puls laeuft ueber set_alpha - kein
# Neu-Rendern pro Frame, handyttauglich.
_boss_glow_cache = {}
_boss_glow_scaled = {}


def _boss_glow(col):
    """Radialer Schein (256px) in der Boss-Farbe - 1x pro Farbe gebaut."""
    if col in _boss_glow_cache:
        return _boss_glow_cache[col]
    d = 256
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    steps = 26
    for i in range(steps, 0, -1):
        r = max(2, int(d * 0.5 * i / steps))
        a = int(165 * (1.0 - i / steps) ** 1.7)
        pygame.draw.circle(surf, (col[0], col[1], col[2], a),
                           (d // 2, d // 2), r)
    _boss_glow_cache[col] = surf
    return surf


# PAKET 8.8b: FLAMMEN-ATEM (Eisdrache) - Rendering. Der Strahl wird pro
# Frame in eine wiederverwendete SRCALPHA-Fläche gezeichnet (3 Schichten:
# rot außen, orange Mitte, gelb-weißer Kern, flackernd) und einmal geblittet.
_beam_tmp = None


def _dragon_mouth_pos(boss, T, s, now_ms):
    """PAKET 8.8c: Maul-Position des (geflippten) Drachen-Sprites in
    Screen-px - gemeinsame Basis fuer Atem, GLUTBOMBEN-Telegraf und
    Bomben-Abschuss-Optik. Der Drache schaut immer zum Schiff (links)."""
    bx, by = T(boss.x, boss.y)
    dimg = load_enemy_image("dragon")
    img_w = dimg.get_width() * s
    img_h = dimg.get_height() * s
    by += math.sin(now_ms * 0.0021 + boss.x * 0.13) * 4.0 * s   # Bob wie im Draw
    mx = bx - img_w * 0.44
    my = by + img_h * 0.06
    return mx, my, img_w, img_h


def _draw_dragon_breath(surface, boss, T, s, ship_x, ship_y, now_ms):
    """Zeichnet Telegraf (Mund glimmt + flackernde Ziellinie) und den
    brennenden Strahl des Eisdrachen. Pure Optik - Schaden/Logik liegen
    in pve_system._dragon_breath."""
    global _beam_tmp
    mx, my, img_w, img_h = _dragon_mouth_pos(boss, T, s, now_ms)

    if boss.breath_phase == 1:
        # --- TELEGRAF: aufglühender Mund + flackernde Ziellinie ---
        prog = 1.0 - max(0.0, boss.breath_t) / pve_sys.BREATH_TELEGRAPH_S
        ang = math.atan2(ship_y - boss.y, ship_x - boss.x)
        glow = _boss_glow((255, 120, 40))
        gr = int(u(10) + prog * u(26) + 2 * math.sin(now_ms * 0.03))
        if gr > 6:
            gs = pygame.transform.smoothscale(glow, (gr, gr))
            gs.set_alpha(int(90 + 150 * prog))
            surface.blit(gs, gs.get_rect(center=(int(mx), int(my))))
        # dünne Warnlinie (flackert, macht die Richtung lesbar)
        if math.sin(now_ms * 0.021) > -0.55:
            ex_ = mx + math.cos(ang) * u(210)
            ey_ = my + math.sin(ang) * u(210)
            pygame.draw.line(surface, (200, 70, 30),
                             (int(mx), int(my)), (int(ex_), int(ey_)), 2)
        return

    # --- STRAHL AKTIV ---
    ang = boss.breath_ang
    rage = getattr(boss, "enraged", False)
    length = pve_sys.BREATH_RANGE * s
    ex_ = mx + math.cos(ang) * length
    ey_ = my + math.sin(ang) * length
    w_end = (30 if rage else 24) * s
    px_, py_ = -math.sin(ang), math.cos(ang)          # Senkrechte
    W, H = surface.get_size()
    if _beam_tmp is None or _beam_tmp.get_size() != (W, H):
        _beam_tmp = pygame.Surface((W, H), pygame.SRCALPHA)
    _beam_tmp.fill((0, 0, 0, 0))
    layers = (((255, 60, 20), 60, 1.30),
              ((255, 145, 35), 130, 0.82),
              ((255, 235, 170), 225, 0.44))
    for i, (col, alpha, wm) in enumerate(layers):
        wf = w_end * wm * (0.84 + 0.16 * math.sin(now_ms * 0.031 + i * 2.1))
        jx = math.sin(now_ms * 0.017 + i) * 3.0 * s
        jy = math.cos(now_ms * 0.019 + i * 1.3) * 3.0 * s
        tex, tey = ex_ + jx, ey_ + jy
        pygame.draw.polygon(_beam_tmp,
                            (col[0], col[1], col[2], alpha),
                            [(mx, my),
                             (tex + px_ * wf, tey + py_ * wf),
                             (tex - px_ * wf, tey - py_ * wf)])
        pygame.draw.circle(_beam_tmp, (col[0], col[1], col[2], alpha),
                           (int(tex), int(tey)), max(3, int(wf * 0.55)))
    surface.blit(_beam_tmp, (0, 0))
    # Mund-Feuer (additiv) + heißer Kern nochmal drüber
    glow = _boss_glow((255, 160, 50))
    gr = int(u(22) + 3 * math.sin(now_ms * 0.028))
    gs = pygame.transform.smoothscale(glow, (gr, gr))
    surface.blit(gs, gs.get_rect(center=(int(mx), int(my))),
                 special_flags=pygame.BLEND_ADD)


# PAKET 8.8c: ZUSATZ-ANGRIFFE rendern - GLUTBOMBEN (Telegraf-Marken +
# bogenfliegende Kometen mit Glut-Schweif) und EISSPIESSE (Warnringe +
# Spalten-Markierung am Boden, aufsteigende Eissäulen). Pure Optik -
# Logik/Schaden liegen in pve_system (boss_bombs / boss_spikes).
def _boss_bomb_pos(b, k):
    """Position der Bombe bei Bahnfortschritt k (0..1) - Welt-px."""
    wx = b.sx + (b.tx - b.sx) * k
    wy = b.sy + (b.ty - b.sy) * k - pve_sys.BOMB_ARC_H * 4.0 * k * (1.0 - k)
    return wx, wy


def _draw_boss_attacks(surface, combat, T, s, now_ms):
    for enemy in combat.enemies:
        if not enemy.is_boss:
            continue
        # ---------- GLUTBOMBEN: Telegraf ----------
        if enemy.atk_kind == 2 and enemy.atk_t > 0 and (enemy.bomb_marks or []):
            prog = 1.0 - max(0.0, enemy.atk_t) / pve_sys.BOMB_TELEGRAPH_S
            if enemy.enemy_type == "dragon":
                mx, my, _, _ = _dragon_mouth_pos(enemy, T, s, now_ms)
            else:
                mx, my = T(enemy.x, enemy.y)
            glow = _boss_glow((255, 120, 40))
            gr = int(u(8) + prog * u(22) + 2 * math.sin(now_ms * 0.031))
            if gr > 6:
                gs = pygame.transform.smoothscale(glow, (gr, gr))
                gs.set_alpha(int(80 + 150 * prog))
                surface.blit(gs, gs.get_rect(center=(int(mx), int(my))))
            pulse = 0.5 + 0.5 * math.sin(now_ms * 0.012 + enemy.x * 0.7)
            for (tx, ty) in enemy.bomb_marks:
                sx_, sy_ = T(tx, ty)
                rr = int((15 + 9 * pulse) * s)
                pygame.draw.circle(surface, (255, 90, 30),
                                   (int(sx_), int(sy_)), rr, 2)
                pygame.draw.circle(surface, (255, 170, 70),
                                   (int(sx_), int(sy_)),
                                   max(2, int(rr * 0.38)), 1)
                pygame.draw.line(surface, (255, 120, 40),
                                 (int(sx_) - rr - 4, int(sy_)),
                                 (int(sx_) + rr + 4, int(sy_)), 1)
        # ---------- EISSPIESSE: Telegraf ----------
        if enemy.atk_kind == 3 and enemy.atk_t > 0 and (enemy.spike_marks or []):
            prog = 1.0 - max(0.0, enemy.atk_t) / pve_sys.SPIKE_TELEGRAPH_S
            pulse = 0.5 + 0.5 * math.sin(now_ms * 0.014 + enemy.x * 0.5)
            for x in enemy.spike_marks:
                bx_, by_ = T(x, 537.0)
                rr = int((13 + 8 * pulse) * s)
                pygame.draw.circle(surface, (120, 225, 255),
                                   (int(bx_), int(by_)), rr, 2)
                pygame.draw.circle(surface, (60, 140, 190),
                                   (int(bx_), int(by_)),
                                   max(2, int(rr * 0.45)), 1)
                # gestrichelte Spalten-Markierung bis ueber das Schiff hinaus
                y0 = int(by_)
                y1 = int(by_ - (250 + 90 * prog) * s)
                seg = max(4, int(9 * s))
                yy = y1
                while yy < y0:
                    pygame.draw.line(surface, (110, 190, 230),
                                     (int(bx_), yy), (int(bx_), min(y0, yy + seg // 2)), 1)
                    yy += seg

    # ---------- GLUTBOMBEN: Flug + Impact-Optik ----------
    for b in getattr(combat, "boss_bombs", []):
        k = max(0.0, min(1.0, b.t / b.T))
        sx_, sy_ = T(*_boss_bomb_pos(b, k))
        # Glut-Schweif (3 abklingende Kreise entlang der Bahn zurueck)
        for i in range(1, 4):
            kk = max(0.0, k - i * 0.05)
            dx_, dy_ = T(*_boss_bomb_pos(b, kk))
            r_ = max(2, int((7 - i * 1.7) * s))
            pygame.draw.circle(surface, (255, 90 + 45 * i, 25),
                               (int(dx_), int(dy_)), r_)
        glow = _boss_glow((255, 150, 45))
        gr = int(u(17) + 2 * math.sin(now_ms * 0.027))
        gs = pygame.transform.smoothscale(glow, (gr, gr))
        surface.blit(gs, gs.get_rect(center=(int(sx_), int(sy_))),
                     special_flags=pygame.BLEND_ADD)
        pygame.draw.circle(surface, (255, 235, 170),
                           (int(sx_), int(sy_)), max(2, int(5.5 * s)))

    # ---------- EISSPIESSE: Ausbruch ----------
    for sp in getattr(combat, "boss_spikes", []):
        p = max(0.0, min(1.0, sp.t / pve_sys.SPIKE_RISE_S))
        ease = 1.0 - (1.0 - p) ** 3
        fade = 1.0 if sp.t <= pve_sys.SPIKE_RISE_S else \
            max(0.0, 1.0 - (sp.t - pve_sys.SPIKE_RISE_S) / 0.45)
        a_out = int(150 * fade)
        a_mid = int(205 * fade)
        a_core = int(255 * fade)
        base_sx, base_sy = T(sp.x, 545.0)
        tip_sx, tip_sy = T(sp.x, 545.0 - 600.0 * ease)
        w0 = 26.0 * s * (0.55 + 0.45 * min(1.0, ease * 2.0))
        # außen (dunkles Blau) -> Mitte (Cyan) -> Kern (weiss)
        for col, wm, a_ in (((40, 95, 145), 1.0, a_out),
                            ((120, 225, 255), 0.62, a_mid),
                            ((235, 250, 255), 0.28, a_core)):
            half = w0 * wm
            pygame.draw.polygon(surface, (col[0], col[1], col[2], a_), [
                (base_sx - half, base_sy),
                (base_sx - half * 0.55, base_sy + (tip_sy - base_sy) * 0.45),
                (tip_sx, tip_sy),
                (base_sx + half * 0.55, base_sy + (tip_sy - base_sy) * 0.45),
                (base_sx + half, base_sy)])
        # heller Boden-Glow an der Bruchstelle
        glow = _boss_glow((140, 220, 255))
        gr = int(u(15) + 3 * math.sin(now_ms * 0.03))
        gs = pygame.transform.smoothscale(glow, (gr, gr))
        gs.set_alpha(int(120 * fade))
        surface.blit(gs, gs.get_rect(center=(int(base_sx), int(base_sy))),
                     special_flags=pygame.BLEND_ADD)


def load_module_image(module_key, level):
    cache_key = f"{module_key}_{level}"
    if cache_key in module_images:
        return module_images[cache_key]
    path = os.path.join(MODULE_FOLDER, f"{module_key}_lvl_{level}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), rect)
        target_w = 40
        target_h = int(cropped.get_height() * (target_w / cropped.get_width()))
        scaled = pygame.transform.smoothscale(cropped, (target_w, target_h))
        module_images[cache_key] = scaled
        return scaled
    except Exception:
        # Bewusst still: Nicht jedes Modul hat Bilder auf jeder Stufe ->
        # dunkler Platzhalter als Rueckfall (wie gehabt).
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(surf, (40, 50, 70), (0, 0, 40, 40), border_radius=5)
        module_images[cache_key] = surf
        return surf


# PAKET 7E: Verfuegbare Kanonen-Bildstufen im Ordner (1x scannen, cachen).
_kan_avail_cache = {}


def _available_kanonen_levels():
    if "lvls" not in _kan_avail_cache:
        lvls = set()
        try:
            for f in os.listdir(KANONEN_FOLDER):
                n = f.lower()
                if n.startswith("kanonen_lvl_") and n.endswith(".png"):
                    try:
                        lvls.add(int(n[len("kanonen_lvl_"):-4]))
                    except ValueError as e:
                        _log.warning("Kanonen-Bildname ohne Levelnummer ueberlesen: %s (%s)",
                                     f, e)
        except OSError as e:
            _log.warning("Kanonen-Ordner nicht lesbar: %s", e)
        _kan_avail_cache["lvls"] = lvls
    return _kan_avail_cache["lvls"]


def _resolve_kanonen_level(level):
    """PAKET 7E: Waffen-Stufe auf vorhandene Bildstufe abbilden
    (1-12 geklemmt; fehlt das Bild, naechstniedrigere Stufe nutzen)."""
    lvl = max(1, min(SHIP_MAX_LEVEL, int(level)))
    avail = _available_kanonen_levels()
    while lvl > 1 and avail and lvl not in avail:
        lvl -= 1
    return lvl


def load_kanonen_image(level):
    lvl = _resolve_kanonen_level(level)
    if lvl in kanonen_images:
        return kanonen_images[lvl]
    path = os.path.join(KANONEN_FOLDER, f"kanonen_lvl_{lvl}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), rect)
        target_w = 25
        target_h = int(cropped.get_height() * (target_w / cropped.get_width()))
        scaled = pygame.transform.smoothscale(cropped, (target_w, target_h))
        kanonen_images[lvl] = scaled
        return scaled
    except Exception:
        # Bewusst still: Fehlende Kanonen-Stufe ist erwartet ->
        # 25x25-Platzhalter (loest _resolve_kanonen_level schon vorher).
        surf = pygame.Surface((25, 25), pygame.SRCALPHA)
        kanonen_images[lvl] = surf
        return surf


def load_video_frames(path):
    """PAKET 8.3: Liest ein Video NATIV ein - primaer mit OpenCV (cv2),
    Fallback imageio. Skalierung erst beim Zeichnen (resize-fest).
    Liefert [] wenn Datei fehlt oder kein Decoder vorhanden ist."""
    frames = []
    if not os.path.exists(path):
        return []
    try:
        import cv2
        cap = cv2.VideoCapture(path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surf = pygame.image.frombuffer(frame.tobytes(),
                                           (frame.shape[1], frame.shape[0]), "RGB")
            frames.append(surf)
        cap.release()
        if frames:
            return frames
    except Exception as e:
        _log.warning("Video-Einlesen mit cv2 fehlgeschlagen (%s): %s",
                     os.path.basename(path), e)
        frames = []
    # PAKET 8.3: Fallback ohne opencv (imageio/FFMPEG), falls installiert
    try:
        import imageio
        reader = imageio.get_reader(path)
        for fr in reader:
            surf = pygame.image.frombuffer(fr.tobytes(),
                                           (fr.shape[1], fr.shape[0]), "RGB")
            frames.append(surf)
        reader.close()
    except Exception as e:
        _log.warning("Video-Fallback imageio fehlgeschlagen (%s): %s",
                     os.path.basename(path), e)
    return frames


def load_frame_folder(path):
    """PAKET 8.3: Laedt eine Bildsequenz (defeat_001.jpg ...) als Video-
    Ersatz. Reines pygame - funktioniert OHNE cv2/imageio auf jedem
    Rechner. Fuer das prozedurale Defeat-Fallback gedacht."""
    frames = []
    if not os.path.isdir(path):
        return []
    for name in sorted(os.listdir(path)):
        if not name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        try:
            img = pygame.image.load(os.path.join(path, name)).convert()
            frames.append(img)
        except Exception as e:
            _log.warning("Frame-Datei unlesbar uebersprungen (%s): %s", name, e)
    return frames


def load_video_any(candidates, label="Video"):
    """PAKET 8.3: Probier die Kandidaten der Reihe nach (Eigenes Video des
    Nutzers zuerst, dann mitgelieferte Fallbacks) und loggt die Wahl."""
    for p in candidates:
        frames = load_video_frames(p)
        if frames:
            print(f"OK: {label} geladen ({len(frames)} Frames) "
                  f"<- {os.path.basename(p)}")
            return frames
    print(f"HINWEIS: {label} nicht geladen - Fallback-Animation aktiv.")
    return []


# Namen + Story der Kampagnen-Sektoren (Positionen/Formen: world_map.SECTOR_UV)
# PAKET 7D: Jeder Sektor erzaehlt seinen Abschnitt der Kampagne - die
# Weltkarte zeigt NUR NOCH Kampagnen-Inhalte (keine Menues mehr).
SECTOR_DATA = {
    1: {"name": "ERDE",
        "story": "Heimatwelt der Flotte. Erste Verteidigungslinie gegen die Invasionsflotte."},
    2: {"name": "RAUMSTATION",
        "story": "Verlassene Orbitalstation. Feindliche Truppen haben die Ringe besetzt."},
    3: {"name": "ASTEROIDENGUERTEL",
        "story": "Verdeckte Feindbasis zwischen den Felsen. Vorsicht: Hinterhalte."},
    4: {"name": "MARS",
        "story": "Kolonie-Kaime auf dem roten Planeten. Die Bergungswerke werden angegriffen."},
    5: {"name": "DUNKLER SEKTOR",
        "story": "Quelle der Invasion. Hier steht das Herz der Feindflotte."},
}


class Game:
    STAGE_CLEAR = "stage_clear"
    VICTORY = "victory"          # AUFTRAG 6: Endscreen nach Kampagne 5 (+ NG+)
    INTRO = "intro"
    LOADING = "loading"
    MENU = "menu"
    PLAYING = "playing"
    STAGES = "stages"
    SETTINGS = "settings"
    RESEARCH = "research"
    SKILLTREE = "skilltree"
    DEFEAT = "defeat"
    PAUSED = "paused"
    # PAKET 8: RPG-Screens (eine Quest-Ansicht, zwei Bereiche + Beschwörung)
    QUESTS_DAILY = "quests_daily"
    QUESTS_WEEKLY = "quests_weekly"
    SUMMON = "summon"

    def __init__(self):
        self.running = True
        self.state = self.INTRO
        self.elapsed = 0.0
        self.loading_time = 0.0

        self.debug_mode = False
        self.last_stage_reward = 0
        self.debug_target = "cannon"
        self.is_dragging_cannon = False
        self.is_dragging_engine = False
        self.debug_cannon_offset = [4, -14]
        self.debug_engine_offset = [-106, -24]
        self.rumble_x = 0.0
        self.rumble_y = 0.0

        self.intro_timer = 0.0
        self.defeat_timer = 0.0
        self._defeat_exit_timer = 0.0   # PAKET 8.4: Nachlauf nach Video-Ende
        self.victory_timer = 0.0
        self.settings_return_state = self.MENU

        self.selected_sector = 0
        self.message = ""
        self.message_timer = 0.0

        # PAKET 8.3: Defeat-Video robust einrichten. Reihenfolge:
        #   1. defeat_animation.mp4   (eigenes Video des Nutzers)
        #   2. defeat_fallback.mp4    (mitgeliefertes Fallback-Video)
        #   3. defeat_fallback/       (Bildsequenz, laeuft OHNE Decoder)
        self.intro_frames = load_video_any(
            [os.path.join(_BASE, "intro2.mp4")], "Intro-Video")
        _defeat_dir = os.path.join(_BASE, "defeat_fallback")
        self.defeat_frames = (load_video_any(
            [os.path.join(_BASE, "defeat_animation.mp4"),
             os.path.join(_BASE, "defeat_fallback.mp4")], "Defeat-Video")
            or load_frame_folder(_defeat_dir))
        if self.defeat_frames:
            print(f"OK: Defeat-Fallback-Sequenz aktiv "
                  f"({len(self.defeat_frames)} Frames).")
        self.victory_frames = load_video_any(
            [os.path.join(_BASE, "victory_screen.mp4")], "Victory-Video")
        if not self.intro_frames:
            self.state = self.MENU

        # Hintergrundbilder (nativ halten, beim Zeichnen einpassen)
        self.menu_bg = self._try_img("menu_bg.png", conv=True)
        self.world_bg = self._try_img("bg_world.jpg", conv=True)
        self.logo_img = None
        logo = self._try_img("logo.png", conv=False)
        if logo is not None:
            self.logo_img = logo
        self.bg_chapter = [self._try_img(f"bg_chapter_1_part_{i}.jpg", conv=True)
                           for i in (1, 2, 3)]
        self._fit_cache = {}
        self._vcache = {}

        self.skills = SkillTree()
        self.nexus = skill_nexus.NexusUI()
        self.nexus_bg = self._try_img("skill_tree_bg.jpg", conv=True)
        # PAKET 7A: interaktive Galaxiekarte + Auswahl-Zustand
        self.gmap = world_map.GalaxyMap()
        self.map_sel = None
        # PAKET 7F: Zoom-Navigation + eigene Szenerie je Kartenobjekt.
        # Kampagne bleibt unveraendert; Hangar/Werft/Nexus bleiben draussen.
        self.map_scene = map_locations.SceneView(os.path.join(_BASE, "scenes"))
        self.map_scene.on_closed = self._map_deselect
        # PAKET 7B: Module VOR dem Schiff laden - die Optik haengt nur am
        # kosmetischen Level (Standard 1), nie an Modul-Stufen (kein
        # automatischer Wechsel mehr, siehe _draw_world).
        # PAKET 7E: Das Level ist jetzt ECHT aufwertbar (Werft-Button
        # "SCHIFF AUFWERTEN", Stufe 1-12, fortress/ship_lvl_x.png).
        self.modules = FortressModules()
        self.fortress = Fortress(FORTRESS_POS[0], FORTRESS_POS[1],
                                 level=self.modules.cosmetic_hull)
        self.sel_module = "kanonen"     # PAKET 7B: Werft-Auswahl
        self._werft_stage = None
        self._werft_panel = None
        # PAKET 7C: Upgrade-Animationen (Energie-Scan, Funken, LVL-Text)
        self.upgrade_fx = UpgradeFX()
        self.engine_effect = EngineEffect(0, 0)
        self.movement = ShipMovement()
        self.fx = combat_fx.CombatFX()
        self.damage_fx = DamageFX()   # PAKET 8.3: Treffer-Explosion am Schiff
        self.burn_fx = BurnFX()       # PAKET 8.7: Feuer ab < 50 % Huelle
        self.bg_fx = bg_fx.BgFX()     # PAKET 8.8: lebendiger Hintergrund
        if shield_gfx.available():
            print(f"OK: Eigene Schild-Grafiken gefunden "
                  f"<- {shield_gfx.source_name() or 'schilder/'}")

        # PAKET 8: RPG-Systeme. Der Spielstand wird um den Block "rpg"
        # erweitert; alte Saves laden ohne Verlust weiter (module_system
        # liefert den gelesenen Block als modules.rpg_raw mit).
        self.rpg = rpg_progression.PlayerProgress()
        self.quests = quest_system.QuestSystem()
        self.summon = summon_system.SummonSystem()
        self._rpg_bundle = rpg_progression.RPGBundle(self.rpg, self.quests,
                                                     self.summon)
        self.modules.rpg_ref = self._rpg_bundle
        self._rpg_bundle.restore(self.modules.rpg_raw)
        self.quests.refresh()
        self._summon_result = None       # letztes Beschwörungs-Ergebnis
        self._ceremony = None            # PAKET 8.5: laufende Zeremonie
        self._summon_tab = "summon"      # "summon" | "collection"
        self._menu_scroll = 0.0          # Overflow-Scroll der Menüleiste
        self._menu_overflow = False
        self._menu_max_scroll = 0
        self._nav_active = None          # PAKET 8.1: aktiver Menuepunkt
        self.last_xp_gain = 0            # für die STAGE-CLEAR-Anzeige
        self.last_levelups = 0
        # Kill-Deltas (Quest-Fortschritt aus echten Gefechten)
        self._kill_seen = {"active": {"normal": 0, "elite": 0, "boss": 0},
                           "idle": {"normal": 0, "elite": 0, "boss": 0}}

        self.idle_combat = PvECombat(is_idle=True, campaign_id=1, stage_id=1,
                                     ship_level=self.modules.ship_level)
        self.pve = PvECombat(is_idle=False, campaign_id=1, stage_id=1,
                             ship_level=self.modules.ship_level)

        self.idle_mode = True
        self.show_upgrades = False

        # UI-Polish: Screen-Fade, Menue-Partikel, Credits-Zahllauf
        self._fade = 0.0
        self._prev_state = None
        self._motes = None
        self._disp_credits = None

        # Eingabe-Zustand (Touch & Maus, Feuer beim Loslassen)
        self._ptr = None
        self._touch_guard = 0.0

        self._load_prefs()
        self._ui = {}
        self._sync_modules_to_combat()

        # PAKET 8.6: IDLE-OEKONOMIE. Offline-Bericht (Abwesenheit seit dem
        # letzten Speichern) einmalig beim Start berechnen; Live-Idle zahlt
        # regelmaessig in die Wallet (Auto-Collect) statt nur beim Beenden.
        self._idle_report = self._compute_idle_report()
        self._idle_auto_t = 0.0        # Sekunden bis zum naechsten Auto-Collect
        self._idle_session_t = 0.0     # PAKET 8.8b: Idle-Dauer dieser Sitzung (8h-Max)
        self._save_heartbeat = 0.0     # Sekunden bis zur naechsten Sicherung

    # ---------------- Hilfs-Loader / Prefs ----------------
    def _try_img(self, name, conv=True):
        path = os.path.join(_BASE, name)
        try:
            img = pygame.image.load(path)
            return img.convert() if conv else img.convert_alpha()
        except Exception:
            # Bewusst still: _try_img ist NUR fuer optionale Bilder da
            # (Fehlen ist der Normalfall) -> None, Aufrufer hat Rueckfall.
            return None

    def _fit_surf(self, img, key, brighten=0):
        """Skaliert ein Hintergrundbild auf Vollbild (Cover), gecacht pro Groesse.
        PAKET 7C: brighten > 0 hellt das Bild beim Cachen auf (BLEND_RGB_ADD),
        damit der Weltraum-Hintergrund lesbar bleibt (einmalig, keine
        Frame-Kosten)."""
        W, H = ui_kit.W, ui_kit.H
        k = (key, W, H)
        out = self._fit_cache.get(k)
        if out is None:
            iw, ih = img.get_size()
            s = max(W / iw, H / ih)
            out = pygame.transform.smoothscale(img, (max(1, int(iw * s)), max(1, int(ih * s))))
            if brighten:
                out.fill((brighten, brighten, min(255, brighten + 8)),
                         special_flags=pygame.BLEND_RGB_ADD)
            if len(self._fit_cache) > 12:
                self._fit_cache.clear()
            self._fit_cache[k] = out
        return out

    def _shgfx_scaled(self, schild_lvl, d):
        """PAKET 8.7: eigene Schild-Grafik auf den Ring-Durchmesser `d`
        skaliert (gecacht pro Stufe+Groesse), sonst None."""
        img = shield_gfx.image_for(schild_lvl)
        if img is None:
            return None
        key = ("shgfx", schild_lvl, d)
        out = self._fit_cache.get(key)
        if out is None:
            try:
                out = pygame.transform.smoothscale(img, (d, d))
            except Exception:
                # Bewusst still: Skalierung kann bei Mini-Groessen (d<2)
                # scheitern -> None, es zeichnet der Standard-Schildring.
                return None
            out.set_alpha(200)          # dezente Transparenz, einmalig
            if len(self._fit_cache) > 12:
                self._fit_cache.clear()
            self._fit_cache[key] = out
        return out

    def _video_frame(self, frames, idx):
        """Skaliert das Videoframe bildschirmfuellend (kleiner Cache)."""
        W, H = ui_kit.W, ui_kit.H
        k = (W, H, idx)
        c = self._vcache
        out = c.get(k)
        if out is None:
            if len(c) > 3:
                c.clear()
            f = frames[idx]
            fw, fh = f.get_size()
            s = max(W / fw, H / fh)
            out = pygame.transform.smoothscale(f, (max(1, int(fw * s)), max(1, int(fh * s))))
            c[k] = out
        return out

    def _load_prefs(self):
        self.prefs = {}
        try:
            with open(_PREFS_PATH, "r", encoding="utf-8") as fh:
                self.prefs = json.load(fh)
        except FileNotFoundError:
            # Bewusst still: Beim allerersten Start existiert ui_prefs.json
            # noch nicht - das ist der normale Neuanfang.
            self.prefs = {}
        except Exception as e:
            _log.warning("ui_prefs.json unlesbar, Einstellungen zurueckgesetzt: %s", e)
            self.prefs = {}
        if self.prefs.get("muted"):
            SFX.muted = True

    def _save_prefs(self):
        try:
            with open(_PREFS_PATH, "w", encoding="utf-8") as fh:
                json.dump(self.prefs, fh)
        except Exception as e:
            _log.warning("Einstellungen konnten nicht gespeichert werden: %s", e)

    # ---------------- Bruecken (Paket 3/4 + PAKET 7B/7C gear_mods) ----------------
    def _sync_modules_to_combat(self):
        """PAKET 7B: Modul-Levels wirken direkt aufs Gefecht.
        gear_mods = Boni der Werft-Module (additiv zu den Skill-Mods, siehe
        pve_system.PvECombat.mod). SYSTEM-SYNERGIE verstaerkt gear_mods.
        PAKET 7C: "huelle" liefert die max. Huelle (+100/Stufe), "schild"
        ist jetzt das Schildsystem (-3% erlittener Schaden je Stufe)."""
        amp = 1.0 + (self.skills.modifiers().get("gear_amp", 0.0)
                     if hasattr(self, "skills") else 0.0)
        kan_l = self.modules.get("kanonen").level
        rea_l = self.modules.get("reaktor").level
        rad_l = self.modules.get("radar").level
        sch_l = self.modules.get("schild").level
        hul_l = self.modules.get("huelle").level
        # PAKET 7E: Schiffs-Rumpf-Stufe (1-12) - +80 Huelle, +3% Schaden/Stufe
        ship_l = self.modules.ship_hull_level
        gear = {
            # REAKTOR: Energieversorgung -> Krit-Chance & Drohnen-Schaden
            "crit_chance": 0.02 * max(0, rea_l - 1) * amp,
            "drone_dmg_pct": 0.06 * max(0, rea_l - 1) * amp,
            # RADAR: Aufklaerung -> Credits & Core-Chance
            "credit_pct": 0.04 * max(0, rad_l - 1) * amp,
            "core_chance": 0.02 * max(0, rad_l - 1) * amp,
            # SCHILD (PAKET 7C): Schadensreduktion, gedeckelt (Skill + Gear)
            "dr_pct": min(0.45, 0.03 * max(0, sch_l - 1) * amp),
            # SCHIFFSRUMPF (PAKET 7E): groessere Rumpfklasse = mehr Feuerkraft
            "dmg_pct": SHIP_DMG_PCT_PER_LVL * max(0, ship_l - 1) * amp,
        }
        # SCHRITT 2: Sammlungs-Passiv der Champions/Einheiten. Jede
        # einmalig besessene Einheit addiert ihren Seltenheits-Bonus auf
        # "drone_dmg_pct" (siehe SummonSystem.collection_mods). Bewusst
        # NICHT mit SYSTEM-SYNERGIE (gear_amp) multipliziert - der
        # Sammlungs-Bonus ist ein eigenes System und bleibt davon
        # unberuehrt.
        col = self.summon.collection_mods() if hasattr(self, "summon") else {}
        gear["drone_dmg_pct"] = gear.get("drone_dmg_pct", 0.0) \
            + float(col.get("drone_dmg_pct", 0.0))
        # AUFTRAG 8: AUSGERUESTETE CHAMPIONS unterstuetzen das Schiff.
        # Aktive Stats (rpg_config.HEROES): dmg_mult -> +x% Schaden (additiv),
        # rate_mult -> Feuerintervall (invers multiplikativ, 1.05 = +5 %
        # Feuerrate), hp -> +flache Huelle. Bewusst OHNE SYSTEM-SYNERGIE
        # (gear_amp) - wie der Sammlungs-Bonus ein eigenes System.
        # Eine Faehigkeit je Champion (max. CHAMPION_HUD_BUTTONS = 2 Buttons)
        # geht als champ_skills ins Gefecht (pve_system.activate_champ_skill).
        helden = self.summon.equipped_heroes() if hasattr(self, "summon") else []
        champ_hp = 0.0
        champ_rate = 1.0
        sk_defs = []
        for _hk, _hero in helden:
            st = _hero.get("stats") or {}
            gear["dmg_pct"] = gear.get("dmg_pct", 0.0) \
                + (float(st.get("dmg_mult", 1.0)) - 1.0)
            _rm = float(st.get("rate_mult", 1.0))
            if _rm > 0.5:
                champ_rate *= 1.0 / _rm
            champ_hp += float(st.get("hp", 0.0))
            _sd = rpg_config.CHAMPION_SKILLS.get(_hk)
            if _sd and len(sk_defs) < rpg_config.CHAMPION_HUD_BUTTONS:
                _d = dict(_sd)
                _d["key"] = _hk
                _d["hero"] = _hero.get("name", _hk)
                sk_defs.append(_d)
        if champ_rate != 1.0:
            gear["rate_mult"] = gear.get("rate_mult", 1.0) * champ_rate
        hp_flat = float(self.skills.modifiers().get("hp_flat", 0.0)) \
            if hasattr(self, "skills") else 0.0
        for combat in (self.idle_combat, self.pve):
            combat.dmg_level = kan_l
            combat.speed_level = self.modules.get("antrieb").level
            combat.cannon_count_level = min(8, 1 + kan_l // 2)
            combat.hangar_level = self.modules.get("hangar").level
            combat.repair_level = self.modules.get("reparatur").level
            combat.ship_level = self.modules.ship_level
            # AUFTRAG 6: NG+-Grad auf beide Gefechte (Gegner/Beute-Skalierung)
            combat.ng_plus = int(getattr(self.modules, "ng_plus", 0))
            if hasattr(self, "skills"):
                self.skills.apply_to_combat(combat)
            combat.gear_mods = gear
            # AUFTRAG 8: Champion-Faehigkeiten ans Gefecht. Laufende
            # Abklingzeiten bleiben erhalten, solange dieselbe Zahl von
            # Faehigkeiten aktiv ist (kein CD-Reset durch Mid-Fight-Sync).
            if len(getattr(combat, "champ_skills", [])) != len(sk_defs):
                combat.champ_cd = [0.0] * len(sk_defs)
            combat.champ_skills = sk_defs
            base_hp = 700.0 + (hul_l - 1) * 100          # PAKET 7C: HUELLE
            base_hp += SHIP_HP_PER_LVL * (ship_l - 1)    # PAKET 7E: SCHIFFSRUMPF
            base_hp += hp_flat            # PAKET 7B: SCHILDKONDENSATOR (flach)
            base_hp += champ_hp           # AUFTRAG 8: Champions (flache Huelle)
            combat.max_player_hp = base_hp * (1.0 + combat.mod("hp_pct", 0.0))
            combat.player_hp = min(combat.player_hp, combat.max_player_hp)
        # PAKET 7B: KONTRAKTE (Oekonomie) - Rabatt auf Werft-Upgrades
        self.modules.cost_discount = self.skills.modifiers().get("cost_discount", 0.0) \
            if hasattr(self, "skills") else 0.0

    def _collect_idle_loot(self):
        """Überweist gesammelte Idle-Credits (und Data Cores) in die Wallet."""
        if self.idle_combat.credits > 0:
            self.modules.credits += self.idle_combat.credits
            self.idle_combat.credits = 0
        if self.idle_combat.data_cores_earned > 0:
            n = self.idle_combat.data_cores_earned
            self.modules.data_cores += n
            self.idle_combat.data_cores_earned = 0
            # SCHRITT 1b: Idle-Cores zaehlen jetzt auch fuer die
            # Sammler-Quests (gleiche Metrik wie der aktive Pfad,
            # PAKET 8) - vorher gingen sie dort verloren.
            self.quests.record("cores_earned", n)
        self.modules.save()

    # ---------------- PAKET 8.6: IDLE-BERICHT (OFFLINE-EINKOMMEN) ------
    def _compute_idle_report(self):
        """Offline-Einkommen für die Zeit seit der letzten Sicherung.
        SCHRITT 3b: Dieselbe Formel wie das Live-Idle - Nominaler Kill-
        Ertrag der hoechsten Stufe (pve_system.stage_nominal_reward,
        gewichtetes Mittel des Spawn-Pools) x erwartete Kill-Rate
        (IDLE_KPS, Messwert Live) x IDLE_EFFICIENCY, multipliziert mit
        denselben Kill-Faktoren wie im Live-Gefecht (1 + idle_pct,
        BAL_CREDITS, BAL_IDLE_CREDITS). Max. 8 h. Liefert None bei
        kurzem Weg, erstem Start oder altem Save."""
        prev = float(getattr(self.modules, "prev_saved_at", 0.0) or 0.0)
        if prev <= 0.0:
            return None
        away = time.time() - prev
        if away < rpg_config.IDLE_MIN_AWAY_S:
            return None
        capped = min(away, rpg_config.IDLE_CAP_S)
        idle_pct = 0.0
        if hasattr(self, "skills"):
            idle_pct = float(self.skills.modifiers().get("idle_pct", 0.0))
        # SCHRITT 3b: Live-Formel statt der alten Naeherungskonstanten
        # (IDLE_CPS_BASE/IDLE_CPS_PER_STAGE) - Offline verdient jetzt
        # dasselbe pro virtuellem Kill wie das Live-Idle.
        # AUFTRAG 6: NG+-Grad erhoelt die Beute (ng_reward_mult) - auch
        # offline, passend zur skalierten Gegnerwelt.
        _ng = int(getattr(self.modules, "ng_plus", 0) or 0)
        nominal = pve_sys.stage_nominal_reward(
            self.modules.highest_stage, self.modules.ship_level) \
            * rpg_config.ng_reward_mult(_ng)
        rate = nominal * rpg_config.IDLE_KPS \
            * (1.0 + idle_pct) * rpg_config.BAL_CREDITS \
            * rpg_config.BAL_IDLE_CREDITS * rpg_config.IDLE_EFFICIENCY
        credits = int(rate * capped)
        cores = min(rpg_config.IDLE_CORE_CAP,
                    int(capped * rpg_config.IDLE_KPS
                        / max(1, rpg_config.IDLE_CORE_KILLS)))
        return {"away_s": away, "capped_s": capped,
                "credits": credits, "cores": cores}

    def _collect_idle_report(self):
        """Offline-Beute abholen: in die Wallet, sichern, Meldung zeigen."""
        rep = self._idle_report
        if not rep:
            return
        self.modules.credits += int(rep["credits"])
        self.modules.data_cores += int(rep["cores"])
        self.modules.save()
        self._idle_report = None
        msg = f"IDLE-BERICHT ABGEHOLT: +{rep['credits']:,} Cr"
        if rep["cores"]:
            msg += f", +{rep['cores']} Cores"
        self.show_message(msg, duration=3.5)
        SFX.play("upgrade")

    @staticmethod
    def _fmt_away(seconds):
        seconds = int(max(0, seconds))
        h, m = seconds // 3600, (seconds % 3600) // 60
        if h >= 1:
            return f"{h} H {m:02d} MIN"
        return f"{max(1, m)} MIN"

    def _layout_idle_report(self):
        """Button-Layout des Idle-Berichts (nur ABHOLEN ist klickbar)."""
        W, H = ui_kit.W, ui_kit.H
        pw = min(W - 2 * margin(), u(430))
        ph = u(250)
        panel = pygame.Rect((W - pw) // 2, (H - ph) // 2 - u(10), pw, ph)
        bw = min(pw - u(40), u(240))
        return {"panel": panel,
                "idle_collect": Btn("idle_collect",
                                    pygame.Rect((W - bw) // 2,
                                                panel.bottom - u(52),
                                                bw, u(38)),
                                    "ABHOLEN", "IN DIE WALLET", CYAN)}

    def _draw_idle_report(self):
        """PAKET 8.6: Belohnungs-Overlay beim Reinkommen - zeigt, was das
        Basis-Team waehrend der Abwesenheit verdient hat (Credits + Data
        Cores). Nur der ABHOLEN-Button ist klickbar."""
        rep = self._idle_report
        if not rep:
            return
        W, H = ui_kit.W, ui_kit.H
        lay = self._layout_idle_report()
        self._ui = {k: v for k, v in lay.items() if isinstance(v, Btn)}
        overlay(SCREEN, 215)
        prect = lay["panel"]
        glass_panel(SCREEN, prect, accent=CYAN, radius=u(12), alpha=235,
                    width=2)
        g = radial_glow_k(CYAN, u(120), 0.22)
        SCREEN.blit(g, g.get_rect(center=(prect.centerx, prect.top + u(4))),
                    special_flags=pygame.BLEND_ADD)
        neon_text(SCREEN, "IDLE-BERICHT", F(16), CYAN,
                  (prect.centerx, prect.y + u(18)), "midtop", 1)
        text(SCREEN, "AUTOMATISCHE SAMMLUNG WÄHREND DEINER ABWESENHEIT",
             F(9), MUTED, (prect.centerx, prect.y + u(44)), "center")
        capped = rep["capped_s"] < rep["away_s"]
        text(SCREEN, f"ABWESEND: {self._fmt_away(rep['away_s'])}"
                     + ("  (ANGERECHNET: 8 H MAX)" if capped else ""),
             F(11), WHITE, (prect.centerx, prect.y + u(68)), "center")
        text(SCREEN, f"+{rep['credits']:,} CREDITS", F(18), GREEN,
             (prect.centerx, prect.y + u(98)), "center")
        if rep["cores"]:
            text(SCREEN, f"+{rep['cores']} DATA CORES", F(13), CYAN,
                 (prect.centerx, prect.y + u(126)), "center")
        else:
            text(SCREEN, "KEINE DATA CORES DIESMAL", F(10), MUTED,
                 (prect.centerx, prect.y + u(126)), "center")
        text(SCREEN, "DIE BEUTE WIRD NACH DEM ABHOLEN GUTGESCHRIEBEN.",
             F(8), DIM, (prect.centerx, prect.y + u(152)), "center")
        draw_compact_btn(SCREEN, lay["idle_collect"],
                         pressed=self._pressed("idle_collect"))

    def _restart_stage(self):
        campaign = self.selected_sector if self.selected_sector > 0 else self.pve.campaign_id
        stage = self.pve.stage_id
        # PAKET 7C: Repeat-Flag fuer die Core-Vergabe (Erstbeendung vs. Farm)
        repeat = (campaign, stage) in self.modules.completed_stages
        self.pve = PvECombat(is_idle=False, campaign_id=campaign, stage_id=stage,
                             ship_level=self.modules.ship_level, is_repeat=repeat)
        self._sync_modules_to_combat()
        self.quests.begin_mission()   # PAKET 8: neuer Missionsversuch, clean
        self.state = self.PLAYING

    def show_message(self, msg, duration=3.0):
        self.message = msg
        self.message_timer = duration

    def _toggle_sound(self):
        SFX.toggle_mute()
        self.prefs["muted"] = bool(SFX.muted)
        self._save_prefs()
        self.show_message(f"SOUND: {'AUS' if SFX.muted else 'AN'}")

    def _overdrive(self):
        if self.idle_mode:
            return
        if self.pve.activate_overdrive():
            self.show_message("ÜBERTAKTUNG AKTIV: doppelte Feuerrate (8s)")
        elif self.pve.mod("overdrive", 0) < 1:
            self.show_message("Übertaktung nicht trainiert (Skill-Nexus, Sparte SPEZIAL)")
        else:
            self.show_message("Übertaktung nicht bereit (Abklingzeit)")

    def _champ_skill(self, idx):
        """AUFTRAG 8: Champion-Faehigkeit (HUD-Button) ausloesen."""
        if self.idle_mode:
            return
        sks = getattr(self.pve, "champ_skills", [])
        if not (0 <= int(idx) < len(sks)):
            return
        sk = sks[int(idx)]
        if self.pve.activate_champ_skill(idx):
            self.show_message(f"{sk.get('hero', '')}: {sk.get('name', '')}!")
        else:
            self.show_message(f"{sk.get('name', '')} nicht bereit (Abklingzeit)")

    def _skill_train(self):
        node_id = self.nexus.selected
        if not node_id:
            return
        ok, reason = self.skills.unlock_info(node_id)
        if not ok:
            self.show_message(f"Nicht moeglich: {reason}")
            return
        cost = self.skills.cost_of(node_id)
        if self.modules.data_cores < cost:
            self.show_message(f"Zu wenig Data Cores: {cost} benoetigt")
            return
        self.modules.data_cores -= cost
        self.skills.unlock(node_id)
        self._sync_modules_to_combat()
        self.modules.save()
        SFX.play("upgrade")
        pos = self.nexus.nodes.get(node_id)
        if pos:
            branch, _i, _n = None, -1, None
            for br in SKILL_TREE:
                for nd in br["nodes"]:
                    if nd["id"] == node_id:
                        branch = br
            self.nexus.fire(pos[0], pos[1], branch["color"] if branch else CYAN)
        self.show_message(f"Skill trainiert: {node_id}")

    def _quit(self):
        self._collect_idle_loot()
        self.running = False

    # ---------------- Hauptschleife ----------------
    def run(self):
        while self.running:
            dt = min(CLOCK.tick(FPS) / 1000.0, 0.05)
            if self.message_timer > 0:
                self.message_timer -= dt
            self.elapsed += dt
            if self._fade > 0:
                self._fade = max(0.0, self._fade - dt * 3.5)
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    # ---------------- Eingabe (Touch + Maus, Tastatur optional) ----------------
    def _fpos(self, event):
        rw, rh = ui_kit.real_size()
        return ui_kit.map_pos((event.x * rw, event.y * rh))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
                return

            if event.type == pygame.FINGERDOWN:
                self._touch_guard = self.elapsed + 0.45
                self._press(self._fpos(event))

            elif event.type == pygame.FINGERUP:
                self._release(self._fpos(event))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.elapsed < self._touch_guard:
                    continue                     # synthetisches Touch-Maus-Event
                pos = ui_kit.map_pos(event.pos)
                if event.button == 1 and self._debug_drag_start(pos):
                    continue
                if event.button == 1:
                    self._press(pos)
                elif event.button == 3 and self.debug_mode and self.state == self.PLAYING:
                    ex = self.fortress.x + self.debug_engine_offset[0]
                    ey = self.fortress.y + self.debug_engine_offset[1]
                    if math.hypot(pos[0] - ex, pos[1] - ey) < 60:
                        self.is_dragging_engine = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.elapsed < self._touch_guard:
                    continue
                if event.button == 1:
                    self._release(ui_kit.map_pos(event.pos))
                self.is_dragging_cannon = False
                self.is_dragging_engine = False

            elif event.type == pygame.MOUSEMOTION:
                self._debug_drag_move(ui_kit.map_pos(event.pos))

            elif event.type == pygame.KEYDOWN:
                self._key(event)

    def _debug_drag_start(self, pos):
        """Desktop-Debug: Kanone/Antrieb ziehen (rechte Maustaste = Antrieb)."""
        if not (self.debug_mode and self.state == self.PLAYING):
            return False
        cx = self.fortress.x + self.debug_cannon_offset[0]
        cy = self.fortress.y + self.debug_cannon_offset[1]
        if math.hypot(pos[0] - cx, pos[1] - cy) < 35:
            self.is_dragging_cannon = True
            self.debug_target = "cannon"
            return True
        return False

    def _debug_drag_move(self, pos):
        if self.is_dragging_cannon:
            self.debug_cannon_offset[0] = pos[0] - self.fortress.x
            self.debug_cannon_offset[1] = pos[1] - self.fortress.y
        if self.is_dragging_engine:
            self.debug_engine_offset[0] = pos[0] - self.fortress.x
            self.debug_engine_offset[1] = pos[1] - self.fortress.y

    def _press(self, pos):
        self._ptr = None
        if self.state == self.SKILLTREE:
            nid = self.nexus.hit(pos)
            if nid:
                self._ptr = {"kind": "node", "id": nid}
                return
        if self.state == self.RESEARCH:
            # PAKET 7B: Modul-Hotspots direkt am Schiff (Release-on-selbigem)
            mk = self._werft_hit(pos)
            if mk:
                self._ptr = {"kind": "mod", "id": mk}
                return
        if (self.state == self.STAGES and self.selected_sector == 0
                and not self.map_scene.blocks_map()):
            # PAKET 7A/7F: Kartenobjekte haben Vorrang - ausser auf dem Panel;
            # waehrend Zoom/Szene uebernehmen die Szenen-Buttons die Eingabe
            self.gmap.prepare(self.world_bg)
            pr = self.gmap.panel_rect()
            if pr and pr.collidepoint(pos):
                pass                       # Panel-Zone: Buttons behandeln
            else:
                nid = self.gmap.hit(pos)
                if nid:
                    self._ptr = {"kind": "obj", "id": nid}
                    return
                if self.map_sel:
                    self._ptr = {"kind": "obj", "id": None}   # leergetippt
                    return
        if self.state == self.SUMMON and self._ceremony:
            # PAKET 8.5: beliebiger Tipp überspringt die Zeremonie
            self._ceremony["skip"] = True
            return
        b = first_hit(self._ui, pos)
        if b:
            ui_kit.mark_pressed(b.id)          # Touch-Ripple
            self._ptr = {"kind": "btn", "id": b.id}
            return
        # AUFTRAG 8: Helden-Karte in der Sammlung angetippt -> Ausruesten
        # (Release auf derselben Karte loest aus - gleiches Muster wie
        # "obj" auf der Kampagnenkarte).
        if self.state == self.SUMMON and self._summon_tab == "collection":
            key = self._collection_hero_hit(pos)
            if key:
                self._ptr = {"kind": "smcard", "id": key}

    def _release(self, pos):
        p, self._ptr = self._ptr, None
        if not p:
            return
        if p["kind"] == "node":
            if self.state == self.SKILLTREE and self.nexus.hit(pos) == p["id"]:
                self.nexus.select(p["id"])
                SFX.play("click", 0.4)
            return
        if p["kind"] == "mod":
            # PAKET 7B: Werft-Modul am Schiff gewaehlt
            if self.state == self.RESEARCH and self._werft_hit(pos) == p["id"]:
                if self.sel_module != p["id"]:
                    SFX.play("click", 0.4)
                self.sel_module = p["id"]
            return
        if p["kind"] == "obj":
            # PAKET 7A: Kartenobjekt gewaehlt (Release-on-selbigem Objekt)
            if self.state == self.STAGES and self.selected_sector == 0:
                if p["id"] is None:
                    self._map_deselect()
                elif self.gmap.hit(pos) == p["id"]:
                    self._map_select(p["id"])
            return
        if p["kind"] == "smcard":
            # AUFTRAG 8: Ausruesten nur, wenn der Finger auf derselben
            # Helden-Karte hochkommt (Release-Bestaetigung wie ueberall).
            if self.state == self.SUMMON and self._summon_tab == "collection" \
                    and self._collection_hero_hit(pos) == p["id"]:
                self._toggle_equip(p["id"])
            return
        b = self._ui.get(p["id"])
        if b and b.hit(pos):
            self._fire(b.id)

    def _key(self, event):
        """PAKET 8.7 MOBILE: KEINE Tastatur-Kurzbefehle mehr (kein ESC,
        kein F1/M/Q/R - das Spiel ist komplett touch-bedienbar). Nur die
        Android-ZURUECK-Taste bleibt aktiv (pausiert / schliesst gestuft),
        weil sie zum System gehoert und auf dem Handy keine Tastatur ist."""
        k = event.key
        if k != pygame.K_AC_BACK:            # Android-Zurueck-Taste
            return
        if self.state == self.PLAYING:
            self.state = self.PAUSED
        elif self.show_upgrades:
            self.show_upgrades = False
        elif self.state == self.STAGES:
            # PAKET 7A/7F: gestuftes Schliessen
            # (Sheet -> Szene schliessen (Zoom zurueck) -> Auswahl -> Menue)
            if self.selected_sector > 0:
                self.selected_sector = 0
            elif self.map_scene.active:
                self.map_scene.close()
            elif self.map_sel:
                self._map_deselect()
            else:
                self.state = self.MENU
        elif self.state in (self.SETTINGS, self.RESEARCH, self.SKILLTREE,
                            self.QUESTS_DAILY, self.QUESTS_WEEKLY, self.SUMMON):
            if self.state == self.SETTINGS:
                self.state = self.settings_return_state
            else:
                self.state = self.MENU

    # ---------------- Update (Logik unveraendert) ----------------
    def update(self, dt):
        self.quests.refresh()   # PAKET 8: Tages-/Wochen-Reset pruefen (billig)
        # Credits-Zahllauf (Anzeige naehert sich dem echten Stand an)
        target = self.modules.credits
        if self._disp_credits is None:
            self._disp_credits = float(target)
        else:
            d = target - self._disp_credits
            self._disp_credits += d * min(1.0, dt * 9.0)
            if abs(d) < 1.0:
                self._disp_credits = float(target)

        # PAKET 8.6: IDLE-LIVE-EINKOMMEN. Im Idle-Betrieb wird das
        # verdiente Geld regelmaessig in die Wallet ueberwiesen.
        # PAKET 8.8b: GEBREMST (Nutzerfeedback) - Auszahlung nur noch ALLE
        # STUNDE (IDLE_PAYOUT_S), und nach 8 h Idle in dieser Sitzung ist
        # das MAXIMUM erreicht: pve_system.income_frozen stoppt Credits
        # und Cores (HUD zeigt "MAXIMUM ERREICHT").
        if self.state == self.PLAYING and self.idle_mode:
            self._idle_auto_t += dt
            self._idle_session_t += dt
            if (self._idle_session_t >= IDLE_SESSION_CAP_S
                    and not getattr(self.idle_combat, "income_frozen", False)):
                self.idle_combat.income_frozen = True
                self.show_message("IDLE-MAXIMUM ERREICHT (8 H) - keine Beute mehr, "
                                  "Verlassen setzt zurueck", duration=4.0)
                SFX.play("hit", 0.5)
            if self._idle_auto_t >= IDLE_PAYOUT_S:
                self._idle_auto_t = 0.0
                cr = int(self.idle_combat.credits)
                co = int(self.idle_combat.data_cores_earned)
                if cr > 0 or co > 0:
                    self._collect_idle_loot()
                    msg = f"IDLE-STUNDENLOHN: +{cr:,} Cr überwiesen"
                    if co:
                        msg += f", +{co} Data Core{'s' if co != 1 else ''}"
                    self.show_message(msg, duration=2.6)
        # PAKET 8.6: Save-Heartbeat haelt "saved_at" frisch (Basis des
        # Offline-Einkommens; schuetzt ausserdem den Fortschritt bei
        # Abstuerzen).
        self._save_heartbeat += dt
        if self._save_heartbeat >= rpg_config.IDLE_SAVE_HEARTBEAT_S:
            self._save_heartbeat = 0.0
            self.modules.save()

        if self.state == self.INTRO:
            if self.intro_frames:
                self.intro_timer += dt
                if self.intro_timer >= len(self.intro_frames) / 30.0:
                    self.state = self.MENU
            return

        if self.state in (self.STAGE_CLEAR, self.VICTORY):   # AUFTRAG 6: auch VICTORY
            if self.victory_frames:
                self.victory_timer += dt * 2.0
                full = len(self.victory_frames) / 30.0
                if self.victory_timer >= full:
                    self.victory_timer = full
            return

        if self.state == self.LOADING:
            self.loading_time += dt
            if self.loading_time >= 2.5:
                self.state = self.MENU
            return

        if self.state == self.DEFEAT:
            # PAKET 8.7: Video laeuft einmal durch, danach bleibt der
            # Endbildschirm mit TOUCH-BUTTONS stehen (kein Auto-Sprung,
            # keine Tastatur-Hinweise - siehe _layout_defeat). Der untere
            # Bereich der eigenen Defeat-Animation enthaelt eingebrannte
            # {R}/{ESC}-Buttons - die Endkarte ueberdeckt genau diesen
            # Streifen mit Touch-Buttons.
            if self.defeat_frames:
                self.defeat_timer += dt
                full = len(self.defeat_frames) / 30.0
                if self.defeat_timer > full:
                    self.defeat_timer = full
            return

        if self.state == self.PAUSED:
            return

        self.fortress.update(dt)
        self.movement.update(dt)
        self.upgrade_fx.update(dt)   # PAKET 7C: Upgrade-Animationen ticken
        self.map_scene.update(dt)    # PAKET 7F: Zoom-/Szenen-Uebergaenge ticken

        engine_lvl = self.modules.get("antrieb").level
        self.engine_effect.update(dt, engine_lvl)

        center = (self.fortress.x, self.fortress.y)
        mounted_cannons = []
        current_offset = self.debug_cannon_offset if self.debug_mode else CANNON_OFFSETS[0]
        for ox, oy in [current_offset]:
            mounted_cannons.append((center[0] + ox, center[1] + oy))

        if self.state == self.PLAYING:
            combat = self.idle_combat if self.idle_mode else self.pve
            if self.idle_mode:
                self.idle_combat.update(dt, center, mounted_cannons)
            else:
                self.pve.update(dt, center, mounted_cannons)
            self.fx.update(dt, combat, center)
            # PAKET 8.3: Einschlags-FX am Schiff aktualisieren (update + decay)
            ship_wx, ship_wy = self.movement.get_position(self.fortress.x,
                                                          self.fortress.y)
            self.damage_fx.update(dt, combat, (ship_wx, ship_wy))
            # PAKET 8.7: Schiff brennt, sobald die Huelle unter 50 % faellt
            self.burn_fx.update(
                dt,
                combat.player_hp / max(1.0, combat.max_player_hp),
                (ship_wx, ship_wy))
            # PAKET 8.8: Hintergrund-Animation nur im aktiven Gefecht
            if not self.idle_mode:
                self.bg_fx.set_stage(combat.stage_id)
                self.bg_fx.update(dt)

            # PAKET 8: Quest-Fortschritt aus echten Gefechts-Ereignissen
            # (Deltas der Kill-Statistik; neues Gefecht startet bei 0).
            seen = self._kill_seen["idle" if self.idle_mode else "active"]
            for k, metric in (("normal", "kills"), ("elite", "elite_kills"),
                              ("boss", "boss_kills")):
                cur = combat.kill_stats[k]
                if cur < seen[k]:            # neues Gefechts-Objekt
                    seen[k] = 0
                d = cur - seen[k]
                seen[k] = cur
                if d > 0 and (not self.idle_mode
                              or rpg_config.QUEST_COUNT_IDLE_KILLS):
                    self.quests.record(metric, d)

            if hasattr(self.pve, 'data_cores_earned') and self.pve.data_cores_earned > 0:
                n_cores = self.pve.data_cores_earned
                self.modules.data_cores += n_cores
                self.pve.data_cores_earned = 0
                self.quests.record("cores_earned", n_cores)   # PAKET 8 (aktiv)
                self.modules.save()

            if not self.idle_mode and self.pve.is_defeated:
                self.quests.note_loss()      # PAKET 8: Mission nicht mehr 'clean'
                # PAKET 8.4: Video von vorn - auch beim zweiten Tod in
                # derselben Session laeuft die Sequenz voll durch.
                self.defeat_timer = 0.0
                self._defeat_exit_timer = 0.0
                self.state = self.DEFEAT
                return

            if not self.idle_mode:
                result = self.pve.get_result()
                if result["won"] and self.state == self.PLAYING:
                    # AUFTRAG 6: Endspiel-Erkennung VOR complete_stage -
                    # Sektor 5 ist die letzte Kampagne (Karte kennt nur 1-5),
                    # Stufe 15 deren Finale. Dann: VICTORY-Screen + NG+.
                    final_win = (self.selected_sector == 5
                                 and self.pve.stage_id == 15)
                    self.modules.complete_stage(
                        campaign_id=self.selected_sector,
                        stage_id=self.pve.stage_id,
                        credits_earned=result["credits_earned"]
                    )
                    # PAKET 8: Spieler-XP + Quest-Fortschritt fuer Missionsende
                    self.last_xp_gain = rpg_config.campaign_xp(
                        self.pve.stage_id, bool(getattr(self.pve, "is_repeat", False)))
                    self.last_levelups, _ = self.rpg.add_xp(self.last_xp_gain)
                    self.quests.record_mission_clear()
                    self.last_stage_reward = result["credits_earned"]
                    self.victory_timer = 0.0
                    if final_win:
                        # AUFTRAG 6: NEW GAME+ freischalten (Grad +1) und
                        # sofort auf beide Gefechte syncen - der naechste
                        # Einsatz laeuft mit skalierten Gegnern/Beute.
                        self.modules.ng_plus = int(getattr(self.modules, "ng_plus", 0)) + 1
                        self.modules.save()
                        self._sync_modules_to_combat()
                        self.state = self.VICTORY
                    else:
                        self.state = self.STAGE_CLEAR
                    SFX.play_victory_audio()
                    return
        elif self.state != self.PAUSED:
            self.fx.update(dt, None)
            self.damage_fx.update(dt, None)   # PAKET 8.3: Shake/Vignette klingen ab

    def credits_display(self):
        """Anzeige-Stand des Credits-Zaehlers (Zahllauf)."""
        return int(round(self._disp_credits or 0.0))

    # ---------------- Aktionen (Fire-on-Release) ----------------
    def _fire(self, bid):
        SFX.play("click", 0.4)
        if bid in ("snd_menu", "snd_res", "snd_stg"):
            self._toggle_sound()
            return
        st = self.state

        if st == self.INTRO:
            self.state = self.MENU
            return

        if st == self.MENU:
            # PAKET 8.6: Idle-Bericht blockiert das Menue bis zum Abholen
            if self._idle_report:
                if bid == "idle_collect":
                    self._collect_idle_report()
                return
            # PAKET 8.1: aktiven Menuepunkt merken (deutlicher Cyan-Akzent)
            if bid in ("btn_idle", "btn_research", "btn_skills", "btn_stages",
                       "btn_daily", "btn_weekly", "btn_summon", "btn_settings"):
                self._nav_active = bid
            if bid == "btn_idle":
                self.idle_mode = True
                self.idle_combat.stage_id = self.modules.highest_stage
                self._sync_modules_to_combat()
                # PAKET 8.8b: frische Idle-Sitzung (1h-Auszahlung + 8h-Max)
                self.idle_combat.income_frozen = False
                self._idle_auto_t = 0.0
                self._idle_session_t = 0.0
                self.state = self.PLAYING
            elif bid == "btn_research":
                self.state = self.RESEARCH
            elif bid == "btn_skills":
                self.nexus.select(None)
                self.state = self.SKILLTREE
            elif bid == "btn_stages":
                self.selected_sector = 0
                self._map_deselect()
                self.state = self.STAGES
            elif bid == "btn_settings":
                self.settings_return_state = self.MENU
                self.state = self.SETTINGS
            elif bid == "btn_daily":            # PAKET 8: Daily-Quests
                self.quests.refresh()
                self.state = self.QUESTS_DAILY
            elif bid == "btn_weekly":           # PAKET 8: Weekly-Quests
                self.quests.refresh()
                self.state = self.QUESTS_WEEKLY
            elif bid == "btn_summon":           # PAKET 8: Beschwoerung
                self.state = self.SUMMON
            elif bid == "menu_left":            # PAKET 8: Leisten-Scroll
                self._menu_scroll = max(0.0, self._menu_scroll - u(150))
            elif bid == "menu_right":
                self._menu_scroll = min(float(self._menu_max_scroll),
                                        self._menu_scroll + u(150))
            elif bid == "btn_quit":
                self._quit()
            elif bid == "snd_menu":
                self._toggle_sound()
            return

        # ---------------- PAKET 8: QUEST-SCREEN ----------------
        if st in (self.QUESTS_DAILY, self.QUESTS_WEEKLY):
            scope_key = "daily" if st == self.QUESTS_DAILY else "weekly"
            if bid == "q_back":
                self.state = self.MENU
            elif bid == "q_tab_d" and scope_key != "daily":
                self.state = self.QUESTS_DAILY
            elif bid == "q_tab_w" and scope_key != "weekly":
                self.state = self.QUESTS_WEEKLY
            elif bid in ("q_bonus", "q_bonus_go"):
                rw = self.quests.claim_bonus(scope_key)
                if rw:
                    self._apply_rewards(rw, "BONUS")
                else:
                    self.show_message("Bonus noch nicht verfuegbar")
            elif bid.startswith("q_claim_"):
                # PAKET 8.7 FIX: Off-by-One (bid[7:] lieferte "_id" statt
                # "id") - genau deshalb liess sich KEINE Daily-Quest
                # abholen. Korrekt: Praefix "q_claim_" hat 8 Zeichen.
                rw = self.quests.claim(scope_key, bid[len("q_claim_"):])
                if rw:
                    self._apply_rewards(rw, "QUEST")
                else:
                    self.show_message("Belohnung nicht verfuegbar")
            elif bid.startswith("qcard_"):
                # PAKET 8.7 MOBILE: Tipp auf die GANZE Karte holt ab
                rw = self.quests.claim(scope_key, bid[len("qcard_"):])
                if rw:
                    self._apply_rewards(rw, "QUEST")
                else:
                    self.show_message("Belohnung nicht verfuegbar")
            return

        # ---------------- PAKET 8: BESCHWOERUNG ----------------
        if st == self.SUMMON:
            if bid == "sm_back":
                self.state = self.MENU
            elif bid == "sm_tab_sum":
                self._summon_tab = "summon"
            elif bid == "sm_tab_col":
                self._summon_tab = "collection"
            elif bid in ("sm_pull1", "sm_pull10"):
                self._do_summon("single" if bid == "sm_pull1" else "multi")
            elif bid == "sm_close":
                self._summon_result = None
            return

        if st == self.RESEARCH:
            if bid == "res_back":
                self.state = self.MENU
            elif bid == "res_ship":
                # PAKET 7E: das Schiff SELBST aufwerten (Stufe 1-12)
                self._buy_ship()
            elif bid == "res_upgrade":
                # PAKET 7B: echtes Upgrade des gewaehlten Moduls
                if self.sel_module:
                    self._buy_module(self.sel_module)
            elif bid.startswith("mod_"):
                # PAKET 7B: Chip-Leiste (Alternative zur Direktwahl am Schiff)
                if self.sel_module != bid[4:]:
                    SFX.play("click", 0.4)
                self.sel_module = bid[4:]
            elif bid.startswith("res_"):
                self._buy_module(bid[4:])
            return

        if st == self.STAGES:
            if bid == "stg_back":
                self.state = self.MENU
                self._map_deselect()
                self.selected_sector = 0
            elif bid == "stg_close":
                self.selected_sector = 0
            elif bid == "map_close":
                # PAKET 7F: Szene schliessen spielt den Zoom zurueck zur Karte
                if self.map_scene.active:
                    self.map_scene.close()
                else:
                    self._map_deselect()
            elif bid == "scene_close":
                self.map_scene.close()
            elif bid == "scene_second":
                # PAKET 7F: vorhandenes Stufen-Sheet ueber der Szene oeffnen
                oid = self.map_sel
                if oid and oid.startswith("sector_"):
                    sec = int(oid.split("_")[1])
                    if sec <= self.modules.highest_campaign:
                        self.selected_sector = sec
            elif bid == "scene_primary":
                # PAKET 7F: Kampfstart ueber den BEKANNTEN Pfad (_map_action)
                self._map_action()
            elif bid == "map_second":
                oid = self.map_sel
                if oid and oid.startswith("sector_"):
                    sec = int(oid.split("_")[1])
                    if sec <= self.modules.highest_campaign:
                        self._map_deselect()
                        self.selected_sector = sec
            elif bid == "map_primary":
                self._map_action()
            elif bid.startswith("stage_"):
                self._try_enter_stage(int(bid[6:]))
            return

        if st == self.SKILLTREE:
            if bid == "nex_back":
                self.state = self.MENU
            elif bid == "nex_train":
                self._skill_train()
            elif bid == "nex_close":
                self.nexus.select(None)
            return

        if st == self.SETTINGS:
            if bid == "set_back":
                self.state = self.settings_return_state
            elif bid == "set_sound":
                self._toggle_sound()
            elif bid == "set_full":
                self._toggle_fullscreen()
            elif bid == "set_debug":
                self.debug_mode = not self.debug_mode
                self.show_message(f"DEBUG MODUS: {'AN' if self.debug_mode else 'AUS'}")
            return

        if st == self.PLAYING:
            if self.show_upgrades:
                if bid == "upg_close":
                    self.show_upgrades = False
                elif bid.startswith("upg_"):
                    self._buy_module(bid[4:])
                return
            if bid == "hud_pause":
                self.state = self.PAUSED
            elif bid == "hud_sound":
                self._toggle_sound()
            elif bid == "hud_upgrades":
                self.show_upgrades = True
            elif bid == "hud_overdrive":
                self._overdrive()
            elif bid.startswith("hud_champ"):      # AUFTRAG 8
                try:
                    self._champ_skill(int(bid[len("hud_champ"):]))
                except ValueError:
                    return
            return

        if st == self.PAUSED:
            if bid == "pau_resume":
                self.state = self.PLAYING
            elif bid == "pau_settings":
                self.settings_return_state = self.PAUSED
                self.state = self.SETTINGS
            elif bid == "pau_sound":
                self._toggle_sound()
            elif bid == "pau_giveup":
                self._collect_idle_loot()
                self.state = self.MENU
            return

        if st == self.DEFEAT:
            # PAKET 8.7: Skip waehrend des Videos.
            # PAKET 8.8a: danach keine Buttons mehr - TAP irgendwo =
            # Stufe neu starten (zum Hauptmenue: im Gefecht Pause ->
            # "ZUM HAUPTMENÜ").
            if bid == "def_skip":
                if self.defeat_frames:
                    self.defeat_timer = len(self.defeat_frames) / 30.0
            elif bid == "def_tap":
                self._restart_stage()
            return

        if st in (self.STAGE_CLEAR, self.VICTORY):   # AUFTRAG 6: gleiche Buttons
            if bid == "vic_skip":
                if self.victory_frames:
                    self.victory_timer = len(self.victory_frames) / 30.0
            elif bid == "vic_continue":
                SFX.stop_music()
                campaign = self.selected_sector if self.selected_sector > 0 else self.pve.campaign_id
                self.state = self.STAGES
                self._map_deselect()
                self.selected_sector = 0
                repeat = (campaign, 1) in self.modules.completed_stages   # PAKET 7C
                self.pve = PvECombat(is_idle=False, campaign_id=campaign, stage_id=1,
                                     ship_level=self.modules.ship_level, is_repeat=repeat,
                                     ng_plus=int(getattr(self.modules, "ng_plus", 0)))
                self.victory_timer = 0.0
            return

    def _buy_module(self, key):
        old_level = self.modules.get(key).level
        try:
            self.modules.upgrade(key)
            self._sync_modules_to_combat()
            SFX.play("upgrade")
            self._start_upgrade_fx(key, old_level + 1)   # PAKET 7C: Feedback
            self.quests.record("module_upgrades", 1)     # PAKET 8: Quest-Fortschritt
        except ValueError as e:
            self.show_message(str(e))

    def _buy_ship(self):
        """PAKET 7E: Das Schiff SELBST aufwerten (Schiffs-Rumpf, Stufe 1-12).
        Echte Wirkung (+80 Huelle, +3% Schaden je Stufe) + neues Schiffsbild
        (fortress/ship_lvl_<Stufe>.png) + Upgrade-Animation am Schiff."""
        try:
            price = self.modules.upgrade_ship()
        except ValueError as e:
            self.show_message(str(e))
            return
        new_lvl = self.modules.ship_hull_level
        self._sync_modules_to_combat()
        # Bild + Caches: neues Schiff sofort ueberall sichtbar
        self.fortress.set_level(new_lvl)
        self._fit_cache.clear()
        _ship_scaled.clear()
        SFX.play("upgrade")
        stage = self._werft_stage
        if stage is not None:
            ship = self._werft_ship_rect(stage)
            self.upgrade_fx.start("ship", new_lvl, ship.centerx, ship.centery,
                                  ICE, rect=ship)
        self.show_message(f"SCHIFF AUFGEWERTET: STUFE {new_lvl}/12 "
                          f"({price} Cr - +80 Hülle, +3% Schaden)")

    def _start_upgrade_fx(self, key, new_level):
        """PAKET 7C: Upgrade-Animation starten (Werft: am Schiff-Hotspot,
        Gefecht-Sheet: auf der Modul-Karte)."""
        try:
            col = self.HOTSPOT_COL.get(key, CYAN)
            if self.state == self.RESEARCH and self._werft_stage:
                hs = self._werft_hotspots().get(key)
                if hs:
                    self.upgrade_fx.start(key, new_level, hs[0], hs[1], col,
                                          rect=self._werft_ship_rect(self._werft_stage))
                    return
            if self.state == self.PLAYING and self.show_upgrades:
                b = self._ui.get("upg_" + key)
                if b is not None:
                    self.upgrade_fx.start(key, new_level, b.rect.centerx,
                                          b.rect.centery, col, rect=b.rect)
                    return
            # Fallback: Schiffsposition in der Arena
            combat = self.idle_combat if self.idle_mode else self.pve
            s, ox, oy, _aw, _ah = self._view()
            sx, sy = self.movement.get_position(self.fortress.x, self.fortress.y)
            self.upgrade_fx.start(key, new_level, ox + sx * s, oy + sy * s, col)
        except Exception as e:
            # Nur Optik-Animation: Schlaegt sie fehl, laeuft das Gefecht
            # unveraendert weiter - der Fehler wird jetzt aber sichtbar.
            _log.warning("Upgrade-Animation fehlgeschlagen (%s): %s", key, e)

    def _try_enter_stage(self, stage):
        sector = self.selected_sector
        unlocked = (sector < self.modules.highest_campaign or
                    (sector == self.modules.highest_campaign and stage <= self.modules.highest_stage))
        if unlocked:
            self._collect_idle_loot()
            self.idle_mode = False
            self.map_scene.abort()   # PAKET 7F: Szene schliesst beim Einsatz
            # PAKET 7C: Wiederholung einer bereits geschafften Stufe?
            repeat = (sector, stage) in self.modules.completed_stages
            self.pve = PvECombat(is_idle=False, campaign_id=sector, stage_id=stage,
                                 ship_level=self.modules.ship_level, is_repeat=repeat)
            self._sync_modules_to_combat()
            self.quests.begin_mission()   # PAKET 8: Mission startet 'clean'
            self.state = self.PLAYING
        else:
            self.show_message(f"Stufe {stage} ist gesperrt! Schaffe erst fruehere Stufen.")

    # ---------------- PAKET 7A: Galaxiekarten-Logik ----------------
    def _map_select(self, oid):
        """Kartenobjekt auswaehlen.
        AUFTRAG 17: ZWEI-KLICK-PRINZIP.
          1. Klick  : Planet wird hervorgehoben (Highlight + Info-Panel) -
                      KEIN Zoom. Noch ein Klick woanders waehlt um.
          2. Klick  : Zoom auf den Planeten + grosses Detail (PAKET-7F-
                      Szene). Rueckkehr zur normalen Karte wie bisher ueber
                      den Schliessen-Button der Szene (bzw. Android-Zurueck).
        Bestehende Funktionen (Panel-Aktionen, Feindsignale, Start) bleiben
        unveraendert - sie wirken auf die SELEKTION, nicht auf den Zoom."""
        if oid != self.map_sel:
            SFX.play("click", 0.4)
            self.map_sel = oid
            self.gmap.select(oid)
            return                       # 1. Klick: nur hervorheben
        obj = world_map.BY_ID.get(oid)
        if obj and not self.map_scene.active:
            SFX.play("click", 0.4)
            self.map_scene.open(oid, obj["uv"])   # 2. Klick: Zoom + Detail

    def _map_deselect(self):
        if self.map_sel:
            self.map_sel = None
            self.gmap.select(None)
        if self.map_scene.active:
            self.map_scene.abort()

    def _map_action(self):
        """Primaer-Aktion des gewaehlten Kartenobjekts.
        PAKET 7D: Die Karte ist Kampagne - nur noch Missionsstarts
        (Sektor, Feindsignale) und der Boss-Kampf. Menues (Werft, Nexus,
        Idle) erreicht man ueber die Befehlsleiste, nicht ueber die Karte."""
        oid = self.map_sel
        if not oid:
            return
        mods = self.modules
        if oid.startswith("sector_"):
            sec = int(oid.split("_")[1])
            if sec > mods.highest_campaign:
                return
            self.selected_sector = sec
            stage = mods.highest_stage if sec == mods.highest_campaign else 15
            self._try_enter_stage(stage)
        elif oid == "signal_a":
            # FEINDSIGNALE: Feindverband im aktiven Sektor - naechster Einsatz
            self.selected_sector = mods.highest_campaign
            self._try_enter_stage(mods.highest_stage)
        elif oid == "signal_b":
            if mods.highest_stage >= 15:
                self.selected_sector = mods.highest_campaign
                self._try_enter_stage(15)
            else:
                return
        self._map_deselect()

    def _map_states(self):
        """Status aller Kartenobjekte (Daten: module_system - unveraendert)."""
        mods = self.modules
        states = {}
        for sec in (1, 2, 3, 4, 5):
            done = sum(1 for (c, _s) in mods.completed_stages if c == sec)
            if sec in mods.completed_campaigns:
                status, scol, col = "ABGESCHLOSSEN", GREEN, GREEN
            elif sec == mods.highest_campaign:
                status, scol, col = "AKTIV", CYAN, CYAN
            elif sec < mods.highest_campaign:
                status, scol, col = "FREIGEGEBEN", GREEN, GREEN
            else:
                status, scol, col = "GESPERRT", MUTED, MUTED
            states[f"sector_{sec}"] = {
                "name": SECTOR_DATA[sec]["name"], "status": status,
                "status_col": scol, "col": col,
                "pulse": sec == mods.highest_campaign,
                "progress": done / 15.0,
            }
        states["signal_a"] = {
            # PAKET 7D: Feindsignale = aktiver Feindverband im Kampagnen-Sektor
            "name": "FEINDSIGNALE",
            "status": f"VERBAND IM SEKTOR {mods.highest_campaign}",
            "status_col": GREEN, "col": GREEN, "pulse": True,
            "lines": [f"Naechster Einsatz: Sektor {mods.highest_campaign} \u00b7 "
                      f"Stufe {mods.highest_stage}"]}
        boss_ready = mods.highest_stage >= 15
        states["signal_b"] = {"name": "BOSS-SIGNAL",
                              "status": "BOSS BEREIT" if boss_ready else "GESPERRT",
                              "status_col": AMBER if boss_ready else MUTED,
                              "col": AMBER if boss_ready else MUTED,
                              "pulse": boss_ready,
                              "lines": [] if boss_ready else
                              [f"Erreiche Stufe 15 in Sektor {mods.highest_campaign}"]}
        return states

    def _map_panel_info(self):
        """Panel-Inhalt fuer das gewaehlte Kartenobjekt (oder None).
        PAKET 7F: liefert zusaetzlich tag/story/battles fuer das
        Szenen-Panel (VERFUEGBARE KAEMPFE)."""
        oid = self.map_sel
        if not oid or oid not in world_map.BY_ID or self.selected_sector > 0:
            return None
        mods = self.modules
        st = self._map_states()[oid]
        loc = map_locations.LOCATIONS.get(oid, {})
        info = {"title": st["name"], "accent": st.get("col", CYAN),
                "status": st["status"], "status_col": st.get("status_col", WHITE),
                "progress": st.get("progress"), "lines": list(st.get("lines", [])),
                "primary": None, "second": None, "progress_text": None,
                "tag": loc.get("kind", ""), "story": "", "battles": []}
        if oid.startswith("sector_"):
            sec = int(oid.split("_")[1])
            done = int(round((st.get("progress") or 0.0) * 15))
            info["progress_text"] = f"{done}/15 STUFEN"
            # PAKET 7D: Story-Zeile des Sektors (Kampagnen-Bezug)
            story = SECTOR_DATA[sec].get("story", "")
            info["story"] = story
            if sec > mods.highest_campaign:
                info["lines"] = [f"Voraussetzung: Sektor {sec - 1} vollstaendig abschliessen"]
                info["battles"] = [{"label": f"SEKTOR {sec - 1} ABSCHLIESSEN",
                                    "note": "GESPERRT", "col": MUTED}]
            else:
                stage = mods.highest_stage if sec == mods.highest_campaign else 15
                info["primary"] = ("KAMPF STARTEN", st.get("col", CYAN), True)
                info["second"] = ("STUFEN", VIOLET, True)
                info["lines"] = [f"Naechster Einsatz: Stufe {stage}"]
                # PAKET 7F: verfuegbare Kaempfe (Kampagnensystem unveraendert)
                battles = [{"label": f"STUFE {stage}", "note": "N\u00c4CHSTER EINSATZ",
                            "col": CYAN}]
                if sec in mods.completed_campaigns:
                    battles = [{"label": "ALLE STUFEN 1-15",
                                "note": "WIEDERHOLBAR", "col": GREEN}]
                else:
                    for stg in (5, 10):
                        if (sec, stg) in mods.completed_stages:
                            battles.append({"label": f"ELITE \u00b7 STUFE {stg}",
                                            "note": "GESCHAFFT", "col": GREEN})
                        elif stg <= mods.highest_stage:
                            battles.append({"label": f"ELITE \u00b7 STUFE {stg}",
                                            "note": "OFFEN", "col": MAGENTA})
                    if mods.highest_stage >= 15:
                        battles.append({"label": "BOSS \u00b7 STUFE 15",
                                        "note": "BEREIT", "col": AMBER})
                info["battles"] = battles[:4]
        elif oid == "signal_a":
            info["primary"] = ("EINSATZ STARTEN", GREEN, True)
            info["story"] = ("Feindlicher Verband im Anmarsch - abfangen, "
                             "bevor er den Sektor erreicht.")
            info["lines"] = [f"Naechster Einsatz: Sektor {mods.highest_campaign} \u00b7 "
                             f"Stufe {mods.highest_stage}",
                             "Feindlicher Verband im Anmarsch - abfangen!"]
            info["battles"] = [{"label": f"SEKTOR {mods.highest_campaign} \u00b7 "
                                         f"STUFE {mods.highest_stage}",
                                "note": "ABFANGEN", "col": GREEN}]
        elif oid == "signal_b":
            if mods.highest_stage >= 15:
                info["primary"] = ("BOSS-ANGRIFF", AMBER, True)
                info["story"] = "Das Flaggschiff des Sektors wartet."
                info["lines"] = [f"Sektor {mods.highest_campaign} \u00b7 Stufe 15",
                                 "Das Flaggschiff des Sektors wartet."]
                info["battles"] = [{"label": "BOSS \u00b7 STUFE 15",
                                    "note": "FLAGSCHIFF", "col": AMBER}]
            else:
                info["story"] = "Ein gewaltiges Signal laeuert im Nebel."
                info["lines"] = [f"Erreiche Stufe 15 in Sektor {mods.highest_campaign}"]
                info["battles"] = [{"label": "BOSS \u00b7 STUFE 15",
                                    "note": "GESPERRT", "col": MUTED}]
        return info

    def _toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
            self.show_message("VOLLBILD umgeschaltet")
        except Exception as e:
            self.show_message(f"Vollbild nicht moeglich: {e}")

    # ---------------- Layouts (einzige Quelle fuer Rects) ----------------
    def _layout_menu(self):
        """PAKET 8.1: kompakte Navigationsleiste - 9 feste Buttons (~65x34,
        Gruppe ~55-65 % der Breite, zentriert, gleichmassige Abstaende).
        Bei schmalen Screens Scroll-Overflow mit Pfeilen. Alle bisherigen
        Button-IDs/Handler bleiben unveraendert; kurze Beschriftungen."""
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        isz = icon_touch()
        ui["snd_menu"] = Btn("snd_menu", pygame.Rect(W - u(8) - isz, u(8), isz, isz),
                             icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        items = [
            ("btn_idle", "IDLE", "play", CYAN),
            ("btn_research", "WERFT", "flask", MAGENTA),
            ("btn_skills", "NEXUS", "hex", AMBER),
            ("btn_stages", "GALAXIE", "map", GREEN),
            ("btn_daily", "DAILY", "list", ICE),
            ("btn_weekly", "WEEKLY", "calendar", VIOLET),
            ("btn_summon", "SUMMON", "star", MAGENTA),
            ("btn_settings", "SYSTEM", "gear", VIOLET),
            ("btn_quit", "ENDE", "power", RED),
        ]
        bar, btns = ui_kit.mini_bar_layout(items)
        self._menu_bar_rect = bar
        # PAKET 8.1: EINE Font fuer alle Beschriftungen (einheitliche
        # Schriftgroesse), laengstes Label ("GALAXIE") bestimmt die Groesse
        self._nav_font = ui_kit.nav_label_font()
        # PAKET 8.1: aktiver Menuepunkt (zuletzt gewaehlter Bereich)
        nav_active = getattr(self, "_nav_active", None)
        for b in btns:
            b.active = (b.id == nav_active)
        # PAKET 8: Overflow ermitteln (Mindestbreite der Buttons erreicht?)
        content_right = btns[-1].rect.right + u(6)
        self._menu_overflow = content_right > W
        self._menu_max_scroll = max(0, content_right - W + u(6))
        self._menu_scroll = max(0.0, min(self._menu_scroll, self._menu_max_scroll))
        if self._menu_overflow:
            off = int(self._menu_scroll)
            for b in btns:
                b.rect.x -= off
            aw = u(24)
            # Pfeile zuerst einsetzen (Hit-Test hat Vorrang am Rand)
            ui["menu_left"] = Btn("menu_left", pygame.Rect(0, bar.y + u(5), aw, bar.h - u(10)),
                                  icon="back", accent=CYAN,
                                  enabled=self._menu_scroll > 0.5)
            ui["menu_right"] = Btn("menu_right", pygame.Rect(W - aw, bar.y + u(5), aw, bar.h - u(10)),
                                   icon="forward", accent=CYAN,
                                   enabled=self._menu_scroll < self._menu_max_scroll - 0.5)
        for b in btns:
            ui[b.id] = b
        return ui

    def _layout_hud(self):
        """PAKET 7A: schmale Aktionsleiste unten - die Spielwelt bleibt frei."""
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        bar = action_bar_rect()
        self._hud_bar_rect = bar
        isz = icon_touch()
        x = u(8)
        ui["hud_pause"] = Btn("hud_pause", pygame.Rect(x, bar.y + (bar.h - isz) // 2,
                                                       isz, isz), icon="pause", accent=CYAN)
        x += isz + u(6)
        ui["hud_sound"] = Btn("hud_sound", pygame.Rect(x, bar.y + (bar.h - isz) // 2,
                                                       isz, isz),
                              icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        x += isz + u(6)                      # AUFTRAG 8: Platz fuer Champion-Buttons
        od_learned = self.skills.level_of("spez_overdrive") > 0
        show_od = (not self.idle_mode) and od_learned
        bw_up = min(u(160), int(W * 0.32))
        bw_od = min(u(150), int(W * 0.30))   # AUFTRAG 8: vorab fuer Platz-Check
        yb = bar.y + u(6)
        bh = bar.h - u(12)
        ui["hud_upgrades"] = Btn("hud_upgrades",
                                 pygame.Rect(W - u(8) - bw_up, yb, bw_up, bh),
                                 "UPGRADES", "Module ausbauen", MAGENTA, icon="flask")
        if show_od:
            cd = float(getattr(self.pve, "overdrive_cd", 0.0) or 0.0)
            ui["hud_overdrive"] = Btn("hud_overdrive",
                                      pygame.Rect(W - u(8) - bw_up - u(8) - bw_od, yb,
                                                  bw_od, bh),
                                      "ÜBERTAKTUNG",
                                      "BEREIT · 8s x2" if cd <= 0 else f"ABKLINGZEIT {int(cd)}s",
                                      VIOLET, enabled=(cd <= 0), icon="bolt")
        # AUFTRAG 8: CHAMPION-SKILL-BUTTONS (max. CHAMPION_HUD_BUTTONS).
        # Nur im aktiven Gefecht mit ausgeruesteten Helden - sonst bleibt
        # die Leiste exakt wie bisher. Platz-Kontrolle: sie stehen links in
        # der Leiste und ueberlappen die rechte Button-Gruppe nicht.
        if not self.idle_mode:
            grenze = W - u(8) - bw_up - u(8)
            if show_od:
                grenze -= bw_od + u(8)
            _kurz = {"nova": "NOVA", "lyra": "LYRA", "ingenieur": "ING."}
            for ci, sk in enumerate(getattr(self.pve, "champ_skills", [])
                                    [:rpg_config.CHAMPION_HUD_BUTTONS]):
                bw_c = min(u(64), int(W * 0.17))
                if x + bw_c + u(6) > grenze:
                    break                    # kein Platz mehr - weniger Buttons
                cds = getattr(self.pve, "champ_cd", [])
                cd0 = float(cds[ci]) if ci < len(cds) else 0.0
                ui[f"hud_champ{ci}"] = Btn(
                    f"hud_champ{ci}",
                    pygame.Rect(x, bar.y + (bar.h - isz) // 2, bw_c, isz),
                    _kurz.get(sk.get("key"), sk.get("hero", "?")[:5]),
                    sk.get("name", ""), AMBER, enabled=(cd0 <= 0))
                x += bw_c + u(6)
        return ui

    def _layout_upgrades(self):
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        landscape = W > H
        if landscape:
            sh = int(H * 0.74)
            sw = min(W - u(16), u(860))
            rect = pygame.Rect((W - sw) // 2, H - sh - u(8), sw, sh)
            cols, rows = 4, 2            # PAKET 7B: 8 Zellen fuer 7 Module
        else:
            sh = int(H * 0.62)
            rect = pygame.Rect(u(8), H - sh - u(8), W - u(16), sh)
            cols, rows = 2, 4            # PAKET 7B: 8 Zellen fuer 7 Module
        cs = u(40)
        ui["upg_close"] = Btn("upg_close", pygame.Rect(rect.right - u(40) - u(10), rect.y + u(8),
                                                       u(40), u(40)),
                              icon="close", accent=RED)
        keys = list(self.modules.modules.keys())
        gap = u(10)
        head = u(48)
        cw = (rect.w - u(24) - gap * (cols - 1)) // cols
        ch = (rect.h - head - u(16) - gap * (rows - 1)) // rows
        for i, key in enumerate(keys):
            r = pygame.Rect(rect.x + u(12) + (i % cols) * (cw + gap),
                            rect.y + head + (i // cols) * (ch + gap), cw, ch)
            ui["upg_" + key] = Btn("upg_" + key, r, accent=CYAN)
        return ui, rect

    def _layout_research(self):
        """PAKET 7B: WERFT - Schiff links, Modul-Chips unten, Detail-Panel
        rechts. Layout ist die einzige Quelle fuer Rects."""
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = icon_touch()
        ui["res_back"] = Btn("res_back", pygame.Rect(m, m, isz, isz), icon="back", accent=CYAN)
        ui["snd_res"] = Btn("snd_res", pygame.Rect(W - m - isz, m, isz, isz),
                            icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        top = m + isz + u(16)
        stage = pygame.Rect(m, top, int(W * 0.54) - m, H - top - m)
        self._werft_stage = stage
        panel = pygame.Rect(stage.right + u(12), top,
                            max(u(240), W - m - stage.right - u(12)), H - top - m)
        self._werft_panel = panel
        bh = btn_h()
        ui["res_upgrade"] = Btn("res_upgrade",
                                pygame.Rect(panel.x + u(14), panel.bottom - bh - u(14),
                                            panel.w - u(28), bh),
                                "UPGRADE", "", GREEN)
        keys = list(self.modules.modules.keys())
        ch_h = u(34)
        chip_y = stage.bottom - ch_h - u(6)
        # PAKET 7E: Schiffs-Upgrade-Button (das Schiff SELBST) ueber der
        # Chip-Leiste - prominent auf der Buehne, immer sichtbar.
        ship_h = u(40)
        ship_btn = pygame.Rect(stage.x + u(6), chip_y - u(8) - ship_h,
                               stage.w - u(12), ship_h)
        ui["res_ship"] = Btn("res_ship", ship_btn, "SCHIFF AUFWERTEN", "", ICE)
        cw = (stage.w - u(6) * (len(keys) - 1)) // len(keys)
        short = self.MOD_SHORT
        for i, key in enumerate(keys):
            mod = self.modules.get(key)
            r = pygame.Rect(stage.x + i * (cw + u(6)), chip_y, cw, ch_h)
            ui["mod_" + key] = Btn("mod_" + key, r, short.get(key, mod.name)[:9],
                                   f"LVL {mod.level}", CYAN,
                                   active=(self.sel_module == key))
        return ui

    # ---------------- PAKET 7B: Werft - Schiff als interaktives Objekt ----------------
    # Modul-Hotspots als UV relativ zur Schiffsbild-Box. Zeichnung und
    # Hit-Test nutzen DIESELBE Quelle (_werft_hotspots).
    SHIP_HOTSPOTS = {
        "radar": (0.90, 0.42),
        "kanonen": (0.50, 0.16),
        "reaktor": (0.62, 0.60),
        "antrieb": (0.04, 0.32),
        "schild": (0.20, 0.68),
        "huelle": (0.34, 0.40),      # PAKET 7C: Schiffshuelle (Rumpf-Mitte)
        "hangar": (0.44, 0.86),
        "reparatur": (0.06, 0.89),
    }
    HOTSPOT_COL = {
        "kanonen": MAGENTA, "schild": CYAN, "huelle": ICE,
        "reaktor": VIOLET, "antrieb": AMBER, "hangar": GREEN,
        "radar": (168, 196, 232), "reparatur": WHITE,
    }
    MOD_SHORT = {"kanonen": "Waffen", "schild": "Schild", "huelle": "Hülle",
                 "reaktor": "Reaktor", "antrieb": "Antrieb", "hangar": "Hangar",
                 "radar": "Radar", "reparatur": "Reparatur"}

    def _werft_ship_rect(self, stage):
        """Box des Schiffsbildes in der Buehne (gecacht pro Groesse)."""
        base = getattr(self.fortress, "_base_image", None)
        iw, ih = base.get_size() if base is not None else (160, 80)
        key = ("werftrect", stage.w, stage.h, iw, ih)
        r = self._fit_cache.get(key)
        if r is None:
            tw = int(stage.w * 0.84)
            th = int(ih * tw / iw)
            maxh = int(stage.h * 0.70)
            if th > maxh:
                th = maxh
                tw = int(iw * th / ih)
            r = pygame.Rect(0, 0, tw, th)
            r.center = stage.center
            r.centery = stage.centery - u(8)
            self._fit_cache[key] = r
        return r

    def _werft_hotspots(self):
        """Screen-Positionen der Modul-Hotspots (EINZIGE Quelle fuer Zeichnen
        und Hit-Test - wie bei der Galaxiekarte)."""
        stage = self._werft_stage
        ship = self._werft_ship_rect(stage)
        return {key: (ship.x + int(ux * ship.w), ship.y + int(uy * ship.h))
                for key, (ux, uy) in self.SHIP_HOTSPOTS.items()}

    def _werft_hit(self, pos):
        """Modul unter dem Finger (Kreis-Hit) oder None. Radius adaptiv:
        skaliert mit dem Schiff, damit die Touch-Kreise auch auf kleinen
        Aufloesungen nicht ueberlappen (bei Mehrfach-Treffer zaehlt der
        naechstgelegene Hotspot)."""
        ship = self._werft_ship_rect(self._werft_stage)
        rad = min(u(30), max(14, int(ship.w * 0.07)))
        best, bd = None, 1e18
        for key, (x, y) in self._werft_hotspots().items():
            d = (pos[0] - x) ** 2 + (pos[1] - y) ** 2
            if d <= rad * rad and d < bd:
                best, bd = key, d
        return best

    def _layout_stages(self):
        """PAKET 7A: Karte liefert Objekt-Hits selbst; hier nur Header-Icons,
        Panel-Buttons (Rechtecke aus world_map) und das Stufen-Sheet."""
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        isz = icon_touch()
        ui["stg_back"] = Btn("stg_back", pygame.Rect(margin(), margin(), isz, isz),
                             icon="back", accent=CYAN)
        ui["snd_stg"] = Btn("snd_stg", pygame.Rect(W - margin() - isz, margin(), isz, isz),
                            icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        if self.selected_sector > 0:
            landscape = W > H
            if landscape:
                sw, sh = min(W - u(20), u(880)), int(H * 0.78)
                rect = pygame.Rect((W - sw) // 2, int(H * 0.14), sw, sh)
                cols, rows = 5, 3
            else:
                rect = pygame.Rect(u(8), int(H * 0.16), W - u(16), int(H * 0.78))
                cols, rows = 3, 5
            head = u(46)
            ui["stg_close"] = Btn("stg_close",
                                  pygame.Rect(rect.right - u(40) - u(10), rect.y + u(8),
                                              u(40), u(40)),
                                  icon="close", accent=RED)
            gap = u(8)
            cw = (rect.w - u(24) - gap * (cols - 1)) // cols
            ch = (rect.h - head - u(14) - gap * (rows - 1)) // rows
            for i in range(15):
                stage = i + 1
                rr = pygame.Rect(rect.x + u(12) + (i % cols) * (cw + gap),
                                 rect.y + head + (i // cols) * (ch + gap), cw, ch)
                ui[f"stage_{stage}"] = Btn(f"stage_{stage}", rr, accent=VIOLET)
            self._stage_sheet_rect = rect
        else:
            # PAKET 7F: im Szenen-Modus die Szenen-Buttons, sonst die
            # Karten-Panel-Buttons (werden von world_map gezeichnet)
            src = (self.map_scene.button_rects() if self.map_scene.active
                   else self.gmap.button_rects())
            for rid, rr in src.items():
                ui[rid] = Btn(rid, rr, accent=CYAN)
        return ui

    def _nex_area(self):
        """Bereich des Nexus-Netzwerks (unter Header, ohne Sheet-Zone im Portrait)."""
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        isz = icon_touch()
        top = m + isz + u(12)
        if W > H:
            bottom = H - u(12)          # Landscape: volle Hoehe, Sheet rechts
        else:
            bottom = H - int(H * 0.24) - u(14)
        return top, bottom

    def _layout_skilltree(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = icon_touch()
        ui["nex_back"] = Btn("nex_back", pygame.Rect(m, m, isz, isz), icon="back", accent=AMBER)
        top, bottom = self._nex_area()
        for nid, rect in self.nexus.hitmap.items():
            ui["node_" + nid] = Btn("node_" + nid, rect, accent=AMBER)
        if self.nexus.selected:
            if self.nexus.train_rect:
                ui["nex_train"] = Btn("nex_train", self.nexus.train_rect, accent=AMBER)
            if self.nexus.close_rect:
                ui["nex_close"] = Btn("nex_close", self.nexus.close_rect, accent=MUTED)
        return ui

    def _layout_settings(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = icon_touch()
        ui["set_back"] = Btn("set_back", pygame.Rect(m, m, isz, isz), icon="back", accent=VIOLET)
        bh = int(btn_h() * 1.15)
        y = m + isz + u(40)
        rows = [("set_sound", "SOUND", "Effekte & Sieg-Musik")]
        if not IS_ANDROID:
            rows.append(("set_full", "VOLLBILD", "Fenster / Vollbild umschalten"))
        rows.append(("set_debug", "DEBUG MODUS", "Entwicklerwerkzeuge (Desktop)"))
        rw = min(W - 2 * m, u(560))
        rx = (W - rw) // 2
        for bid, lab, sub in rows:
            ui[bid] = Btn(bid, pygame.Rect(rx, y, rw, bh), lab, sub, VIOLET)
            y += bh + u(12)
        self._settings_rows_end = y
        return ui

    def _layout_pause(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        pw = min(W - 2 * m, u(430))
        bh = btn_h()
        gap = u(12)
        head = u(56)
        ph = head + 4 * bh + 5 * gap
        px, py = (W - pw) // 2, (H - ph) // 2
        labels = [
            ("pau_resume", "FORTSETZEN", "", GREEN),
            ("pau_settings", "EINSTELLUNGEN", "", VIOLET),
            ("pau_sound", "SOUND: " + ("AUS" if SFX.muted else "AN"), "", CYAN),
            ("pau_giveup", "ZUM HAUPTMENÜ" if self.idle_mode else "AUFGEBEN", "", RED),
        ]
        for i, (bid, lab, sub, acc) in enumerate(labels):
            ui[bid] = Btn(bid, pygame.Rect(px + u(20), py + head + i * (bh + gap), pw - u(40), bh),
                          lab, sub, acc)
        self._pause_rect = pygame.Rect(px, py, pw, ph)
        return ui

    def _layout_defeat(self):
        """PAKET 8.7: Waehrend des Videos ist der ganze Screen der
        unsichtbare Skip.
        PAKET 8.8a (Nutzerwunsch "die zusaetzlichen Buttons weg"):
        Nach dem Video KEINE Buttons mehr - ein TAP irgendwo startet die
        Stufe neu.
        PAKET 8.8b: Der End-VORHANG ist wieder hoeher (u(124) statt
        u(96)) und mit Verlaufskante - die in die Defeat-Animation
        eingebrannten {R}-NEUSTART/HAUPTMENUE-Buttons guckten oben wieder
        heraus (Nutzer: "Es kommt wieder ein pop up"). Zusätzlich wird
        das Video per cover-fit auf den ganzen Screen skaliert, sodass
        die eingebrannten Buttons IMMER am unteren Rand liegen."""
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        if self.defeat_frames and self.defeat_timer < len(self.defeat_frames) / 30.0:
            ui["def_skip"] = Btn("def_skip", pygame.Rect(0, 0, W, H))
            return ui
        ended = not self.defeat_frames or \
            self.defeat_timer >= len(self.defeat_frames) / 30.0
        if ended:
            self._defeat_card_rect = pygame.Rect(0, H - u(124), W, u(124))
            # Kompletter Screen = unsichtbare Tap-Zone (Neustart)
            ui["def_tap"] = Btn("def_tap", pygame.Rect(0, 0, W, H))
        return ui

    def _layout_clear(self):
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        ended = (not self.victory_frames) or self.victory_timer >= len(self.victory_frames) / 30.0
        if not ended:
            ui["vic_skip"] = Btn("vic_skip", pygame.Rect(0, 0, W, H))
            return ui
        bw = int(W * 0.62)
        bh = int(btn_h() * 1.25)
        ui["vic_continue"] = Btn("vic_continue",
                                 pygame.Rect((W - bw) // 2, int(H * 0.66), bw, bh),
                                 "WEITER", "", CYAN)
        return ui

    def _layout_intro(self):
        W, H = ui_kit.W, ui_kit.H
        return {"intro_skip": Btn("intro_skip", pygame.Rect(0, 0, W, H))}

    def _pressed(self, bid):
        return bool(self._ptr and self._ptr["id"] == bid)

    # ---------------- Zeichnen ----------------
    def _draw_menu_backdrop(self):
        W, H = ui_kit.W, ui_kit.H
        SCREEN.fill(VOID)
        if self.menu_bg is not None:
            img = self._fit_surf(self.menu_bg, "menu_bg", brighten=14)   # 7C: heller
            SCREEN.blit(img, ((W - img.get_width()) // 2, (H - img.get_height()) // 2))
            overlay(SCREEN, 96)   # PAKET 7C: 140 -> 96, Hintergrund lesbarer
        else:
            grid_bg(SCREEN, self.elapsed)
            overlay(SCREEN, 40)
        # Driftende Staub-Partikel (dezente Hintergrund-Animation)
        if self._motes is None:
            rnd = random.Random(77)
            self._motes = [(rnd.random(), rnd.random(),
                            0.006 + rnd.random() * 0.014,
                            rnd.random() * 6.28,
                            rnd.choice((1, 1, 2))) for _ in range(18)]
        for nx, ny, sp, ph, rad in self._motes:
            y = ((ny - self.elapsed * sp * 0.06) % 1.0) * H
            x = ((nx + 0.03 * math.sin(self.elapsed * 0.25 + ph)) % 1.0) * W
            k = 0.35 + 0.35 * math.sin(self.elapsed * 1.4 + ph)
            pygame.draw.circle(SCREEN, _mote_col(k), (int(x), int(y)), rad)

    def _draw_header(self, title, title_color=WHITE):
        """Titel + Icons sind Teil der Layouts; hier nur der Titeltext (kompakt)."""
        W, H = ui_kit.W, ui_kit.H
        isz = icon_touch()
        neon_text(SCREEN, title, F(14), title_color, (W // 2, margin() + isz // 2), "center", 1)

    def draw_menu(self):
        """PAKET 7A: Neon-Glow-Header, Status-Chips, schmale Aktionsleiste."""
        W, H = ui_kit.W, ui_kit.H
        if self._idle_report:              # PAKET 8.6: Offline-Belohnung
            self._draw_menu_backdrop()     # abgedunkeltes Menue dahinter
            self._draw_idle_report()
            return
        self._draw_menu_backdrop()
        self._ui = self._layout_menu()
        top = u(12)
        # --- Neon-Glow: langsame, gestaffelte Puls-Phasen (Cyan vs. Magenta) ---
        k_c = pulse(self.elapsed, 4.4, 0.0)
        k_m = pulse(self.elapsed, 4.4, math.pi)
        if self.logo_img is not None:
            iw, ih = self.logo_img.get_size()
            lw = int(W * 0.34)
            lh = int(ih * lw / iw)
            maxh = int(H * 0.16)
            if lh > maxh:
                lh = maxh
                lw = int(ih * lh / ih)
            key = ("logo", lw, lh)
            img = self._fit_cache.get(key)
            if img is None:
                img = pygame.transform.smoothscale(self.logo_img, (lw, lh))
                self._fit_cache[key] = img
            lcx, lcy = W // 2, top + lh // 2
            g1 = radial_glow_k(CYAN, int(lw * 0.42), 0.15 + 0.15 * k_c)
            SCREEN.blit(g1, g1.get_rect(center=(lcx - int(lw * 0.30), lcy)),
                        special_flags=pygame.BLEND_ADD)
            g2 = radial_glow_k(MAGENTA, int(lw * 0.42), 0.15 + 0.15 * k_m)
            SCREEN.blit(g2, g2.get_rect(center=(lcx + int(lw * 0.30), lcy)),
                        special_flags=pygame.BLEND_ADD)
            SCREEN.blit(img, ((W - lw) // 2, top))
            header_end = top + lh + u(8)
        else:
            g1 = radial_glow_k(CYAN, u(140), 0.16 + 0.16 * k_c)
            SCREEN.blit(g1, g1.get_rect(center=(W // 2, top + u(30))),
                        special_flags=pygame.BLEND_ADD)
            g2 = radial_glow_k(MAGENTA, u(140), 0.16 + 0.16 * k_m)
            SCREEN.blit(g2, g2.get_rect(center=(W // 2, top + u(66))),
                        special_flags=pygame.BLEND_ADD)
            neon_text(SCREEN, "CORRIDOR", F(30), CYAN, (W // 2, top), "midtop", 2)
            neon_text(SCREEN, "SLAYER", F(30), MAGENTA, (W // 2, top + u(38)), "midtop", 2)
            header_end = top + u(78) + u(6)
        # --- schmales Command-Banner (7D: getoentes Glas statt Schwarz) ---
        bw = min(W - 2 * margin(), u(280))
        brect = pygame.Rect((W - bw) // 2, header_end, bw, u(22))
        _ban = pygame.Surface((brect.w, brect.h), pygame.SRCALPHA)
        _ban.fill((70, 52, 14, 110))
        SCREEN.blit(_ban, brect.topleft)
        pygame.draw.rect(SCREEN, (150, 116, 52), brect, 1, border_radius=u(5))
        text(SCREEN, "COMMAND INTERFACE", F(9), AMBER, brect.center, "center")
        # --- PAKET 8: zentrale Ressourcen-Anzeige (4 Ressourcen + XP-Fortschritt)
        self._draw_rpg_chips(brect.bottom + u(7),
                             extra=(f"SCHIFF LVL {self.modules.ship_hull_level}/{SHIP_MAX_LEVEL}", CYAN))
        # --- schmale Aktionsleiste: PAKET 8 Mini-Buttons mit Scroll-Clip ---
        bar = self._menu_bar_rect
        draw_action_bar(SCREEN, bar, CYAN, self.elapsed)
        prev_clip = SCREEN.get_clip()
        SCREEN.set_clip(bar)
        order = ["btn_idle", "btn_research", "btn_skills", "btn_stages",
                 "btn_daily", "btn_weekly", "btn_summon", "btn_settings",
                 "btn_quit"]
        for bid in order:
            b = self._ui.get(bid)
            if b is None:
                continue
            pk = None
            if bid == "btn_stages":          # bewusst NUR EIN Kern-Puls
                pk = pulse(self.elapsed, 3.2, 0.0)
            elif bid == "btn_daily" and self.quests.claimable_count("daily") > 0:
                pk = pulse(self.elapsed, 2.2, 1.1)
            elif bid == "btn_weekly" and self.quests.claimable_count("weekly") > 0:
                pk = pulse(self.elapsed, 2.2, 2.2)
            # PAKET 8.1: eigener Nav-Renderer (Metall + Cyan-Kontur,
            # einheitliche Font); Quest-/Beschwoerungs-Buttons unveraendert
            ui_kit.draw_nav_btn(SCREEN, b, pressed=self._pressed(bid),
                                pulse_k=pk, font=self._nav_font)
        SCREEN.set_clip(prev_clip)
        if self._menu_overflow:
            for bid in ("menu_left", "menu_right"):
                b = self._ui.get(bid)
                if b is not None:
                    ui_kit.draw_nav_btn(SCREEN, b, pressed=self._pressed(bid),
                                        font=self._nav_font)
        draw_compact_icon_btn(SCREEN, self._ui["snd_menu"],
                              pressed=self._pressed("snd_menu"))
        text(SCREEN, VERSION, F(8), DIM, (W // 2, bar.y - u(13)), "midtop")

    def _draw_module_card(self, rect, key, pressed=False, big=False):
        """PAKET 7A: kompaktere Karten (duenne Kontur, engere Typo).
        PAKET 7D: transparent-getoente Flaeche statt Schwarz (Glas)."""
        mod = self.modules.get(key)
        _card = pygame.Surface((max(2, rect.w), max(2, rect.h)), pygame.SRCALPHA)
        _card.fill((*((26, 62, 92) if pressed else (16, 40, 62)), 150 if pressed else 110))
        SCREEN.blit(_card, rect.topleft)
        pygame.draw.rect(SCREEN, CYAN if pressed else CYAN_SOFT, rect,
                         2 if pressed else 1, border_radius=u(8))
        img = load_module_image(key, mod.level)
        isz = u(38) if big else u(30)
        img_s = _scaled(_module_scaled, (key, mod.level, isz), img, isz / max(1, img.get_width()))
        SCREEN.blit(img_s, img_s.get_rect(center=(rect.centerx, rect.y + u(8) + isz // 2)))
        y = rect.y + u(10) + isz + u(3)
        text(SCREEN, mod.name.upper(), F(10), WHITE, (rect.centerx, y), "midtop")
        text(SCREEN, f"LVL {mod.level}", F(10), CYAN, (rect.centerx, y + u(15)), "midtop")
        if mod.level >= mod.max_level:
            text(SCREEN, "MAX", F(10), AMBER, (rect.centerx, y + u(28)), "midtop")
        else:
            # PAKET 7D: kein Stufen-Gate mehr - nur Credits (und MAX) begrenzen
            col = GREEN if self.modules.credits >= mod.cost else RED
            text(SCREEN, f"{mod.cost} Cr", F(10), col, (rect.centerx, y + u(28)), "midtop")

    def draw_research(self):
        """PAKET 7B: WERFT - das Schiff ist die interaktive Upgrade-Flaeche.
        Hotspots direkt am Modul-Sitz + Chip-Leiste; Detail-Panel mit echten
        Werten, naechster Stufe, Kosten und Upgrade-Button."""
        self._draw_menu_backdrop()
        self._ui = self._layout_research()
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        self._draw_header("SCHIFFS-WERFT", CYAN)
        text(SCREEN, f"CREDITS: {self.credits_display():,} Cr", F(11), GREEN,
             (W - m - icon_touch() - u(4), m + icon_touch() // 2), "midright")
        stage = self._werft_stage
        panel = self._werft_panel
        ship = self._werft_ship_rect(stage)
        # --- Buehne + Schiff (kosmetische Optik - stabil, keine Auto-Aufwertung) ---
        glass_panel(SCREEN, stage, accent=CYAN_SOFT, radius=u(12), alpha=110, width=1)
        # PAKET 7C: dezenter Kameraimpuls waehrend einer Upgrade-Animation
        shx, shy = self.upgrade_fx.shake()
        ship_draw = ship.move((shx, shy))
        base = getattr(self.fortress, "_base_image", None)
        if base is not None:
            # PAKET 7E: Cache-Key mit Schiffs-Stufe - nach einem Upgrade
            # erscheint das neue Schiffsbild sofort (kein altes Caching).
            lvl_now = self.modules.ship_hull_level
            img = self._fit_cache.get(("werftship", lvl_now, ship.w, ship.h))
            if img is None:
                img = pygame.transform.smoothscale(base, (ship.w, ship.h))
                self._fit_cache[("werftship", lvl_now, ship.w, ship.h)] = img
            SCREEN.blit(img, ship_draw.topleft)
        else:
            ox, oy = self.fortress.x, self.fortress.y
            self.fortress.x, self.fortress.y = ship_draw.center
            self.fortress.draw(SCREEN)
            self.fortress.x, self.fortress.y = ox, oy
        # --- PAKET 7C: Drohnen-Vorschau - der Hangar-Zustand ist VOR dem
        # Gefecht am Schiff sichtbar (Anzahl + Formation je Stufe) ---
        hang_l = self.modules.get("hangar").level
        extra_d = int(self.skills.modifiers().get("extra_drones", 0)) \
            if hasattr(self, "skills") else 0
        if hang_l > 1:
            n_prev = min(6, hang_l - 1 + extra_d)
            for i in range(n_prev):
                orb = self.elapsed * 0.7 + i * (math.tau / n_prev)
                dx = ship.centerx + int(math.cos(orb) * ship.w * 0.58)
                dy = ship.centery - u(6) + int(math.sin(orb) * ship.h * 0.82)
                _draw_drone_sprite(SCREEN, dx, dy, orb + math.pi / 2,
                                   scale=1.0, ghost=True, level=hang_l)
        text(SCREEN, "MODULE ANTIPPEN ODER CHIP-LEISTE NUTZEN", F(8), MUTED,
             (stage.centerx, stage.y + u(7)), "midtop")
        # --- PAKET 7E: Schiffs-Stufe + Aufwertung (das Schiff SELBST) ---
        ship_lvl = self.modules.ship_hull_level
        text(SCREEN, f"SCHIFF LVL {ship_lvl}/{SHIP_MAX_LEVEL}", F(9), ICE,
             (stage.right - u(10), stage.y + u(7)), "midright")
        sbtn = self._ui["res_ship"]
        s_cost = self.modules.ship_upgrade_cost()
        if ship_lvl >= SHIP_MAX_LEVEL:
            sbtn.label = "SCHIFF: MAXIMALE STUFE"
            sbtn.sub = f"Rumpfklasse {SHIP_MAX_LEVEL} erreicht"
            sbtn.enabled = False
        else:
            sbtn.label = f"SCHIFF AUFWERTEN \u2192 LVL {ship_lvl + 1}"
            sbtn.sub = f"{s_cost} Cr \u00b7 +80 Hülle \u00b7 +3% Schaden"
            sbtn.enabled = self.modules.credits >= s_cost
        draw_compact_btn(SCREEN, sbtn, pressed=self._pressed("res_ship"))
        # --- Hotspots (Zeichnen & Hit-Test: dieselbe Quelle) ---
        hs = self._werft_hotspots()
        for key, (x, y) in hs.items():
            sel = (key == self.sel_module)
            col = self.HOTSPOT_COL.get(key, CYAN)
            rad = u(8)
            if sel:
                k = pulse(self.elapsed, 2.6)
                pygame.draw.circle(SCREEN, col, (x, y), rad + u(2), 2)
                pr = rad + u(4) + int(u(4) * k)
                pygame.draw.circle(SCREEN, col, (x, y), pr, 1)
                pygame.draw.circle(SCREEN, _mix_col(col, WHITE, 0.4), (x, y), max(2, u(2)))
                target = (panel.left, min(max(y, panel.y + u(30)), panel.bottom - u(30)))
                pygame.draw.line(SCREEN, _mix_col(col, (10, 20, 34), 0.35),
                                 (x + rad + u(4), y), target, 1)
            else:
                pygame.draw.circle(SCREEN, _mix_col(col, (10, 20, 34), 0.45), (x, y), rad, 1)
            name = self.MOD_SHORT.get(key, key)[:9]
            text(SCREEN, name, F(8), col if sel else MUTED,
                 (x, y + rad + u(4)), "midtop")
            # PAKET 7C: Upgrade-Zustand direkt am Hotspot ablesbar
            text(SCREEN, f"LVL {self.modules.get(key).level}", F(7),
                 CYAN_SOFT if sel else DIM,
                 (x, y + rad + u(15)), "midtop")
        # --- Detail-Panel ---
        key = self.sel_module or "kanonen"
        mod = self.modules.get(key)
        glass_panel(SCREEN, panel, accent=CYAN, radius=u(12), alpha=216, width=2)
        pad = u(14)
        neon_text(SCREEN, mod.name.upper(), F(13), CYAN,
                  (panel.x + pad, panel.y + u(10)), "topleft", 1)
        y = panel.y + u(32)
        desc_f = F(9)
        for ln in wrap_text(mod.description, desc_f, panel.w - pad * 2)[:2]:
            text(SCREEN, ln, desc_f, MUTED, (panel.x + pad, y))
            y += int(desc_f.get_height() * 1.25)
        y += u(4)
        text(SCREEN, f"STUFE {mod.level} / {mod.max_level}", F(11), WHITE,
             (panel.x + pad, y))
        y += u(18)
        for v in module_effect_values(key, mod.level)[:3]:
            text(SCREEN, f"> {v}", F(9), CYAN_SOFT, (panel.x + pad, y))
            y += u(13)
        y += u(5)
        upg = self._ui["res_upgrade"]
        price = max(1, int(round(mod.cost * (1.0 - min(0.5, self.modules.cost_discount)))))
        if mod.level >= mod.max_level:
            text(SCREEN, "MAXIMAL AUSGEBAUT", F(10), GREEN, (panel.x + pad, y))
            upg.enabled = False
            upg.sub = "MAX"
        else:
            text(SCREEN, f"NAECHSTE STUFE: {module_next_effect(key)}", F(9), WHITE,
                 (panel.x + pad, y))
            y += u(14)
            col = GREEN if self.modules.credits >= price else RED
            disc = (f"  (KONTRAKTE -{int(round(self.modules.cost_discount * 100))}%)"
                    if self.modules.cost_discount > 0.001 else "")
            text(SCREEN, f"Kosten: {price} Cr{disc}", F(10), col, (panel.x + pad, y))
            upg.enabled = self.modules.credits >= price
            upg.sub = "" if upg.enabled else "ZU WENIG CREDITS"
            # PAKET 7D: Herkunft der Credits transparent anzeigen
            if not upg.enabled:
                y += u(14)
                text(SCREEN, "Credits: Kämpfe, Feindsignale & Idle-Betrieb", F(8),
                     MUTED, (panel.x + pad, y))
        draw_compact_btn(SCREEN, upg, pressed=self._pressed("res_upgrade"))
        # --- Chip-Leiste (Alternative zur Direktwahl am Schiff) ---
        for bid, b in self._ui.items():
            if bid.startswith("mod_"):
                b.active = (bid[4:] == self.sel_module)
                draw_compact_btn(SCREEN, b, pressed=self._pressed(bid))
        draw_compact_icon_btn(SCREEN, self._ui["res_back"], pressed=self._pressed("res_back"))
        draw_compact_icon_btn(SCREEN, self._ui["snd_res"], pressed=self._pressed("snd_res"))
        # PAKET 7C: Upgrade-Animation (Scan, Impuls, Funken, LVL-Text) UEBER
        # allem anderen zeichnen
        self.upgrade_fx.draw(SCREEN)

    def draw_stages(self):
        """PAKET 7A/7F: bg_world.jpg als interaktive Karte (world_map.py);
        Antippen startet Zoom + Orts-Szenerie (map_locations.py). Das
        Stufen-Sheet legt sich weiterhin darueber."""
        W, H = ui_kit.W, ui_kit.H
        states = self._map_states()
        if self.map_scene.active:
            # PAKET 7F: Zoom-/Szenen-Ansicht ersetzt die Kartenansicht
            self.map_scene.draw(SCREEN, self.world_bg, self.elapsed,
                                self._map_panel_info())
        else:
            info = self._map_panel_info()
            self.gmap.draw(SCREEN, self.world_bg, self.elapsed, states, info)
        if self.debug_mode and not self.map_scene.in_scene:
            self.gmap.draw_debug(SCREEN)
        self._ui = self._layout_stages()
        draw_compact_icon_btn(SCREEN, self._ui["stg_back"], pressed=self._pressed("stg_back"))
        draw_compact_icon_btn(SCREEN, self._ui["snd_stg"], pressed=self._pressed("snd_stg"))
        # PAKET 7D: Karte = Kampagne (Story-Bezug im Titel)
        neon_text(SCREEN, "KAMPAGNE", F(12), ICE,
                  (W // 2, margin() + icon_touch() // 2), "center", 1)
        if self.selected_sector > 0:
            overlay(SCREEN, 110)
            rect = self._stage_sheet_rect
            glass_panel(SCREEN, rect, accent=VIOLET, radius=u(12), alpha=226, width=2)
            name = SECTOR_DATA[self.selected_sector]["name"]
            neon_text(SCREEN, f"SEKTOR {self.selected_sector} · {name}", F(13), VIOLET,
                      (rect.centerx, rect.y + u(8)), "midtop", 1)
            for bid, b in self._ui.items():
                if bid.startswith("stage_"):
                    self._draw_stage_cell(b.rect, int(bid[6:]), pressed=self._pressed(bid))
            draw_compact_icon_btn(SCREEN, self._ui["stg_close"],
                                  pressed=self._pressed("stg_close"))

    def _draw_stage_cell(self, rect, stage, pressed=False):
        sector = self.selected_sector
        is_completed = (sector, stage) in self.modules.completed_stages
        is_unlocked = (sector < self.modules.highest_campaign or
                       (sector == self.modules.highest_campaign and stage <= self.modules.highest_stage))
        is_boss = stage == 15
        is_semi = stage in (5, 10)
        if is_completed:
            border, fill, inner = GREEN, (10, 30, 20), (5, 15, 10)
        elif is_unlocked:
            border, fill, inner = VIOLET, (20, 10, 35), (10, 5, 20)
        else:
            border, fill, inner = DIM, (5, 5, 10), (2, 2, 5)
        if is_boss:
            border = AMBER if is_unlocked else RED
        elif is_semi:
            border = VIOLET if is_unlocked else MAGENTA
        if pressed:
            border = WHITE
        cut = max(4, int(min(rect.w, rect.h) * 0.16))
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        outer = [(x + cut, y), (x + w - cut, y), (x + w, y + cut), (x + w, y + h - cut),
                 (x + w - cut, y + h), (x + cut, y + h), (x, y + h - cut), (x, y + cut)]
        pygame.draw.polygon(SCREEN, fill, outer)
        pygame.draw.polygon(SCREEN, border, outer, max(2, u(3)))
        ix, iy, iw, ih = rect.inflate(-u(10), -u(10))
        ic = max(3, cut - u(2))
        innerp = [(ix + ic, iy), (ix + iw - ic, iy), (ix + iw, iy + ic), (ix + iw, iy + ih - ic),
                  (ix + iw - ic, iy + ih), (ix + ic, iy + ih), (ix, iy + ih - ic), (ix, iy + ic)]
        pygame.draw.polygon(SCREEN, inner, innerp, 1)
        if is_boss or is_semi:
            label = "BOSS" if is_boss else "ELITE"
            lab_col = AMBER if (is_boss and is_unlocked) else (RED if is_boss else MAGENTA)
            text(SCREEN, label, F(9), lab_col, (rect.centerx, rect.y + u(8)), "midtop")
            text(SCREEN, str(stage), F(14), WHITE if is_unlocked else MUTED,
                 (rect.centerx, rect.centery + u(6)), "center")
        else:
            text(SCREEN, str(stage), F(16), WHITE if is_unlocked else MUTED,
                 rect.center, "center")

    def draw_skill_tree(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        isz = icon_touch()
        top, bottom = self._nex_area()
        cores = self.modules.data_cores
        self.nexus.draw(SCREEN, self.elapsed, self.skills, cores, SKILL_TREE,
                        top, bottom, bg=self.nexus_bg)
        self._ui = self._layout_skilltree()
        draw_compact_icon_btn(SCREEN, self._ui["nex_back"], pressed=self._pressed("nex_back"))
        neon_text(SCREEN, "SKILL-NEXUS", F(15), AMBER, (W // 2, m + isz // 2), "center", 1)
        text(SCREEN, f"DATA CORES: {cores}", F(11), GREEN if cores > 0 else RED,
             (W - m - u(6), m + isz // 2), "midright")

    def draw_settings(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        self._draw_menu_backdrop()
        self._ui = self._layout_settings()
        self._draw_header("EINSTELLUNGEN", VIOLET)
        toggles = {"set_sound": not SFX.muted,
                   "set_full": bool(pygame.display.is_fullscreen()),
                   "set_debug": self.debug_mode}
        for bid, b in self._ui.items():
            if bid.startswith("set_") and bid != "set_back":
                draw_compact_btn(SCREEN, b, pressed=self._pressed(bid))
                trect = pygame.Rect(b.rect.right - u(66) - u(12), b.rect.centery - u(14), u(56), u(28))
                draw_toggle(SCREEN, trect, toggles.get(bid, False))
        draw_compact_icon_btn(SCREEN, self._ui["set_back"], pressed=self._pressed("set_back"))
        info_y = getattr(self, "_settings_rows_end", H // 2) + u(10)
        info = [VERSION,
                "Optimiert für Touch: alle Funktionen komplett antippbar."]
        if ui_kit.ROTATED:
            info.append("Rotationsschicht aktiv: Ausgabe immer im Querformat.")
        f = F(10)
        y = info_y
        for ln in info:
            text(SCREEN, ln, f, MUTED, (W // 2, y), "midtop")
            y += int(f.get_height() * 1.4)

    def draw_pause_menu(self):
        overlay(SCREEN, 185)
        self._ui = self._layout_pause()
        rect = self._pause_rect
        glass_panel(SCREEN, rect, accent=CYAN, radius=u(12), alpha=228, width=2)
        neon_text(SCREEN, "PAUSIERT", F(17), WHITE, (rect.centerx, rect.y + u(12)), "midtop", 1)
        for bid, b in self._ui.items():
            draw_compact_btn(SCREEN, b, pressed=self._pressed(bid))

    def _view(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        if W > H:
            # LANDSCAPE: 16:9-Welt nahezu randlos (nur hauchduenner Inset)
            inset = u(6)
            avail_w = W - 2 * inset
            avail_h = H - 2 * inset
            s = min(avail_w / WORLD_W, avail_h / WORLD_H)
            aw, ah = int(WORLD_W * s), int(WORLD_H * s)
            ox, oy = (W - aw) // 2, (H - ah) // 2
            return s, ox, oy, aw, ah
        isz = max(u(40), min(W, H) // 14)
        top = m + isz + u(12)
        if not self.idle_mode:
            top += u(18) + u(10)
        deck = btn_h() + m + u(16)
        avail_w = W - u(10)
        avail_h = max(50, H - top - deck)
        s = min(avail_w / WORLD_W, avail_h / WORLD_H)
        aw, ah = int(WORLD_W * s), int(WORLD_H * s)
        ox, oy = (W - aw) // 2, top + (avail_h - ah) // 2
        return s, ox, oy, aw, ah

    def draw_playing(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        SCREEN.fill(VOID)          # Full-Flush: keine Restpixel aus dem Vorbild-Screen
        combat = self.idle_combat if self.idle_mode else self.pve
        landscape = W > H
        s, ox, oy, aw, ah = self._view()
        ox += int(self.fx.shake_x)   # Screen-Shake nur auf der Arena
        oy += int(self.fx.shake_y)
        ox += int(self.damage_fx.shake_x)   # PAKET 8.3: Treffer-Shake
        oy += int(self.damage_fx.shake_y)
        rect = pygame.Rect(ox, oy, aw, ah)
        ch_bg = None
        idx = 0
        if not self.idle_mode and self.bg_chapter[0] is not None:
            idx = 0 if combat.stage_id <= 5 else (1 if combat.stage_id <= 10 else 2)
            ch_bg = self.bg_chapter[idx]
        if landscape:
            # Kein schwarzer Leerraum: Kapitel-Bild cover-skalierd hinter die Arena
            if ch_bg is not None:
                img = self._fit_surf(ch_bg, ("chapcover", idx), brighten=22)  # 7C: heller
                SCREEN.blit(img, ((W - img.get_width()) // 2, (H - img.get_height()) // 2))
                overlay(SCREEN, 26)   # PAKET 7C: 60 -> 26
            else:
                grid_bg(SCREEN, self.elapsed)
        if ch_bg is not None:
            key = ("chap", idx, aw, ah)
            img = self._fit_cache.get(key)
            if img is None:
                img = pygame.transform.smoothscale(ch_bg, (aw, ah))
                img.fill((22, 22, 30), special_flags=pygame.BLEND_RGB_ADD)  # 7C: heller
                self._fit_cache[key] = img
            SCREEN.blit(img, rect.topleft)
            dim = self._fit_cache.get(("dim", aw, ah))
            if dim is None:
                dim = pygame.Surface((aw, ah), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 14))   # PAKET 7C: 50 -> 14 (lesbarer Weltraum)
                self._fit_cache[("dim", aw, ah)] = dim
            SCREEN.blit(dim, rect.topleft)
        elif not landscape:
            SCREEN.set_clip(rect)
            grid_bg(SCREEN, self.elapsed)
            SCREEN.set_clip(None)
        SCREEN.set_clip(rect)
        try:
            self._draw_world(combat, s, ox, oy)
        finally:
            SCREEN.set_clip(None)
        col = (30, 60, 88)
        cl, lw = u(16), max(2, u(2))
        for (cx, cy, dx, dy) in ((rect.left, rect.top, 1, 1), (rect.right, rect.top, -1, 1),
                                 (rect.left, rect.bottom, 1, -1), (rect.right, rect.bottom, -1, -1)):
            pygame.draw.line(SCREEN, col, (cx, cy + dy * cl), (cx, cy), lw)
            pygame.draw.line(SCREEN, col, (cx, cy), (cx + dx * cl, cy), lw)
        # PAKET 8.3: rote Rand-Vignette nach Treffern / kritischer Huelle
        self.damage_fx.draw_vignette(SCREEN)
        isz = max(u(40), min(W, H) // 14)
        if not self.idle_mode:
            hp_ratio = combat.player_hp / max(1.0, combat.max_player_hp)
            if landscape:
                bar = pygame.Rect(int(W * 0.5 - u(215)), m + u(2), u(430), u(16))
            else:
                bar = pygame.Rect(m, m + isz + u(10), W - 2 * m, u(16))
            pygame.draw.rect(SCREEN, (20, 30, 45), bar, border_radius=u(8))
            hpc = GREEN if hp_ratio > 0.3 else RED
            pygame.draw.rect(SCREEN, hpc, (bar.x, bar.y, int(bar.w * hp_ratio), bar.h),
                             border_radius=u(8))
            # Segment-Markierungen (10% Raster)
            for i in range(1, 10):
                tx = bar.x + int(bar.w * i / 10)
                pygame.draw.line(SCREEN, (14, 22, 32), (tx, bar.y + 1), (tx, bar.bottom - 1), 1)
            border_c = CYAN_SOFT
            if hp_ratio <= 0.3:
                k = 0.5 + 0.5 * math.sin(self.elapsed * 7.0)
                border_c = (int(120 + 135 * k), int(30 + 20 * k), int(45 + 30 * k))
                glow = radial_glow(RED, 26)
                SCREEN.blit(glow, glow.get_rect(center=bar.center),
                            special_flags=pygame.BLEND_ADD)
            pygame.draw.rect(SCREEN, border_c, bar, 2, border_radius=u(8))
            text(SCREEN, f"HÜLLE {int(combat.player_hp)} / {int(combat.max_player_hp)}",
                 F(10), WHITE, bar.center, "center")
            neon_text(SCREEN, f"CREDITS: {combat.credits:,}", F(12), GREEN,
                      (W - m, m + u(2)), "topright")
            neon_text(SCREEN, f"SEKTOR {combat.campaign_id} · STUFE {combat.stage_id:02d}",
                      F(10), AMBER, (W - m, m + u(24)), "topright")
        else:
            neon_text(SCREEN, f"IDLE-BEUTE: +{combat.idle_loot_earned:,} Cr", F(12), GREEN,
                      (W - m, m + u(2)), "topright")
            neon_text(SCREEN, f"GESAMT: {self.modules.credits + combat.credits:,} Cr", F(10),
                      MUTED, (W - m, m + u(24)), "topright")
            # PAKET 8.8b: Stundenlohn-Rhythmus + 8h-Maximum sichtbar
            if getattr(self.idle_combat, "income_frozen", False):
                neon_text(SCREEN, "MAXIMUM ERREICHT (8 H)", F(10), RED,
                          (W - m, m + u(44)), "topright")
            else:
                rest = max(0, int(IDLE_PAYOUT_S - self._idle_auto_t))
                neon_text(SCREEN, f"AUSZAHLUNG IN {rest // 60:02d}:{rest % 60:02d}", F(10),
                          MUTED, (W - m, m + u(44)), "topright")
        self._ui = self._layout_hud()
        draw_action_bar(SCREEN, self._hud_bar_rect, CYAN, self.elapsed)
        for bid, b in self._ui.items():
            draw_compact_btn(SCREEN, b, pressed=self._pressed(bid))
        # Uebertaktungs-Cooldown: duenne Fortschrittslinie im Button
        od = self._ui.get("hud_overdrive")
        if od is not None and not self.idle_mode:
            cd = float(getattr(self.pve, "overdrive_cd", 0.0) or 0.0)
            if cd > 0:
                prog = 1.0 - min(1.0, cd / 45.0)
                lr = od.rect.inflate(-u(16), -u(16))
                pygame.draw.line(SCREEN, VIOLET, (lr.x, lr.bottom - u(3)),
                                 (lr.x + int(lr.w * prog), lr.bottom - u(3)), max(2, u(2)))
        # AUFTRAG 8: Champion-Abklingzeiten als duenne Fortschrittslinie
        if not self.idle_mode:
            _sks = getattr(self.pve, "champ_skills", [])
            _cds = getattr(self.pve, "champ_cd", [])
            for ci in range(rpg_config.CHAMPION_HUD_BUTTONS):
                b = self._ui.get(f"hud_champ{ci}")
                if b is None or ci >= len(_cds) or _cds[ci] <= 0.0:
                    continue
                total = max(0.1, float(_sks[ci].get("cd", 10.0))) \
                    if ci < len(_sks) else 1.0
                prog = 1.0 - min(1.0, _cds[ci] / total)
                lr = b.rect.inflate(-u(10), -u(10))
                pygame.draw.line(SCREEN, AMBER, (lr.x, lr.bottom - u(3)),
                                 (lr.x + int(lr.w * prog), lr.bottom - u(3)),
                                 max(2, u(2)))
        if self.show_upgrades:
            overlay(SCREEN, 185)
            ui_sheet, sheet_rect = self._layout_upgrades()
            self._ui = ui_sheet
            glass_panel(SCREEN, sheet_rect, accent=MAGENTA, radius=u(12), alpha=226, width=2)
            neon_text(SCREEN, "MODULE & UPGRADES", F(13), MAGENTA,
                      (sheet_rect.centerx, sheet_rect.y + u(10)), "midtop", 1)
            text(SCREEN, f"CREDITS: {self.credits_display():,} Cr", F(10), GREEN,
                 (sheet_rect.x + u(14), sheet_rect.y + u(14)))
            for bid, b in ui_sheet.items():
                if bid.startswith("upg_") and bid != "upg_close":
                    self._draw_module_card(b.rect, bid[4:], pressed=self._pressed(bid))
            draw_compact_icon_btn(SCREEN, ui_sheet["upg_close"], pressed=self._pressed("upg_close"))
            self.upgrade_fx.draw(SCREEN)   # PAKET 7C: Upgrade-Animation auf der Karte

    def _draw_world(self, combat, s, ox, oy):
        def T(x, y):
            return (ox + x * s, oy + y * s)

        # PAKET 8.8: lebendiger Hintergrund (Nebel, Staub, Glut) - immer
        # die Ebene direkt UBER dem Kapitel-Bild, unter allem Gameplay.
        if not self.idle_mode and self.bg_chapter[0] is not None:
            self.bg_fx.draw(SCREEN, T, s, self.elapsed)

        ship_x, ship_y = self.movement.get_position(self.fortress.x, self.fortress.y)
        angle = self.movement.get_angle()
        ex, ey = T(ship_x + self.debug_engine_offset[0], ship_y + self.debug_engine_offset[1])
        self.engine_effect.set_position(ex, ey)
        self.engine_effect.draw(SCREEN)

        sx, sy = T(ship_x, ship_y)
        schild_lvl = self.modules.get("schild").level
        if schild_lvl > 1:
            rad = (60 + schild_lvl * 5) * s
            pulse = math.sin(self.elapsed * 4) * 3
            # PAKET 8.7: EIGENE Schild-Grafik (z. B. DS4/schilder/schild_3.png)
            # verwenden, sobald sie vorhanden ist - die Kreise bleiben als
            # funktionaler Basis-Ring (Treffer-Feedback, immer lesbar).
            d = max(4, int((rad + pulse) * 2.12))
            sh_img = self._shgfx_scaled(schild_lvl, d)
            if sh_img is not None:
                SCREEN.blit(sh_img, sh_img.get_rect(center=(int(sx), int(sy))))
            pygame.draw.circle(SCREEN, (0, 255, 255), (int(sx), int(sy)), int(rad + pulse), 2)
            pygame.draw.circle(SCREEN, (0, 180, 200), (int(sx), int(sy)), int(rad + pulse + 5 * s), 1)

        base = getattr(self.fortress, "_base_image", None)
        if base:
            # PAKET 7E: Cache-Key mit Schiffs-Stufe (neues Bild nach Upgrade)
            img = _scaled(_ship_scaled, ("ship", self.modules.ship_hull_level),
                          base, s)
            rot = pygame.transform.rotate(img, angle)
            SCREEN.blit(rot, rot.get_rect(center=(int(sx), int(sy))))
        else:
            orig = (self.fortress.x, self.fortress.y)
            self.fortress.x, self.fortress.y = sx, sy
            self.fortress.draw(SCREEN)
            self.fortress.x, self.fortress.y = orig

        _now_ms = pygame.time.get_ticks()
        for enemy in combat.enemies:
            # PAKET 8.8c: Maul-Zustand des Drachen - GESCHLOSSEN im
            # Normalflug, OFFEN nur beim Angriff (Atem-Telegraf/Strahl,
            # Bomben-/Spiess-Telegraf). Der breath_phase-Check ist das
            # Sicherheitsnetz, falls mouth_open fehlt.
            if enemy.enemy_type == "dragon":
                maw = (getattr(enemy, "mouth_open", False)
                       or getattr(enemy, "breath_phase", 0) > 0)
                if maw:
                    img0 = load_enemy_image("dragon")
                    ckey = enemy.enemy_type
                else:
                    img0 = load_enemy_variant("dragon", "_closed")
                    ckey = "dragon_closed"   # eigener Cache-Key!
            else:
                img0 = load_enemy_image(enemy.enemy_type)
                ckey = enemy.enemy_type
            img = _scaled(_enemy_scaled, ckey, img0, s)
            # AUFTRAG 15 (2. DURCHLAUF): Ausrichtung zentral über
            # enemy_rotated() - Nase jedes Gegnertyps zeigt zum Schiff,
            # einheitlich in Kampagne und Idle (siehe Tabellen oben).
            rot = enemy_rotated(img, enemy.enemy_type,
                                enemy.x, enemy.y, ship_x, ship_y)
            ex, ey = T(enemy.x, enemy.y)
            # PAKET 8.8a: BOSS-PRAESENZ - pulsierende Aura in Boss-Farbe
            # plus langsames Schweben. Nur ZEICHNUNG: Position/Kollision/
            # Logik bleiben unangetastet. Aura-Groesse haengt am
            # unrotierten Sprite (stabil -> Cache-Treffer, keine
            # Smoothscale-Last pro Frame).
            if enemy.is_boss:
                glow = _boss_glow(enemy.boss_col)
                gr = int(max(img.get_width(), img.get_height()) * 0.78)
                if gr > 10:
                    gk = (enemy.boss_col, gr)
                    gs = _boss_glow_scaled.get(gk)
                    if gs is None:
                        gs = pygame.transform.smoothscale(glow, (gr, gr))
                        if len(_boss_glow_scaled) > 24:
                            _boss_glow_scaled.clear()
                        _boss_glow_scaled[gk] = gs
                    gs.set_alpha(int(150 + 70 * math.sin(_now_ms * 0.0032)))
                    SCREEN.blit(gs, gs.get_rect(center=(int(ex), int(ey))))
                ey += math.sin(_now_ms * 0.0021 + enemy.x * 0.13) * 4.0 * s
            SCREEN.blit(rot, rot.get_rect(center=(int(ex), int(ey))))
            # PAKET 8.3: ENT-Ueberladung - der HP-Balken steht nicht mehr
            # permanent ueber JEDEM Gegner (Dauer-Unruhe), sondern nur noch
            # bei beschädigten Gegnern, und dann schmaler/dezenter.
            # PAKET 8.8a: Bosse gar nicht - sie haben den grossen
            # Namensbalken oben, der Mini-Balken klebt sonst in der Grafik.
            if enemy.hp < enemy.max_hp and not enemy.is_boss:
                bw, bh = 34 * s, 3 * s
                bar = pygame.Rect(int(ex - bw / 2), int(ey - 32 * s),
                                  max(2, int(bw)), max(2, int(bh)))
                pygame.draw.rect(SCREEN, (24, 26, 30), bar,
                                 border_radius=max(1, int(bh / 2)))
                pygame.draw.rect(SCREEN, GREEN,
                                 (bar.x, bar.y,
                                  max(0, int(bar.w * enemy.hp / max(1, enemy.max_hp))),
                                  bar.h), border_radius=max(1, int(bh / 2)))

        # PAKET 8.8b: FLAMMEN-ATEM des Eisdrachen zeichnen (Telegraf /
        # Strahl). Nach der Gegner-Schleife, damit der Strahl aus dem
        # Maul zu brennen scheint.
        _db = getattr(combat, "boss_ref", None)
        if (_db is not None and _db.hp > 0
                and getattr(_db, "breath_phase", 0) > 0
                and _db.enemy_type == "dragon"):
            _draw_dragon_breath(SCREEN, _db, T, s, ship_x, ship_y, _now_ms)
        # PAKET 8.8c: Zusatz-Angriffe (GLUTBOMBEN / EISSPIESSE) rendern -
        # ebenfalls nach der Gegner-Schleife, ueber dem Hintergrund.
        _draw_boss_attacks(SCREEN, combat, T, s, _now_ms)

        target = min(combat.enemies, key=lambda e: e.x) if combat.enemies else None
        # PAKET 7E: Der Geschuetzturm zeigt jetzt die WAFFEN-Stufe (Modul
        # "kanonen") - Waffen aufwerten veraendert Bild UND Schaden. Bild =
        # kanonen/kanonen_lvl_<1..12>.png; fehlt ein Bild, liefert der
        # Loader automatisch die naechstniedrigere vorhandene Stufe.
        kanonen_lvl = self.modules.get("kanonen").level
        current_offset = self.debug_cannon_offset if self.debug_mode else CANNON_OFFSETS[0]
        cox, coy = current_offset
        cx, cy = T(ship_x + cox, ship_y + coy)
        ang_deg = math.degrees(math.atan2(target.y - ship_y - coy, target.x - ship_x - cox)) if target else 0
        turret0 = load_kanonen_image(kanonen_lvl)
        turret = _scaled(_kanonen_scaled, kanonen_lvl, turret0, s)
        rot = pygame.transform.rotate(turret, -ang_deg)
        sw, sh = int(30 * s), int(15 * s)
        shadow = pygame.Surface((max(2, sw), max(2, sh)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 100), (0, 0, sw, sh))
        SCREEN.blit(shadow, (cx - sw // 2, cy + int(5 * s)))
        SCREEN.blit(rot, rot.get_rect(center=(int(cx), int(cy))))

        # --- PAKET 7C: gezielte Upgrade-Optiken (NUR das jeweilige Modul
        # veraendert sichtbar etwas - keine automatische Gesamtaufwertung) ---
        rea_l = self.modules.get("reaktor").level
        if rea_l > 1:
            # Reaktor: pulsierender Energiekern im Schiffs-Zentrum
            k = 0.5 + 0.5 * math.sin(self.elapsed * 3.0 + 0.4)
            g = radial_glow_k(VIOLET, int(u(12) + rea_l * 2), 0.14 + 0.16 * k)
            SCREEN.blit(g, g.get_rect(center=(int(sx), int(sy))),
                        special_flags=pygame.BLEND_ADD)
        hul_l = self.modules.get("huelle").level
        if hul_l > 1:
            # Schiffshuelle: verstaerkte Platten (zwei helle Kiel-Linien)
            a = 80 + int(60 * (0.5 + 0.5 * math.sin(self.elapsed * 2.2)))
            pl1 = pygame.Surface((max(2, int(56 * s)), max(2, int(3 * s))), pygame.SRCALPHA)
            pl1.fill((150, 190, 235, a))
            SCREEN.blit(pl1, (int(sx - 30 * s), int(sy + 6 * s)))
            pl2 = pygame.Surface((max(2, int(40 * s)), max(2, int(2 * s))), pygame.SRCALPHA)
            pl2.fill((150, 190, 235, int(a * 0.7)))
            SCREEN.blit(pl2, (int(sx - 22 * s), int(sy + 12 * s)))
        rad_l = self.modules.get("radar").level
        if rad_l > 1:
            # Radar: rotierender Erfassungsstrahl um das Schiff
            ang = self.elapsed * 1.6
            rr = (52 + rad_l * 2.5) * s
            pygame.draw.arc(SCREEN, (168, 196, 232),
                            (int(sx - rr), int(sy - rr), int(rr * 2), int(rr * 2)),
                            ang, ang + 1.0, 1)
        # --- PAKET 7C: HANGAR-DROHNEN SICHTBAR (echte Einheiten um das
        # Schiff; reagieren auf Hangar-Stufe: Anzahl, Groesse, Ringe) ---
        hang_l = self.modules.get("hangar").level
        if hang_l > 1:
            for d in getattr(combat, "drones", []):
                dx, dy = T(d.x, d.y)
                sc = 0.55 + 0.45 * d.spawn_t        # gestaffelter Einflug
                _draw_drone_sprite(SCREEN, int(dx), int(dy), d.angle,
                                   scale=sc * s * 1.15, level=hang_l)

        # Kampfeffekte: Projektiloptik, Spuren, Treffer, Explosionen, Muzzle
        self.fx.draw(SCREEN, combat, T, s, self.elapsed)
        # PAKET 8.3: Einschlags-Explosion am Schiff (Ringe, Funken, Flash)
        self.damage_fx.draw_world(SCREEN, T, self.elapsed)
        # PAKET 8.7: Feuer/Rauch/Funken am angeschlagenen Schiff (< 50 % HP)
        self.burn_fx.draw(SCREEN, T, s, self.elapsed)

        # -------------------------------------------------------------
        # PAKET 8.8: Boss-HUD - Lebensbalken oben mittig + Einzugs-Banner
        # -------------------------------------------------------------
        if not self.idle_mode:
            boss = getattr(combat, "boss_ref", None)
            if boss is not None and boss.hp > 0:
                bx, by = T(WORLD_W * 0.5, 30)
                bw = int(min(430.0, WORLD_W * 0.55) * s)
                bh = max(6, int(9 * s))
                rad = max(1, bh // 2)
                bar = pygame.Rect(int(bx - bw / 2), int(by), bw, bh)
                pygame.draw.rect(SCREEN, (14, 17, 24), bar, border_radius=rad)
                fill_w = int(bw * max(0.0, min(1.0, boss.hp / max(1.0, boss.max_hp))))
                if fill_w > 0:
                    pygame.draw.rect(SCREEN, boss.boss_col,
                                     (bar.x, bar.y, fill_w, bar.h),
                                     border_radius=rad)
                pygame.draw.rect(SCREEN, (205, 220, 240), bar, 1,
                                 border_radius=rad)
                fnt = F(max(11, fs(14)))
                text(SCREEN, boss.name, fnt, (238, 243, 250),
                     (int(bx), bar.y - max(3, int(u(3)))), anchor="midbottom")
                text(SCREEN, "BOSS", F(max(9, fs(10))), boss.boss_col,
                     (bar.x - max(6, int(u(7))), bar.y + bar.h // 2),
                     anchor="midright")
            bbt = getattr(combat, "boss_banner_t", 0.0)
            if bbt > 0:
                fade = max(0.0, min(1.0, bbt / 0.6))
                bx, by = T(WORLD_W * 0.5, WORLD_H * 0.40)
                col = boss.boss_col if boss is not None else AMBER
                fnt = F(max(20, fs(32)))
                img = fnt.render(getattr(combat, "boss_name", "BOSS"),
                                 True, (12, 14, 18))
                img.set_alpha(int(210 * fade))
                SCREEN.blit(img, img.get_rect(center=(int(bx) + 2, int(by) + 2)))
                img = fnt.render(getattr(combat, "boss_name", "BOSS"),
                                 True, col)
                img.set_alpha(int(255 * fade))
                SCREEN.blit(img, img.get_rect(center=(int(bx), int(by))))
                sfnt = F(max(11, fs(14)))
                sub = sfnt.render("BOSSGEFECHT", True, (235, 240, 248))
                sub.set_alpha(int(235 * fade))
                SCREEN.blit(sub, sub.get_rect(center=(int(bx), int(by) + int(fs(26)))))

        for dn in getattr(combat, "damage_numbers", []):
            alpha = max(0, min(255, int(255 * dn.life / max(0.001, dn.max_life))))
            f = F((20 if dn.big else 14) * s)
            surf = f.render(str(dn.value), True, dn.color)
            surf.set_alpha(alpha)
            dx, dy = T(dn.x, dn.y)
            SCREEN.blit(surf, surf.get_rect(center=(int(dx), int(dy))))

    def _draw_debug(self):
        s, ox, oy, aw, ah = self._view()
        cx, cy = ox + (self.fortress.x + 0) * s, oy + self.fortress.y * s
        ship_x, ship_y = self.movement.get_position(self.fortress.x, self.fortress.y)
        cx, cy = ox + ship_x * s, oy + ship_y * s
        pygame.draw.line(SCREEN, RED, (cx - 20, cy), (cx + 20, cy), 2)
        pygame.draw.line(SCREEN, RED, (cx, cy - 20), (cx, cy + 20), 2)
        tx, ty = ox + (ship_x + self.debug_cannon_offset[0]) * s, oy + (ship_y + self.debug_cannon_offset[1]) * s
        pygame.draw.circle(SCREEN, GREEN, (int(tx), int(ty)), 20, 1)
        text(SCREEN, "DEBUG: TAB = Ziel · Pfeile = justieren", F(9), RED,
             (ui_kit.W // 2, ui_kit.H - btn_h() - margin() - u(26)), "midtop")

    def _video_overlay(self, frames, timer, speed=1.0):
        """Zeichnet das aktuelle Videoframe; True, wenn beendet.
        PAKET 8.8b: Frame wird auf "cover" skaliert (füllt den Screen
        immer ganz) - eingebrannte UI-Elemente der Animation liegen dann
        garantiert am Screen-Rand und werden vom End-Vorhang verdeckt."""
        W, H = ui_kit.W, ui_kit.H
        if not frames:
            return True
        full = len(frames) / 30.0
        idx = min(int(timer * 30), len(frames) - 1)
        frame = self._video_frame(frames, idx)
        SCREEN.fill((0, 0, 0))
        fw, fh = frame.get_size()
        if fw < W or fh < H:                     # cover-fit (8.8b)
            k = max(W / fw, H / fh)
            frame = pygame.transform.scale(frame, (int(fw * k) + 1,
                                                   int(fh * k) + 1))
        SCREEN.blit(frame, ((W - frame.get_width()) // 2,
                            (H - frame.get_height()) // 2))
        return timer >= full

    def draw_defeat(self):
        """PAKET 8.8b: Video-Playback (cover-fit), danach End-VORHANG mit
        Verlaufskante: "SCHIFF ZERSTÖRT" + pulsierendes "TIPPEN FÜR
        NEUSTART". KEINE Buttons (8.8a) - ein Tipp irgendwo startet die
        Stufe neu. Der hoehere Vorhang verdeckt jetzt zuverlaessig die
        eingebrannten {R}/HAUPTMENUE-Buttons der Animation."""
        self._ui = self._layout_defeat()
        if not self.defeat_frames:
            SCREEN.fill((16, 0, 4))
        else:
            self._video_overlay(self.defeat_frames, self.defeat_timer)
        ended = (not self.defeat_frames) or \
            self.defeat_timer >= len(self.defeat_frames) / 30.0
        if ended and "def_tap" in self._ui:
            card = self._defeat_card_rect
            shade = pygame.Surface((card.w, card.h), pygame.SRCALPHA)
            shade.fill((5, 2, 6, 232))
            SCREEN.blit(shade, card.topleft)
            # Verlaufskante oben (8.8b): weicher Uebergang statt harter Linie
            gh = max(10, u(22))
            gk = (card.w, gh)
            grad = getattr(self, "_defeat_grad", None)
            if grad is None or grad.get_size() != gk:
                grad = pygame.Surface(gk, pygame.SRCALPHA)
                for yy in range(gh):
                    grad.fill((5, 2, 6, int(232 * (1.0 - yy / (gh - 1)))),
                              (0, yy, gk[0], 1))
                self._defeat_grad = grad
            SCREEN.blit(grad, (card.x, card.y - gh))
            neon_text(SCREEN, "SCHIFF ZERSTÖRT", F(15), RED,
                      (card.centerx, card.y + u(46)), "center", 2)
            # Pulsierender Hinweis statt Buttons (8.8a)
            _p = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.003)
            _hc = (int(96 + 96 * _p), int(96 + 88 * _p), int(106 + 90 * _p))
            neon_text(SCREEN, "TIPPEN FÜR NEUSTART", F(11), _hc,
                      (card.centerx, card.y + u(88)), "center", 1)

    def draw_stage_clear(self):
        W, H = ui_kit.W, ui_kit.H
        self._ui = self._layout_clear()
        if self.victory_frames:
            ended = self._video_overlay(self.victory_frames, self.victory_timer)
            if not ended:
                self._draw_skip_hint()
                return
            overlay(SCREEN, 90)
        else:
            overlay(SCREEN, 150)
        neon_text(SCREEN, "STUFE GESCHAFFT!", F(24), GREEN, (W // 2, int(H * 0.44)), "midtop", 2)
        neon_text(SCREEN, f"+{self.last_stage_reward:,} CREDITS", F(15), WHITE,
                  (W // 2, int(H * 0.44) + u(44)), "midtop", 1)
        # PAKET 8: Spieler-XP fuer die Mission + Levelaufstiege anzeigen
        if self.last_xp_gain > 0:
            col = CYAN if self.last_levelups <= 0 else GREEN
            msg = f"+{self.last_xp_gain} XP  ·  SPIELER LVL {self.rpg.level}"
            if self.last_levelups > 0:
                msg = f"+{self.last_xp_gain} XP  ·  LEVEL-AUFSCHWUNG: LVL {self.rpg.level}!"
            neon_text(SCREEN, msg, F(13), col,
                      (W // 2, int(H * 0.44) + u(70)), "midtop", 1)
        for bid, b in self._ui.items():
            draw_compact_btn(SCREEN, b, pressed=self._pressed(bid))

    def draw_victory(self):
        """AUFTRAG 6: Endscreen nach Kampagne 5 (Sektor 5, Stufe 15).
        Nutzt dasselbe Victory-Video + die gleichen Buttons wie STAGE_CLEAR,
        zeigt aber das Kampagnen-Finale und den freigeschalteten NG+-Grad.
        WEITER fuehrt zurueck zur Karte - der naechste Einsatz laeuft mit
        skalierten Gegnern (rpg_config.NG_*)."""
        W, H = ui_kit.W, ui_kit.H
        self._ui = self._layout_clear()
        if self.victory_frames:
            ended = self._video_overlay(self.victory_frames, self.victory_timer)
            if not ended:
                self._draw_skip_hint()
                return
            overlay(SCREEN, 110)
        else:
            overlay(SCREEN, 170)
        gold = (255, 190, 76)
        neon_text(SCREEN, "KAMPAGNE 5 ABGESCHLOSSEN!", F(23), gold,
                  (W // 2, int(H * 0.36)), "midtop", 2)
        ng = int(getattr(self.modules, "ng_plus", 0))
        neon_text(SCREEN, f"DIE GALAXIE IST BEFREIT  ·  NEW GAME+ {ng} AKTIV",
                  F(15), WHITE, (W // 2, int(H * 0.36) + u(46)), "midtop", 1)
        neon_text(SCREEN, "Gegner und Bosse sind staerker - Beute und Cores "
                          "sind es auch.",
                  F(11), CYAN, (W // 2, int(H * 0.36) + u(80)), "midtop", 1)
        if self.last_xp_gain > 0:
            msg = f"+{self.last_xp_gain} XP  ·  SPIELER LVL {self.rpg.level}"
            neon_text(SCREEN, msg, F(13), CYAN,
                      (W // 2, int(H * 0.36) + u(106)), "midtop", 1)
        for bid, b in self._ui.items():
            draw_compact_btn(SCREEN, b, pressed=self._pressed(bid))

    # ================= PAKET 8: RPG-SCREENS =================

    @staticmethod
    def _reward_text(rw):
        """Kompakte Belohnungs-Anzeige aus einem Reward-Dict."""
        parts = []
        if rw.get("xp"):
            parts.append(f"+{rw['xp']} XP")
        if rw.get("credits"):
            parts.append(f"+{rw['credits']:,} Cr")
        if rw.get("quantum"):
            parts.append(f"+{rw['quantum']} {rpg_config.QUANTUM_NAME}")
        if rw.get("cores"):
            parts.append(f"+{rw['cores']} CORES")
        return "  ".join(parts)

    def _apply_rewards(self, rw, source=""):
        """Belohnungen gutschreiben (XP/QUANTUM -> rpg, Credits/Cores ->
        modules) und als Nachricht zusammenfassen. Einzige Gutschreib-
        stelle - damit bleiben alle Werte ueberall gleich."""
        if not rw:
            return
        parts = []
        if rw.get("xp"):
            ups, gained = self.rpg.add_xp(rw["xp"])
            parts.append(f"+{gained} XP")
            if ups:
                parts.append(f"LEVEL {self.rpg.level}!")
        if rw.get("credits"):
            self.modules.credits += int(rw["credits"])
            parts.append(f"+{rw['credits']:,} Cr")
        if rw.get("quantum"):
            self.rpg.add_quantum(rw["quantum"])
            parts.append(f"+{rw['quantum']} {rpg_config.QUANTUM_NAME}")
        if rw.get("cores"):
            self.modules.data_cores += int(rw["cores"])
            parts.append(f"+{rw['cores']} CORES")
        self.modules.save()
        self.show_message((source + ": " if source else "") + "  ".join(parts))

    def _draw_rpg_chips(self, y, extra=None):
        """PAKET 8: zentrale Ressourcen-Anzeige - Level (mit XP-Balken),
        CREDITS, DATA CORES, QUANTUM (+ optionaler Extra-Chip)."""
        W = ui_kit.W
        f = F(9)
        chips = [(f"LVL {self.rpg.level}", CYAN, self.rpg.xp_ratio()),
                 (f"CREDITS {self.credits_display():,}", GREEN, None),
                 (f"DATA CORES {self.modules.data_cores}", AMBER, None),
                 (f"{rpg_config.QUANTUM_NAME} {self.rpg.quantum}", VIOLET, None)]
        if extra:
            chips.append((extra[0], extra[1], None))
        widths = [f.size(c)[0] + u(18) for c, _col, _r in chips]
        total = sum(widths) + u(6) * (len(chips) - 1)
        if total > W - u(12):      # sehr schmale Screens: Extra-Chip weglassen
            chips = chips[:4]
            widths = widths[:4]
            total = sum(widths) + u(6) * 3
        x = (W - total) // 2
        for (c, col, ratio), wch in zip(chips, widths):
            crect = pygame.Rect(x, y, wch, u(20))
            glass_panel(SCREEN, crect, accent=col, radius=u(5), alpha=160, width=1)
            text(SCREEN, c, f, WHITE, (crect.centerx, crect.centery - u(2)), "center")
            if ratio is not None:
                br = crect.inflate(-u(8), 0)
                br.y = crect.bottom - u(4)
                br.height = u(2)
                pygame.draw.rect(SCREEN, DIM, br, border_radius=1)
                fill = pygame.Rect(br.x, br.y, int(br.w * max(0.0, min(1.0, ratio))), br.height)
                if fill.w > 0:
                    pygame.draw.rect(SCREEN, col, fill, border_radius=1)
            x += wch + u(6)

    # ---------------- PAKET 8: QUESTS (DAILY / WEEKLY) ----------------
    def _layout_quests(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = icon_touch()
        ui["q_back"] = Btn("q_back", pygame.Rect(m, m, isz, isz), icon="back", accent=CYAN)
        ui["snd_q"] = Btn("snd_q", pygame.Rect(W - m - isz, m, isz, isz),
                          icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        tabw = min(u(260), W - 2 * m - 2 * isz - u(20))
        taby = m + (isz - u(30)) // 2
        ui["q_tab_d"] = Btn("q_tab_d", pygame.Rect((W - tabw) // 2, taby, tabw // 2, u(30)),
                            "DAILY", "", CYAN)
        ui["q_tab_w"] = Btn("q_tab_w", pygame.Rect((W - tabw) // 2 + tabw // 2, taby,
                                                   tabw - tabw // 2, u(30)),
                            "WEEKLY", "", VIOLET)
        scope_key = "daily" if self.state == self.QUESTS_DAILY else "weekly"
        accent = CYAN if scope_key == "daily" else VIOLET   # 8.7: fuer qcard
        defs = self.quests.active_defs(scope_key)
        y = u(106)
        # PAKET 8.7 MOBILE: Karten hoeher (72 statt 56), groesserer Abhol-
        # Button - die komplette Karte ist zusaetzlich antippbar.
        ch, gap = u(72), u(10)
        cards = []
        for q in defs:
            rect = pygame.Rect(m, y, W - 2 * m, ch)
            cards.append((q["id"], rect))
            # PAKET 8: Abhol-Button je Quest (rechts in der Karte,
            # PAKET 8.7: daumenfreundlich vergroessert)
            ui["q_claim_" + q["id"]] = Btn("q_claim_" + q["id"],
                                           pygame.Rect(rect.right - u(126) - u(10),
                                                       rect.centery - u(19), u(126), u(38)),
                                           "ABHOLEN", "", GREEN, enabled=False)
            # PAKET 8.7: GANZE Karte als Touch-Ziel (muss NACH dem Claim-
            # Button in der Reihenfolge stehen - first_hit gewinnt sonst)
            ui["qcard_" + q["id"]] = Btn("qcard_" + q["id"], rect,
                                         "", "", accent, enabled=False)
            y += ch + gap
        # Abschlussbonus-Banner + Abhol-Button
        ui["q_bonus"] = Btn("q_bonus", pygame.Rect(m, y + u(4), W - 2 * m, u(52)),
                            "", "", AMBER)
        ui["q_bonus_go"] = Btn("q_bonus_go",
                               pygame.Rect(m + W - 2 * m - u(126) - u(10), y + u(10),
                                           u(126), u(38)),
                               "ABHOLEN", "", AMBER, enabled=False)
        self._quest_cards = cards
        return ui

    def draw_quests(self):
        W, H = ui_kit.W, ui_kit.H
        self.quests.refresh()
        self._ui = self._layout_quests()
        # Lesbarkeits-Band hinter der Kopfzeile (Backdrop-Logo abdunkeln)
        band = pygame.Surface((W, u(100)), pygame.SRCALPHA)
        band.fill((4, 9, 18, 205))
        SCREEN.blit(band, (0, 0))
        scope_key = "daily" if self.state == self.QUESTS_DAILY else "weekly"
        accent = CYAN if scope_key == "daily" else VIOLET
        title = "TAGESAUFGABEN" if scope_key == "daily" else "WOCHENAUFGABEN"
        # Titel links neben dem Zurueck-Button (Tabs sitzen zentriert)
        neon_text(SCREEN, title, F(14), accent,
                  (margin() + icon_touch() + u(12), margin() + icon_touch() // 2), "midleft", 1)
        self._draw_rpg_chips(u(64))
        # Tab-Umschalter (aktiv-Zustand je Bereich)
        for bid in ("q_tab_d", "q_tab_w"):
            b = self._ui[bid]
            b.active = (bid == "q_tab_d") == (scope_key == "daily")
            ui_kit.draw_mini_btn(SCREEN, b, pressed=self._pressed(bid))
        # Reset-Hinweis (lokale Systemzeit)
        now = datetime.datetime.now()
        if scope_key == "daily":
            nxt = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0,
                                                             second=0, microsecond=0)
            left = int((nxt - now).total_seconds())
            info = f"RESET UM 00:00 LOKAL - IN {left // 3600}:{(left % 3600) // 60:02d} H"
        else:
            days = (7 - now.isoweekday()) % 7
            when = "HEUTE" if days == 0 else f"IN {days} TAGEN"
            info = f"RESET MONTAG 00:00 LOKAL ({when})"
        text(SCREEN, info, F(9), MUTED, (W // 2, u(94)), "center")
        # Quest-Karten
        for qid, rect in self._quest_cards:
            q = next((x for x in self.quests.active_defs(scope_key) if x["id"] == qid),
                     None)
            if q is None:
                continue
            prog = self.quests.progress_of(scope_key, qid)
            claimed = self.quests.is_claimed(scope_key, qid)
            complete = prog >= q["goal"]
            glass_panel(SCREEN, rect, accent=accent, radius=u(6),
                        alpha=150 if not claimed else 90, width=1)
            name_f = fit_font(q["name"], 13, rect.w - u(230))
            text(SCREEN, q["name"], name_f,
                 MUTED if claimed else (accent if complete else WHITE),
                 (rect.x + u(10), rect.y + u(8)), "topleft")
            desc_f = fit_font(q["desc"], 10, rect.w - u(230))
            text(SCREEN, q["desc"], desc_f, DIM if claimed else WHITE,
                 (rect.x + u(10), rect.y + u(28)), "topleft")
            text(SCREEN, self._reward_text(q["rewards"]), F(10), AMBER,
                 (rect.x + u(10), rect.bottom - u(10)), "midleft")
            # Fortschrittsbalken + Zaehler
            br = pygame.Rect(rect.x + u(10), rect.bottom - u(26), rect.w - u(240), u(7))
            pygame.draw.rect(SCREEN, (14, 24, 38), br, border_radius=3)
            k = max(0.0, min(1.0, prog / float(q["goal"])))
            fill = pygame.Rect(br.x, br.y, int(br.w * k), br.height)
            if fill.w > 0:
                pygame.draw.rect(SCREEN, GREEN if complete else accent, fill, border_radius=3)
            text(SCREEN, f"{prog}/{q['goal']}", F(9), MUTED,
                 (br.right + u(6), br.centery), "midleft")
            # Abhol-Button rechts (PAKET 8.7: ganze Karte antippbar)
            cb = self._ui.get("q_claim_" + qid)
            card_btn = self._ui.get("qcard_" + qid)
            claimable = complete and not claimed
            if cb is not None:
                cb.enabled = claimable
            if card_btn is not None:
                card_btn.enabled = claimable
            if claimed:
                text(SCREEN, "ERHALTEN", F(11), GREEN,
                     (cb.rect.centerx, cb.rect.centery), "center")
            elif complete:
                k = 0.5 + 0.5 * math.sin(self.elapsed * 4.0)
                glow = radial_glow_k(GREEN, u(46), 0.10 + 0.08 * k)
                SCREEN.blit(glow, glow.get_rect(center=cb.rect.center),
                            special_flags=pygame.BLEND_ADD)
                ui_kit.draw_mini_btn(SCREEN, cb, pressed=self._pressed(cb.id))
            else:
                ui_kit.draw_mini_btn(SCREEN, cb, pressed=self._pressed(cb.id))
        # Abschlussbonus
        scope = self.quests.daily if scope_key == "daily" else self.quests.weekly
        bb = self._ui["q_bonus"]
        ready = self.quests.all_complete(scope_key) and not scope["bonus_claimed"]
        bonus = rpg_config.DAILY_BONUS if scope_key == "daily" else rpg_config.WEEKLY_BONUS
        glass_panel(SCREEN, bb.rect, accent=AMBER,
                    radius=u(6), alpha=150 if ready else 90, width=1)
        text(SCREEN, self.quests.bonus_ready(scope_key), F(11),
             AMBER if ready else MUTED, (bb.rect.x + u(10), bb.rect.y + u(10)), "topleft")
        text(SCREEN, self._reward_text(bonus) + ("  - ALLE AUFGABEN ERFUELLT" if ready
                                                 else "  - ERFUELLE ALLE AUFGABEN"),
             F(9), DIM if not ready else WHITE, (bb.rect.x + u(10), bb.rect.y + u(26)), "topleft")
        if scope["bonus_claimed"]:
            text(SCREEN, "ERHALTEN", F(10), GREEN, (bb.rect.right - u(60), bb.rect.centery), "center")
        else:
            bb.enabled = ready
            self._ui["q_bonus_go"].enabled = ready
            ui_kit.draw_mini_btn(SCREEN, self._ui["q_bonus_go"],
                                 pressed=self._pressed("q_bonus_go"))
        # Zurueck + Sound
        for bid in ("q_back", "snd_q"):
            draw_compact_icon_btn(SCREEN, self._ui[bid], pressed=self._pressed(bid))

    # ---------------- PAKET 8: BESCHWOERUNG ----------------
    def _layout_summon(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = icon_touch()
        ui["sm_back"] = Btn("sm_back", pygame.Rect(m, m, isz, isz), icon="back", accent=CYAN)
        ui["snd_s"] = Btn("snd_s", pygame.Rect(W - m - isz, m, isz, isz),
                          icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        tabw = min(u(320), W - 2 * m - 2 * isz - u(20))
        taby = m + (isz - u(30)) // 2
        ui["sm_tab_sum"] = Btn("sm_tab_sum", pygame.Rect((W - tabw) // 2, taby, tabw // 2, u(30)),
                               "BESCHWOEREN", "", MAGENTA)
        ui["sm_tab_col"] = Btn("sm_tab_col", pygame.Rect((W - tabw) // 2 + tabw // 2, taby,
                                                         tabw - tabw // 2, u(30)),
                               "SAMMLUNG", "", AMBER)
        if self._summon_tab == "summon":
            bw2 = min(u(190), (W - 2 * m - u(24)) // 2)
            ui["sm_pull1"] = Btn("sm_pull1", pygame.Rect(m, H - u(66), bw2, u(40)),
                                 f"BESCHWOEREN 1x", f"{summon_system.SummonSystem.cost('single')} CORES",
                                 MAGENTA)
            ui["sm_pull10"] = Btn("sm_pull10", pygame.Rect(W - m - bw2, H - u(66), bw2, u(40)),
                                  f"BESCHWOEREN 10x", f"{summon_system.SummonSystem.cost('multi')} CORES",
                                  VIOLET)
        if self._summon_result:
            ui["sm_close"] = Btn("sm_close", pygame.Rect(W - m - u(34), u(100), u(34), u(34)),
                                 icon="close", accent=RED)
        return ui

    def _do_summon(self, kind):
        """Beschwörung ausfuehren: Cores abziehen, Ergebnis vorbereiten,
        Duplikat-Credits gutschreiben. Kosten/Kanzahlen kommen aus rpg_config."""
        try:
            res = self.summon.pull(self.modules.data_cores, kind)
        except ValueError as e:
            self.show_message(str(e))
            return
        self.modules.data_cores -= res["spent"]
        if res["credits_back"]:
            self.modules.credits += res["credits_back"]
        self.modules.save()
        self._summon_result = res
        self._summon_tab = "summon"
        # PAKET 8.5/8.6: Zeremonie-Tier nach bester Seltenheit der Ziehung;
        # fuer die Offenbarung wird die beste Einheit gross inszeniert.
        order = rpg_config.RARITY_ORDER
        best_item = max(res["results"],
                        key=lambda i: order.index(
                            rpg_config.UNITS_BY_KEY[i["key"]]["rarity"]))
        best_r = rpg_config.UNITS_BY_KEY[best_item["key"]]["rarity"]
        self._ceremony = {"t0": pygame.time.get_ticks(),
                          "tier": "epic" if order.index(best_r) >= 2
                          else "normal",
                          "best_key": best_item["key"],
                          "count": len(res["results"]),
                          "new": bool(best_item["new"]),
                          "sc": {}}   # Scale-Cache (Smoothscale ist teuer)
        SFX.play("upgrade")

    # ---------------- PAKET 8.6: BESCHWOERUNGS-ZEREMONIE ----------------
    # Fuenf inszenierte Phasen: KONVERGENZ (dunkle Kammer, Energie
    # sammelt sich) -> MATERIALISIERUNG (die Kapsel flickert auf das
    # Podest - vorher ist sie bewusst NICHT sichtbar) -> AUFLADUNG
    # (Streifen glimmen, Zittern steigt) -> BURST (Energie-Blitz aus dem
    # Nutzer-Sheet, Kapsel loest sich auf) -> OFFENBARUNG (die beste
    # gezogene Einheit steigt auf, Banner mit Name + Seltenheit).

    def _ceremony_ms(self, tier):
        return (rpg_config.CEREMONY_MS_EPIC if tier == "epic"
                else rpg_config.CEREMONY_MS_NORMAL)

    def _cs_scaled(self, img, w, h):
        """Smoothscale mit Cache pro Zeremonie (sonst 60x/s neu skalieren)."""
        key = (id(img), w, h)
        c = self._ceremony["sc"]
        out = c.get(key)
        if out is None:
            if len(c) > 96:
                c.clear()
            out = pygame.transform.smoothscale(img, (max(2, w), max(2, h)))
            c[key] = out
        return out

    def _draw_summon_ceremony(self):
        """PAKET 8.6: Inszenierte Zeremonie nach jeder Ziehung. Liefert
        True, solange sie laeuft - danach erscheint die normale
        Ergebnis-Ansicht. Beliebiger Tipp ueberspringt."""
        if not self._ceremony:
            return False
        W, H = ui_kit.W, ui_kit.H
        self._ui = {}          # keine Buttons klickbar waehrend der Zeremonie
        tier = self._ceremony["tier"]
        total = self._ceremony_ms(tier)
        t = pygame.time.get_ticks() - self._ceremony["t0"]
        if self._ceremony.get("skip"):
            t = total
        if t >= total:
            self._ceremony = None
            return False
        cs = summon_system.ceremony_assets(tier, (W, H))
        prog = t / total
        accent = cs["accent"]
        epic = (tier == "epic")
        P1, P2, P3, P4 = (rpg_config.CEREMONY_P1_KONVERGENZ,
                          rpg_config.CEREMONY_P2_MATERIAL,
                          rpg_config.CEREMONY_P3_AUFLADUNG,
                          rpg_config.CEREMONY_P4_BURST)

        # Ankerpunkte: Kapsel-Podest (normal) bzw. Portal-Mitte (epic)
        if epic:
            ax, ay = int(W * 0.503), int(H * 0.46)
            floor_y = int(H * 0.625)
        else:
            ax, ay = W // 2, int(H * 0.545)
            floor_y = int(H * 0.615)

        def put(img, center, w, h, alpha=255, additive=False):
            if img is None or alpha <= 0 or w < 3 or h < 3:
                return
            s = self._cs_scaled(img, int(w), int(h))
            if alpha < 255:
                s = s.copy()
                s.set_alpha(int(max(0, min(255, alpha))))
            SCREEN.blit(s, s.get_rect(center=(int(center[0]), int(center[1]))),
                        special_flags=pygame.BLEND_ADD if additive else 0)

        # --- Screen-Shake (steigt bis zum Burst, klingt danach ab) ---
        if prog < P3:
            shake = 0.0
        elif prog < P4:
            shake = 3.0 * (prog - P3) / max(0.0001, P4 - P3)
        else:
            shake = 7.0 * max(0.0, 1.0 - (prog - P4)
                              / max(0.0001, 1.0 - P4))
        ox = int(random.uniform(-shake, shake))
        oy = int(random.uniform(-shake, shake))

        # --- Kulisse + Dunkelheits-Regie (Kapsel bleibt zuerst verborgen) ---
        if epic:
            if prog < P2:
                dark = int(228 - 92 * (prog / P2))
            elif prog < P3:
                dark = int(136 - 58 * ((prog - P2) / max(0.0001, P3 - P2)))
            else:
                dark = int(78 - 78 * min(1.0, (prog - P3)
                                         / max(0.0001, 1.0 - P3)))
        else:
            if prog < P1:
                dark = int(215 - 30 * (prog / P1))
            elif prog < P2:
                dark = 185
            elif prog < P3:
                dark = int(185 - 150 * ((prog - P2) / max(0.0001, P3 - P2)))
            else:
                dark = int(35 * max(0.0, 1.0 - (prog - P3)
                                    / max(0.0001, 1.0 - P3)))
        SCREEN.blit(cs["backdrop"], (ox, oy))
        if dark > 0:
            dk = pygame.Surface((W, H), pygame.SRCALPHA)
            dk.fill((2, 4, 9, dark))
            SCREEN.blit(dk, (0, 0))

        # --- Boden-Glow + rotierender Runenring (Phasen 1-3) ---
        if prog < P4:
            rg = prog / P4
            put(cs["glow"], (ax, floor_y - u(6)), u(220 + 60 * rg),
                u(110 + 30 * rg), alpha=int(70 + 60 * rg), additive=True)
            ring_r = u(150)
            rr = pygame.Rect(0, 0, ring_r, int(ring_r * 0.42))
            rr.center = (ax, floor_y - u(4))
            pygame.draw.arc(SCREEN, accent, rr, t / 300.0,
                            t / 300.0 + 1.9, max(2, u(2)))
            pygame.draw.arc(SCREEN, accent, rr.inflate(u(46), u(20)),
                            -t / 230.0, -t / 230.0 + 1.2,
                            max(1, u(1) + 1))

        # --- Funken: konvergieren in Phase 1, kreisen danach ---
        embers = cs["embers"]
        n_e = min(11, max(6, W // 110))
        for k in range(n_e):
            base_a = k * (2 * math.pi / n_e) + t / 900.0
            if prog < P2:
                # spiralförmig nach innen
                kph = min(1.0, prog / P2)
                rad = W * (0.46 - 0.38 * kph) * (0.85 + 0.15 * math.sin(k * 2.1))
                alpha = int(80 + 130 * kph)
                sp_scale = 0.30 + 0.16 * math.sin(t / 170.0 + k)
                ex = ax + math.cos(base_a * 2.2) * rad
                ey = floor_y - u(10) + math.sin(base_a * 2.2) * rad * 0.42 \
                     - u(60) * kph
            else:
                rad = u(92 + 22 * math.sin(t / 260.0 + k))
                ang = base_a + t / (340.0 + 12.0 * (k % 3))
                ex = ax + math.cos(ang) * rad
                ey = ay + math.sin(ang) * rad * (0.55 if epic else 0.62)
                alpha = 120 if prog < P4 else int(120 * max(
                    0.0, 1.0 - (prog - P4) / max(0.0001, 1.0 - P4)))
                sp_scale = 0.30 + 0.16 * math.sin(t / 150.0 + k)
            sp = embers[(t // 150 + k) % len(embers)]
            sw = sp.get_width() * sp_scale
            sh = sp.get_height() * sw / max(1, sp.get_width())
            put(sp, (ex, ey), sw, sh, alpha=alpha)

        # --- Phasen 2/3: Kapsel (normal) bzw. Portal-Swirl (epic) ---
        if epic:
            e_frames = cs["energy_pm"]      # praemultipliziert (BLEND_ADD)
            if prog < P2:
                kph = prog / P2
                put(e_frames[0], (ax, ay), W * (0.16 + 0.10 * kph),
                    W * (0.16 + 0.10 * kph) * 1.25,
                    alpha=int(90 + 110 * kph), additive=True)
            elif prog < P4:
                kph = (prog - P2) / max(0.0001, P4 - P2)
                idx = (t // 160) % len(e_frames)
                sc = 0.34 + 0.34 * kph + 0.05 * math.sin(t / 110.0)
                put(e_frames[idx], (ax, ay), W * sc, W * sc * 1.22,
                    alpha=int(170 + 70 * math.sin(t / 90.0)), additive=True)
                # Blitz-Bögen (zitternde Polylinien)
                if prog > P3:
                    for b in range(3):
                        sxp = ax + random.uniform(-W * 0.16, W * 0.16)
                        syp = ay - random.uniform(H * 0.10, H * 0.24)
                        pts = [(sxp, syp)]
                        for seg in range(4):
                            fseg = (seg + 1) / 4.0
                            pts.append((sxp + (ax - sxp) * fseg
                                        + random.uniform(-14, 14),
                                        syp + (ay - syp) * fseg
                                        + random.uniform(-10, 10)))
                        pygame.draw.lines(SCREEN, accent, False, pts, 2)
        else:
            caps = cs["capsules"]
            cap = caps[(t // 210) % len(caps)]
            cap_h = u(270)
            cap_w = cap_h * cap.get_width() / max(1, cap.get_height())
            cap_c = (ax, floor_y - u(6) - cap_h * 0.5)   # steht AUF dem Podest
            if prog >= P2 and prog < P4:
                kph = (prog - P2) / max(0.0001, P4 - P2)
                if prog < P3:
                    # Materialisierung: Flicker + leichtes Jitter
                    flick = ((t / 1000.0 * 9.0) % 1.0) < 0.72 or kph > 0.55
                    ca = int(200 * min(1.0, kph * 2.4)) if flick else 30
                    cs_scale = 0.92 + 0.08 * min(1.0, kph * 1.6)
                    jx = random.uniform(-2.5, 2.5) if not flick else 0
                    put(cap, (cap_c[0] + jx, cap_c[1]), cap_w * cs_scale,
                        cap_h * cs_scale, alpha=ca)
                    put(cs["glow"], (ax, floor_y - u(20)), u(180),
                        u(90), alpha=int(50 + 60 * kph), additive=True)
                else:
                    # Aufladung: Streifen glimmen, Kapsel zittert
                    j = 1.0 + 0.06 * math.sin(t / 45.0)
                    put(cap, (ax + random.uniform(-3, 3),
                              cap_c[1] + random.uniform(-2, 2)),
                        cap_w * j, cap_h * j, alpha=255)
                    put(cs["glow"], (cap_c[0], cap_c[1]), u(230 + 60 * math.sin(t / 80.0)),
                        u(150), alpha=int(90 + 70 * math.sin(t / 90.0)),
                        additive=True)
            elif prog >= P4:
                # Burst: Kapsel loest sich auf (schneller Alpha-Abfall)
                kph = (prog - P4) / max(0.0001, 1.0 - P4)
                put(cap, (cap_c[0], cap_c[1] - u(30) * kph), cap_w,
                    cap_h, alpha=int(255 * max(0.0, 1.0 - kph * 3.0)))

        # --- Burst (Phase 4): Nutzer-Flash + Weissblende ---
        if P4 <= prog < 1.0:
            kph = (prog - P4) / max(0.0001, 1.0 - P4)
            fp = min(1.0, kph / 0.35)
            fw = W * (0.30 + 1.15 * fp)
            fh = fw * cs["flash_pm"].get_height() / max(1, cs["flash_pm"].get_width())
            put(cs["flash_pm"], (ax, ay), fw, fh,
                alpha=int(250 * (1.0 - abs(fp * 2 - 1))) if fp < 1.0 else 0,
                additive=True)
            white = int(215 * math.sin(min(1.0, kph / 0.45) * math.pi))
            if white > 0:
                ws = pygame.Surface((W, H), pygame.SRCALPHA)
                ws.fill((238, 244, 255, white))
                SCREEN.blit(ws, (0, 0))

        # --- Offenbarung (ab P4-Grenze): Einheit steigt auf ---
        if prog >= P4:
            kph = (prog - P4) / max(0.0001, 1.0 - P4)          # 0..1
            unit = rpg_config.UNITS_BY_KEY.get(self._ceremony["best_key"])
            rcol = rpg_config.RARITY_INFO[unit["rarity"]]["color"] \
                if unit else accent
            spr = self.summon.sprite(self._ceremony["best_key"], u(320))
            if spr is not None:
                sh = u(290)
                sw = sh * spr.get_width() / max(1, spr.get_height())
                rise = (1.0 - min(1.0, kph / 0.42)) ** 2        # ease-out
                rc = (ax, floor_y - u(4) - sh * 0.5 + u(46) * rise)
                # Rarity-Strahlen hinter der Einheit
                rays_a = int(70 * min(1.0, kph * 2.5))
                if rays_a > 0:
                    ray_s = pygame.Surface((W, H), pygame.SRCALPHA)
                    rcx, rcy = int(rc[0]), int(rc[1])
                    for i in range(10):
                        a = t / 2600.0 + i * math.pi / 5.0
                        ln = int(max(W, H) * 0.42)
                        dx, dy = math.cos(a), math.sin(a)
                        pygame.draw.line(ray_s, (*rcol, rays_a),
                                         (rcx - dx * ln, rcy - dy * ln),
                                         (rcx + dx * ln, rcy + dy * ln),
                                         max(2, u(3)))
                    SCREEN.blit(ray_s, (0, 0),
                                special_flags=pygame.BLEND_ADD)
                rg = cs["glow"]
                put(rg, (rc[0], rc[1] + u(30)), u(430), u(240),
                    alpha=int(90 * min(1.0, kph * 2.0)), additive=True)
                put(spr, (rc[0], rc[1] + u(30) * rise), sw, sh,
                    alpha=int(255 * min(1.0, kph * 3.0)))
            # Banner mit Name + Seltenheit
            if unit is not None:
                bw = min(W - 2 * margin(), u(400))
                brect = pygame.Rect((W - bw) // 2, H - u(120), bw, u(58))
                ba = int(235 * min(1.0, max(0.0, (kph - 0.25) / 0.3)))
                if ba > 0:
                    panel_s = pygame.Surface(brect.size, pygame.SRCALPHA)
                    panel_s.fill((6, 10, 18, ba))
                    pygame.draw.rect(panel_s, (*rcol, ba),
                                     panel_s.get_rect(), 2,
                                     border_radius=u(8))
                    SCREEN.blit(panel_s, brect.topleft)
                    nf = fit_font(unit["name"], 13, brect.w - u(20))
                    text(SCREEN, unit["name"], nf, rcol,
                         (brect.centerx, brect.y + u(17)), "center")
                    sub = rpg_config.RARITY_INFO[unit["rarity"]]["label"]
                    if self._ceremony["count"] > 1:
                        sub += f"  ·  BESTE VON {self._ceremony['count']} ZIEHUNGEN"
                    if self._ceremony["new"]:
                        sub += "  ·  NEU!"
                    sf = fit_font(sub, 9, brect.w - u(16))
                    text(SCREEN, sub, sf, WHITE if not self._ceremony["new"]
                         else GREEN, (brect.centerx, brect.y + u(40)), "center")

        text(SCREEN, "TIPPEN = ÜBERSPRINGEN", F(9), ICE,
             (W // 2, H - u(26)), "center")
        return True

    # ---------------- AUFTRAG 8: CHAMPION-AUSRUESTUNG (SAMMLUNG) --------
    def _collection_card_rects(self):
        """Kartengeometrie der Sammlungs-Ansicht. Zeichnung und Tap-
        Auswertung nutzen dieselbe Rechnung (keine Doppel-Pflege)."""
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        col = self.summon.collection()
        area = pygame.Rect(m, u(116), W - 2 * m, H - u(116) - u(16))
        cols = max(3, area.w // u(150))
        rows = (len(col) + cols - 1) // cols
        cw = area.w // cols - u(6)
        ch = min(u(104), (area.h - u(6) * (rows - 1)) // rows)
        out = []
        for i, entry in enumerate(col):
            cx = area.x + (i % cols) * (cw + u(6))
            cy = area.y + (i // cols) * (ch + u(6))
            out.append((entry, pygame.Rect(cx, cy, cw, ch)))
        return out

    def _collection_hero_hit(self, pos):
        """AUFTRAG 8: Key der angetippten, besessenen HELDEN-Karte
        (Sammlung) oder None. Drohnen und unbekannte Karten sind keine
        Ziele."""
        for entry, rect in self._collection_card_rects():
            unit = entry["unit"]
            if rect.collidepoint(pos) and entry["owned"] and unit.get("hero"):
                return unit["key"]
        return None

    def _toggle_equip(self, key):
        """AUFTRAG 8: Helden an-/ablegen (Tap auf die Sammlungs-Karte).
        Freier Slot = erster leerer; bereits ausgeruestet = ablegen.
        Danach Sync (aktive Stats/Faehigkeiten) + Spielstand sichern."""
        einheiten = rpg_config.UNITS_BY_KEY
        slot = next((i for i, k in enumerate(self.summon.equipped)
                     if k == key), None)
        if slot is not None:
            self.summon.unequip(slot)
            self.show_message(f"{einheiten[key]['name']} ABGERÜSTET")
        else:
            freie = next((i for i, k in enumerate(self.summon.equipped)
                          if k is None), None)
            if freie is None:
                self.show_message("ALLE CHAMPION-SLOTS BESETZT "
                                  "- erst einen Helden ablegen")
                return
            try:
                self.summon.equip(freie, key)
            except ValueError as e:
                self.show_message(str(e))
                return
            st = einheiten[key].get("stats") or {}
            msg = (f"{einheiten[key]['name']} AUSGERÜSTET (SLOT {freie + 1})"
                   f"  ·  Schaden +{int((float(st.get('dmg_mult', 1.0)) - 1.0) * 100)}%"
                   f"  ·  +{int(float(st.get('hp', 0.0)))} Huelle")
            sk = rpg_config.CHAMPION_SKILLS.get(key)
            if sk:
                msg += f"  ·  {sk['name']}"
            self.show_message(msg)
        self._sync_modules_to_combat()
        self.modules.save()               # equipped landet im RPG-Block
        SFX.play("click", 0.5)

    def draw_summon(self):
        W, H = ui_kit.W, ui_kit.H
        if self._draw_summon_ceremony():
            return
        self._ui = self._layout_summon()
        # Lesbarkeits-Band hinter der Kopfzeile (Backdrop-Logo abdunkeln)
        band = pygame.Surface((W, u(100)), pygame.SRCALPHA)
        band.fill((4, 9, 18, 205))
        SCREEN.blit(band, (0, 0))
        self._draw_rpg_chips(u(64))
        # Titel links neben dem Zurueck-Button (Tabs sitzen zentriert)
        neon_text(SCREEN, "BESCHWOERUNG", F(14), MAGENTA,
                  (margin() + icon_touch() + u(12), margin() + icon_touch() // 2), "midleft", 1)
        for bid in ("sm_tab_sum", "sm_tab_col"):
            b = self._ui[bid]
            b.active = (bid == ("sm_tab_sum" if self._summon_tab == "summon"
                                else "sm_tab_col"))
            ui_kit.draw_mini_btn(SCREEN, b, pressed=self._pressed(bid))
        m = margin()
        if self._summon_tab == "summon":
            # Kosten + transparente Chancen (aus rpg_config)
            text(SCREEN, f"KOSTEN: {summon_system.SummonSystem.cost('single')} DATA CORES JE ZIEHUNG"
                         f"  ·  10x FUER {summon_system.SummonSystem.cost('multi')} CORES",
                 F(10), WHITE, (W // 2, u(96)), "center")
            rates = "  ·  ".join(f"{rpg_config.RARITY_INFO[r]['label']} {int(k * 100)}%"
                                 for r, k in summon_system.SummonSystem.rates())
            text(SCREEN, "CHANCEN: " + rates, F(9), MUTED, (W // 2, u(112)), "center")
            # Ergebnisbereich
            area = pygame.Rect(m, u(126), W - 2 * m, H - u(126) - u(78))
            res = self._summon_result
            if res:
                n = len(res["results"])
                cols = max(1, min(n, area.w // u(96)))
                cw = area.w // cols - u(6)
                ch = u(96)
                for i, item in enumerate(res["results"]):
                    cx = area.x + (i % cols) * (cw + u(6))
                    cy = area.y + (i // cols) * (ch + u(6))
                    card = pygame.Rect(cx, cy, cw, ch)
                    unit = rpg_config.UNITS_BY_KEY[item["key"]]
                    rar = rpg_config.RARITY_INFO[unit["rarity"]]
                    glass_panel(SCREEN, card, accent=rar["color"], radius=u(6),
                                alpha=170 if item["new"] else 120, width=1)
                    # PAKET 8.5: Helden bekommen ihr Kopfbild, Drohnen den Sprite
                    port = summon_system.SummonSystem.portrait(item["key"], u(52))
                    if port is not None:
                        img = port
                        if img.get_width() > card.w - u(8):
                            img = pygame.transform.smoothscale(
                                img, (card.w - u(8), u(52)))
                        SCREEN.blit(img, img.get_rect(
                            center=(card.centerx, card.y + u(30))))
                    else:
                        spr = self.summon.sprite(item["key"], u(46))
                        if spr:
                            SCREEN.blit(spr, spr.get_rect(
                                center=(card.centerx, card.y + u(30))))
                    nf = fit_font(unit["name"], 9, card.w - u(8))
                    text(SCREEN, unit["name"], nf, rar["color"],
                         (card.centerx, card.y + u(56)), "center")
                    # SCHRITT 2: Passiv-Bonus der Einheit auf der Karte
                    pf = fit_font(summon_system.SummonSystem.passiv_label(unit["rarity"]),
                                  8, card.w - u(6))
                    text(SCREEN, summon_system.SummonSystem.passiv_label(unit["rarity"]),
                         pf, GREEN, (card.centerx, card.y + u(68)), "center")
                    if item["new"]:
                        text(SCREEN, "NEU!", F(9), GREEN, (card.centerx, card.bottom - u(9)), "center")
                    elif item["dup_credits"]:
                        df = fit_font(f"DUPLIKAT +{item['dup_credits']:,} Cr",
                                      8, card.w - u(6))
                        text(SCREEN, f"DUPLIKAT +{item['dup_credits']:,} Cr", df, MUTED,
                             (card.centerx, card.bottom - u(9)), "center")
                if res["credits_back"]:
                    text(SCREEN, f"DUPLIKAT-ENTSCHAEDIGUNG: +{res['credits_back']:,} CREDITS",
                         F(9), GREEN, (W // 2, area.bottom + u(4)), "center")
            else:
                text(SCREEN, "ZIEHE EINHEITEN, UM DEINE SAMMLUNG ZU ERWEITERN.",
                     F(10), MUTED, (area.centerx, area.centery - u(20)), "center")
                text(SCREEN, "DUPLIKATE WERDEN ALS CREDITS ERSATZ AUSGEZAHLT.",
                     F(9), DIM, (area.centerx, area.centery + u(2)), "center")
            # Zieh-Buttons
            for bid in ("sm_pull1", "sm_pull10"):
                b = self._ui.get(bid)
                if b is not None:
                    b.enabled = self.modules.data_cores >= summon_system.SummonSystem.cost(
                        "single" if bid == "sm_pull1" else "multi")
                    ui_kit.draw_mini_btn(SCREEN, b, pressed=self._pressed(bid))
        else:
            # Sammlung
            col = self.summon.collection()
            owned_unique = self.summon.unique_owned()
            text(SCREEN, f"SAMMLUNG: {owned_unique}/{len(rpg_config.ALL_PULLABLE)} EINHEITEN"
                         f"  ·  {self.summon.total_owned()} GEZOGEN",
                 F(10), WHITE, (W // 2, u(96)), "center")
            # AUFTRAG 8: Kartengeometrie geteilt mit der Tap-Auswertung
            # (_collection_card_rects) - Zeichnen und Ausruesten rechnen
            # identisch.
            for entry, card in self._collection_card_rects():
                unit, count = entry["unit"], entry["count"]
                rar = rpg_config.RARITY_INFO[unit["rarity"]]
                glass_panel(SCREEN, card, accent=rar["color"] if entry["owned"] else DIM,
                            radius=u(6), alpha=170 if entry["owned"] else 80, width=1)
                # AUFTRAG 8: Helden-Karten - Status und Ausruestung sichtbar
                ist_held = bool(unit.get("hero")) and entry["owned"]
                slot_nr = (self.summon.equipped.index(unit["key"]) + 1
                           if unit["key"] in self.summon.equipped else 0)
                if ist_held and slot_nr:
                    pygame.draw.rect(SCREEN, AMBER, card, 2, border_radius=u(6))
                spr = self.summon.sprite(unit["key"], u(44))
                if spr:
                    img = spr
                    if not entry["owned"]:
                        img = spr.copy()
                        img.set_alpha(60)   # dunkle Silhouette (unbekannt)
                    SCREEN.blit(img, img.get_rect(center=(card.centerx, card.y + u(28))))
                    if not entry["owned"]:
                        text(SCREEN, "?", F(14), MUTED, (card.centerx, card.y + u(28)), "center")
                nf = fit_font(unit["name"], 9, card.w - u(8))
                text(SCREEN, unit["name"] if entry["owned"] else "UNBEKANNT", nf,
                     rar["color"] if entry["owned"] else MUTED,
                     (card.centerx, card.y + u(54)), "center")
                if ist_held:
                    # AUFTRAG 8: Seltenheitszeile zeigt die Faehigkeit
                    _sk = rpg_config.CHAMPION_SKILLS.get(unit["key"])
                    _lab = (f'{rar["label"]} · {_sk["name"]}'
                            if _sk else rar["label"])
                    _f = fit_font(_lab, 8, card.w - u(6))
                    text(SCREEN, _lab, _f, rar["color"],
                         (card.centerx, card.y + u(66)), "center")
                else:
                    text(SCREEN, rar["label"], F(8),
                         rar["color"] if entry["owned"] else DIM,
                         (card.centerx, card.y + u(66)), "center")
                # SCHRITT 2: Passiv-Bonus je Karte (auch bei unbekannten
                # Einheiten sichtbar - die Seltenheit ist ja sichtbar).
                # AUFTRAG 8: Helden zeigen stattdessen ihre aktiven Stats.
                _zeile = (summon_system.SummonSystem.champion_stats_text(unit)
                          if ist_held
                          else summon_system.SummonSystem.passiv_label(unit["rarity"]))
                pf = fit_font(_zeile, 8, card.w - u(6))
                text(SCREEN, _zeile, pf,
                     GREEN if entry["owned"] else DIM,
                     (card.centerx, card.y + u(78)), "center")
                if ist_held and slot_nr:
                    _bl = f"SLOT {slot_nr} · AKTIV"
                    _bf = fit_font(_bl, 8, card.w - u(6))
                    text(SCREEN, _bl, _bf, AMBER,
                         (card.centerx, card.bottom - u(9)), "center")
                elif ist_held:
                    _bl = "TIPPEN = AUSRÜSTEN"
                    _bf = fit_font(_bl, 8, card.w - u(6))
                    text(SCREEN, _bl, _bf, MUTED,
                         (card.centerx, card.bottom - u(9)), "center")
                elif entry["owned"]:
                    text(SCREEN, f"x{count}", F(9), WHITE,
                         (card.centerx, card.bottom - u(9)), "center")
        cb = self._ui.get("sm_close")
        if cb is not None:
            draw_compact_icon_btn(SCREEN, cb, pressed=self._pressed("sm_close"))
        for bid in ("sm_back", "snd_s"):
            draw_compact_icon_btn(SCREEN, self._ui[bid], pressed=self._pressed(bid))

    def draw_intro(self):
        W, H = ui_kit.W, ui_kit.H
        self._ui = self._layout_intro()
        ended = self._video_overlay(self.intro_frames, self.intro_timer)
        if not ended:
            self._draw_skip_hint()

    def _draw_skip_hint(self):
        W, H = ui_kit.W, ui_kit.H
        f = F(11)
        label = "TIPPEN = ÜBERSPRINGEN"
        rect = f.size(label)
        bar = pygame.Rect((W - rect[0]) // 2 - u(14), H - u(54) - u(10), rect[0] + u(28), u(34))
        pygame.draw.rect(SCREEN, (0, 0, 0), bar, border_radius=u(8))
        pygame.draw.rect(SCREEN, (60, 80, 100), bar, 1, border_radius=u(8))
        text(SCREEN, label, f, ICE, bar.center, "center")

    def draw_loading(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        pw = min(W - 2 * m, u(460))
        rect = pygame.Rect((W - pw) // 2, int(H * 0.38), pw, u(120))
        panel(SCREEN, rect, fill=(3, 8, 17), border=(16, 42, 60), radius=u(12))
        neon_text(SCREEN, "SYSTEM INITIALIZATION", F(14), WHITE,
                  (rect.centerx, rect.y + u(14)), "midtop", 1)
        prog = min(1.0, self.loading_time / 2.5)
        bar = pygame.Rect(rect.x + u(30), rect.y + u(64), pw - u(60), u(14))
        pygame.draw.rect(SCREEN, (10, 25, 40), bar, border_radius=u(6))
        pygame.draw.rect(SCREEN, CYAN, (bar.x, bar.y, int(bar.w * prog), bar.h), border_radius=u(6))
        pygame.draw.rect(SCREEN, LINE, bar, 2, border_radius=u(6))
        text(SCREEN, f"LOADING… {int(prog * 100)}%", F(10), CYAN,
             (rect.centerx, rect.y + u(90)), "midtop")
        if ui_kit.ROTATED:
            text(SCREEN, "QUERFORMAT AKTIV - GERÄT GEBENENFALLS DREHEN", F(9), MUTED,
                 (W // 2, H - u(30)), "midtop")

    def _draw_message(self):
        W, H = ui_kit.W, ui_kit.H
        if self.message_timer <= 0 or not self.message:
            return
        f = F(12)
        lines = wrap_text(self.message, f, W - 2 * margin() - u(30))
        h = int(f.get_height() * 1.3) * len(lines) + u(18)
        rect = pygame.Rect(0, 0, W - 2 * margin(), h)
        rect.center = (W // 2, H - bar_h() - margin() - u(36))
        panel(SCREEN, rect, fill=(5, 10, 21), border=AMBER, radius=u(10))
        y = rect.y + u(9)
        for ln in lines:
            text(SCREEN, ln, f, WHITE, (rect.centerx, y), "midtop")
            y += int(f.get_height() * 1.3)

    def draw(self):
        # Landscape-Layer: liefert die Zeichen-Surface (real oder virtuell gedreht)
        surf = ui_kit.begin_frame()
        global SCREEN
        SCREEN = surf
        st = self.state
        if self._prev_state != st:
            self._prev_state = st
            self._fade = 1.0
        if st == self.INTRO:
            self.draw_intro()
        elif st == self.DEFEAT:
            self.draw_defeat()
        else:
            if st in (self.MENU, self.RESEARCH, self.SETTINGS, self.SKILLTREE,
                      self.LOADING, self.QUESTS_DAILY, self.QUESTS_WEEKLY,
                      self.SUMMON):
                self._draw_menu_backdrop()
            if st == self.LOADING:
                self.draw_loading()
            elif st == self.MENU:
                self.draw_menu()
            elif st == self.RESEARCH:
                self.draw_research()
            elif st == self.SETTINGS:
                self.draw_settings()
            elif st == self.STAGES:
                self.draw_stages()
            elif st == self.SKILLTREE:
                self.draw_skill_tree()
            elif st in (self.QUESTS_DAILY, self.QUESTS_WEEKLY):   # PAKET 8
                self.draw_quests()
            elif st == self.SUMMON:                               # PAKET 8
                self.draw_summon()
            elif st in (self.PLAYING, self.PAUSED) \
                    or (st in (self.STAGE_CLEAR, self.VICTORY) and not self.victory_frames):
                self.draw_playing()
            if st == self.PAUSED:
                self.draw_pause_menu()
            if st == self.STAGE_CLEAR:
                self.draw_stage_clear()
            elif st == self.VICTORY:                     # AUFTRAG 6
                self.draw_victory()
            if self.debug_mode and st == self.PLAYING:
                self._draw_debug()
            self._draw_message()
        if self._fade > 0.01:
            ui_kit.overlay(surf, int(170 * self._fade))
        ui_kit.end_frame()
        pygame.display.flip()


_ship_scaled = {}


def _draw_drone_sprite(surface, x, y, angle, scale=1.0, ghost=False, level=1):
    """PAKET 7C: Zeichnet eine Hangar-Drohne als EIGENE kleine Einheit:
    pfeilfoermiger Koerper in Flugrichtung, Gluehkern, Triebwerksspur.
    ghost=True  : blass (Werft-Vorschau, kein Glow/keine Ringe)
    level       : Hangar-Stufe -> ab 4 weisser Ring, ab 7 Doppelring
                  ('verbesserte Drohnen' auf hoeheren Stufen sichtbar)."""
    scale = max(0.15, min(2.4, scale))
    r = max(3, int(u(7) * scale))
    if ghost:
        body, glow = (150, 220, 208), (96, 170, 158)
    else:
        body, glow = (255, 96, 198), (255, 62, 177)     # Magenta-Werksfarbe
    ca, sa = math.cos(angle), math.sin(angle)
    # Triebwerksspur (hinter der Drohne)
    pygame.draw.line(surface, glow,
                     (x - ca * r * 0.9, y - sa * r * 0.9),
                     (x - ca * r * 1.9, y - sa * r * 1.9), max(1, u(1)))
    # Koerper: Pfeilform (Nase in Flugrichtung)
    pts = [(x + ca * r * 1.5, y + sa * r * 1.5),
           (x - ca * r * 0.8 - sa * r * 0.9, y - sa * r * 0.8 + ca * r * 0.9),
           (x - ca * r * 0.35, y - sa * r * 0.35),
           (x - ca * r * 0.8 + sa * r * 0.9, y - sa * r * 0.8 - ca * r * 0.9)]
    pygame.draw.polygon(surface, (10, 18, 30), pts)
    pygame.draw.polygon(surface, body, pts, max(1, int(u(1.4))))
    # Gluehkern + additiver Glow (nur im Gefecht)
    pygame.draw.circle(surface, glow, (int(x), int(y)), max(1, int(r * 0.34)))
    if not ghost:
        g = radial_glow_k(glow, int(r * 2.3), 0.32)
        surface.blit(g, g.get_rect(center=(int(x), int(y))),
                     special_flags=pygame.BLEND_ADD)
        if level >= 4:
            pygame.draw.circle(surface, WHITE, (int(x), int(y)), int(r * 1.1), 1)
        if level >= 7:
            pygame.draw.circle(surface, glow, (int(x), int(y)), int(r * 1.45), 1)


def _mote_col(k):
    """Farbe der Hintergrund-Partikel (dezentes Cyan-Grau, k = 0..1)."""
    v = int(40 + 110 * k)
    return (int(v * 0.55), int(v * 0.85), v)


if __name__ == "__main__":
    Game().run()
