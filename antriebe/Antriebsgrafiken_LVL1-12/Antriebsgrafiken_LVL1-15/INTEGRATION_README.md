# INTEGRATION: Antriebsgrafiken LVL 1-15

Paket fuer `kingbilo54-beep/corridorslayer` (Branch `glm-werft-integration`).

## 1) Dateien einspielen
Den Ordner `antriebe/Antriebsgrafiken_LVL1-12/` aus diesem Paket 1:1 in
das Repository kopieren (bestehende Dateien derselben Namen ersetzen,
neue Dateien kommen hinzu). Der Ordnername bleibt unveraendert, damit
`ENGINE_SPRITE_FOLDER` in main.py weitergueltig ist.

Enthalten:
- `atlas/` 15 Atlanten (LVL 01-15) — 512x3072, 8 Frames @ 12 fps
- `ebenen/` 45 Ebenen-Dateien (Body / Flame / Glow je Stufe)
- `designs/` separierte Originaldesigns LVL 13-15 (Referenz/Marketing)
- `previews/` GIFs je Stufe + animierte Gesamtuebersicht
- `meta.json` (15 Stufen, Anker (336,200), scale, flame_rgb, ...)
- `graphics levels 13-15.jpg` (unveraenderte Original-Quelle)
- `README.md` (Ordner-Dokumentation)

## 2) Notwendige main.py-Aenderung (eine Zeile)
In `_load_engine_sprite_data` (ca. Zeile 1878):

    -    lvl = max(1, min(12, int(level)))
    +    lvl = max(1, min(15, int(level)))

Alternativ Patch einspielen: `integration/main_py_patch.diff`
(`patch -p1 < main_py_patch.diff` aus dem Repo-Hauptordner — Pfad im
Diff auf die eigene Kopie anpassen) oder die mitgelieferte gepatchte
Kopie `integration/main_py_neu__load_engine_sprite_data.py` vergleichen.

## 3) Pruefen
    python integration/integration_check.py

Prueft: 15 Stufen in meta.json, alle 45 Ebenen- + 15 Atlas-Dateien,
Dateigroessen (512x384 / 512x3072), frames/fps = 8/12, und — falls
pygame installiert ist — das echte Laden wie in `_load_engine_sprite_data`.

## 4) Was NICHT geaendert wurde
- LVL 1-9 Grafiken: byte-identisch zum Repo-Stand.
- Spiellogik, Balancing, Werft, engine_effect.py: unveraendert.
  (`antrieb` hat in game_data.xlsx bereits MaxLevel 15; engine_effect
  akzeptiert beliebige Level; die Werft-Vorschau nutzt weiterhin die
  12 PNGs im Ordner `antrieb/` und blendet fuer 13-15 auf die letzte.)
- Die Original-Quelldatei `graphics levels 13-15.jpg`: unveraendert.

## 5) Methodik LVL 13-15 (Originaltreue)
Die drei Triebwerke wurden aus dem Gemeinschaftsbild getrennt:
Hintergrund-Floodfill (weich), Koerpermarker je Triebwerk, Effekt-Pixel
per Diagonalachse dem richtigen Triebwerk zugeordnet (Wirbel->13,
Strahl->14, Strahl+Lichtbogen->15). Grenzen laufen durch Hintergrund/
leere Glow-Zonen, nie durch einen soliden Koerper. Die Designs liegen
1:1 in `designs/` bei. Fuer die Spiel-Flammen wurde die etablierte
Teardrop-Form (wie LVL 1-12) in der Palette der Originale umgesetzt
(13 Plasmasturm mit rotierenden Baendern, 14 Neon-Rim, 15 Novakern +
Goldfunken) - Feuerkugel am Ausgang, 8 Frames @ 12 fps, loop-sicher.

## 6) QC
`qc/kontaktbogen_lvl01-15.jpg` (alle Stufen nebeneinander),
`qc/ingame_darstellung_lvl01-15.jpg` (draw_engine_sprites-Skalierung
Glow 4.3x / Flamme 3.6x / Body 3.0x um den Anker),
`qc/qc_report.json` (Dateigroessen, Anker, Loop-Differenz, Monotonie).
