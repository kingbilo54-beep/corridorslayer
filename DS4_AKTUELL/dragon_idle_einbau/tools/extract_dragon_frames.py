#!/usr/bin/env python3
"""
Sprite-Sheet-Extraktor fuer CORRIDOR SLAYER.
Zerschneidet ein Animations-Sprite-Sheet (z.B. dragon_idle_sheet_8frames_1024x420.png)
in einzelne, gleich grosse Frames mit Alpha-Kanal und speichert sie im Format,
das die Spiel-Animation erwartet:

    enemy_dragon_idle_0.png ... enemy_dragon_idle_7.png

Robust gegenüber:
- Streifen-Layout (8x1) und Grid-Layout (4x2 / 2x4 / 1x8)
- Transparentem Hintergrund ODER einfarbigem Hintergrund (Auto-Farbkey + Despill)
- Leichtem Randrauschen (Auto-Toleranz aus den Bildrändern)

Aufruf:
    python3 extract_dragon_frames.py SHEET.png [--frames 8] [--outdir DIR]
                                              [--basename enemy_dragon_idle] [--debug]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw


def build_content_mask(arr: np.ndarray):
    """Erzeugt eine bool-Maske der Bildinhalte. Gibt (maske, methode) zurueck."""
    h, w = arr.shape[:2]
    alpha = arr[:, :, 3]

    # Fall 1: Bild hat bereits Transparenz
    if (alpha < 16).mean() > 0.02 and alpha.min() < 10:
        return alpha > 16, "alpha"

    # Fall 2: einfarbiger Hintergrund -> aus den Bildraendern bestimmen
    border = np.concatenate([
        arr[:2, :, :3].reshape(-1, 3),
        arr[-2:, :, :3].reshape(-1, 3),
        arr[:, :2, :3].reshape(-1, 3),
        arr[:, -2:, :3].reshape(-1, 3),
    ]).astype(np.float64)
    bg = np.median(border, axis=0)
    dist = np.sqrt(((arr[:, :, :3].astype(np.float64) - bg) ** 2).sum(axis=2))
    border_dist = np.concatenate([
        dist[:2].ravel(), dist[-2:].ravel(), dist[:, :2].ravel(), dist[:, -2:].ravel()
    ])
    tol = float(np.percentile(border_dist, 99) + 10.0)
    tol = max(20.0, tol)

    # weiche Kanten: Alpha steigt von 0.5*tol bis 1.0*tol an
    soft = np.clip((dist - tol * 0.5) / (tol * 0.5), 0.0, 1.0)
    mask = dist > tol
    arr[:, :, 3] = (soft * 255).astype(np.uint8)  # WICHTIG: Maske in Alpha schreiben!

    # Despill bei gruener Kulisse (ueberall, auch am weichen Rand)
    r, g, b = arr[:, :, 0].astype(np.int32), arr[:, :, 1].astype(np.int32), arr[:, :, 2].astype(np.int32)
    if bg[1] > bg[0] + 20 and bg[1] > bg[2] + 20:
        avg = (r + b) // 2
        spill = g > avg
        g2 = arr[:, :, 1].copy()
        g2[spill] = avg[spill]
        arr[:, :, 1] = g2
        return mask, f"colorkey(green, tol={tol:.0f}, despill)"

    return mask, f"colorkey(rgb=({bg[0]:.0f},{bg[1]:.0f},{bg[2]:.0f}), tol={tol:.0f})"


def runs_of(bool_1d):
    """Liste der (start, ende) Intervalle von True-Bloecken."""
    runs, start = [], None
    for i, v in enumerate(bool_1d):
        if v and start is None:
            start = i
        elif not v and start is not None:
            runs.append((start, i))
            start = None
    if start is not None:
        runs.append((start, len(bool_1d)))
    return runs


def split_by_gaps(mask, expected):
    """Zerlegt die Maske via Spalten-/Zeilenluecken in Zellen (x0,x1,y0,y1)."""
    h, w = mask.shape[:2]
    col_runs = runs_of(mask.any(axis=0))
    if not col_runs:
        return None
    if len(col_runs) == expected:
        cells = []
        for x0, x1 in col_runs:
            row_runs = runs_of(mask[:, x0:x1].any(axis=1))
            if len(row_runs) == 1:
                y0, y1 = row_runs[0]
                cells.append((x0, x1, y0, y1))
            else:
                return None  # unklare Struktur
        return cells
    # Grid-Vermutung: n Spaltenblöcke mit je expected/n Zeilenblöcken
    if expected % len(col_runs) == 0:
        per_col = expected // len(col_runs)
        cells = []
        for x0, x1 in col_runs:
            row_runs = runs_of(mask[:, x0:x1].any(axis=1))
            if len(row_runs) != per_col:
                return None
            for y0, y1 in row_runs:
                cells.append((x0, x1, y0, y1))
        return cells
    return None


def split_uniform(mask, expected):
    """Fallback: gleichmaessige Raster, bewertet nach Inhalts-Kompaktheit."""
    h, w = mask.shape[:2]
    best, best_score = None, None
    for cols, rows in [(8, 1), (4, 2), (2, 4), (1, 8)]:
        if expected != cols * rows or w % cols or h % rows:
            continue
        cw, ch = w // cols, h // rows
        areas, covered = [], 0
        for r in range(rows):
            for c in range(cols):
                sub = mask[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw]
                frac = sub.mean()
                areas.append(frac)
                covered += frac > 0.01
        score = (covered, -float(np.std(areas)))
        if best_score is None or score > best_score:
            best_score = score
            best = (cols, rows, cw, ch)
    if best is None:
        return None
    cols, rows, cw, ch = best
    return [(c * cw, (c + 1) * cw, r * ch, (r + 1) * ch)
            for r in range(rows) for c in range(cols)]


def extract(sheet_path, outdir, basename, expected, debug=False):
    img = Image.open(sheet_path).convert("RGBA")
    arr = np.array(img)
    h, w = arr.shape[:2]

    mask, method = build_content_mask(arr)
    frac = float(mask.mean())
    print(f"[i] Sheet: {w}x{h}px | Hintergrund-Erkennung: {method} | Inhaltsanteil: {frac*100:.1f}%")
    if frac < 0.01 or frac > 0.95:
        print("[!] WARNUNG: Masken-Anteil untypisch – Ergebnis bitte visuell pruefen!")

    cells = split_by_gaps(mask, expected) or split_uniform(mask, expected)
    if cells is None:
        print("[X] Konnte Layout nicht bestimmen (8x1/4x2/2x4/1x8 mit 8 Frames erwartet).")
        sys.exit(1)
    if len(cells) < expected:
        print(f"[X] Nur {len(cells)} Zellen statt {expected} gefunden.")
        sys.exit(1)
    cells = cells[:expected]
    print(f"[i] Layout erkannt: {len(cells)} Zellen, z.B. erste Zelle {cells[0]}")

    # Vereinheitlichter Zuschnitt: gemeinsame Bounding-Box in Zell-lokalen
    # Koordinaten. Jeder Frame wird auf eine KONSTANTE Leinwand pastiert,
    # damit alle Frames exakt gleich gross sind (keine Wackler).
    boxes = []
    for (x0, x1, y0, y1) in cells:
        sub = mask[y0:y1, x0:x1]
        ys, xs = np.where(sub)
        if len(xs) == 0:
            boxes.append(None)
            continue
        boxes.append((xs.min(), xs.max(), ys.min(), ys.max()))
    valid = [b for b in boxes if b]
    ux0 = max(0, int(min(b[0] for b in valid)) - 2)
    uy0 = max(0, int(min(b[2] for b in valid)) - 2)
    ux1 = int(max(b[1] for b in valid)) + 3
    uy1 = int(max(b[3] for b in valid)) + 3
    fw, fh = ux1 - ux0, uy1 - uy0
    print(f"[i] Einheitliche Frame-Groesse: {fw}x{fh}px")

    os.makedirs(outdir, exist_ok=True)
    outs = []
    for i, ((x0, x1, y0, y1), box) in enumerate(zip(cells, boxes)):
        cell = arr[y0:y1, x0:x1]
        frame = np.zeros((fh, fw, 4), dtype=np.uint8)
        if box is not None:
            ch, cw = cell.shape[:2]
            sx0, sy0 = max(ux0, 0), max(uy0, 0)
            sx1, sy1 = min(ux1, cw), min(uy1, ch)
            if sx1 > sx0 and sy1 > sy0:
                frame[sy0 - uy0:sy1 - uy0, sx0 - ux0:sx1 - ux0] = cell[sy0:sy1, sx0:sx1]
        out = os.path.join(outdir, f"{basename}_{i}.png")
        Image.fromarray(frame).save(out)
        outs.append(out)
        print(f"    -> {os.path.basename(out)}  ({fw}x{fh})")

    if debug:
        # Kontaktbogen auf Schachbrett zum Alpha-Check
        tile = 8
        dbg = Image.new("RGB", (fw * len(outs) + 10 * (len(outs) + 1), fh + 20), (14, 18, 30))
        dr = ImageDraw.Draw(dbg)
        x = 10
        for i, o in enumerate(outs):
            f = Image.open(o)
            for yy in range(0, fh, tile):
                for xx in range(0, fw, tile):
                    col = (46, 56, 78) if ((xx // tile + yy // tile) % 2 == 0) else (28, 36, 54)
                    dr.rectangle([x + xx, 10 + yy, x + xx + tile - 1, 10 + yy + tile - 1], fill=col)
            dbg.paste(f, (x, 10), f)
            dr.text((x + fw // 2 - 4, fh + 2), str(i), fill=(200, 220, 255))
            x += fw + 10
        dbg.save(os.path.join(outdir, "_debug_contact.png"))
        print(f"[i] Debug-Kontaktbogen: {os.path.join(outdir, '_debug_contact.png')}")

    return outs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet", help="Pfad zum Sprite-Sheet PNG")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--outdir", default="enemys")
    ap.add_argument("--basename", default="enemy_dragon_idle")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()
    extract(args.sheet, args.outdir, args.basename, args.frames, args.debug)


if __name__ == "__main__":
    main()
