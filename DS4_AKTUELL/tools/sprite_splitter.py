# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | SPRITE-SPLITTER - Einzeln-Sprites aus dem Sheet
=====================================================================
NUTZUNG (im Spielordner DS4_AKTUELL):
    python tools\\sprite_splitter.py
    python tools\\sprite_splitter.py "C:\\Pfad\\zu\\enemy_dragon\\attack2"
    python tools\\sprite_splitter.py mein_sheet.png --out ordner

Ohne Argument werden ALLE Zustands-Ordner des Drachen abgearbeitet
(idle, attack, attack2, hurt, ... - jeder Ordner unter
enemys\\enemy_dragon, der ein Sheet enthaelt). Genau richtig fuer neue
Sheets wie attack2: ein Lauf, alle Zustaende zerlegt.

Was passiert:
  * Das Spritesheet (png/jpg, transparent ODER mit Hintergrund) wird
    in die EINZELNEN Sprites zerlegt - wie sie im Bild stehen:
    Mehrteilige Frames (Koerper + Fluegel + Effekt mit kleinen
    Luecken) werden zu EINEM Frame zusammengefasst, grosse Luecken
    trennen die Frames, lueckenlose Streifen werden per Perioden-
    Erkennung (Autokorrelation) gleichmaessig geteilt.
  * Die Sprites werden als nummerierte PNGs IN DEN ORDNER des Sheets
    geschrieben - beim Standard-Pfad ...\\enemys\\enemy_dragon\\hurt
    als enemy_dragon_hurt_0.png, enemy_dragon_hurt_1.png, ... Genau
    diese Namen laedt das Spiel ZUERST (Vorrang vor dem Sheet).
  * Reihenfolge: links -> rechts (oben -> unten bei Grids).
  * Diese Datei ist unabhaengig - sie aendert NICHTS am Spiel, sie
    schreibt nur Bilddateien. Laufen lassen, Spiel neu starten.

