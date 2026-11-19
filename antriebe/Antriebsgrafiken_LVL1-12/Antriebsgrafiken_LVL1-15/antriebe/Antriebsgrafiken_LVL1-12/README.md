# Antriebsgrafiken LVL 1-15

Erweiterung des bestehenden Satzes auf **15 Stufen** (Ordnername aus
Kompatibilitaetsgruenden unveraendert: `Antriebsgrafiken_LVL1-12`).
Die Ausrichtung der Referenzen wurde nicht veraendert: Flamme spritzt nach
oben-links, Gehaeuse laeuft nach unten-rechts, 3/4-Perspektive erhalten.

## Was wurde geaendert?
- **LVL 1-9:** unveraendert uebernommen (bewährte Grafiken).
- **LVL 10-12:** Koerper aus den hochaufgeloesten Referenz-Sprites neu
  extrahiert (eingebrannte Flammenreste und Schattenwuerfe entfernt),
  LVL 10 sichtbar vergroessert (Koerperdiagonale ~200 -> ~300 px), neue
  grosse Flammen mit Feuerkugel am Ausgang, neues Glow.
- **LVL 13-15:** originalgetreu separiert aus `graphics levels 13-15.jpg`
  (Watershed-/Achsen-Separation, keine erfundenen Designs). Koerper-
  Diagonalen ~420/434/459 px. Flammen als Plasmasturm (13), Neonlanze (14)
  und Novakern mit Goldfunken (15) - Palette je Originaldesign.
- **Groessenentwicklung** monoton steigend LVL 10 -> 15
  (Koerperdiag. 299/349/393/419/434/459 px).
- **meta.json** um die Stufen 13-15 erweitert (10-12 aktualisiert);
  Stufen 1-9 unveraendert. Anker bleibt (336, 200) in der 512x384-Zelle,
  8 Frames @ 12 fps, nahtloser Loop.

## Inhalt
- `atlas/` — fertige Animations-Atlanten LVL 1-15 (Koerper+Flamme+Glow),
  8 Frames @ 12 fps, Zelle 512x384, vertikal gestapelt (512x3072).
- `ebenen/` — einzelne Ebenen je Stufe: `_body_`, `_flame_8frames_`,
  `_glow_8frames_` (je 512x384 bzw. 512x3072).
- `designs/` — die separierten Original-Designs LVL 13-15
  (transparent, voll aufgeloest, inkl. Wirbel/Strahl/Bogen-Effekte).
- `previews/` — GIF-Vorschau je Stufe + `alle_stufen_animiert.gif`.
- `graphics levels 13-15.jpg` — unveraenderte Original-Quellgrafik.
- `meta.json` — 15 Stufen mit Anker, Skalierung, Flammenfarbe.

## Notwendige Aenderung an main.py
In `_load_engine_sprite_data` die Stufen-Obergrenze von 12 auf 15 heben:

    -    lvl = max(1, min(12, int(level)))
    +    lvl = max(1, min(15, int(level)))

Exakter Patch: `integration/main_py_patch.diff`.
Pruefung: `python integration/integration_check.py` (Repo-Hauptordner).

Die Module `antrieb` haben in `game_data.xlsx` bereits MaxLevel 15;
weitere Codeaenderungen sind nicht erforderlich. `engine_effect.py`
und die Werft-Vorschau (`load_antrieb_image`) funktionieren unveraendert
(die Werft blendet fuer Stufen 13-15 auf die letzte vorhandene PNG).
