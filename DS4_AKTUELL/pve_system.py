"""CORRIDOR SLAYER | PvE Combat & Dynamic Upgrade Engine."""
import math
import random
import openpyxl
import os
from pathlib import Path   # SCHRITT 1c: Excel-Pfad unabhaengig vom Arbeitsordner
from dataclasses import dataclass
from sound_system import SFX
# SCHRITT 3: Globale BAL_*-Koeffizienten liegen zentral im BALANCE-Block
# von rpg_config.py und werden nur noch importiert (Werte identisch).
from rpg_config import (BAL_PLAYER_DMG, BAL_PLAYER_RATE, BAL_PLAYER_HP,
                        BAL_ENEMY_HP, BAL_ENEMY_DMG, BAL_BOSS_HP,
                        BAL_CREDITS, BAL_IDLE_CREDITS,
                        BAL_LATE_STAGE_HP, BAL_LATE_STAGE_DMG,
                        ng_hp_mult, ng_dmg_mult, ng_reward_mult,   # AUFTRAG 6: NG+
                        CAMPAIGN_HP_MULT, CAMPAIGN_DMG_MULT,       # AUFTRAG 16b
                        CAMPAIGN_REWARD_MULT, CAMPAIGN_SPAWN_SPD,
                        IDLE_LIVE_CORE_CAP)                        # AUFTRAG 22

ENEMY_DATA = {}
PLAYER_DATA = {}

try:
    # SCHRITT 1c: game_data.xlsx liegt neben dieser Datei - nicht mehr im
    # Arbeitsverzeichnis. So laedt das Spiel die Werte auch, wenn es aus
    # einem anderen Ordner (anderes CWD) gestartet wurde.
    wb = openpyxl.load_workbook(str(Path(__file__).parent / "game_data.xlsx"))
    ws_e = wb["Enemies"]
    headers_e = [cell.value for cell in ws_e[1]]
    for row in ws_e.iter_rows(min_row=2, values_only=True):
        if row[0]: ENEMY_DATA[row[0].lower()] = dict(zip(headers_e, row))
            
    ws_p = wb["Player"]
    for row in ws_p.iter_rows(min_row=2, values_only=True):
        if row[0]: PLAYER_DATA[row[0]] = row[1]
except Exception as e:
    print(f"⚠️ Fehler beim Laden der Excel-Datei: {e}")

# PAKET 8.2: Asset-Ordner erst neben dieser Datei, dann alter Hartpfad
# (gleiche Logik wie main._folder) - damit die lokalen Gegnerbilder in
# enemys/ greifen und der Spawn-Pool sie findet.
_BASE = os.path.dirname(os.path.abspath(__file__))


def _folder(name, old_abs):
    p = os.path.join(_BASE, name)
    if os.path.isdir(p):
        return p
    if os.path.isdir(old_abs):
        return old_abs
    return p


