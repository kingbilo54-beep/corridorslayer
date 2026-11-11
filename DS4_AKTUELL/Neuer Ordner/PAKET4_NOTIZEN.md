# CORRIDOR SLAYER – PAKET 4: OVERHAUL

**Installation:** `patch_paket4.py` herunterladen → in den **DS4-Ordner** legen (neben `main.py`) → `py patch_paket4.py`
Das Skript ist idempotent (mehrfach ausführbar), legt vorab Backups an (`main_backup_paket4.py`, `pve_system_backup_paket4.py`) und bricht ab, statt Dateien zu verfälschen, falls ein Code-Anker nicht passt.

---

## 1. Victory-Video: Fehleranalyse & Fix

**Ursache (war im alten main.py):** Nach einem Sieg sprang der Code direkt zurück zur STUFENKAMPAGNE-Karte. Der Zustand `STAGE_CLEAR` existierte zwar – war aber **unerreichbar**. Das Video wurde beim Start zwar geladen (victory_frames), aber es gab keinen draw()-Zweig und keine Methode, es anzuzeigen.

**Fix (Phase A, identisch zu Paket 3, wird übersprungen falls schon installiert):**
- Sieg → `STAGE_CLEAR`-Screen: Video läuft (30 fps, 2× Tempo), danach WEITER-Button → zurück zur Karte
- Tonspur wird automatisch aus `victory_screen.mp4` extrahiert (`victory_audio.mp3`) und synchron abgespielt; ohne `imageio-ffmpeg` ertönt ein synthetischer Jingle
- Kein Video vorhanden → Fallback-Panel „STUFE GESCHAFFT!" mit Credits-Anzeige

## 2. Damage-Numbers (Phase B)

- Schwebende Schadenszahlen am Trefferpunkt, steigen auf, faden aus (~0.9 s)
- **Gegner treffen = Cyan**, **Kritischer Treffer = Amber, größer**, **Spieler wird getroffen = Rot**
- Anzeige des tatsächlich verursachten Schadens (nach Abfang-Feld-Reduktion, Krit- und BULLY-Multiplikatoren)
- `EXEK!`-Anzeige bei Exekutor-Trigger

## 3. Skill-Tree „TECH-TERMINAL" (Phase C)

Neue Datei `skill_tree.py` + neuer Menüpunkt **SKILL-TREE** (Hauptmenü). Währung: **Data Cores**
(1 Core pro Kampagnen-Kill, Idle: 1 Core pro 25 Kills, KERN-SEPARATOR verdoppelt mit Chance).

4 Sparten à 5 Nodes (Vorauswahl wie in den Referenz-Screenshots, Detail-Panel unten mit TRAIN-Button,
Sparten-Farben: Waffen=Magenta, Verteidigung=Cyan, Energie=Amber, Spezial=Violett, gesperrt=grau):

| Sparte | Nodes (Max) |
|---|---|
| **WAFFENSYSTEME** | GEWEHRVERSTÄRKER (5) +10%/Stufe Schaden · SCHNELLFEUER (5) −6%/Stufe Intervall · MEHRFACHLAUF (2) +1 Projektil/Salve · ZIELRECHNER (5) +5%/Stufe Krit-Chance · PANZERBRECHER (4) Krit ×2.0 → ×3.0 |
| **VERTEIDIGUNG** | VERSTÄRKTE HÜLLE (5) +12%/Stufe max. HP · NANO-REPARATUR (5) +1 HP/s · ABFANG-FELD (2) −10%/Stufe Schaden · NOTKÜHLUNG (1) +25% Feuerrate unter 30% HP · PULSGENERATOR (4) Gegen-Pulse nach Treffern |
| **ENERGIE & ÖKONOMIE** | ENERGIELEITUNG (5) +8%/Stufe Drohnen-Schaden · HANGAR-TAKTIK (2) +1 Drohne · IDLE-PROTOKOLL (5) +15%/Stufe Idle-Einkommen · KRIEGSKASSE (5) +10%/Stufe Credits · KERN-SEPARATOR (4) +10%/Stufe Doppel-Core |
| **SPEZIALSYSTEME** | BULLY (4) +12%/Stufe vs. Ziele < 50% HP · EXEKUTOR (2) 10%/Stufe Hinrichtung < 20% HP · SPRENGSPITZE (1) Kills explodieren (AoE) · ADRENALIN-KERN (3) +2%/Stufe pro 10% fehlender HP · **ÜBERTAKTUNG (1): Taste Q – 8 s doppelte Feuerrate, 45 s CD** |