Tipp: Die Konsole zeigt die erkannte Frame-Anzahl. Erwartest du 8
und siehst 7 oder 27, schick mir das Sheet - dann verfeinere ich
die Schwelle. Aber: der Spiel-Loader benutzt jetzt dieselbe Logik
und faengt die ueblichen Faelle automatisch.
"""
import os
import re
import sys
import pygame

# =====================================================================
# FILTER - 1:1 aus main.py uebernommen (automatisch generiert durch
# scripts/build_tool_from_main.py). Der Spiel-Loader und dieses Tool
# teilen sich DAMIT exakt dieselbe Sprite-Filterung - was das Tool
# anzeigt, laedt das Spiel genauso.
# =====================================================================
import math  # noqa: E402  (von einigen Filter-Fallbacks genutzt)


def _downscaled(sheet, maxdim=1024):
    w, h = sheet.get_size()
    k = min(1.0, maxdim / float(max(w, h)))
    if k >= 1.0:
        return sheet, 1.0
    nw, nh = max(2, int(w * k)), max(2, int(h * k))
    return pygame.transform.smoothscale(sheet, (nw, nh)), k


def _detect_background(sheet):
    """Liefert (bg_color|None, bg_share). Deckt der Bildrand opaque und
    einfarbig, ist das ein Sheet MIT Hintergrund (z. B. JPG/Export)."""
    small, _k = _downscaled(sheet, 512)
    w, h = small.get_size()
    border = []
    for x in range(0, w, 2):
        border.append(small.get_at((x, 0)))
        border.append(small.get_at((x, h - 1)))
    for y in range(0, h, 2):
        border.append(small.get_at((0, y)))
        border.append(small.get_at((w - 1, y)))
    opaque = [c for c in border if c.a >= 200]
    if len(opaque) < 0.55 * len(border):
        return None, 0.0
    counts = {}
    for c in opaque:
        key = (c.r // 16 * 16, c.g // 16 * 16, c.b // 16 * 16)
        counts[key] = counts.get(key, 0) + 1
    col, n = max(counts.items(), key=lambda kv: kv[1])
    return col, n / float(len(border))


def _content_mask(sheet):
    """Content-Maske: Bits = zum Motiv gehoerige Pixel.
    -> (maske, hatte_hintergrund, hintergrundfarbe). Die Maske dient der
    BLOCK-Suche (Komponenten); die saubere Pixel-Befreiung vom
    Hintergrund macht _cleaned_surface (Flood-Fill von den Raendern)."""
    bg_col, share = _detect_background(sheet)
    if bg_col is not None:
        bg_mask = pygame.mask.from_threshold(
            sheet, bg_col, threshold=(14, 14, 14, 255))
        bg_mask.invert()                     # in-place: Bits = Motiv
        if bg_mask.count() > 0:
            return bg_mask, True, bg_col
    return pygame.mask.from_surface(sheet, threshold=0), False, None


def _bg_border_seeds(img, bg_col, max_step=96):
    """Seed-Punkte am Bildrand, die zum Hintergrund passen (numpy-Array
    HxWx4, Hintergrund quantisiert) - Startpunkte des Flood-Fills."""
    import numpy as np
    h, w = img.shape[0], img.shape[1]
    bg = np.array(bg_col, dtype=np.int16)
    seeds = []
    pts = []
    for x in range(0, w, max(1, min(max_step, w // 4 or 1))):
        pts += [(x, 0), (x, h - 1)]
    for y in range(0, h, max(1, min(max_step, h // 4 or 1))):
        pts += [(0, y), (w - 1, y)]
    for (x, y) in pts:
        px = img[y, x, :3].astype(np.int16)
        if np.abs(px - bg).max() <= 20:
            seeds.append((int(x), int(y)))
    return seeds


def _bg_clean_cv2(sheet, bg_col):
    """Hintergrund per Flood-Fill von allen Rand-Seeds entfernen (cv2,
    C-Tempo). Im Gegensatz zum Farb-Key werden nur ERREICHBARE
    Hintergrund-Pixel entfernt - dunkle Motiv-Partien bleiben ganz.
    Liefert convert_alpha-Surface oder None (cv2/numpy fehlt)."""
    try:
        import cv2
        import numpy as np
    except Exception:
        return None
    try:
        w, h = sheet.get_size()
        src = sheet.convert_alpha()
        raw = pygame.image.tobytes(src, "RGBA")
        img = np.frombuffer(raw, np.uint8).reshape((h, w, 4))
        bgr = np.ascontiguousarray(img[:, :, :3][:, :, ::-1])
        work = bgr.copy()
        mask2 = np.zeros((h + 2, w + 2), np.uint8)
        flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
        for seed in _bg_border_seeds(img, bg_col):
            if mask2[seed[1] + 1, seed[0] + 1]:
                continue
            cv2.floodFill(work, mask2, seed, 0,
                          loDiff=(8, 8, 8), upDiff=(8, 8, 8),
                          flags=flags)
        bg = mask2[1:-1, 1:-1] > 0
        content = (~bg).astype(np.uint8)
        kern = np.ones((5, 5), np.uint8)
        content = cv2.morphologyEx(content, cv2.MORPH_CLOSE, kern)
        out = src.copy()
        pa = pygame.surfarray.pixels_alpha(out)
        pa[:] = np.transpose(content * 255).astype(np.uint8)
        del pa
        return out
    except Exception:
        return None


def _cleaned_surface(sheet, mask, had_bg, bg_col=None):
    """Sheet mit entferntem Hintergrund: 1. Wahl cv2-Flood-Fill (keine
    Loecher im Motiv), Fallback Mask.to_surface (Faerbung strikt)."""
    if not had_bg:
        return sheet
    if bg_col is not None:
        out = _bg_clean_cv2(sheet, bg_col)
        if out is not None:
            return out
    try:
        blank = pygame.Surface(sheet.get_size(), pygame.SRCALPHA)
        src = sheet.convert_alpha()
        strict = pygame.mask.from_threshold(
            sheet, bg_col, threshold=(8, 8, 8, 255))
        strict.invert()
        return strict.to_surface(setsurface=src, unsetsurface=blank,
                                 setcolor=None, unsetcolor=(0, 0, 0, 0))
    except Exception:
        return sheet


def _component_boxes(mask):
    """Bounding-Boxen aller zusammenhaengenden Content-Bloecke."""
    boxes = []
    try:
        comps = mask.connected_components(1)
    except Exception:
        try:
            comps = mask.connected_components()
        except Exception:
            return boxes
    mw, mh = mask.get_size()
    min_area = max(24, (mw * mh) // 40000)
    for c in comps:
        if c.count() < min_area:
            continue
        pts = c.outline()
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        if x1 - x0 >= 2 and y1 - y0 >= 2:
            boxes.append(pygame.Rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1))
    return boxes


def _y_overlap(a, b, frac=0.35):
    ov = min(a.bottom, b.bottom) - max(a.top, b.top)
    return ov > frac * min(a.h, b.h)


def _gap_mode(gaps, median_w):
    """Drei Faelle der Luecken zwischen Content-Bloecken (auf der
    Streifen-Achse sortiert):
      'parts'      - alle Luecken winzig (Sprite-Teile desselben
                     Frames, z. B. 2-3 px) -> ALLES verschmilzt, die
                     Perioden-Erkennung uebernimmt.
      'clusters'   - klare zwei Groessenklassen (Teile 2-3 px vs.
                     Frames ~130 px) -> Schwelle im groessten
                     multiplikativen Sprung.
      'separated'  - Luecken gleichmaessig SUBSTANZIELL -> die Bloecke
                     SIND bereits die Frames (nicht verschmelzen!).
    """
    pos = sorted(g for g in gaps if g > 0)
    if not pos:
        return "parts", 1e9
    small_abs = max(4.0, 0.02 * median_w)
    if pos[-1] <= small_abs:
        return "parts", 1e9
    if pos[-1] / max(1.0, float(pos[0])) >= 3.0:
        best_i, best_ratio = 0, 0.0
        for i in range(len(pos) - 1):
            ratio = pos[i + 1] / max(1.0, float(pos[i]))
            if ratio > best_ratio:
                best_ratio, best_i = ratio, i
        return "clusters", (pos[best_i] + pos[best_i + 1]) / 2.0
    return "separated", 0.0


def _merge_boxes_to_frames(boxes, horizontal):
    """Content-Bloecke -> Frames. Streifen-Achse: horizontal (w >= h)
    oder vertikal. Modus 'separated': Bloecke sind bereits Frames -
    ABER erst nach Sanitaets-Check (Rausch-/Teil-Boxen aussieben,
    einheitliche Breiten - sonst ist 'separiert' nur scheinbar so und
    es folgt die y-Band-Verschmelzung + Perioden-Erkennung).
    Modus 'clusters': Verschmelzen kleiner Teile-Luecken (nur bei
    y-Ueberlappung). Modus 'parts': alles verschmilzt (-> Fallback).
    Danach: Kleinteile (Effekt-Orb) dem Frame im selben x-Bereich
    zuschlagen, ungewoehlich breite Boxen teilen, row-major ordnen."""
    if not boxes:
        return []

    def _sorted(bs):
        return sorted(bs, key=(lambda r: (r.x, r.y)) if horizontal
                      else (lambda r: (r.y, r.x)))

    def _gaps(bs):
        if horizontal:
            return [bs[i + 1].x - (bs[i].x + bs[i].width)
                    for i in range(len(bs) - 1)]
        return [bs[i + 1].y - (bs[i].y + bs[i].height)
                for i in range(len(bs) - 1)]

    boxes = _sorted(boxes)
    widths = sorted(b.width for b in boxes)
    median_w = widths[len(widths) // 2]
    mode, thr = _gap_mode(_gaps(boxes), median_w)
    if mode == "separated":
        # Sanitaets-Check: echter Frame-Streifen oder nur Stueckwerk?
        # (a) Rausch-/Teil-Boxen mit < 4 % der 75-%-Flaeche fliegen.
        areas = sorted(b.width * b.height for b in boxes)
        ref = areas[int(len(areas) * 0.75)]
        boxes = [b for b in boxes
                 if b.width * b.height >= max(200.0, 0.04 * ref)]
        if len(boxes) >= 2:
            boxes = _sorted(boxes)
            widths = sorted(b.width for b in boxes)
            median_w = widths[len(widths) // 2]
            mode, thr = _gap_mode(_gaps(boxes), median_w)
            # (b) Breiten-Mix: groesste >> median -> Fragmente statt
            # Frames (z. B. Drache + gleichmaessig verteilte Effekt-
            # Stueckchen) -> Verschmelzen + Perioden-Erkennung.
            if mode == "separated" and max(widths) > 2.5 * median_w:
                mode = "parts"
        else:
            mode = "parts"
    if mode == "separated":
        merged = [b.copy() for b in boxes]
    elif mode == "clusters":
        merged = [boxes[0].copy()]
        for i in range(1, len(boxes)):
            prev = merged[-1]
            if horizontal:
                gap = boxes[i].x - (prev.x + prev.width)
            else:
                gap = boxes[i].y - (prev.y + prev.height)
            if gap < thr and _y_overlap(prev, boxes[i]):
                prev.union_ip(boxes[i])
            else:
                merged.append(boxes[i].copy())
    else:  # parts: nur innerhalb y-Baender verschmelzen (Grids bleiben)
        merged = [boxes[0].copy()]
        for i in range(1, len(boxes)):
            prev = merged[-1]
            if _y_overlap(prev, boxes[i]):
                prev.union_ip(boxes[i])
            else:
                merged.append(boxes[i].copy())
    # Abgetrennte Kleinteile (Effekt-Orb ueber dem Kopf) dem Frame im
    # selben Streifen-Bereich zuschlagen: voll enthalten, deutlich
    # schmaler, vertikal nahe.
    widths = sorted(b.width for b in merged)
    median_w = widths[len(widths) // 2]
    keep = [True] * len(merged)
    order = sorted(range(len(merged)),
                   key=lambda i: merged[i].width, reverse=True)
    for j in order:
        if not keep[j]:
            continue
        big = merged[j]
        for i in range(len(merged)):
            if i == j or not keep[i]:
                continue
            small = merged[i]
            if (small.width <= 0.6 * big.width
                    and small.x >= big.x and small.right <= big.right
                    and (small.top - big.top) < 0.5 * big.h
                    and small.y >= big.y - big.h * 0.35):
                big.union_ip(small)
                keep[i] = False
    merged = [b for b, k in zip(merged, keep) if k]
    # Sicherheit: ungewoehlich breite Box (aneinanderklebende Frames)
    # in round(w / median) gleiche Zellen teilen.
    out = []
    for b in merged:
        if median_w > 0 and b.width > 1.8 * median_w:
            n = max(2, int(round(b.width / float(median_w))))
            step = b.width / float(n)
            for k in range(n):
                x0 = b.x + int(round(k * step))
                x1 = b.x + int(round((k + 1) * step))
                out.append(pygame.Rect(x0, b.y, x1 - x0, b.h))
        else:
            out.append(b)
    # row-major Ordnung: y-Baender, darin links -> rechts
    out.sort(key=lambda r: (r.y + r.h / 2.0, r.x))
    bands = []
    for r in out:
        placed = False
        for band in bands:
            ref = band[0]
            ov = min(ref.bottom, r.bottom) - max(ref.top, r.top)
            if ov > 0.5 * min(ref.h, r.h):
                band.append(r)
                placed = True
                break
        if not placed:
            bands.append([r])
    bands.sort(key=lambda band: min(r.y for r in band))
    ordered = []
    for band in bands:
        band.sort(key=lambda r: r.x)
        ordered.extend(band)
    return ordered


def _aligned_frames(cleaned, boxes):
    """Jede Box zentriert auf eine gemeinsame, gleich grosse transpa-
    rente Leinwand blitten -> einheitliche Frame-Groesse UND - und das
    ist fuer die Animation entscheidend - das Motiv sitzt in JEDER
    Frame an derselben Stelle (das Spiel zeichnet das Sprite zentriert
    auf die Gegner-Position; wuerde man die Sheet-Positionen 1:1
    erhalten, wuerde das Motiv pro Frame quer ueber den Schirm
    springen)."""
    gw = max(b.width for b in boxes)
    gh = max(b.height for b in boxes)
    frames = []
    for b in boxes:
        part = cleaned.subsurface((b.x, b.y, b.width, b.height))
        canvas = pygame.Surface((gw, gh), pygame.SRCALPHA)
        canvas.blit(part, ((gw - b.width) // 2, (gh - b.height) // 2))
        frames.append(canvas)
    return frames


def _profile_runs_1d(profile, min_val, gap):
    runs, start, empty = [], None, 0
    for i, val in enumerate(profile):
        if val >= min_val:
            if start is None:
                start = i
            empty = 0
        elif start is not None:
            empty += 1
            if empty >= gap:
                runs.append((start, i - empty + 1))
                start, empty = None, 0
    if start is not None:
        runs.append((start, len(profile)))
    return [r for r in runs if r[1] - r[0] >= 2]


def _shift_diff(prof, step):
    """Mittlerer Profil-Unterschied bei Verschiebung um step (wrap-
    around, das Sheet ist ein Loop)."""
    n = len(prof)
    s = int(round(step))
    if s <= 0 or s >= n:
        return 1.0
    total = 0
    for x in range(n):
        total += abs(prof[x] - prof[(x + s) % n])
    return total / float(n * 255)


def _axis_profile(surface, horizontal, had_bg=False, bg_col=None):
    """1D-Inhalts-Profil entlang der Streifen-Achse (0..255).
    Transparente Sheets: gemitteltes ALPHA je Spalte/Reihe.
    Hintergrund-Sheets: gemittelter FARB-ABSTAND zum Hintergrund
    (Alpha ist dort konstant 255 und damit nutzlos)."""
    w, h = surface.get_size()
    outer = w if horizontal else h
    if outer < 2:
        return [], 4
    strip = pygame.transform.smoothscale(
        surface, (outer, 1)) if horizontal else pygame.transform.smoothscale(
            surface, (1, outer))
    if not had_bg or bg_col is None:
        prof = [strip.get_at((i, 0) if horizontal else (0, i)).a
                for i in range(outer)]
        return prof, 4
    br, bg_, bb = bg_col
    prof = []
    for i in range(outer):
        c = strip.get_at((i, 0) if horizontal else (0, i))
        d = max(abs(c.r - br), abs(c.g - bg_), abs(c.b - bb))
        prof.append(min(255, d * 3))         # Kontrast fuer die Schwelle
    return prof, 12


def _best_strip_count(sheet, horizontal, had_bg=False, bg_col=None):
    """Perioden-Erkennung fuer lueckenlose Streifen via AUTOKORRELATION:
    Gut ist eine Frame-Anzahl n, deren Schrittweite das Profil sauber
    wiederholt (kleiner Shift-Diff) UND deren HALBE Schrittweite es
    NICHT schon wiederholt (Grundperiode, kein Vielfaches). Bevorzugt
    kleinere n bei Gleichstand."""
    small, _k = _downscaled(sheet, 1024)
    ow, oh = small.get_size()
    horizontal = ow >= oh
    prof, _mv = _axis_profile(small, horizontal, had_bg, bg_col)
    outer = len(prof)
    best_n, best_score = None, None
    scores = {}
    for n in range(2, 25):
        step = outer / float(n)
        if step < 8:
            break
        d = _shift_diff(prof, step)
        d_half = (_shift_diff(prof, step / 2.0)
                  if step / 2.0 >= 8 else d)
        seg_mass = []
        for i in range(n):
            a, b = int(round(i * step)), int(round((i + 1) * step))
            seg_mass.append(sum(prof[a:b]))
        mean_m = sum(seg_mass) / float(n)
        cv = 0.0
        if mean_m > 0:
            var = sum((m - mean_m) ** 2 for m in seg_mass) / float(n)
            cv = (var ** 0.5) / mean_m
        score = d - 0.8 * d_half + 0.15 * cv
        scores[n] = score
        if best_score is None or score < best_score:
            best_n, best_score = n, score
    if best_n is None:
        w, h = sheet.get_size()
        return max(2, min(32, int(round(max(w, h) / float(min(w, h))))))
    # Gleichstand: kleinere n bevorzugen (Uebersegmentierung vermeiden)
    for n in range(2, best_n):
        if n in scores and scores[n] <= best_score * 1.08:
            return n
    return best_n


def _plausible_frames(boxes):
    """Plausibilitaets-Filter fuer Komponenten-Ergebnisse bei Backgrund-
    Sheets (Rausch-Sprenkel und Fragmente aussieben). Nur Boxen mit
    >= 2 % der groessten Flaeche und >= 12 % der groessten Breite
    bleiben; mehr als 24 Frames sind unplaussibel."""
    if len(boxes) < 2 or len(boxes) > 24:
        return []
    max_a = max(b.width * b.height for b in boxes)
    max_w = max(b.width for b in boxes)
    keep = [b for b in boxes
            if b.width * b.height >= 0.02 * max_a
            and b.width >= 0.12 * max_w]
    return keep if len(keep) >= 2 else []


def _split_anim_sheet(sheet):
    """Filtert die EINZELNEN Sprites aus einem Spritesheet. Liefert eine
    Liste gleich grosser, ausgerichteter Frames (>= 2) oder []."""
    w, h = sheet.get_size()
    if w < 4 or h < 4:
        return []
    try:
        mask, had_bg, bg_col = _content_mask(sheet)
    except Exception:
        mask, had_bg, bg_col = (pygame.mask.from_surface(sheet,
                                  threshold=0), False, None)
    cleaned = _cleaned_surface(sheet, mask, had_bg, bg_col)
    # Bei Hintergrund-Sheets wird Pfad 2/3 auf dem ORIGINAL geschnitten
    # (die Bereinigung kann bei Motiv-farbigem Grund rueckresten) - die
    # Bereinigung dient nur Pfad 1 (Komponenten-Boxen).
    prof_sheet = sheet if had_bg else cleaned

    # --- Pfad 1: ECHTE Sprite-Filterung (Connected Components) -------
    box_mask = mask
    if had_bg and cleaned is not sheet:
        try:
            bm = pygame.mask.from_surface(cleaned, threshold=0)
            if bm.count() > 0:
                box_mask = bm
        except Exception:
            pass
    try:
        boxes = _component_boxes(box_mask)
        boxes = _merge_boxes_to_frames(boxes, w >= h)
        if had_bg:
            boxes = _plausible_frames(boxes)
    except Exception:
        boxes = []
    if len(boxes) >= 2:
        try:
            return _aligned_frames(cleaned, boxes)
        except Exception:
            pass

    # --- Pfad 2: Profil-Fallback (Luecken in einer Achse) ------------
    horizontal = w >= h
    outer, inner = (w, h) if horizontal else (h, w)
    prof, min_val = _axis_profile(prof_sheet, horizontal, had_bg, bg_col)
    runs = _profile_runs_1d(prof, min_val, 2)
    frames = []
    if len(runs) >= 2:
        inner_per_run = []
        for (a0, a1) in runs:
            if horizontal:
                sub = prof_sheet.subsurface((a0, 0, a1 - a0, h))
            else:
                sub = prof_sheet.subsurface((0, a0, w, a1 - a0))
            prof2, mv2 = _axis_profile(sub, not horizontal,
                                       had_bg, bg_col)
            inner_per_run.append(_profile_runs_1d(prof2, mv2, 1))
        counts = {len(r) for r in inner_per_run}
        if len(counts) == 1 and next(iter(counts)) >= 2:
            # GRID-Sheet: jede Spalte enthaelt gleich viele Reihen ->
            # Zellen row-major herausfiltern.
            k = next(iter(counts))
            if horizontal:
                for j in range(k):
                    for (a0, a1), iruns in zip(runs, inner_per_run):
                        b0, b1 = iruns[j]
                        frames.append(prof_sheet.subsurface(
                            (a0, b0, a1 - a0, b1 - b0)).copy())
            else:
                for (a0, a1), iruns in zip(runs, inner_per_run):
                    for j in range(k):
                        b0, b1 = iruns[j]
                        frames.append(prof_sheet.subsurface(
                            (b0, a0, b1 - b0, a1 - a0)).copy())
            return frames
        # Streifen: Mini-Bloecke (Sprite-Teile) zuerst wie in Pfad 1
        # clusterieren - sind danach < 2 Bloecke, ist der Streifen
        # lueckenlos/parts -> Perioden-Erkennung (Pfad 3) uebernehmen.
        run_rects = [(pygame.Rect(a0, 0, a1 - a0, h) if horizontal
                      else pygame.Rect(0, a0, w, a1 - a0))
                     for (a0, a1) in runs]
        try:
            merged_runs = _merge_boxes_to_frames(run_rects, horizontal)
        except Exception:
            merged_runs = run_rects
        if len(merged_runs) < 2:
            frames = []
        else:
            inner_runs = [r for iruns in inner_per_run for r in iruns]
            if inner_runs:
                i0 = max(0, min(r0 for r0, _r1 in inner_runs))
                i1 = min(inner, max(r1 for _r0, r1 in inner_runs))
            else:
                i0, i1 = 0, inner
            for b in merged_runs:
                if horizontal:
                    frames.append(prof_sheet.subsurface(
                        (b.x, i0, b.width, i1 - i0)).copy())
                else:
                    frames.append(prof_sheet.subsurface(
                        (i0, b.y, i1 - i0, b.height)).copy())
        if frames:
            return frames

    # --- Pfad 3: lueckenlos -> Perioden-Erkennung -> gleiche Teilung -
    n = _best_strip_count(prof_sheet, horizontal, had_bg, bg_col)
    step = outer / float(n)
    for i in range(n):
        a0, a1 = int(round(i * step)), int(round((i + 1) * step))
        if horizontal:
            frames.append(prof_sheet.subsurface((a0, 0, a1 - a0, h)).copy())
        else:
            frames.append(prof_sheet.subsurface((0, a0, w, a1 - a0)).copy())
    return frames


def _split_file(path, out_dir, prefix, start_idx):
    """Ein Sheet splitten -> nummerierte PNGs. Rueckgabe: Anzahl."""
    sheet = pygame.image.load(path).convert_alpha()
    frames = _split_anim_sheet(sheet)
    n = 0
    for k, fr in enumerate(frames):
        out = os.path.join(out_dir, f"{prefix}_{start_idx + k}.png")
        pygame.image.save(fr, out)
        n += 1
    return n, sheet.get_size(), [f.get_size() for f in frames[:3]]


def _looks_numbered(name):
    return bool(re.search(r"_\d+\.png$", name.lower()))


def _process_folder(target, out_arg=None):
    """Einen Zustands-Ordner abarbeiten (Sheet(s) -> nummerierte PNGs).
    Rueckgabe: Anzahl erzeugter Frames, None bei Fehler."""
    if not os.path.isdir(target):
        print(f"[FEHLER] Ordner/Datei nicht gefunden: {target}")
        return None

    folder = os.path.abspath(target)
    # Namensmuster fuer das Spiel ableiten: .../enemy_dragon/hurt ->
    # enemy_dragon_hurt_<nr>.png (genau das sucht main.py zuerst).
    state = os.path.basename(folder.rstrip("\\/").rstrip("/")).lower()
    parent = os.path.basename(os.path.dirname(folder.rstrip("\\/")))
    etype = parent.lower()
    if etype.startswith("enemy_"):
        etype = etype[len("enemy_"):]
    prefix = f"enemy_{etype}_{state}" if etype and state else "sprite"

    sheets = [f for f in sorted(os.listdir(folder))
              if f.lower().endswith((".png", ".jpg", ".jpeg"))
              and not f.startswith("_")
              and not _looks_numbered(f)]
    if not sheets:
        return 0
    idx = 0
    for name in sheets:
        path = os.path.join(folder, name)
        try:
            n, size, sample = _split_file(path, folder, prefix, idx)
        except Exception as exc:
            print(f"[WARNUNG] {name} uebersprungen: {exc}")
            continue
        print(f"[OK] {name} ({size[0]}x{size[1]}) -> {n} Sprites "
              f"als {prefix}_{idx}..{prefix}_{idx + n - 1}.png "
              f"(Beispiel-Frame: {sample[0][0]}x{sample[0][1]})")
        idx += n
    if idx:
        print(f"-> {folder}: {idx} Einzeln-Sprites "
              f"(nummerierte Frames gewinnen im Spiel)")
    return idx


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    out_arg = None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 < len(argv):
            out_arg = argv[i + 1]
            args = [a for a in args if a != "--out" and a != out_arg]
    target = args[0] if args else None

    if target and os.path.isfile(target):
        folder = os.path.dirname(os.path.abspath(target))
        stem = os.path.splitext(os.path.basename(target))[0]
        prefix = out_arg and os.path.basename(out_arg) or f"{stem}_sprite"
        out_dir = out_arg and os.path.dirname(out_arg) or folder
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        os.chdir(folder or ".")
        n, size, sample = _split_file(target, out_dir, prefix, 0)
        print(f"[OK] {os.path.basename(target)} ({size[0]}x{size[1]}) "
              f"-> {n} Einzeln-Sprites als {prefix}_0..{n - 1}.png")
        return 0

    if target is None:
        # AUFTRAG ATTACK2: ohne Argument ALLE Zustands-Ordner des
        # Drachen abarbeiten (idle, attack, attack2, hurt, ...) -
        # ein Lauf zerlegt jedes neue Sheet.
        base = os.path.join("enemys", "enemy_dragon")
        if not os.path.isdir(base):
            print(f"[FEHLER] {base} nicht gefunden - "
                  "aus dem Spielordner (DS4_AKTUELL) starten.")
            return 1
        gesamt = 0
        for entry in sorted(os.listdir(base)):
            sub = os.path.join(base, entry)
            if os.path.isdir(sub):
                n = _process_folder(sub)
                if n:
                    gesamt += n
        print()
        print(f"FERTIG: {gesamt} Einzeln-Sprites ueber alle "
              "Zustands-Ordner von enemys/enemy_dragon.")
        print("Das Spiel laedt diese Dateien automatisch (nummerierte "
              "Frames haben Vorrang vor dem Sheet).")
        return 0

    n = _process_folder(target, out_arg)
    if n is None:
        return 1
    if n == 0:
        print(f"[FEHLER] Kein Spritesheet (png/jpg) in {target} gefunden.")
        return 1
    return 0


if __name__ == "__main__":
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import re as _re  # noqa: F401  (fuer _looks_numbered)
    pygame.init()
    try:
        pygame.display.set_mode((64, 64))
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