ENEMY_FOLDER = _folder("enemys",
                       r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\enemys")

# PAKET 8.2 + PUNKT-4-ABGLEICH: Eingebauter Gegner-Roster als Fallback,
# falls game_data.xlsx fehlt (Distribution ohne Excel). Seit dem Abgleich
# ist er 1:1 deckungsgleich mit dem Sheet "Enemies" der game_data.xlsx -
# dieselben 16 Typen, dieselben Werte, inkl. Min_Ship_Level. Excel bleibt
# Vorrang, sobald sie existiert; der PVE88-Merge unten ist bei der
# abgeglichenen Excel eine No-Op und schuetzt nur noch gegen AELTERE
# Excel-Dateien (ohne die Spalte Min_Ship_Level / neue Typen).
# Pool-Regeln (unveraendert): Nur wer Min_Ship_Level <= Schiffslevel und
# Spawn_Weight > 0 hat UND eine Datei enemys/enemy_<key>.png besitzt,
# kommt in den Spawn-Pool (Pruefung in _spawn_single_enemy).
#   shard/husk/wraith/hive : GEPARKT (Min_Ship_Level 99 haelt sie aus
#     jedem Pool heraus - Grafiken vorhanden, Freischaltung ist eine
#     spaetere Balancing-Entscheidung, hier nur Datensatz wie zuvor im
#     alten Fallback).
#   destroyer/bomber/frigate/boss : Alt-Excel-Datensaetze OHNE Grafik -
#     spawnen nie, zaehlen aber weiterhin im nominalen Beute-Mittel
#     (stage_nominal_reward), genau wie vor dem Abgleich.
#   Idle_HP_Mult/Idle_Speed_Mult sind Alt-Excel-Datenbestand und werden
#     im Code nicht gelesen (bei carrier + allen 8 neuen Typen undefiniert).
# Skalierung: HP(w) = (Base_HP + w*HP_Add) * HP_Mult^w * BAL_ENEMY_HP
#             DMG(w) = (Base_Damage + w*Dmg_Add) * BAL_ENEMY_DMG
if not ENEMY_DATA:
    ENEMY_DATA = {
        # Swarman-Droene (magenta) - Startgegner, schnell & schwach
        "skitter": {"Base_HP": 20, "Base_Speed": 60, "Base_Damage": 5,
                    "Base_Reward": 10, "Min_Ship_Level": 1,
                    "Spawn_Weight": 60, "HP_Add_Per_Stage": 15,
                    "HP_Mult_Per_Stage": 1.08, "Speed_Add_Per_Stage": 2,
                    "Damage_Add_Per_Stage": 2, "Idle_HP_Mult": 0.3,
                    "Idle_Speed_Mult": 0.5, "Idle_Reward_Mult": 1.0},
        # Void Lancer - normaler Gegner (Excel-Stand; der ALTE Fallback
        # behandelte lancer als Stufe-15-Boss, seit PAKET 8.8 laufen die
        # Bosse ueber BOSS_DATA - lancer ist seitdem wieder regulier).
        "lancer": {"Base_HP": 80, "Base_Speed": 30, "Base_Damage": 15,
                   "Base_Reward": 25, "Min_Ship_Level": 1,
                   "Spawn_Weight": 20, "HP_Add_Per_Stage": 40,
                   "HP_Mult_Per_Stage": 1.1, "Speed_Add_Per_Stage": 1,
                   "Damage_Add_Per_Stage": 3, "Idle_HP_Mult": 0.4,
                   "Idle_Speed_Mult": 0.6, "Idle_Reward_Mult": 1.2},
        # Interceptor - basis der Boss-Stufe 5 (TARNJAEGER, eigene Werte
        # in BOSS_DATA); hier die regulier-Excel-Zeile
        "interceptor": {"Base_HP": 40, "Base_Speed": 80, "Base_Damage": 8,
                        "Base_Reward": 15, "Min_Ship_Level": 1,
                        "Spawn_Weight": 10, "HP_Add_Per_Stage": 20,
                        "HP_Mult_Per_Stage": 1.09, "Speed_Add_Per_Stage": 3,
                        "Damage_Add_Per_Stage": 2, "Idle_HP_Mult": 0.35,
                        "Idle_Speed_Mult": 0.6, "Idle_Reward_Mult": 1.1},
        # Alt-Excel-Datensatz OHNE Grafik (spawn nie, nur Beute-Mittel)
        "destroyer": {"Base_HP": 150, "Base_Speed": 20, "Base_Damage": 25,
                      "Base_Reward": 50, "Min_Ship_Level": 1,
                      "Spawn_Weight": 5, "HP_Add_Per_Stage": 60,
                      "HP_Mult_Per_Stage": 1.12, "Speed_Add_Per_Stage": 0.5,
                      "Damage_Add_Per_Stage": 5, "Idle_HP_Mult": 0.3,
                      "Idle_Speed_Mult": 0.4, "Idle_Reward_Mult": 1.5},
        # Gruener Kreuzer - schwerer Trefferblock (Elite-Gegner, PVE88)
        "carrier": {"Base_HP": 190, "Base_Speed": 22, "Base_Damage": 15,
                    "Base_Reward": 58, "Min_Ship_Level": 8,
                    "Spawn_Weight": 8, "HP_Add_Per_Stage": 24,
                    "HP_Mult_Per_Stage": 1.06, "Speed_Add_Per_Stage": 0.15,
                    "Damage_Add_Per_Stage": 2.0, "Idle_Reward_Mult": 1.15},
        # Alt-Excel-Datensatz OHNE Grafik (spawn nie, nur Beute-Mittel)
        "bomber": {"Base_HP": 60, "Base_Speed": 40, "Base_Damage": 20,
                   "Base_Reward": 30, "Min_Ship_Level": 1,
                   "Spawn_Weight": 8, "HP_Add_Per_Stage": 30,
                   "HP_Mult_Per_Stage": 1.09, "Speed_Add_Per_Stage": 1,
                   "Damage_Add_Per_Stage": 4, "Idle_HP_Mult": 0.35,
                   "Idle_Speed_Mult": 0.5, "Idle_Reward_Mult": 1.2},
        # Alt-Excel-Datensatz OHNE Grafik (spawn nie, nur Beute-Mittel)
        "frigate": {"Base_HP": 100, "Base_Speed": 35, "Base_Damage": 12,
                    "Base_Reward": 40, "Min_Ship_Level": 1,
                    "Spawn_Weight": 6, "HP_Add_Per_Stage": 50,
                    "HP_Mult_Per_Stage": 1.11, "Speed_Add_Per_Stage": 1.5,
                    "Damage_Add_Per_Stage": 3, "Idle_HP_Mult": 0.3,
                    "Idle_Speed_Mult": 0.5, "Idle_Reward_Mult": 1.4},
        # Alt-Excel-Datensatz OHNE Grafik; ECHTE Bosse laufen ueber
        # BOSS_DATA (Stufe 5/10/15), dieser Schluessel ist nur Reserve
        "boss": {"Base_HP": 500, "Base_Speed": 15, "Base_Damage": 50,
                 "Base_Reward": 150, "Min_Ship_Level": 1,
                 "Spawn_Weight": 1, "HP_Add_Per_Stage": 200,
                 "HP_Mult_Per_Stage": 1.15, "Speed_Add_Per_Stage": 0.5,
                 "Damage_Add_Per_Stage": 10, "Idle_HP_Mult": 0.1,
                 "Idle_Speed_Mult": 0.3, "Idle_Reward_Mult": 2.0},
        # PVE88-TYPEN (steht 1:1 auch in game_data.xlsx):
        # Insektenbrut - flotter Nahkaempfer, mittlere Huelle
        "stalker": {"Base_HP": 48, "Base_Speed": 78, "Base_Damage": 9,
                    "Base_Reward": 24, "Min_Ship_Level": 4,
                    "Spawn_Weight": 15, "HP_Add_Per_Stage": 11,
                    "HP_Mult_Per_Stage": 1.05, "Speed_Add_Per_Stage": 0.5,
                    "Damage_Add_Per_Stage": 1.5, "Idle_Reward_Mult": 1.0},
        # Qualle - langsam, tanky, treibt heran
        "medusa": {"Base_HP": 110, "Base_Speed": 30, "Base_Damage": 11,
                   "Base_Reward": 38, "Min_Ship_Level": 6,
                   "Spawn_Weight": 11, "HP_Add_Per_Stage": 17,
                   "HP_Mult_Per_Stage": 1.06, "Speed_Add_Per_Stage": 0.2,
                   "Damage_Add_Per_Stage": 1.7, "Idle_Reward_Mult": 1.1},
        # Cthulhu-Auge - spaeter Haertling, hoher Schaden
        "eye": {"Base_HP": 150, "Base_Speed": 42, "Base_Damage": 17,
                "Base_Reward": 52, "Min_Ship_Level": 10,
                "Spawn_Weight": 8, "HP_Add_Per_Stage": 22,
                "HP_Mult_Per_Stage": 1.06, "Speed_Add_Per_Stage": 0.3,
                "Damage_Add_Per_Stage": 2.3, "Idle_Reward_Mult": 1.15},
        # Kristallkluft - sehr tanky, sehr langsam (Endgame-Block)
        "crystal": {"Base_HP": 260, "Base_Speed": 16, "Base_Damage": 13,
                    "Base_Reward": 70, "Min_Ship_Level": 12,
                    "Spawn_Weight": 6, "HP_Add_Per_Stage": 30,
                    "HP_Mult_Per_Stage": 1.07, "Speed_Add_Per_Stage": 0.1,
                    "Damage_Add_Per_Stage": 2.0, "Idle_Reward_Mult": 1.2},
        # AUFTRAG 21: FREIGESCHALTET (waren geparkt mit Min_Ship_Level 99).
        # Sektor-10-13-Gate = sie erscheinen natuerlich im Endgame
        # (Sektor 5-8); Sektor 1-4-Erst-Spiele (Schiff < 10) bleiben
        # unveraendert - Pool und Seed-Paarungen identisch zum Vorbild.
        # Kristall-Abfangjaeger (gruen, Asteroidenguertel-Palette)
        "shard": {"Base_HP": 30, "Base_Speed": 72, "Base_Damage": 6,
                  "Base_Reward": 26, "Min_Ship_Level": 10,
                  "Spawn_Weight": 20, "HP_Add_Per_Stage": 8,
                  "HP_Mult_Per_Stage": 1.05, "Speed_Add_Per_Stage": 0.5,
                  "Damage_Add_Per_Stage": 1.4, "Idle_Reward_Mult": 1.0},
        # Tarnkopf-Dart (violett, Dunkler-Sektor-Palette)
        "wraith": {"Base_HP": 40, "Base_Speed": 95, "Base_Damage": 8,
                   "Base_Reward": 32, "Min_Ship_Level": 11,
                   "Spawn_Weight": 14, "HP_Add_Per_Stage": 9,
                   "HP_Mult_Per_Stage": 1.05, "Speed_Add_Per_Stage": 0.6,
                   "Damage_Add_Per_Stage": 1.6, "Idle_Reward_Mult": 1.1},
        # Panzerkanonenboot (magenta-rot, Raumstation-Palette)
        "husk": {"Base_HP": 64, "Base_Speed": 36, "Base_Damage": 10,
                 "Base_Reward": 40, "Min_Ship_Level": 12,
                 "Spawn_Weight": 16, "HP_Add_Per_Stage": 14,
                 "HP_Mult_Per_Stage": 1.06, "Speed_Add_Per_Stage": 0.3,
                 "Damage_Add_Per_Stage": 1.8, "Idle_Reward_Mult": 1.05},
        # Bio-Traeger (biolumineszent gruen, Feindsignale-Palette)
        "hive": {"Base_HP": 130, "Base_Speed": 24, "Base_Damage": 13,
                 "Base_Reward": 60, "Min_Ship_Level": 13,
                 "Spawn_Weight": 8, "HP_Add_Per_Stage": 20,
                 "HP_Mult_Per_Stage": 1.07, "Speed_Add_Per_Stage": 0.2,
                 "Damage_Add_Per_Stage": 2.2, "Idle_Reward_Mult": 1.15},
    }


# PAKET 8.8: NEUE GEGNER AUS DEN ALTEN BOSS-GRAFIKEN DES NUTZERS.
# Die Grafiken (enemys/enemy_<key>.png) liefert der Nutzer - sie waren
# bisher nirgends registriert. PUNKT-4-ABGLEICH: Diese 5 Typen stehen
# jetzt 1:1 auch in game_data.xlsx (Sheet Enemies, inkl. carrier auf
# diesem Stand statt der alten Alt-Excel-Zeile) - bei der abgeglichenen
# Excel ist der update() unten eine No-Op (Werte identisch); er bleibt
# als Schutz aktiv, falls eine AELTERE game_data.xlsx (ohne die Spalte
# Min_Ship_Level oder ohne diese Zeilen) eingesetzt wird.
PVE88_ROSTER = {
    # Insektenbrut - flotter Nahkaempfer, mittlere Huelle
    "stalker": {"Base_HP": 48, "Base_Speed": 78, "Base_Damage": 9,
                "Base_Reward": 24, "Min_Ship_Level": 4,
                "Spawn_Weight": 15, "HP_Add_Per_Stage": 11,
                "HP_Mult_Per_Stage": 1.05, "Speed_Add_Per_Stage": 0.5,
                "Damage_Add_Per_Stage": 1.5, "Idle_Reward_Mult": 1.0},
    # Qualle - langsam, tanky, treibt heran
    "medusa": {"Base_HP": 110, "Base_Speed": 30, "Base_Damage": 11,
               "Base_Reward": 38, "Min_Ship_Level": 6,
               "Spawn_Weight": 11, "HP_Add_Per_Stage": 17,
               "HP_Mult_Per_Stage": 1.06, "Speed_Add_Per_Stage": 0.2,
               "Damage_Add_Per_Stage": 1.7, "Idle_Reward_Mult": 1.1},
    # Gruener Kreuzer - schwerer Trefferblock (Elite-Gegner)
    "carrier": {"Base_HP": 190, "Base_Speed": 22, "Base_Damage": 15,
                "Base_Reward": 58, "Min_Ship_Level": 8,
                "Spawn_Weight": 8, "HP_Add_Per_Stage": 24,
                "HP_Mult_Per_Stage": 1.06, "Speed_Add_Per_Stage": 0.15,
                "Damage_Add_Per_Stage": 2.0, "Idle_Reward_Mult": 1.15},
    # Cthulhu-Auge - spaeter Haertling, hoher Schaden
    "eye": {"Base_HP": 150, "Base_Speed": 42, "Base_Damage": 17,
            "Base_Reward": 52, "Min_Ship_Level": 10,
            "Spawn_Weight": 8, "HP_Add_Per_Stage": 22,
            "HP_Mult_Per_Stage": 1.06, "Speed_Add_Per_Stage": 0.3,
            "Damage_Add_Per_Stage": 2.3, "Idle_Reward_Mult": 1.15},
    # Kristallkluft - sehr tanky, sehr langsam (Endgame-Block)
    "crystal": {"Base_HP": 260, "Base_Speed": 16, "Base_Damage": 13,
                "Base_Reward": 70, "Min_Ship_Level": 12,
                "Spawn_Weight": 6, "HP_Add_Per_Stage": 30,
                "HP_Mult_Per_Stage": 1.07, "Speed_Add_Per_Stage": 0.1,
                "Damage_Add_Per_Stage": 2.0, "Idle_Reward_Mult": 1.2},
}
ENEMY_DATA.update(PVE88_ROSTER)

# ----------------------------------------------------------------------
# AUFTRAG 21: TYP-EIGENE VERHALTENS- & FX-TABELLEN (reine Code-Daten,
# keine neuen Grafik-Assets). Jeder Normal-Gegnertyp bekommt:
#   * eigene BEWEGUNG (Logik, nicht nur Zeichnung): bob (Auf/Ab),
#     sway (leichtes seitliches Schlingern) - Kollisionen/Targeting
#     folgen e.x/e.y, also bewusst in der Logik.
#   * eigene SCHUSS-CHARAKTERISTIK (Feuerrate, Projektil-Tempo/Groesse).
#   * die vier neu freigeschalteten Typen je ein EIGENES Angriffs-
#     muster: shard = Zickzack + Doppelschuss, wraith = Phasen-DASH,
#     husk = KAMIKAZE-Rammstoss (fliegt bis zur Festung durch),
#     hive = Faecher-Salve (3 Projektile).
# Bestandstypen bleiben bewusst NAH am bisherigen Charakter (kleine
# Amplituden, Feuerraten um den alten 1.5-3.0 s-Band), damit die
# Sektor 1-5-Balance nicht kippt (Simulation beweist es).
ENEMY_BEHAVIOR = {
    #            bob_amp bob_f  sway_amp sway_f   cd_lo cd_hi proj_speed proj_size
    "skitter":     dict(bob_amp=9.0, bob_f=2.3, sway_amp=6.0, sway_f=2.0,
                        cd=(1.1, 2.0), proj_speed=270.0, proj_size=4),
    "lancer":      dict(bob_amp=5.0, bob_f=1.1, sway_amp=4.0, sway_f=1.0,
                        cd=(1.6, 3.0), proj_speed=240.0, proj_size=5),
    "interceptor": dict(bob_amp=7.0, bob_f=2.0, sway_amp=10.0, sway_f=2.6,
                        cd=(1.3, 2.4), proj_speed=300.0, proj_size=4),
    "bomber":      dict(bob_amp=4.0, bob_f=0.9, sway_amp=3.0, sway_f=0.8,
                        cd=(1.8, 3.2), proj_speed=210.0, proj_size=7),
    "frigate":     dict(bob_amp=5.0, bob_f=1.0, sway_amp=5.0, sway_f=1.1,
                        cd=(1.7, 3.1), proj_speed=250.0, proj_size=5),
    "destroyer":   dict(bob_amp=3.0, bob_f=0.7, sway_amp=2.0, sway_f=0.5,
                        cd=(2.0, 3.4), proj_speed=230.0, proj_size=7),
    "stalker":     dict(bob_amp=8.0, bob_f=2.6, sway_amp=8.0, sway_f=2.4,
                        cd=(1.2, 2.3), proj_speed=280.0, proj_size=4),
    "medusa":      dict(bob_amp=6.0, bob_f=1.3, sway_amp=4.0, sway_f=0.9,
                        cd=(1.5, 2.9), proj_speed=220.0, proj_size=5),
    "carrier":     dict(bob_amp=3.0, bob_f=0.8, sway_amp=2.0, sway_f=0.6,
                        cd=(1.9, 3.3), proj_speed=240.0, proj_size=6),
    "eye":         dict(bob_amp=5.0, bob_f=1.5, sway_amp=6.0, sway_f=1.4,
                        cd=(1.4, 2.7), proj_speed=290.0, proj_size=5),
    "crystal":     dict(bob_amp=3.0, bob_f=0.8, sway_amp=2.0, sway_f=0.6,
                        cd=(1.8, 3.2), proj_speed=230.0, proj_size=6),
    # --- AUFTRAG 21: die vier freigeschalteten Typen mit EIGENEM Muster ---
    "shard":       dict(bob_amp=14.0, bob_f=3.4, sway_amp=10.0, sway_f=3.0,
                        cd=(1.0, 1.8), proj_speed=330.0, proj_size=4,
                        pattern="zigzag"),     # Zickzack + Doppelschuss
    "wraith":      dict(bob_amp=6.0, bob_f=1.8, sway_amp=6.0, sway_f=1.6,
                        cd=(1.3, 2.5), proj_speed=310.0, proj_size=4,
                        pattern="dash"),       # Phasen-DASH Richtung Festung
    "husk":        dict(bob_amp=4.0, bob_f=1.0, sway_amp=3.0, sway_f=0.7,
                        cd=(1.7, 3.0), proj_speed=250.0, proj_size=6,
                        pattern="kamikaze"),   # Rammt bis zur Festung
    "hive":        dict(bob_amp=5.0, bob_f=0.9, sway_amp=3.0, sway_f=0.8,
                        cd=(2.2, 3.6), proj_speed=230.0, proj_size=5,
                        pattern="fan"),        # 3er-Faecher-Salve
}

# FX-Palette je Typ (Treffer-Glitzer + Explosionsfarbe) - passend zur
# vorhandenen Sprite-Palette, keine neuen Assets:
ENEMY_FX_COL = {
    "skitter": (170, 255, 120), "lancer": (255, 210, 90),
    "interceptor": (130, 200, 255), "bomber": (255, 120, 60),
    "frigate": (150, 220, 170), "destroyer": (255, 90, 70),
    "stalker": (200, 255, 110), "medusa": (255, 140, 220),
    "carrier": (120, 255, 150), "eye": (255, 70, 110),
    "crystal": (110, 220, 255), "shard": (140, 255, 190),
    "husk": (255, 110, 200), "wraith": (190, 120, 255),
    "hive": (120, 255, 140), "boss": (255, 170, 0),
}

# PAKET 8.8: BOSSE. Vorher gab es nur DEN Einen Boss (Stufe 15, lancer,
# HP x0.7 abgeschwaecht, EIN gezielter Schuss alle 1,5-3 s) - bei
# Endgame-DPS tot in Sekunden ("Der Boss ist viel zu einfach"). Jetzt:
#   Stufe 5  - TARNJAEGER   (interceptor, 3er-Fächer, schnell)
#   Stufe 10 - SCHLACHTSCHIFF (brute, 5er-Fächer + Schwerer Schuss)
#   Stufe 15 - EISDRACHE    (dragon, 5er-Fächer, WUT-Phase unter 50 %)
# Jeder Boss: Panzerung (dr = prozentuale Schadensreduktion), eigenes
# Feuer-Muster (_boss_shoot), hoher Schaden, fette Beute.
BOSS_DATA = {
    # AUFTRAG 16 (2. DURCHLAUF): KAMPAGNE 1 MIT SCHIFF L4-5 SCHAFFBAR.
    # Nutzer: "Bereits Kampagne 1 verlangt praktisch ein Schiff auf
    # Level 7 und vergleichbar hoch gelevelte Module." Ursache: die
    # Boss-HP wuchsen mit hp_mult^Stufe unabhaengig vom Sektor - Stufe
    # 10/15 verlangten Schiff L8-12 (siehe alte Simulator-Profile).
    # Neu (Simulation tools/simulate_boss.py + simulate_campaign.py,
    # passives Ausweich-Modell):
    #   Stufe 5  TARNJAEGER    : unveraendert - Schiff 4 gewinnt sicher
    #   Stufe 10 SCHLACHTSCHIFF: HP 2600->1500, dmg 42->26
    #                            Schiff 4-5 gewinnt, knapp-Prof. "hart"
    #   Stufe 15 EISDRACHE     : HP 2600-> 700, dmg 55->28
    #                            Schiff 4-5 gewinnt (Finale ~25-30 s TTK)
    # Zusaetzlich unterliegen Atem/Bomben/Spiesse jetzt BAL_ENEMY_DMG
    # (siehe _boss_fx_dmg) und Sektor 2-5 skalieren mit CAMPAIGN_*_MULT
    # (rpg_config) - jede weitere Kampagne wird spuerbar schwerer.
    5:  {"type": "interceptor", "name": "TARNJÄGER",
         "base_hp": 950, "hp_mult": 1.18, "dr": 0.10, "speed": 34,
         "damage": 24, "reward": 200, "col": (176, 120, 255)},
    10: {"type": "brute", "name": "SCHLACHTSCHIFF",
         "base_hp": 1500, "hp_mult": 1.18, "dr": 0.15, "speed": 26,
         "damage": 26, "reward": 400, "col": (255, 80, 60)},
    15: {"type": "dragon", "name": "EISDRACHE",
         "base_hp": 700, "hp_mult": 1.18, "dr": 0.20, "speed": 30,
         "damage": 26, "reward": 750, "col": (130, 225, 255)},
}

# Feuer-Muster je Boss-TYP (Typen sind exklusiv den Bossen vorbehalten):
#   fan      : Projektile je Salve (Winkel-Fächer um das Schiff)
#   spread   : Fächer-Gesamtwinkel in Grad
#   cadence  : Sekunden pro Salve (Zufall zwischen min/max)
#   b_speed  : Projektil-Tempo (normal: 250)
#   heavy    : jeder 3. Salve zusaetzlich ein SCHWERER gezielter Schuss
BOSS_TYPE_CFG = {
    "interceptor": {"fan": 3, "spread": 26.0, "cadence": (1.15, 1.6),
                    "b_speed": 290.0, "size": 6, "heavy": False},
    # AUFTRAG 16b: SCHLACHTSCHIFF/EISDRACHE - Salvenpausen vergroessert
    # (vorher 1.5-2.1 / 1.5-2.0). Grund: im passiven Ausweich-Modell lag
    # die erlittene Dauerlast knapp ueber der Ueberlebenszeit von
    # Schiff-4-Profilen; mit laengeren Pausen gewinnt Reaktivieren
    # (Reparatur-Drohnen) die Kante zurueck, das Angriffsmuster bleibt.
    "brute":        {"fan": 5, "spread": 55.0, "cadence": (1.9, 2.6),
                     "b_speed": 265.0, "size": 7, "heavy": True},
    "dragon":       {"fan": 5, "spread": 60.0, "cadence": (1.9, 2.5),
                     "b_speed": 275.0, "size": 7, "heavy": True},
}

# AUFTRAG 19 (PUNKT 2): Eigenstaendige Boss-Belegung der SEKTOREN 6-8.
# Sektor 1-5 bleiben bei BOSS_DATA (unveraendert). Fuer 6-8 wird dieselbe
# Drei-Bosse-Struktur (Stufe 5/10/15) mit den VORHANDENEN drei Boss-Typen
# (interceptor/brute/dragon, gleiche Grafiken und Feuer-Muster) in neuer
# Reihenfolge und mit eigenen Namen/Werten gefuert - keine neuen Assets.
# Die Basen sind bewusst KLEINER gewaehlt als bei Sektor 1, weil
# boss_stats_for_stage mit CAMPAIGN_HP_MULT (6.25 in Sektor 8) und
# hp_mult^Stufe (1.18^15) multipliziert - Simulationstest:
# tools/simulate_boss.py (Sektor-Uebersicht) / tools/simulate_campaign.py.
#   Sektor 6 "DER RISS":     St5 SPLITTERJAEGER / St10 RINGKREUZER /
#                            St15 ABYSSDRACHE
#   Sektor 7 "NEBELKERN":    St5 NEBELBOLLWERK / St10 NEBELDRACHE /
#                            St15 SPLITTERKOENIG (schnelles Finale)
#   Sektor 8 "KERNWELT":     St5 KERNBRUT / St10 SCHWARMHEROLD /
#                            St15 KERNHERRSCHER (gepanzertes Finale)
BOSS_SECTOR_DATA = {
    6: {
        5:  {"type": "interceptor", "name": "SPLITTERJÄGER",
             "base_hp": 1150, "hp_mult": 1.18, "dr": 0.12, "speed": 34,
             "damage": 26, "reward": 260, "col": (176, 120, 255)},
        10: {"type": "brute", "name": "RINGKREUZER",
             "base_hp": 750, "hp_mult": 1.18, "dr": 0.18, "speed": 26,
             "damage": 30, "reward": 520, "col": (255, 80, 60)},
        15: {"type": "dragon", "name": "ABYSSDRACHE",
             "base_hp": 1100, "hp_mult": 1.18, "dr": 0.24, "speed": 30,
             "damage": 30, "reward": 950, "col": (130, 225, 255)},
    },
    7: {
        5:  {"type": "brute", "name": "NEBELBOLLWERK",
             "base_hp": 900, "hp_mult": 1.18, "dr": 0.14, "speed": 26,
             "damage": 28, "reward": 320, "col": (255, 80, 60)},
        10: {"type": "dragon", "name": "NEBELDRACHE",
             "base_hp": 650, "hp_mult": 1.18, "dr": 0.20, "speed": 30,
             "damage": 32, "reward": 640, "col": (130, 225, 255)},
        15: {"type": "interceptor", "name": "SPLITTERKÖNIG",
             "base_hp": 950, "hp_mult": 1.18, "dr": 0.26, "speed": 34,
             "damage": 34, "reward": 1200, "col": (176, 120, 255)},
    },
    8: {
        5:  {"type": "dragon", "name": "KERNBRUT",
             "base_hp": 800, "hp_mult": 1.18, "dr": 0.16, "speed": 30,
             "damage": 30, "reward": 400, "col": (130, 225, 255)},
        10: {"type": "interceptor", "name": "SCHWARMHEROLD",
             "base_hp": 550, "hp_mult": 1.18, "dr": 0.22, "speed": 34,
             "damage": 34, "reward": 800, "col": (176, 120, 255)},
        15: {"type": "brute", "name": "KERNHERRSCHER",
             "base_hp": 800, "hp_mult": 1.18, "dr": 0.30, "speed": 26,
             "damage": 38, "reward": 1600, "col": (255, 80, 60)},
    },
}


def boss_cfg_for(campaign_id, stage_id):
    """EINE Quelle fuer die Boss-Belegung (AUFTRAG 19): Sektor 1-5 nutzt
    die historische Tabelle BOSS_DATA (unveraendert), Sektor 6-8 ihre
    eigene Tabelle BOSS_SECTOR_DATA. Nicht-Boss-Stufen -> None. Alle
    Leser (pve_system, main, Simulatoren) rufen DIESE Funktion - nie
    BOSS_DATA direkt."""
    st = int(stage_id)
    sec = BOSS_SECTOR_DATA.get(max(1, int(campaign_id)))
    if sec and st in sec:
        return sec[st]
    return BOSS_DATA.get(st)

# PAKET 8.8a: TREFFERRADIUS der Bosse. Die Bosse sind fuer die Praesenz
# deutlich groesser gezeichnet (ENEMY_IMG_W in main.py: 150/195/235) -
# die alte Starre-Zone von 30 waere nur noch ein Punkt in der Mitte.
# Die Trefferzone waechst mit: groesseres Ziel, fairer Treffwechsel.
# Normal-Gegner bleiben bei 30.
# HOTFIX A2 (nachgezogen): Der Eisdrache wurde auf 300 Pixel Breite
# vergroessert (ENEMY_IMG_W dragon 235 -> 300 in main.py). Damit die
# Trefferzone mitwaechst, gilt der A2-Wert 75 (statt 60).
BOSS_HIT_R = {"interceptor": 46, "brute": 54, "dragon": 75}

# PAKET 8.8b: FLAMMENDER ATEM des EISDRACHEN. Der Drache benutzt KEINE
# Kugel-Projektile mehr (Nutzerwunsch: "Ein Strahl waere richtig hammer.
# Oder ein flammender Atem. aber nicht diese Kugeln."). Ablauf:
#   Telegraf (~0,6 s): Mund glimmt auf, Ziellinie folgt noch dem Schiff
#   Zuendung: Richtung FRIEREN eingefroren - wer sich bewegt, weicht aus
#   Strahl (~1 s): Schaden pro Tick im Kegel, Glut-Partikel, Impact-FX
# Danach Pause (BREATH_CD), in der Wut-Phase kuerzer/staerker/laenger.
BREATH_TELEGRAPH_S = 0.62   # Mund glimmt, Ziel folgt dem Schiff
BREATH_ACTIVE_S = 0.95      # Strahl brennt (normal)
BREATH_ACTIVE_RAGE_S = 1.25 # Strahl brennt laenger in der Wut-Phase
BREATH_RANGE = 640.0        # Reichweite in Welt-px
BREATH_HALF_ANGLE = 0.32    # Kegel-Halbwinkel in rad (~18 Grad)
BREATH_DPS = 46.0           # Schaden pro Sekunde im Strahl
BREATH_DPS_RAGE_MULT = 1.3  # ... in der Wut-Phase
BREATH_TICK_S = 0.25        # Schadens-Tick alle 0,25 s
BREATH_CD = (2.6, 3.4)      # Pause zwischen zwei Atem-Attacken (s)
BREATH_CD_RAGE = (1.7, 2.3) # ... in der Wut-Phase

# PAKET 8.8c: BOSS-REPERTOIRE & ABSTAND. Nutzerfeedback: "Der Boss kommt
# jedoch viel zu nahe zum Schluss. Der Kampf ist auch viel zu monoton.
# Der Boss sollte eine Bandbreite an verschiedenen Angriffen haben,
# zumindest 2 weitere. der Boss sollte auch etwas mehr nach oben und
# unten sich bewegen."
#   BOSS_HOLD_X : Bosse stoppen WEITER DRAUSSEN als Normalgegner (400) -
#                 die Schnauze bleibt klar vom Schiff weg, auch am Ende.
#   BOSS_MOVE_* : echte Auf/Ab-Bewegung (vorher nur 4 px Zeichnungs-Bob):
#                 zwei ueberlagerte, langsame Sinuswellen wirken majestaetisch
#                 und lassen den Atem manchmal am Schiff vorbei ziehen.
#   BOMB_*      : GLUTBOMBEN - bogenfliegende Feuerbomben mit AoE-Explosion
#                 (EISDRACHE + SCHLACHTSCHIFF).
#   SPIKE_*     : EISSPIESSE - telegrafierte Eruptionen aus dem Untergrund
#                 (EISDRACHE + TARNJAEGER).
BOSS_HOLD_X = {"interceptor": 520.0, "brute": 545.0, "dragon": 560.0}
BOSS_MOVE_AMP = 55.0         # Haupt-Amplitude (px)
BOSS_MOVE_AMP2 = 18.0        # Neben-Amplitude (Unregelmaessigkeit)
BOSS_MOVE_SPD = 0.42         # rad/s -> ~15 s pro Haupt-Schwingung
BOSS_MOVE_SPD2 = 0.83        # zweite Welle
BOSS_Y_MIN, BOSS_Y_MAX = 150.0, 390.0

BOMB_TELEGRAPH_S = 0.55      # Mund gloht, Zielmarken pulsieren (s)
BOMB_COUNT = 3               # +2 in der Wut-Phase
BOMB_ARC_T = (0.85, 1.10)    # Flugzeit je Bombe (s)
BOMB_ARC_H = 150.0           # Bogenhoehe (px)
BOMB_DMG = 34.0              # Schaden je Explosion (vor Modul-DR)
BOMB_AOE_R = 95.0            # Explosions-Radius
BOMB_CD = (2.2, 3.0)         # eigener Rhythmus (neben Atem/Faecher)
BOMB_CD_RAGE = (1.6, 2.2)

SPIKE_TELEGRAPH_S = 0.70     # Warnringe + Spalten-Markierung (s)
SPIKE_RISE_S = 0.40          # Ausbruchsdauer (s)
SPIKE_COUNT = 3              # +1 in der Wut-Phase
SPIKE_DMG = 30.0             # Schaden je Spitze (vor Modul-DR)
SPIKE_R = 52.0               # Treffer-Halbbreite der Spalte
SPIKE_HIT_CHANCE = 0.45      # Chance, dass eine Spitze die Schiffs-Spalte trifft
SPIKE_CD = (2.4, 3.2)
SPIKE_CD_RAGE = (1.7, 2.3)

# SCHRITT 3: Die BAL_*-Koeffizienten (PAKET 4/8.4/8.7: Spieler-/Gegner-
# Skalierung, Oekonomie-Bremskloetze, Fahrendaempfung) stehen jetzt im
# BALANCE-Block von rpg_config.py und werden oben importiert. Die
# ERKLAERUNGSDOKUMENTATION dazu steht dort mit.

# PAKET 8.7: KAMPAGNE-FAHRENDAEMPFUNG (Nutzer-Feedback: "Obwohl alles
# auf Lvl 3/4 und Kanonen Lvl 7, schaffe ich Stufe 12/13 nicht").
# Die Gegner skalierten hart weiter (Stufe 12: 14 Gegner, Stufe 13: 15),
# waehrend die Preise die Upgrades drosseln. Zwei Stellschrauben:
#   1. Weniger Gegner je Stufe: count = 2 + max(1, round(stage * 0.72))
#      (Stufe 1 -> 3, Stufe 5 -> 6, Stufe 8 -> 8, Stufe 10 -> 9,
#       Stufe 12/13 -> 11 statt 14/15)
#   2. Daempfung von HP (+Schaden) ab Stufe 9, kumulativ je Stufe:
#      (BAL_LATE_STAGE_* aus rpg_config)
# Fruehe Stufen (1-8) bleiben unveraendert - dort war das Gefuehl gut.
ENEMY_COUNT_PER_STAGE = 0.72     # Gegner = 2 + max(1, round(stage * dies))


def stage_enemy_count(stage_id):
    """PAKET 8.7: Gegnerzahl einer aktiven Kampagnen-Stufe (kein Boss)."""
    return 2 + max(1, int(round(max(1, int(stage_id)) * ENEMY_COUNT_PER_STAGE)))


# AUFTRAG 16b: KAMPAGNEN-SKALIERUNG - kleine Lesehelfer (Sektor 1-5).
def campaign_hp_mult(campaign_id):
    return float(CAMPAIGN_HP_MULT.get(max(1, int(campaign_id)), 1.0))


def campaign_dmg_mult(campaign_id):
    return float(CAMPAIGN_DMG_MULT.get(max(1, int(campaign_id)), 1.0))


def campaign_reward_mult(campaign_id):
    return float(CAMPAIGN_REWARD_MULT.get(max(1, int(campaign_id)), 1.0))


def campaign_spawn_mult(campaign_id):
    """Faktor auf das Spawn-Intervall (kleiner = Gegner kommen schneller)."""
    return float(CAMPAIGN_SPAWN_SPD.get(max(1, int(campaign_id)), 1.0))


def boss_stats_for_stage(stage_id, campaign_id=1):
    """AUFTRAG 16b: Boss-Grundwerte (HP, Schaden, Beute) einer Stufe,
    inkl. Kampagnen-Skalierung - die EINE Quelle fuer Spiel UND
    Simulatoren (kein Formel-Doppel mehr). liefert None, wenn die Stufe
    kein Bossgefecht ist."""
    cfg = boss_cfg_for(campaign_id, stage_id)
    if cfg is None:
        return None
    hp = float(cfg["base_hp"]) * (float(cfg["hp_mult"]) ** int(stage_id)) \
        * BAL_BOSS_HP * campaign_hp_mult(campaign_id)
    dmg = float(cfg["damage"]) * BAL_ENEMY_DMG * campaign_dmg_mult(campaign_id)
    reward = int(round(float(cfg["reward"]) * campaign_reward_mult(campaign_id)))
    return hp, dmg, reward


def stage_late_hp_factor(stage_id):
    return BAL_LATE_STAGE_HP ** max(0, int(stage_id) - 8)


def stage_late_dmg_factor(stage_id):
    return BAL_LATE_STAGE_DMG ** max(0, int(stage_id) - 8)


def stage_nominal_reward(stage_id, ship_level=12, campaign_id=1):
    """SCHRITT 3b: Nominaler Kill-Ertrag einer Stufe (VOR allen
    Multiplikatoren wie BAL_CREDITS/idle_pct). Gewichtetes Mittel des
    Spawn-Pools (Min_Ship_Level-Gate + Spawn_Weight, ohne PNG-Pruefung
    - deterministisch), mit derselben Reward-Formel wie
    _spawn_single_enemy: (Base_Reward + Stufe*2) * Idle_Reward_Mult,
    AUFTRAG 16b: x Kampagnen-Beute-Faktor (Idle ruft mit Sektor 1 ->
    dort unveraendert x1.0). Genutzt vom Offline-Idle-Bericht
    (main._compute_idle_report) und vom Oekonomie-Simulator
    (tools/simulate_economy.py)."""
    stage_id = max(1, int(stage_id))
    ship_level = max(1, int(ship_level))
    pool = [d for d in ENEMY_DATA.values()
            if ship_level >= int(d.get("Min_Ship_Level", 1))
            and float(d.get("Spawn_Weight", 10)) > 0]
    if not pool:
        pool = [{"Base_Reward": 10, "Idle_Reward_Mult": 1.0}]
    total_w = sum(float(d.get("Spawn_Weight", 10)) for d in pool)
    avg = 0.0
    for d in pool:
        w = float(d.get("Spawn_Weight", 10)) / total_w
        r = (float(d.get("Base_Reward", 10)) + stage_id * 2) \
            * float(d.get("Idle_Reward_Mult", 1.0))
        avg += w * r
    avg *= campaign_reward_mult(campaign_id)   # AUFTRAG 16b
    return int(avg)

@dataclass
class Enemy:
    name: str
    hp: float
    max_hp: float
    damage: int
    speed: float
    reward: int
    enemy_type: str
    x: float = 0.0
    y: float = 0.0
    attack_cooldown: float = 2.0
    hit_flash: float = 0.0
    # PAKET 8.8: Boss-Felder (nur bei Bossen gesetzt)
    is_boss: bool = False
    dr: float = 0.0            # Panzerung: 0..0.5 Schadensreduktion
    boss_cd: float = 0.0       # Salven-Timer
    volley: int = 0            # Salven-Zaehler (Schwerer Schuss je 3.)
    enraged: bool = False      # Eisdrache: Wut-Phase unter 50 % HP
    boss_col: tuple = (255, 60, 60)
    # PAKET 8.8b: Flammen-Atem des Eisdrachen (ersetzt Kugel-Faecher)
    breath_phase: int = 0      # 0 = Pause, 1 = Telegraf, 2 = Strahl aktiv
    breath_t: float = 0.0      # Restzeit der aktuellen Phase
    breath_ang: float = 0.0    # Strahl-Richtung (bei Zuendung FEST)
    breath_tick: float = 0.0   # Schadens-Tick-Timer im Strahl
    # PAKET 8.8c: Angriffs-Bandbreite + Bewegung (nur Bosse gesetzt)
    atk_cd: float = 3.5        # Timer der ZUSATZ-Angriffe (Bomben/Spiesse)
    atk_kind: int = 0          # laufender Zusatz-Angriff: 2 = Bomben, 3 = Spiesse
    atk_t: float = 0.0         # Restzeit des Telegrafen
    last_atk: int = -1         # letzter Zusatz-Angriff (keine Sofort-Wiederholung)
    bomb_marks: list = None    # geplante Einschlag-Ziele (waehrend Telegraf)
    spike_marks: list = None   # geplante Eruption-Spalten (waehrend Telegraf)
    base_y: float = 270.0      # Ruhelage der Vertikalbewegung
    move_phase: float = 0.0    # Phasenversatz der Sinuswellen
    mouth_open: bool = False   # Maul-Zustand (Drachen-Sprite offen/geschlossen)
    # AUFTRAG 21: Typ-eigene Bewegung & Angriffsmuster (Normal-Gegner)
    mv_phase: float = 0.0      # Phasenversatz Bob/Sway (Random je Spawn)
    pattern: str = "shot"      # "shot" (klassisch) | "zigzag" | "dash" | "kamikaze" | "fan"
    dash_t: float = 0.0        # wraith: Rest-Dauer des laufenden Dash
    dash_cd: float = 0.0       # wraith: Cooldown bis zum naechsten Dash
    kamikaze_hit: bool = False # husk: Kontakt-Schaden bereits ausgeloesst

@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    color: tuple
    size: int
    speed: float = 550.0
    kind: str = "player"
    is_drone: bool = False

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: tuple
    size: float
    life: float
    max_life: float

@dataclass
class DamageNumber:
    """NEU PAKET 4: Schwebende Schadenszahl am Trefferpunkt."""
    x: float
    y: float
    value: str
    color: tuple
    life: float = 0.9
    max_life: float = 0.9
    vy: float = -46.0
    big: bool = False

@dataclass
class BossBomb:
    """PAKET 8.8c: bogenfliegende GLUTBOMBE eines Bosses. Fliegt auf einer
    quadratischen Kurve vom Maul zum Einschlag und explodiert mit AoE-
    Schaden (faellt gegen die Entfernung ab). main.py zeichnet Komet +
    Glut-Schweif + Impact; Logik/Schaden liegen hier."""
    sx: float
    sy: float
    tx: float
    ty: float
    T: float = 1.0             # Flugzeit (s)
    t: float = 0.0
    damage: float = 34.0
    col: tuple = (255, 120, 40)

@dataclass
class BossSpike:
    """PAKET 8.8c: EISSPIESS-Eruption aus dem Untergrund. Die Spalte bei
    x wird telegrafiert (Warnring + gestrichelte Linie, main.py), dann
    bricht die Saeule hoch und trifft EINMAL, wenn sie die Schiffs-Spalte
    durchstoessen wuerde (|Schiff.x - x| < SPIKE_R)."""
    x: float
    t: float = 0.0
    damage: float = 30.0
    col: tuple = (130, 225, 255)
    hit_done: bool = False

@dataclass
class DroneUnit:
    """PAKET 7C: Echte Hangar-Drohne als eigene Einheit.
    Kreist um das Schiff, zielt selbststaendig und feuert magenta Projektile
    (is_drone=True). main.py zeichnet sie sichtbar - sie sind keine blossen
    Zahlen/Icons mehr. spawn_t (0..1) steuert den Einflug/Scale-In."""
    idx: int
    x: float
    y: float
    phase: float
    fire_cd: float
    spawn_t: float = 0.0
    angle: float = 0.0

class PvECombat:
    def __init__(self, is_idle=True, campaign_id=1, stage_id=1, ship_level=1,
                 is_repeat=False, ng_plus=0):
        self.is_idle = is_idle
        self.campaign_id = campaign_id
        self.stage_id = stage_id
        self.ship_level = ship_level
        # PAKET 7C: True = Stufe wurde bereits mindestens einmal beendet
        # (Main setzt das anhand completed_stages). Steuert die Core-Vergabe.
        self.is_repeat = bool(is_repeat)
        # AUFTRAG 6: NEW GAME+ Grad (0 = erster Durchlauf). Skaliert Gegner,
        # Bosse und Beute (rpg_config.NG_*); main.py setzt ihn beim Sync.
        self.ng_plus = max(0, int(ng_plus))
        
        self.credits = 0
        self.idle_loot_earned = 0 
        self.stage_cleared = False # NEU: Flag für abgeschlossene Stufe
        
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.particles: list[Particle] = []
        self.damage_numbers: list[DamageNumber] = []   # NEU PAKET 4
        self.muzzle_flashes = []
        # PAKET 8.3: Treffer-AUF-DAS-SCHIFF als Ereignisliste (Welt-Koordinaten
        # + Schaden). main.py uebergibt sie an effects/damage_fx.py, das die
        # Einschlags-Explosion am Schiff zeichnet. Hauptgame bleibt unberuehrt.
        self.hit_events = []
        
        self.max_player_hp = float(PLAYER_DATA.get("base_max_hp", 500.0)) * BAL_PLAYER_HP   # NEU PAKET 4: Balancing
        self.player_hp = self.max_player_hp
        
        self.dmg_level = 1
        self.speed_level = 1
        self.cannon_count_level = 1
        self.hangar_level = 1
        self.repair_level = 1
        
        self.skill_mods = {}          # NEU PAKET 4: Modifikatoren aus dem Skill-Tree
        self.gear_mods = {}           # NEU PAKET 7B: Modifikatoren der Schiffs-Module
        self._last_stand_used = False # NEU PAKET 7B: LETZTER WILLE (1x pro Gefecht)
        self.retaliate_timer = 0.0    # NEU PAKET 4: PULSGENERATOR
        self.retaliate_tick = 0.0     # NEU PAKET 4
        self.overdrive_timer = 0.0    # NEU PAKET 4: UEBERTAKTUNG
        self.overdrive_cd = 0.0       # NEU PAKET 4
        # AUFTRAG 8: CHAMPIONS - aktive Faehigkeiten. main.py befuellt
        # champ_skills beim Sync (ausgeruestete Helden, max. 2 HUD-Buttons):
        # Eintraege {"key","hero","name","cd","desc",...Effektfelder}.
        # champ_cd[i] = Rest-Abklingzeit von Slot i (Sekunden).
        self.champ_skills: list = []
        self.champ_cd: list = []
        self.crit_buff_t = 0.0        # LYRA ZIEL-OVERLAY: Restzeit
        self.crit_buff_pct = 0.0      # LYRA ZIEL-OVERLAY: Krit-Bonus
        self.idle_kill_counter = 0    # NEU PAKET 4: Idle liefert Data Cores
        # PAKET 8.8b: IDLE-MAXIMUM - main.py friert das Idle-Einkommen ein,
        # sobald die Idle-Sitzung 8 h erreicht hat (AFK-Profit-Bremse).
        self.income_frozen = False
        # AUFTRAG 22: Live-Idle-Cores je FENSTER deckeln (wie der Offline-
        # Bericht: IDLE_LIVE_CORE_CAP). main.py spiegelt den Zaehler in den
        # Spielstand (Neustart-resistent) und setzt ihn beim Laden zurueck.
        self.idle_cores_used = 0
        # PAKET 8.8c: Zusatz-Angriffe der Bosse (Bandbreite gegen Monotonie)
        self.boss_bombs: list = []   # fliegende GLUTBOMBEN
        self.boss_spikes: list = []  # aktive EISSPIESS-Eruptionen
        # PAKET 8: Kill-Statistik fuer Quests (echte Gameplay-Ereignisse).
        # 'normal' zaehlt ALLE Abschuesse, 'elite'/'boss' zusaetzlich die
        # Spezialkaempfe - main.py leitet Deltas ans Quest-System weiter.
        self.kill_stats = {"normal": 0, "elite": 0, "boss": 0}
        # PAKET 8.8: Boss-Anzeige (main.py liest das fuer Balken/Banner)
        self.boss_ref = None          # aktiver Boss (Enemy) oder None
        self.boss_name = ""
        self.boss_banner_t = 0.0      # Einzugs-Banner-Restzeit (Sekunden)
        self.auto_fire_timer = 0.0
        self.drone_timer = 0.0
        
        self.spawn_queue = 0
        self.spawn_timer = 0.0
        self.data_cores_earned = 0
        # PAKET 7C: sichtbare Hangar-Drohnen (Einheiten, keine Zahlen mehr)
        self.drones: list[DroneUnit] = []
        self.combat_time = 0.0
        self.spawn_stage()

    @property
    def cannon_damage(self):
        base = float(PLAYER_DATA.get("base_cannon_damage", 12.0))
        mult = float(PLAYER_DATA.get("cannon_dmg_mult", 1.2))
        raw = base * (mult ** (self.dmg_level - 1)) * BAL_PLAYER_DMG
        raw *= 1.0 + self.mod("dmg_pct", 0.0)          # NEU PAKET 4: GEWEHRVERSTÄRKER
        return raw * self._missing_hp_factor()

    def _missing_hp_factor(self):
        """NEU PAKET 4: ADRENALIN-KERN - mehr Schaden, je niedriger die Huelle.
        AUFTRAG 2 + 4: (a) dezimalstetige Rechnung statt Ganzzahl-Trunkierung
        - vorher int(missing*10): jede Stufe unter 10 % fehlender Huelle gab
        0 Bonus und 47 % fehlende Huelle wirkten wie 40 %. Jetzt stetig.
        (b) Modifikator heisst jetzt "adrenaline_dmg" (statt "adrenalin_dmg")
        - eindeutig getrennt von "adrenaline_cool" (NOTKUEHLUNG)."""
        if self.max_player_hp <= 0:
            return 1.0
        missing = 1.0 - max(0.0, min(1.0, self.player_hp / self.max_player_hp))
        return 1.0 + self.mod("adrenaline_dmg", 0.0) * (missing * 10.0)

    # NEU PAKET 7B: Schluessel, die als Multiplikatoren (nicht Summanden) wirken
    _MULT_KEYS = ("rate_mult", "proj_speed_mult", "drone_rate_mult")

    def mod(self, key, default=0.0):
        """PAKET 4/7B: Modifikator lesen.
        Quelle 1: skill_mods (Skill-Tree via apply_to_combat).
        Quelle 2: gear_mods (Schiffs-Module via _sync_modules_to_combat).
        Multiplikative Schluessel werden verkettet, additive summiert."""
        try:
            v = self.skill_mods.get(key, default)
        except AttributeError:
            v = default
        gear = getattr(self, "gear_mods", None) or {}
        g = gear.get(key)
        if g is None or not isinstance(v, (int, float)) or not isinstance(g, (int, float)):
            return v
        if key in self._MULT_KEYS:
            return v * g
        return v + g

    def activate_overdrive(self):
        """NEU PAKET 4: UEBERTAKTUNG (Spezialsparte) - 8s doppelte Feuerrate, 45s CD."""
        if self.is_idle or self.mod("overdrive", 0) < 1:
            return False
        if self.overdrive_cd > 0 or self.overdrive_timer > 0:
            return False
        self.overdrive_timer = 8.0
        self.overdrive_cd = 45.0
        return True

    def activate_champ_skill(self, idx: int) -> bool:
        """AUFTRAG 8: Aktive Faehigkeit eines ausgeruesteten Champions.
        idx = Index in champ_skills (Reihenfolge der HUD-Buttons). Wirkt
        nur im aktiven Gefecht (is_idle -> False). Liefert True, wenn die
        Faehigkeit ausgeloest wurde; False bei Abklingzeit/ohne Ziel.
        Effektwerte (mult/crit_pct/dur/heal_pct) stehen in
        rpg_config.CHAMPION_SKILLS und werden von main.py mitgeliefert."""
        if self.is_idle or not (0 <= int(idx) < len(self.champ_skills)):
            return False
        i = int(idx)
        sk = self.champ_skills[i]
        if self.champ_cd[i] > 0.0:
            return False
        key = sk.get("key")

        if key == "nova":
            # PLASMASTOSS: ein Schlag mit 4x Kanonenschaden aufs vorderste
            # Ziel (das dem Schiff am naechsten steht). Boss-Panzerung und
            # BOSS-JAEGER wirken wie bei normalen Projektil-Treffern; Krit
            # ist bewusst ausgenommen (Spezialfaehigkeit, kein Schuss).
            ziel = None
            for e in self.enemies:
                if e.hp > 0 and (ziel is None or e.x < ziel.x):
                    ziel = e
            if ziel is None:
                return False
            dmg = self.cannon_damage * float(sk.get("mult", 4.0))
            if ziel.is_boss:                     # PAKET 8.8: wie Projektil-Treffer
                dmg *= 1.0 - ziel.dr
                dmg *= 1.0 + self.mod("boss_dmg_pct", 0.0)
            dmg = max(1, int(dmg))
            ziel.hp -= dmg
            ziel.hit_flash = 0.15
            self._spawn_damage(ziel.x, ziel.y - 34, dmg, (255, 190, 76), big=True)
            for _a in range(16):                 # Einschlags-Partikel
                self.particles.append(Particle(
                    ziel.x + random.uniform(-14, 14),
                    ziel.y + random.uniform(-14, 14),
                    random.uniform(-140, 140), random.uniform(-140, 60),
                    (176, 120, 255), random.uniform(2.0, 5.5), 0.4, 0.4))
            if ziel.hp <= 0 and ziel in self.enemies:
                # gleiche Abwicklung wie ein Projektil-Kill (SCHRITT 1a):
                # Belohnungen + Explosion + Quest-Buchung.
                self._grant_kill_rewards(ziel)
                self._spawn_explosion(ziel.x, ziel.y, ziel.enemy_type)
                self._quest_kill_book()
                self.enemies.remove(ziel)
            SFX.play("explosion", 0.35)

        elif key == "lyra":
            # ZIEL-OVERLAY: zeitlich begrenzter Krit-Bonus (wirkt in der
            # Projektil-Treffer-Schleife, siehe crit_chance dort).
            self.crit_buff_pct = float(sk.get("crit_pct", 0.25))
            self.crit_buff_t = max(self.crit_buff_t, float(sk.get("dur", 6.0)))
            SFX.play("upgrade", 0.4)

        elif key == "ingenieur":
            # FELD-REPARATUR: sofortige Heilung (% der max. Huille).
            heal = self.max_player_hp * float(sk.get("heal_pct", 0.12))
            vor = self.player_hp
            self.player_hp = min(self.max_player_hp, self.player_hp + heal)
            geheilt = int(self.player_hp - vor)
            if geheilt > 0:
                self._spawn_damage(100, 210, f"+{geheilt}", (0, 255, 130),
                                   big=True)
            SFX.play("upgrade", 0.5)

        else:
            return False

        self.champ_cd[i] = float(sk.get("cd", 10.0))
        return True

    def _spawn_damage(self, x, y, value, color, big=False):
        """NEU PAKET 4: schwebende Schadenszahl am Trefferpunkt."""
        try:
            self.damage_numbers.append(DamageNumber(x=x, y=y, value=str(value), color=color, big=big))
        except AttributeError:
            pass
    
    @property
    def attack_rate(self):
        base = float(PLAYER_DATA.get("base_fire_rate", 0.8))
        mult = float(PLAYER_DATA.get("fire_rate_mult", 0.85))
        rate = base * (mult ** (self.speed_level - 1)) * BAL_PLAYER_RATE
        rate *= self.mod("rate_mult", 1.0)          # NEU PAKET 4: SCHNELLFEUER
        if self.overdrive_timer > 0:                # NEU PAKET 4: UEBERTAKTUNG (x2)
            rate *= 0.5
        # AUFTRAG 4: Modifikator "adrenaline" -> "adrenaline_cool"
        # (kein Namenskonflikt mehr mit "adrenaline_dmg")
        if self.mod("adrenaline_cool", 0) >= 1 and self.player_hp < self.max_player_hp * 0.3:
            rate *= 0.75                            # NEU PAKET 4: NOTKUEHLUNG
        return rate
    
    @property
    def cannon_count(self): return min(8, self.cannon_count_level + int(self.mod("extra_cannons", 0)))   # NEU PAKET 4: MEHRFACHLAUF

    # ------------------------------------------------------------------
    # PUNKT 3 (AUFTRAG): EINE Berechnungsgrundlage fuer Spiel + Simulatoren.
    # tools/simulate_boss / simulate_economy / simulate_campaign rufen
    # nur noch total_dps() auf - die Formeln stehen GENAU HIER und nicht
    # mehr kopiert in den Tools. Der echte Treffer-Pfad (Projektil-Schleife,
    # Krit-Wurf unten bei ~Z.1317) hat denselben Erwartungswert wie
    # expected_crit_mult(); salvo_damage() ist exakt die Summe der
    # Projectile.damage-Werte, die eine Salve erzeugt (Krit erst auf Hit).
    # ------------------------------------------------------------------
    def expected_crit_mult(self, include_lyra=True):
        """Erwartungswert-Multiplikator kritischer Treffer.
        include_lyra=False: Basis ohne zeitweises Lyra-Ziel-Overlay."""
        ch = self.mod("crit_chance", 0.0)
        if include_lyra and self.crit_buff_t > 0.0:
            ch += self.crit_buff_pct          # LYRA ZIEL-OVERLAY (AUFTRAG 8)
        ch = max(0.0, min(1.0, ch))
        return 1.0 + ch * (self.mod("crit_mult", 2.0) - 1.0)

    def salvo_damage(self):
        """Erwarteter Schaden EINER Salve: alle Kanonen auf ein Ziel."""
        return self.cannon_count * self.cannon_damage * self.expected_crit_mult()

    def cannon_dps(self):
        return self.salvo_damage() / max(0.05, self.attack_rate)

    def drone_dps(self):
        """Hangar-Drohnen (PAKET 7C): Anzahl + Feuerraten wie update()."""
        n = max(0, min(6, (self.hangar_level - 1)
                       + int(self.mod("extra_drones", 0))))
        if n <= 0:
            return 0.0
        drone_dmg = self.cannon_damage * float(PLAYER_DATA.get("drone_damage_mult", 0.5)) \
            * (1.0 + self.mod("drone_dmg_pct", 0.0))
        rate_mult = max(0.4, self.mod("drone_rate_mult", 1.0))
        ivg = sum((1.15 + 0.18 * (i % 3)) for i in range(n)) / n * rate_mult
        return n * drone_dmg / max(0.05, ivg)

    def total_dps(self, boss_dr=0.0):
        """Gesamt-DPS auf ein Ziel mit Panzerung boss_dr
        (Kanonen + Drohnen, inkl. Boss-JAEGER-Bonus)."""
        return (self.cannon_dps() + self.drone_dps()) \
            * (1.0 - boss_dr) * (1.0 + self.mod("boss_dmg_pct", 0.0))

    def spawn_stage(self):
        self.enemies.clear()
        self.projectiles.clear()
        self.particles.clear()
        self.muzzle_flashes.clear()
        self.hit_events.clear()   # PAKET 8.3: keine alten Einschlaege uebernehmen
        self.stage_cleared = False
        
        # PAKET 8.8: Boss-Logik - Stufe 5/10/15 sind Bossgefechte
        if not self.is_idle and self.stage_id in BOSS_DATA:
            self.spawn_queue = 1
        else:
            # PAKET 8.7: Gegnerzahl ueber stage_enemy_count (daempft das
            # fruehere 2 + stage, das auf Stufe 12/13 14-15 Gegner bedeutete)
            self.spawn_queue = 999 if self.is_idle else stage_enemy_count(self.stage_id)
            
        self.spawn_timer = 2.0

    def _spawn_single_enemy(self):
        # PAKET 8.8: Boss-Logik ueber BOSS_DATA (Stufe 5/10/15)
        # AUFTRAG 19: Boss-Belegung ueber die EINE Zuordnung (Sektor 1-5
        # historische Tabelle, 6-8 eigene Tabellen - siehe boss_cfg_for).
        boss_cfg = boss_cfg_for(self.campaign_id, self.stage_id) \
            if not self.is_idle else None
        if boss_cfg:
            e_type = boss_cfg["type"]
            # AUFTRAG 16b: Boss-Werte ueber die EINE Quelle (inkl.
            # Kampagnen-Skalierung - Sektor 2-5 Bosse sind jetzt spuerbar
            # staerker als Sektor 1).
            b_hp, b_dmg, b_reward = boss_stats_for_stage(self.stage_id,
                                                         self.campaign_id)
            hp = b_hp
            speed = float(boss_cfg["speed"])
            damage = int(b_dmg)
            reward = b_reward
            # AUFTRAG 6: NG+-Skalierung gilt auch fuer Bosse (HP/Schaden/Beute)
            _ng = max(0, int(getattr(self, "ng_plus", 0)))
            if _ng > 0:
                hp *= ng_hp_mult(_ng)
                damage = int(round(damage * ng_dmg_mult(_ng)))
                reward = int(round(reward * ng_reward_mult(_ng)))
            lane_y = 270
        else:
            available_enemies = []
            weights = []
            for k, data in ENEMY_DATA.items():
                min_lvl = int(data.get("Min_Ship_Level", 1))
                if self.ship_level >= min_lvl:
                    img_path = os.path.join(ENEMY_FOLDER, f"enemy_{k}.png")
                    if os.path.exists(img_path):
                        available_enemies.append(k)
                        weights.append(data.get("Spawn_Weight", 10))
                    
            if not available_enemies:
                available_enemies = ["skitter"]
                weights = [100]

            # PAKET 8.3: ENT-Ueberladung - pro Stufe max. 2 Gegnertypen
            # gleichzeitig. Vorher mischten sich ALLE freigeschalteten Typen
            # in jeder Welle, was unruhig wirkte. Die Stufen-Paarung ist
            # deterministisch (Seed aus Sektor+Stufe), damit jede Stufe
            # ihr eigenes, konsistentes Gegnerpaar hat.
            if len(available_enemies) > 2:
                seed = f"pool::{self.campaign_id}::{self.stage_id}"
                picker = random.Random(seed)
                idx = list(range(len(available_enemies)))
                picker.shuffle(idx)
                keep = sorted(idx[:2])
                available_enemies = [available_enemies[i] for i in keep]
                weights = [weights[i] for i in keep]

            e_type = random.choices(available_enemies, weights=weights, k=1)[0]
            data = ENEMY_DATA.get(e_type, {"Base_HP": 20, "Base_Speed": 50, "Base_Damage": 5, "Base_Reward": 10})
            
            lane_y = random.choice([200, 270, 340]) + random.uniform(-30, 30)
            
            # PAKET 8.7: spaete Stufen daempfen (siehe Konstanten oben)
            late_hp = stage_late_hp_factor(self.stage_id)
            late_dmg = stage_late_dmg_factor(self.stage_id)
            hp = (float(data.get("Base_HP", 20)) + (self.stage_id * float(data.get("HP_Add_Per_Stage", 10)))) * (float(data.get("HP_Mult_Per_Stage", 1.05)) ** self.stage_id) * BAL_ENEMY_HP * late_hp   # 8.7: + late_hp
            speed = float(data.get("Base_Speed", 50)) + (self.stage_id * float(data.get("Speed_Add_Per_Stage", 0)))
            damage = (float(data.get("Base_Damage", 5)) + (self.stage_id * float(data.get("Damage_Add_Per_Stage", 2)))) * BAL_ENEMY_DMG * late_dmg   # 8.7: + late_dmg
            reward = int((float(data.get("Base_Reward", 10)) + (self.stage_id * 2)) * float(data.get("Idle_Reward_Mult", 1.0)))
            # AUFTRAG 16b: KAMPAGNEN-SKALIERUNG - Sektor 2-5 Gegner sind
            # spuerbar staerker/begehrenswerter als Sektor 1 (Sektor 1 = x1.0,
            # Schiff L4-5 muessen dort bestehen koennen).
            hp *= campaign_hp_mult(self.campaign_id)
            damage *= campaign_dmg_mult(self.campaign_id)
            reward = int(round(reward * campaign_reward_mult(self.campaign_id)))
            # AUFTRAG 6: NG+-Skalierung (VOR dem Idle-One-Shot, damit das
            # Idle bei hp=1 bleibt - nur Beute/Schaden skalieren mit).
            _ng = max(0, int(getattr(self, "ng_plus", 0)))
            if _ng > 0:
                hp *= ng_hp_mult(_ng)
                damage *= ng_dmg_mult(_ng)
                reward = int(round(reward * ng_reward_mult(_ng)))

            if self.is_idle:
                hp = 1.0 # One-Shot im Idle
                speed *= 0.4 
                
        is_b = bool(boss_cfg)
        e = Enemy(
            name=e_type.upper(), hp=hp, max_hp=hp,
            damage=int(damage), speed=speed, reward=reward,
            x=1000.0, y=lane_y,
            attack_cooldown=random.uniform(1.0, 3.0),
            enemy_type=e_type
        )
        if is_b:                          # PAKET 8.8: Boss-Metadaten
            e.is_boss = True
            e.dr = float(boss_cfg["dr"])
            e.boss_cd = 2.2               # kurze Schonfrist nach Einzug
            e.boss_col = boss_cfg["col"]
            # PAKET 8.8c: Bewegungs-Ruhelage, Phasenversetzter Auf/Ab-Drift
            # und Start-Timer fuer die Zusatz-Angriffe.
            e.base_y = float(lane_y)
            e.move_phase = random.uniform(0.0, math.tau)
            e.atk_cd = 3.5
            self.boss_ref = e
            self.boss_name = boss_cfg["name"]
            self.boss_banner_t = 3.0
        else:
            # AUFTRAG 21: Typ-eigene Verhalten (Bewegung + Muster) setzen.
            # base_y dient als Ruhelage der Typ-Bewegung (Bob um die Spawn-
            # Spur); Kollisionen/Targeting folgen e.x/e.y unveraendert.
            e.base_y = float(lane_y)
            bh = ENEMY_BEHAVIOR.get(e.enemy_type)
            if bh:
                e.pattern = bh.get("pattern", "shot")
                e.mv_phase = random.uniform(0.0, math.tau)
                e.dash_cd = random.uniform(2.0, 4.0)
        self.enemies.append(e)

    def _boss_shoot(self, e, cx, cy):
        """PAKET 8.8: Boss-Salve - Winkel-Faecher um das Schiff, jeder 3.
        Salve zusaetzlich ein SCHWERER gezielter Schuss.
        PAKET 8.8b: Der EISDRACHE wird hier NICHT mehr bedient - er hat
        jetzt den Flammen-Atem (_dragon_breath, kein Kugel-Projektil mehr).
        Die Wut-Phase des Drachen wanderte dorthin."""
        cfg = BOSS_TYPE_CFG.get(e.enemy_type)
        if cfg is None or e.enemy_type == "dragon":   # 8.8b: Drache ausgenommen
            e.boss_cd = random.uniform(1.5, 3.0)
            return
        dx, dy = cx - e.x, cy - e.y
        base = math.atan2(dy, dx)
        fan = cfg["fan"] + (2 if e.enraged else 0)
        spread = cfg["spread"] + (14.0 if e.enraged else 0.0)
        for i in range(fan):
            if fan <= 1:
                ang = base
            else:
                ang = base + math.radians(spread) * (i / (fan - 1) - 0.5)
            self.projectiles.append(Projectile(
                x=e.x, y=e.y, vx=math.cos(ang), vy=math.sin(ang),
                damage=e.damage, color=e.boss_col, size=cfg["size"],
                speed=cfg["b_speed"], kind="enemy"))
        e.volley += 1
        if cfg["heavy"] and e.volley % 3 == 0:
            self.projectiles.append(Projectile(
                x=e.x, y=e.y, vx=math.cos(base), vy=math.sin(base),
                damage=int(e.damage * 1.5), color=(255, 240, 160),
                size=cfg["size"] + 2, speed=cfg["b_speed"] * 1.12,
                kind="enemy"))
        e.boss_cd = random.uniform(*cfg["cadence"]) * (0.72 if e.enraged else 1.0)

    def _dragon_breath(self, e, cx, cy, dt, dist_to_ship):
        """PAKET 8.8b: FLAMMENDER ATEM des Eisdrachen. Kein Kugel-Projektil
        mehr - stattdessen ein telegrafierter Flammenstrahl:
          Phase 1 (Telegraf): Mund glimmt, Ziel folgt noch dem Schiff
          Phase 2 (Strahl): Richtung eingefroren, Schaden pro Tick im
            Kegel, Glut-Partikel entlang des Strahls, Impact am Schiff.
        Die Wut-Phase (< 50 % HP) ist hierher umgezogen: laengerer Strahl,
        mehr Schaden, kuerzere Pause."""
        # Wut-Phase (ehemals in _boss_shoot)
        if not e.enraged and e.hp < e.max_hp * 0.5:
            e.enraged = True
            e.damage = int(e.damage * 1.15)
            e.speed += 8.0
            self._spawn_damage(e.x, e.y - 46, "WUT!", (130, 225, 255), big=True)

        if e.breath_phase == 0 and e.atk_kind == 0:
            e.boss_cd -= dt
            if e.boss_cd <= 0 and dist_to_ship < 560.0:
                e.breath_phase = 1                      # Telegraf startet
                e.breath_t = BREATH_TELEGRAPH_S
                e.breath_ang = math.atan2(cy - e.y, cx - e.x)
                if not self.is_idle:
                    SFX.play("explosion", 0.22)         # dumpfes Aufheulen
        elif e.breath_phase == 1:
            # Telegraf: Richtung verfolgt das Schiff noch (ausweichbar)
            e.breath_ang = math.atan2(cy - e.y, cx - e.x)
            e.breath_t -= dt
            if e.breath_t <= 0:
                e.breath_phase = 2                      # ZUENDUNG: Richtung fix
                e.breath_t = BREATH_ACTIVE_RAGE_S if e.enraged else BREATH_ACTIVE_S
                e.breath_tick = 0.0
        else:
            e.breath_t -= dt
            ang = math.atan2(cy - e.y, cx - e.x)
            dist = math.hypot(cx - e.x, cy - e.y)
            diff = abs((ang - e.breath_ang + math.pi) % math.tau - math.pi)
            if dist < BREATH_RANGE and diff < BREATH_HALF_ANGLE:
                e.breath_tick -= dt
                if e.breath_tick <= 0:
                    e.breath_tick = BREATH_TICK_S
                    dps = BREATH_DPS * (BREATH_DPS_RAGE_MULT if e.enraged else 1.0) \
                        * self._boss_fx_dmg()   # AUFTRAG 16b: globale Koeffizienten
                    # PUNKT-4-AUFTRAG: Schadensrechnung (dr_pct, Idle-Schutz,
                    # LETZTER WILLE) zentral - vorher ging der Atem am
                    # Last-Stand-Skill vorbei.
                    applied = self._apply_player_damage(
                        dps * BREATH_TICK_S, cx, cy)
                    self._spawn_damage(cx + random.uniform(-34, 34), cy - 62,
                                       applied, (255, 140, 40))
                    # Impact am Schiff buchen (Damage-FX zeichnet Einschlag)
                    self.hit_events.append((float(cx), float(cy - 20), float(applied)))
                    if len(self.hit_events) > 32:
                        del self.hit_events[:-16]
                    if not self.is_idle:
                        SFX.play("hit", 0.3)
            # Glut-Partikel entlang des Strahls (welt-Koordinaten)
            for _ in range(2):
                tt = random.uniform(0.12, 1.0)
                px = e.x + math.cos(e.breath_ang) * BREATH_RANGE * tt
                py = e.y + math.sin(e.breath_ang) * BREATH_RANGE * tt
                self.particles.append(Particle(
                    px, py, random.uniform(-30, 30), random.uniform(-70, -10),
                    (255, random.randint(120, 190), 30),
                    random.uniform(2.5, 6.0), 0.45, 0.45))
            if e.breath_t <= 0:
                e.breath_phase = 0
                lo, hi = BREATH_CD_RAGE if e.enraged else BREATH_CD
                e.boss_cd = random.uniform(lo, hi)

    # ---------------- PAKET 8.8c: GLUTBOMBEN & EISSPIESSE ----------------
    def _apply_player_damage(self, raw_amount, x, y):
        """PUNKT-4-AUFTRAG: EIN zentraler Schadenspfad am Schiff, den jetzt
        ALLE Schadensquellen benutzen (Gegner-/Boss-Projektile, Drachen-
        Atem, GLUTBOMBEN/EISSPIESSE). Reihenfolge wie im bisherigen
        Projektil-Pfad (PAKET 8.8c):
          1. Modul-Panzerung (dr_pct, ABFANG-FELD)
          2. min 1 - auch ein durchgekommenes Beispiel trifft mindestens 1
          3. Idle-Schutz: Huelle bleibt bei min. 1 HP (Idle verliert nie)
          4. Gefecht: Huelle kann auf 0 fallen; LETZTER WILLE (PAKET 7B,
             Skill last_stand) rettet EINMAL pro Gefecht mit 30 % max HP -
             JETZT fuer alle Pfade, vorher nur fuer Projektile.
        Die schwebenden Schadenszahlen/Impact-Events bleiben beim Aufrufer
        (unterschiedliche Anzeige-Positionen/Farben). Liefert den
        angewendeten Schaden zurueck."""
        applied = raw_amount * (1.0 - self.mod("dr_pct", 0.0))
        applied = max(1, int(applied))
        if self.is_idle:
            self.player_hp = max(1.0, self.player_hp - applied)
        else:
            self.player_hp = max(0.0, self.player_hp - applied)
            # NEU PAKET 7B / PUNKT-4: LETZTER WILLE - einmal pro Gefecht
            # 30 % HP zurueck, jetzt in ALLEN Schadenspfaden.
            if (self.player_hp <= 0 and self.mod("last_stand", 0) >= 1
                    and not self._last_stand_used):
                self._last_stand_used = True
                self.player_hp = max(1.0, self.max_player_hp * 0.30)
                self._spawn_damage(x, y - 80, "LETZTER WILLE!", (77, 255, 181), big=True)
                SFX.play("upgrade", 0.6)
        return applied

    def _ship_damage(self, amount, x, y):
        """PAKET 8.8c: Schaden am Schiff buchen (AoE der Boss-Zusatz-
        angriffe): schwebende Schadenszahl, Impact-FX am Schiff. Die
        Schadensrechnung (dr_pct, Idle-Schutz, LETZTER WILLE) laeuft
        PUNKT-4-AUFTRAG zentral ueber _apply_player_damage - der LETZTE
        WILLE greift damit auch bei Bomben/Spiessen."""
        applied = self._apply_player_damage(amount, x, y)
        self._spawn_damage(x, y - 15, applied, (255, 77, 100))
        self.hit_events.append((float(x), float(y), float(applied)))
        if len(self.hit_events) > 32:
            del self.hit_events[:-16]

    def _boss_fx_dmg(self):
        """AUFTRAG 16b: Globaler Schadenskoeffizient fuer die Boss-
        ZUSATZANGRIFFE (Atem/Bomben/Spiesse). Vorher umgingen diese den
        globalen BAL_ENEMY_DMG-Faktor - der Drachen-Atem war damit
        relativ zur uebrigen Gegnergefahr zu hart. Jetzt gilt dieselbe
        Regel wie fuer jeden anderen Gegnerschaden: x BAL_ENEMY_DMG und
        x Kampagnen-Faktor (Sektor 2-5 skalieren mit)."""
        return BAL_ENEMY_DMG * campaign_dmg_mult(self.campaign_id)

    def _bombs_target(self, e, cx, cy):
        """Ziele des GLUTBOMBEN-Telegrafen: die Haelfte zielt aufs Schiff
        (leicht streuend), der Rest verteilt sich im Schiffs-Viertel. Die
        Marken pulsieren schon VOR dem Abschuss (main.py zeichnet sie)."""
        n = BOMB_COUNT + (2 if e.enraged else 0)
        marks = []
        for i in range(n):
            if i < max(1, n // 2):
                tx = cx + random.uniform(-70.0, 70.0)
                ty = cy + random.uniform(-55.0, 45.0)
            else:
                tx = random.uniform(80.0, 380.0)
                ty = random.uniform(150.0, 400.0)
            marks.append((tx, ty))
        e.bomb_marks = marks

    def _bombs_launch(self, e):
        """Abschuss aus dem Maul (der Drache schaut immer zum Schiff ->
        Mund links). Danach eigener Cooldown - der Faecher/Atem laeuft
        unveraendert daneben weiter."""
        mx, my = e.x - 100.0, e.y + 6.0
        rage = bool(getattr(e, "enraged", False))
        for (tx, ty) in (e.bomb_marks or []):
            self.boss_bombs.append(BossBomb(
                sx=mx, sy=my, tx=tx, ty=ty,
                T=random.uniform(*BOMB_ARC_T),
                damage=BOMB_DMG * (1.2 if rage else 1.0) * self._boss_fx_dmg(),   # AUFTRAG 16b
                col=e.boss_col))
        e.bomb_marks = None
        e.atk_kind = 0
        lo, hi = BOMB_CD_RAGE if rage else BOMB_CD
        e.atk_cd = random.uniform(lo, hi)

    def _spikes_target(self, e, cx, cy):
        """Spalten fuer den EISSPIESS-Telegrafen waehlen. Mit einer
        Wahrscheinlichkeit von SPIKE_HIT_CHANCE (Wut: 80 %) liegt eine
        Spitze direkt in der Schiffs-Spalte - sonst daneben (dann zeigt
        der Angriff nur, was haette kommen koennen)."""
        n = SPIKE_COUNT + (1 if e.enraged else 0)
        xs = []
        if random.random() < (0.8 if e.enraged else SPIKE_HIT_CHANCE):
            xs.append(cx + random.uniform(-14.0, 14.0))
        pool = [210.0, 330.0, 450.0, 570.0, 90.0]
        random.shuffle(pool)
        for x in pool:
            if len(xs) >= n:
                break
            if all(abs(x - u) > 70.0 for u in xs):
                xs.append(x)
        e.spike_marks = xs[:n]

    def _spikes_launch(self, e):
        for x in (e.spike_marks or []):
            self.boss_spikes.append(BossSpike(
                x=x, damage=SPIKE_DMG * (1.2 if e.enraged else 1.0)
                   * self._boss_fx_dmg(),   # AUFTRAG 16b: globale Koeffizienten
                col=e.boss_col))
        e.spike_marks = None
        e.atk_kind = 0
        lo, hi = SPIKE_CD_RAGE if e.enraged else SPIKE_CD
        e.atk_cd = random.uniform(lo, hi)

    def _boss_extra_attack(self, e, cx, cy, dt, dist):
        """PAKET 8.8c: die ZUSATZ-ANGRIFFE der Bosse im EIGENEN Rhythmus -
        sie laufen NEBEN dem bisherigen Muster (Faecher/Atem) und brechen
        die Monotonie. Alles telegrafiert, damit es lesbar bleibt:
          GLUTBOMBEN (2): Mund gloht, Einschlags-Marken pulsieren, dann
                          bogenfliegende Feuerbomben mit AoE-Explosion.
          EISSPIESSE (3): Warnringe am Boden + Spalten-Markierung, dann
                          brechen Eissäulen hoch (Schaden bei Durchstossen
                          der Schiffs-Spalte).
        Drache: beide, Schlachtschiff: Bomben, Tarnjaeger: Spiesse.
        Kein Sofort-Wiederholen desselben Angriffs."""
        # laufenden Telegraf weiterschreiben
        if e.atk_kind == 2:
            e.atk_t -= dt
            if e.atk_t <= 0:
                self._bombs_launch(e)
            return
        if e.atk_kind == 3:
            e.atk_t -= dt
            if e.atk_t <= 0:
                self._spikes_launch(e)
            return

        # Maul-Zustand (Drache): offen bei Atem ODER laufendem Zusatz-Angriff
        e.mouth_open = getattr(e, "breath_phase", 0) > 0
        e.atk_cd -= dt
        if e.atk_cd > 0 or dist > 640.0:
            return
        if getattr(e, "breath_phase", 0) > 0:   # nicht mitten in den Atem hinein
            return
        menu = {"dragon": [2, 3], "brute": [2],
                "interceptor": [3]}.get(e.enemy_type)
        if not menu:
            return
        opts = [k for k in menu if k != e.last_atk] or menu
        kind = random.choice(opts)
        e.last_atk = kind
        if kind == 2:
            e.atk_kind = 2
            e.atk_t = BOMB_TELEGRAPH_S
            self._bombs_target(e, cx, cy)
        else:
            e.atk_kind = 3
            e.atk_t = SPIKE_TELEGRAPH_S
            self._spikes_target(e, cx, cy)
        if not self.is_idle:
            SFX.play("explosion", 0.18)      # kurzes Aufheulen vor dem Angriff

    def _spawn_explosion(self, x, y, enemy_type):
        """AUFTRAG 21: Zerstoerung mit TYP-EIGENER Farbpalette (ENEMY_FX_COL,
        passend zur vorhandenen Sprite-Farbwelt) und Groesse nach HP-Klasse:
        Tanky-Typen brechen langsamer/grosser auseinander, flinke Typen
        kleiner/schneller. 3-4 groessere Truemmer-Stuecke dazu. Reine
        Partikel-Effekte, keine neuen Grafik-Assets."""
        col = ENEMY_FX_COL.get(enemy_type, (255, 170, 0))
        count = 25 if (not self.is_idle and self.stage_id in BOSS_DATA) else 15
        big = enemy_type in ("crystal", "carrier", "hive", "destroyer", "husk")
        speed = 120.0 if big else 150.0
        life = 0.75 if big else 0.6
        
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            vx = math.cos(angle) * random.uniform(0.2, 1.5) * speed
            vy = math.sin(angle) * random.uniform(0.2, 1.5) * speed
            size = random.uniform(2, 8)
            self.particles.append(Particle(x, y, vx, vy, col, size, life, life))
        # Truemmer-Stuecke: groesser, langsamer, lange sichtbar
        for _ in range(4 if big else 2):
            angle = random.uniform(0, math.tau)
            vx = math.cos(angle) * random.uniform(0.4, 0.9) * speed * 0.6
            vy = math.sin(angle) * random.uniform(0.4, 0.9) * speed * 0.6
            size = random.uniform(7, 12)
            self.particles.append(Particle(x, y, vx, vy, col, size,
                                           life * 1.6, life * 1.6))

    def update(self, dt: float, center=(100, 270), cannon_positions=None):
        cx, cy = center
        self.combat_time += dt
        if self.boss_banner_t > 0:    # PAKET 8.8: Banner ausblenden
            self.boss_banner_t = max(0.0, self.boss_banner_t - dt)

        # AUFTRAG 8: Champion-Faehigkeiten - Abklingzeiten + Krit-Buff
        # laufen mit der Gefechtszeit.
        for _ci in range(len(self.champ_cd)):
            if self.champ_cd[_ci] > 0.0:
                self.champ_cd[_ci] = max(0.0, self.champ_cd[_ci] - dt)
        if self.crit_buff_t > 0.0:
            self.crit_buff_t = max(0.0, self.crit_buff_t - dt)
        
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            if p.life <= 0: self.particles.remove(p)

        for mf in list(self.muzzle_flashes):
            mf[3] -= dt
            if mf[3] <= 0: self.muzzle_flashes.remove(mf)


        for dn in list(self.damage_numbers):   # NEU PAKET 4: Schadenszahlen
            dn.y += dn.vy * dt
            dn.vy *= (1.0 - 1.5 * dt)
            dn.life -= dt
            if dn.life <= 0:
                self.damage_numbers.remove(dn)

        # PAKET 8.8c: GLUTBOMBEN fliegen (Bezier-Bogen) und schlagen ein;
        # EISSPIESSE brechen aus und treffen einmal pro Spalte.
        for b in list(self.boss_bombs):
            b.t += dt
            if b.t >= b.T:
                d = math.hypot(cx - b.tx, cy - b.ty)
                if d < BOMB_AOE_R:
                    self._ship_damage(b.damage * (1.0 - 0.45 * d / BOMB_AOE_R),
                                      b.tx, b.ty)
                for _ in range(14):
                    ang = random.uniform(0, math.tau)
                    spd = random.uniform(40.0, 210.0)
                    self.particles.append(Particle(
                        b.tx, b.ty,
                        math.cos(ang) * spd, math.sin(ang) * spd - 40.0,
                        (255, random.randint(120, 190), 30),
                        random.uniform(2.5, 6.5), 0.55, 0.55))
                if not self.is_idle:
                    SFX.play("explosion", 0.42)
                self.boss_bombs.remove(b)
            elif random.random() < 0.6:
                # Glut-Schweif entlang der Flugbahn
                k = b.t / b.T
                px_ = b.sx + (b.tx - b.sx) * k
                py_ = b.sy + (b.ty - b.sy) * k - BOMB_ARC_H * 4.0 * k * (1.0 - k)
                self.particles.append(Particle(
                    px_, py_, random.uniform(-20, 20), random.uniform(-30, 10),
                    (255, random.randint(100, 170), 20),
                    random.uniform(2.0, 4.5), 0.35, 0.35))
        for s in list(self.boss_spikes):
            s.t += dt
            if not s.hit_done and s.t >= SPIKE_RISE_S * 0.35:
                s.hit_done = True
                if abs(cx - s.x) < SPIKE_R:
                    self._ship_damage(s.damage, s.x, cy)
                if not self.is_idle:
                    SFX.play("hit", 0.4)
            if s.t < SPIKE_RISE_S:
                # Frostpartikel an der aufsteigenden Spitze
                p = s.t / SPIKE_RISE_S
                tip_y = 540.0 - 600.0 * (1.0 - (1.0 - p) ** 3)
                for _ in range(2):
                    self.particles.append(Particle(
                        s.x + random.uniform(-16, 16), tip_y,
                        random.uniform(-60, 60), random.uniform(-120, -30),
                        (170, random.randint(220, 245), 255),
                        random.uniform(2.0, 4.0), 0.4, 0.4))
            if s.t > SPIKE_RISE_S + 0.45:
                self.boss_spikes.remove(s)

        rep_val = float(PLAYER_DATA.get("repair_per_level", 2.0))
        base_regen = 1.5 + self.mod("regen", 0.0)   # NEU PAKET 4: Grundreparatur + NANO-REPARATUR
        if self.player_hp < self.max_player_hp:
            self.player_hp += base_regen * dt
            if self.repair_level > 1:
                self.player_hp += (self.repair_level * rep_val) * dt
        if self.is_idle and self.player_hp < self.max_player_hp:
            self.player_hp += 20 * dt

        # NEU PAKET 4: Uebertaktungs-Timer + Vergeltungs-Pulse
        if self.overdrive_cd > 0:
            self.overdrive_cd = max(0.0, self.overdrive_cd - dt)
        if self.overdrive_timer > 0:
            self.overdrive_timer = max(0.0, self.overdrive_timer - dt)
        if self.retaliate_timer > 0 and not self.is_idle:
            self.retaliate_timer -= dt
            self.retaliate_tick -= dt
            if self.retaliate_tick <= 0 and self.enemies:
                self.retaliate_tick = 0.5
                for tgt in sorted(self.enemies, key=lambda en: en.x)[:2]:
                    dx, dy = tgt.x - cx, tgt.y - cy
                    dist = math.hypot(dx, dy) or 1
                    self.projectiles.append(Projectile(
                        x=cx, y=cy - 40, vx=dx / dist, vy=dy / dist,
                        damage=self.cannon_damage * 0.4, color=(153, 94, 255),
                        size=3, speed=650.0, kind="player", is_drone=True))
            
        if self.spawn_queue > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self._spawn_single_enemy()
                self.spawn_queue -= 1
                # AUFTRAG 16b: Spawn-Rate skaliert mit der Kampagne
                # (Sektor 2-5 lassen Gegner schneller nachruecken).
                _spd = 1.0 if self.is_idle else campaign_spawn_mult(self.campaign_id)
                self.spawn_timer = random.uniform(2.5, 5.0) * _spd if self.is_idle \
                    else random.uniform(1.0, 2.5) * _spd

        for e in list(self.enemies):
            e.hit_flash = max(0.0, e.hit_flash - dt)

            if e.is_boss:
                # PAKET 8.8c: Bosse halten ABSTAND (Nutzer: "Der Boss kommt
                # jedoch viel zu nahe zum Schluss") - sie stoppen weiter
                # draussen als Normalgegner (400), die Schnauze bleibt weg.
                stop_x = BOSS_HOLD_X.get(e.enemy_type, 400.0)
                if e.x > stop_x:
                    e.x -= e.speed * dt
                else:
                    e.x = stop_x
                # PAKET 8.8c: echte Auf/Ab-Bewegung (vorher nur 4 px
                # Zeichnungs-Bob): zwei ueberlagerte, langsame Sinuswellen,
                # in Grenzen gehalten - Logik (Atem-Ziel etc.) folgt e.y.
                e.y = e.base_y + math.sin(self.combat_time * BOSS_MOVE_SPD + e.move_phase) * BOSS_MOVE_AMP \
                    + math.sin(self.combat_time * BOSS_MOVE_SPD2 + e.move_phase * 1.7) * BOSS_MOVE_AMP2
                if e.y < BOSS_Y_MIN:
                    e.y = BOSS_Y_MIN
                elif e.y > BOSS_Y_MAX:
                    e.y = BOSS_Y_MAX
            else:
                # AUFTRAG 21: TYP-EIGENE BEWEGUNG (Logik, nicht nur Zeichnung).
                bh = ENEMY_BEHAVIOR.get(e.enemy_type)
                if e.pattern == "kamikaze":
                    # HUSK: Rammt bis zur Festung durch (kein Stop bei 400).
                    if (not e.kamikaze_hit
                            and math.hypot(cx - e.x, cy - e.y) < 90.0):
                        e.kamikaze_hit = True
                        applied = self._apply_player_damage(
                            e.damage * 1.5, e.x, e.y)
                        self._spawn_damage(cx, cy - 40, int(applied),
                                           (255, 110, 200))
                        self._spawn_explosion(e.x, e.y, e.enemy_type)
                        SFX.play("explosion", 0.4)
                        self.enemies.remove(e)
                        continue
                    if e.x > cx - 20.0:
                        e.x -= e.speed * dt
                else:
                    stop_x = 400.0
                    if e.x > stop_x:
                        e.x -= e.speed * dt
                    else:
                        e.x = stop_x
                # Phasen-DASH des WRAITH: alle 3.5-5.5 s ein kurzer
                # Vorstoss (0.35 s), danach wieder normale Annaeherung.
                if e.pattern == "dash":
                    if e.dash_t > 0.0:
                        e.dash_t -= dt
                        e.x -= 260.0 * dt
                    else:
                        e.dash_cd -= dt
                        if e.dash_cd <= 0.0:
                            e.dash_t = 0.35
                            e.dash_cd = random.uniform(3.5, 5.5)
                # Bob (Auf/Ab) + leichtes Sway-x um den Annaherungspfad,
                # Amplituden/Frequenzen aus der Typ-Tabelle (klein).
                if bh:
                    e.y = e.base_y + math.sin(
                        self.combat_time * bh["bob_f"] + e.mv_phase) * bh["bob_amp"]
                    e.x += math.sin(
                        self.combat_time * bh["sway_f"] + e.mv_phase * 1.3) \
                        * bh["sway_amp"] * dt

            dist_to_ship = math.hypot(cx - e.x, cy - e.y)
            if dist_to_ship < 550: 
                # PAKET 8.8: Bosse feuern Faecher-Salven (_boss_shoot),
                # Normalgegner wie gehabt einen gezielten Schuss.
                # PAKET 8.8b: Der EISDRACHE hat den FLAMMEN-ATEM statt
                # Kugel-Faechern (Strahl, telegrafiert, Schaden pro Tick).
                # PAKET 8.8c: ZUSAETZLICH im eigenen Rhythmus GLUTBOMBEN
                # bzw. EISSPIESSE (_boss_extra_attack) -> keine Monotonie.
                if e.is_boss:
                    if e.enemy_type == "dragon":
                        self._dragon_breath(e, cx, cy, dt, dist_to_ship)
                    else:
                        e.boss_cd -= dt
                        if e.boss_cd <= 0:
                            self._boss_shoot(e, cx, cy)
                    self._boss_extra_attack(e, cx, cy, dt, dist_to_ship)
                else:
                    e.attack_cooldown -= dt
                    if e.attack_cooldown <= 0:
                        # AUFTRAG 21: Feuerrate/Projektil-Tempo/-Groesse je
                        # Typ; HIVE = 3er-Faecher, SHARD = Doppel-Schuss.
                        bh = ENEMY_BEHAVIOR.get(e.enemy_type)
                        cd_band = bh["cd"] if bh else (1.5, 3.0)
                        p_speed = bh["proj_speed"] if bh else 250.0
                        p_size = bh["proj_size"] if bh else 5
                        p_col = ENEMY_FX_COL.get(e.enemy_type, (255, 0, 0))
                        e.attack_cooldown = random.uniform(*cd_band)
                        dx, dy = cx - e.x, cy - e.y
                        dist = math.hypot(dx, dy) or 1
                        b_vx, b_vy = dx / dist, dy / dist
                        offsets = (0.0,)
                        if bh and bh.get("pattern") == "fan":
                            offsets = (-0.20, 0.0, 0.20)   # hive: Faecher
                        elif bh and bh.get("pattern") == "zigzag":
                            offsets = (-0.10, 0.10)        # shard: Doppelschuss
                        for off in offsets:
                            ca, sa = math.cos(off), math.sin(off)
                            self.projectiles.append(
                                Projectile(x=e.x, y=e.y,
                                           vx=b_vx * ca - b_vy * sa,
                                           vy=b_vx * sa + b_vy * ca,
                                           damage=e.damage, color=p_col,
                                           size=p_size, speed=p_speed,
                                           kind="enemy"))

        # PAKET 8.8c: Bosse halten weiter Abstand (520-560), bleiben aber
        # ZIELBAR - sonst wuerden Kanonen/Drohnen den Boss nie beachten.
        visible_enemies = [e for e in self.enemies
                           if e.x < 450 or e.is_boss]
        if visible_enemies and cannon_positions:
            target = min(visible_enemies, key=lambda e: e.x)
            self.auto_fire_timer -= dt
            if self.auto_fire_timer <= 0:
                self.auto_fire_timer = self.attack_rate
                SFX.play("shoot", 0.3)
                for pos in cannon_positions[:self.cannon_count]:
                    kx, ky = pos[0], pos[1]
                    dx, dy = target.x - kx, target.y - ky
                    dist = math.hypot(dx, dy) or 1
                    self.projectiles.append(
                        Projectile(x=kx, y=ky, vx=dx/dist, vy=dy/dist, damage=self.cannon_damage, color=(0, 255, 255), size=4, kind="player", is_drone=False,
                                   speed=600.0 * max(0.5, self.mod("proj_speed_mult", 1.0)))   # NEU PAKET 7B: TEMPFELD
                    )
                    self.muzzle_flashes.append([kx, ky, math.atan2(dy, dx), 0.08])

        # -------------------------------------------------------------
        # PAKET 7C: HANGAR-DROHNEN als sichtbare Einheiten (ersetzt die
        # alte Volley-Logik, gleiche Schadensformel -> ENERGIELEITUNG,
        # REAKTOR und TEMPFELD wirken weiter). Anzahl = (hangar-1) +
        # HANGAR-TAKTIK, gedeckelt auf 6 (Performance).
        # -------------------------------------------------------------
        if self.hangar_level > 1:
            desired = max(0, min(6, (self.hangar_level - 1)
                                 + int(self.mod("extra_drones", 0))))
            if len(self.drones) < desired:
                self.drone_timer -= dt
                if self.drone_timer <= 0:
                    # Nachschub startet gestaffelt durch (KUEHLSYSTEM beschl.
                    # den Einflug, drone_rate_mult < 1 = schneller)
                    self.drone_timer = 0.85 * max(0.4, self.mod("drone_rate_mult", 1.0))
                    i = len(self.drones)
                    self.drones.append(DroneUnit(
                        idx=i, x=cx + 26.0, y=cy - 44.0,
                        phase=i * (math.tau / max(1, desired)) ,
                        fire_cd=0.7 + 0.25 * i, spawn_t=0.0))
            drone_dmg = self.cannon_damage * float(PLAYER_DATA.get("drone_damage_mult", 0.5)) * (1.0 + self.mod("drone_dmg_pct", 0.0))
            rate_mult = max(0.4, self.mod("drone_rate_mult", 1.0))
            for d in self.drones:
                d.spawn_t = min(1.0, d.spawn_t + dt * 1.7)
                # Orbit um das Schiff (Ellipse, Staffel-Positionen via idx)
                n = max(1, len(self.drones))
                orb = self.combat_time * 0.85 + d.idx * (math.tau / n)
                radius = 58.0 + 16.0 * (d.idx % 2)
                tx = cx + math.cos(orb) * radius
                ty = cy + math.sin(orb) * radius * 0.60 - 12.0
                k = min(1.0, dt * 3.4)
                prev_x, prev_y = d.x, d.y
                d.x += (tx - d.x) * k
                d.y += (ty - d.y) * k
                if visible_enemies:
                    tgt = min(visible_enemies,
                              key=lambda e: math.hypot(e.x - d.x, e.y - d.y))
                    d.angle = math.atan2(tgt.y - d.y, tgt.x - d.x)
                    d.fire_cd -= dt
                    if d.fire_cd <= 0:
                        d.fire_cd = (1.15 + 0.18 * (d.idx % 3)) * rate_mult
                        dx, dy = tgt.x - d.x, tgt.y - d.y
                        dist = math.hypot(dx, dy) or 1
                        self.projectiles.append(
                            Projectile(x=d.x, y=d.y, vx=dx / dist, vy=dy / dist,
                                       damage=drone_dmg, color=(255, 62, 177),
                                       size=3, speed=700.0, kind="player",
                                       is_drone=True))
                else:
                    d.angle = math.atan2(d.y - prev_y, d.x - prev_x + 1e-6)

        for p in list(self.projectiles):
            p.x += p.vx * p.speed * dt
            p.y += p.vy * p.speed * dt
            
            if p.kind == "player":
                for e in list(self.enemies):
                    # PAKET 8.8a: Boss-Trefferzone waechst mit der Groesse
                    r_e = BOSS_HIT_R.get(e.enemy_type, 30) if e.is_boss else 30
                    if math.hypot(e.x - p.x, e.y - p.y) < r_e:
                        dmg = p.damage
                        # AUFTRAG 8: LYRA ZIEL-OVERLAY addiert zeitweise
                        # Krit-Chance (crit_buff_pct, siehe activate_champ_skill).
                        crit = random.random() < (self.mod("crit_chance", 0.0)
                                                  + (self.crit_buff_pct
                                                     if self.crit_buff_t > 0.0
                                                     else 0.0))
                        if crit:
                            dmg *= self.mod("crit_mult", 2.0)   # NEU PAKET 4: ZIELRECHNER/PANZERBRECHER
                        if e.is_boss:                                                # PAKET 8.8
                            dmg *= 1.0 - e.dr                                        # PAKET 8.8: Panzerung
                            dmg *= 1.0 + self.mod("boss_dmg_pct", 0.0)               # BOSS-JAEGER (jetzt alle Bosse)
                        if self.mod("bully", 0.0) > 0 and e.hp < e.max_hp * 0.5:
                            dmg *= 1.0 + self.mod("bully", 0.0)   # NEU PAKET 4: BULLY
                        dmg = max(1, int(dmg))
                        e.hp -= dmg
                        e.hit_flash = 0.15
                        # AUFTRAG 21: Treffer-Glitzer in der Typ-Farbe
                        _fx = ENEMY_FX_COL.get(e.enemy_type, (0, 255, 255))
                        self.particles.append(Particle(
                            p.x, p.y,
                            random.uniform(-50, 50), random.uniform(-50, 50),
                            _fx, random.uniform(2.0, 4.0), 0.28, 0.28))
                        if crit:
                            self._spawn_damage(e.x, e.y - 30, dmg, (255, 190, 76), big=True)
                        else:
                            self._spawn_damage(e.x, e.y - 30, dmg, (0, 255, 255))
                        if (self.mod("execute_chance", 0.0) > 0 and 0 < e.hp <= e.max_hp * 0.2
                                and random.random() < self.mod("execute_chance", 0.0)):
                            e.hp = -1   # NEU PAKET 4: EXEKUTOR
                            self._spawn_damage(e.x, e.y - 55, "EXEK!", (255, 77, 100), big=True)
                        if p in self.projectiles: self.projectiles.remove(p)
                        if e.hp <= 0 and e in self.enemies:
                            # SCHRITT 1a: Belohnung (Credits/Salvage/Cores)
                            # jetzt gebuendelt im Helper - identisch zum
                            # Kettenkill unten.
                            self._grant_kill_rewards(e)
                            self._spawn_explosion(e.x, e.y, e.enemy_type)
                            SFX.play("explosion", 0.5)
                            # PAKET 8: Abschuss fuer Quest-Fortschritt buchen
                            self._quest_kill_book()
                            if self.mod("explosive", 0) >= 1 and not self.is_idle:
                                for o in list(self.enemies):   # NEU PAKET 4: SPRENGSPITZE
                                    if o is e:
                                        continue
                                    if math.hypot(o.x - e.x, o.y - e.y) < 90:
                                        o.hp -= self.cannon_damage * 0.3
                                        self._spawn_damage(o.x, o.y - 30, int(self.cannon_damage * 0.3), (255, 190, 76))
                                        if o.hp <= 0 and o in self.enemies:
                                            # SCHRITT 1a: Kettenabschuss bekommt
                                            # jetzt dieselbe Belohnung wie der
                                            # Hauptkill (Credits + Core-Wurf),
                                            # nicht nur die Quest-Buchung.
                                            self._grant_kill_rewards(o)
                                            self._spawn_explosion(o.x, o.y, o.enemy_type)
                                            self.enemies.remove(o)
                                            # PAKET 8: Kettenabschuss zaehlt mit
                                            self._quest_kill_book()
                            self.enemies.remove(e)
                        break
            
            elif p.kind == "enemy":
                if math.hypot(cx - p.x, cy - p.y) < 80:
                    # PUNKT-4-AUFTRAG: Schadensrechnung (ABFANG-FELD dr_pct,
                    # Idle-Schutz, LETZTER WILLE) zentral - Verhalten
                    # identisch zum bisherigen Projektil-Pfad (PAKET 7B).
                    applied = self._apply_player_damage(p.damage, cx, cy)
                    self._spawn_damage(p.x, p.y - 15, applied, (255, 77, 100))   # NEU PAKET 4: Schadenszahl (Spieler)
                    # PAKET 8.3: Einschlag fuer die Damage-FX am Schiff buchen
                    self.hit_events.append((float(p.x), float(p.y), float(applied)))
                    if len(self.hit_events) > 32:      # Sicherheitsdeckel
                        del self.hit_events[:-16]
                    if self.mod("retaliate", 0) > 0:
                        self.retaliate_timer = 2.0 + 0.5 * self.mod("retaliate", 0)   # NEU PAKET 4: PULSGENERATOR
                    if p in self.projectiles: self.projectiles.remove(p)
                    if not self.is_idle:
                        SFX.play("hit", 0.5)

            if p.x > 650 or p.x < -100 or p.y < 0 or p.y > 600:
                if p in self.projectiles: self.projectiles.remove(p)

        # NEU: Stufe abgeschlossen, aber NICHT automatisch die nächste starten!
        if not self.is_idle and not self.enemies and self.spawn_queue == 0:
            self.stage_cleared = True

    # ---------------- SCHRITT 1a: Kill-Belohnung gebuendelt ------------
    def _grant_kill_rewards(self, enemy):
        """Vollstaendige Belohnung fuer EINEN Abschuss buchen: Credits
        (inkl. Frost-Pruefung, credit_pct/idle_pct, BAL_CREDITS),
        SCHROTTBERGUNG und Data-Core-Wurf. Wird vom Hauptkill UND vom
        SPRENGSPITZE-Kettenkill benutzt, damit beide identisch entlohnt
        werden (SCHRITT 1a). Quest-Buchung bleibt beim Aufrufer."""
        # PAKET 8.8b: IDLE-MAXIMUM - wenn main.py das Einkommen
        # eingefroren hat (8 h Idle erreicht), gibt es hier NICHTS
        # mehr (keine Credits, keine Cores); Abschuesse/Quests
        # zaehlen weiter.
        frozen = self.is_idle and self.income_frozen
        gain_mult = 0.0 if frozen else \
            (1.0 + self.mod("idle_pct", 0.0)) if self.is_idle else (1.0 + self.mod("credit_pct", 0.0))
        if not frozen:
            gain_mult *= BAL_CREDITS * (BAL_IDLE_CREDITS if self.is_idle else 1.0)
        reward = int(enemy.reward * gain_mult)   # NEU PAKET 4: IDLE-PROTOKOLL/KRIEGSKASSE
        self.credits += reward
        if not self.is_idle:                                 # NEU PAKET 7B
            extra = int(self.mod("salvage_flat", 0))         # NEU PAKET 7B: SCHROTTBERGUNG
            if extra:
                self.credits += extra
        if self.is_idle:
            self.idle_loot_earned += reward
            self.idle_kill_counter += 1
            # PAKET 8.4: Idle-Cores seltener (1/25 -> 1/60 Kills)
            # PAKET 8.8b: ... und gar nicht mehr nach 8 h
            if not frozen and self.idle_kill_counter % 60 == 0:
                # AUFTRAG 22: Core-Deckel je 24-h-Fenster (war ungedeckelt:
                # ~105 Cores je 8-h-Sitzung; Offline-Bericht: 20).
                if self.idle_cores_used < IDLE_LIVE_CORE_CAP:
                    self.data_cores_earned += 1   # Idle -> Data Cores
                    self.idle_cores_used += 1
        else:
            # PAKET 7C/8.4: BALANCING DER CORE-VERGABE.
            # Erstbeendung: 30% je Kill (vorher 100% - das
            # flutete den Skill-Baum nach einer Kampagne).
            # Wiederholung: 10% je Kill, Elite-Stufen (5,10)
            # 25%, Boss 1 garantiert - Farmen lohnt nur
            # noch marginal, First-Clear bleibt im Vorteil.
            if self.is_repeat:
                if self.stage_id == 15:
                    cores = 1
                elif self.stage_id in (5, 10):
                    cores = 1 if random.random() < 0.25 else 0
                else:
                    cores = 1 if random.random() < 0.10 else 0
                if random.random() < self.mod("core_chance", 0.0):
                    cores += 1
            else:
                cores = (1 if random.random() < 0.30 else 0) \
                        + (1 if random.random() < self.mod("core_chance", 0.0) else 0)
            self.data_cores_earned += cores

    # ---------------- PAKET 8: Quest-Buchung ----------------
    def _quest_kill_book(self):
        """Abschuss klassifizieren und in kill_stats buchen (kein direkter
        Rückgriff auf das Quest-System - main.py polls die Deltas)."""
        if self.stage_id == 15:
            self.kill_stats["boss"] += 1
        elif self.stage_id in (5, 10):
            self.kill_stats["elite"] += 1
        self.kill_stats["normal"] += 1

    def get_result(self):
        """Gibt das Ergebnis der Stufe zurück, damit main.py es verarbeiten kann."""
        return {
            "won": not self.is_defeated and self.stage_cleared,
            "credits_earned": self.credits
        }

    @property
    def is_defeated(self):
        return self.player_hp <= 0 and not self.is_idle