- Freischaltung: Vorgänger-Stufen nötig (Schwellen 0/1/2/4/6 pro Position) → gesperrte Nodes sind grau markiert
- Speicherung: `corridor_slayer_skills.json` (unabhängig vom Modul-Save)
- Effekte wirken sofort auf Idle + Kampagne (Sync nach jedem Kauf)
- Tasten: **Q** = Übertaktung, **M** = Sound, **ESC** = zurück

## 4. Grundausstattung & Balancing (Phase D)

Globale Koeffizienten in `pve_system.py` (wirken **zusätzlich** auf Excel-Werte, falls `game_data.xlsx` vorhanden):

| Größe | Vorher | Nachher |
|---|---|---|
| Kanonenschaden | 12,0 | **19,2** (×1.6) |
| Feuerintervall | 0,80 s | **0,70 s** (×0.88) |
| Max. Hülle | 500 | **700** (+100 je Schild-Stufe) |
| Grundreparatur | 0 (nur ab Stufe 2) | **1,5 HP/s** immer |
| Gegner-HP | 100 % | **85 %** (Boss 70 %) |
| Gegner-Schaden | 100 % | **70 %** |
| Gegneranzahl/Stufe | 3+Stufe | **2+Stufe** |

**Simulierte Kurve (echte Engine, Grundausstattung ohne Käufe):** Stufen 1–6 = SIEG (Rest-Hülle 98 % → 34 %), Stufe 7+ = Niederlage → **exakt der gewünschte Loop:** Basis trägt den Einstieg, ab Stufe 7 investieren. Mit den ersten Modul-Upgrades (nach 6 Siegen freigeschaltet) + 2 Skill-Stufen: Stufen 6–11 alles Siege (Rest-Hülle 60–90 %). Idle-Einkommen: jetzt zusätzlich Data Cores → Skill-Tree profitiert auch vom Idle-Modus langfristig.

## Verifikation (automatisiert, headless)

- Patch auf **3 Szenarien** getestet: frisch (ohne Paket 3), Upgrade (mit Paket 3), doppelt ausgeführt → jeweils alle Edits + Kompilierung OK
- Smoke-Tests: Damage-Numbers (Farben/Werte), ABFANG-FELD, Krit/BULLY/EXEKUTOR-Pfad, Idle-Cores nach 25 Kills, Gegner-Skalierung Stufe 5, komplettes `Game()` headless, **Victory-Flow** Sieg → STAGE_CLEAR → WEITER → Karte, Skill-Tree-UI (auswählen/trainieren/sperren, Core-Abbuchung, Live-Sync), Taste Q, ESC-Handling

## Bekannte Probleme / Hinweise

1. **`imageio-ffmpeg` fehlt** → Tonspur wird nicht extrahiert; dann synthetischer Sieg-Jingle. `pip install imageio-ffmpeg` behebt es (Skript erneut ausführen – wird erkannt).
2. **Excel-Balance:** Die Koeffizienten multiplizieren die Excel-Werte. Bei stark abweichenden Werten in `game_data.xlsx` verschiebt sich die Kurve (Richtung bleibt gleich).
3. **Hintergrund-Bugfix inklusive:** `hasattr(self, 'bg_stage_1_5')` prüfte ein nie existierendes Attribut – die Kapitel-Hintergründe wurden nie gezeichnet. Korrigiert.
4. Unverändert bewusst gelassen: `module_system.py` (Gating funktioniert), `cannon_system.py` (weiterhin ungenutzt – Spritesheet-/Turm-Thema ist ein separates Paket), hartcodierte `C:\Users\bsahi\...`-Pfade, `segoeui`-Schrift.
5. Stufe 15 (Boss) nutzt optisch den Lancer-Grafik-Satz; ein eigener Boss-Look wäre ein späteres Paket.
