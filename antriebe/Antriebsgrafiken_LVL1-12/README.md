# Antriebsgrafiken LVL 1-12

Basiert 1:1 auf den neuen Referenzbildern (12 Triebwerks-Stufen).
Die Ausrichtung der Referenz wurde nicht veraendert: Flamme spritzt nach
oben-links, Gehaeuse laeuft nach unten-rechts, 3/4-Perspektive erhalten.

## Inhalt
- `atlas/` — fertige Animations-Atlanten (Koerper + Flamme + Glow),
  8 Frames @ 12 fps, nahtloser Loop, Zelle 512x384, vertikal gestapelt
  (Datei 512x3072). Dateiname: `engine_lvlNN_anim_8frames_512x384.png`.
- `ebenen/` — einzelne Ebenen fuer die eigene Komposition im Spiel:
  - `engine_lvlNN_body_512x384.png` — statischer Koerper ohne Flamme
  - `engine_lvlNN_flame_8frames_512x384.png` — animierte Flamme (8 Frames)
  - `engine_lvlNN_glow_8frames_512x384.png` — animiertes Flammenleuchten
- `previews/` — GIF-Vorschau je Stufe, kombinierte animierte Uebersicht
  (`alle_stufen_animiert.gif`) und statischer Kontaktbogen.

## Konventionen (wie im bisherigen Spiel)
- Alle 12 Sprites: gleiche Canvas (512x384), gleicher Anker:
  Koerper-Zentrum bei (336, 200) in jeder Zelle.
- Groesse wächst monoton von LVL 1 (93 px Koerper-Diagonale) bis
  LVL 12 (320 px), korrigiert gegenueber der Referenz per isotone Fit.
- Flammenfarben wie Referenz: LVL 1-6 orange-rot, LVL 7-9 gelb-weiss,
  LVL 10-12 blau.
- Hintergrund: komplett transparent (weisser Grund und Bodenschatten
  der Referenz entfernt).

## Animation
Radiale Deformation um die Flammenwurzel (Laengenpuls -4 % bis +13 %),
Spitzen-Sway und Helligkeitspuls; Phase 8 Frames = Phase 0 -> nahtlos.
Frame 0 jedes Atlas entspricht der bereinigten Referenz.

## Hinweise zur Integration
- Werft-/Upgrade-Logik unberuehrt; Grafiken ersetzen nur die Assets.
- Fuer Montage am Schiff: `body` statisch platzieren, `flame`+`glow`
  dahinter mit demselben Anker (Zellkoordinaten) komponieren.
- `meta.json` enthaelt je Stufe Skalierung, Flammenfarbe und Ankerdaten.
