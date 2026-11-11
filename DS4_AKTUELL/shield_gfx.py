# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 8.7: EIGENE SCHILD-GRAFIKEN LADEN
============================================================
Nutzer-Feedback: "Die Schilder, die ich generiert habe, werden gar
nicht verwendet - die liegen alle im DS4-Ordner."

Bisher zeichnete main.py den Schildring nur als zwei Cyan-Kreise. Dieses
Modul sucht die generierten Schild-Bilder und liefert sie pro Stufe:

  1. Suchordner (neben main.py, in dieser Reihenfolge):
       schilder/, schild/, DS4/schilder/, DS4/schild/, DS4/
     plus - falls vorhanden - der alte Entwicklungspfad
       C:\\Users\\bsahi\\Desktop\\corridorSlayers\\DS4\\schilder
       ...\\DS4\\schild  und  ...\\DS4
  2. Dateinamen: alles mit "schild" im Namen (.png/.jpg/.jpeg/.webp).
     Stufen-Zuordnung ueber die ERSTE Zahl im Namen:
       schild_lvl_3.png / schild_3.png / schild3.jpg  -> Stufe 3
       shield_lvl_5.png (englisch, mit "schild"? nein - "schild"
       muss enthalten sein; "shield" wird NICHT erkannt)
     Dateien OHNE Zahl gelten fuer alle Stufen (generisch).
  3. image_for(level): genau passendes Level, sonst die naechst-
     niedrigere vorhandene Stufe, sonst generisch, sonst None.

So kommt das Spiel auch ohne Upload aus: Sobald der DS4-/schilder-
Ordner neben dem Spiel liegt, werden die Grafiken automatisch benutzt
(Timeout-freier Verzeichnis-Scan beim ersten Zugriff, danach Cache).
"""
import os
import re
import pygame

_BASE = os.path.dirname(os.path.abspath(__file__))

# Alte Entwicklungspfade (wie main._folder / pve_system) - nur aktiv,
# wenn es sie wirklich gibt.
_LEGACY = [
    r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\schilder",
    r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\schild",
    r"C:\Users\bsahi\Desktop\corridorSlayers\DS4",
]

_SEARCH_DIRS = [
    os.path.join(_BASE, "schilder"),
    os.path.join(_BASE, "schild"),
    os.path.join(_BASE, "DS4", "schilder"),
    os.path.join(_BASE, "DS4", "schild"),
    os.path.join(_BASE, "DS4"),
] + _LEGACY

_IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")
_NUM_RE = re.compile(r"(\d+)")

_scanned = False
_by_level = {}      # int level -> Pfad
_generic = []       # Pfade ohne Zahl
_surface_cache = {}  # Pfad -> Surface (nicht skaliert)


def _scan():
    """Alle Suchordner einmalig nach Schild-Bildern durchsuchen."""
    global _scanned
    if _scanned:
        return
    _scanned = True
    best_by_level = {}
    for d in _SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        try:
            names = sorted(os.listdir(d))
        except OSError:
            continue
        for name in names:
            low = name.lower()
            if "schild" not in low or not low.endswith(_IMG_EXT):
                continue
            path = os.path.join(d, name)
            m = _NUM_RE.search(low)
            if m:
                lvl = int(m.group(1))
                if lvl >= 1:
                    # Erster Ordner gewinnt; innerhalb: hoechste Zahl?
                    # Nein: JEDE Datei mit eigener Zahl registrieren -
                    # image_for greift sich die passende/niedrigere.
                    if lvl not in best_by_level:
                        best_by_level[lvl] = path
            else:
                _generic.append(path)
    _by_level.update(best_by_level)


def available():
    """True, wenn ueberhaupt eine Schild-Grafik gefunden wurde."""
    _scan()
    return bool(_by_level or _generic)


def image_for(level):
    """Schild-Grafik fuer eine Modul-Stufe (oder None).
    Reihenfolge: exakte Stufe -> naechstniedrigere -> generisch."""
    _scan()
    path = None
    lvl = max(1, int(level))
    if lvl in _by_level:
        path = _by_level[lvl]
    else:
        lower = [l for l in _by_level if l < lvl]
        if lower:
            path = _by_level[max(lower)]
    if path is None and _generic:
        path = _generic[0]
    if path is None:
        return None
    surf = _surface_cache.get(path)
    if surf is None:
        try:
            surf = pygame.image.load(path).convert_alpha()
        except Exception:
            try:
                surf = pygame.image.load(path).convert()
            except Exception:
                surf = None
        if surf is not None:
            # Kein Grafikspeicher-Ueberlauf: Bilder moderat begrenzen
            w, h = surf.get_size()
            if max(w, h) > 512:
                k = 512.0 / max(w, h)
                surf = pygame.transform.smoothscale(
                    surf, (max(1, int(w * k)), max(1, int(h * k))))
            _surface_cache[path] = surf
    return surf


def source_name():
    """Ordner der ersten gefundenen Grafik (fuer Meldungen)."""
    _scan()
    path = next(iter(_by_level.values()), None) or (_generic[0] if _generic else None)
    return os.path.dirname(path) if path else ""
