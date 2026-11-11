# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 8 - RPG-KONFIGURATION (ZENTRALE QUELLE)
==================================================================
Alle Werte des RPG-Progressionssystems an einem Ort:
  - XP-Kurve des Spielerlevels
  - Kampagnen-XP (First Clear / Wiederholung / Elite / Boss)
  - Daily-/Weekly-Quest-Pools, Boni und Belohnungen
  - Beschwörung: Kosten, Wahrscheinlichkeiten, Duplikat-Entschädigung
  - Einheiten-Katalog (12 Einheiten, 4 Seltenheitsstufen)

KEINE anderen Datei darf Balance-Werte dieses Systems hart kodieren.
Nur diese Datei aendern, um zu balancen.
"""
import math

# ----------------------------------------------------------------------
# Ressourcen
# ----------------------------------------------------------------------
QUANTUM_NAME = "QUANTUM"          # Premium-Waehrung (Anzeige im HUD)

# ----------------------------------------------------------------------
# SCHRITT 3: ZENTRALER BALANCE-BLOCK
# ----------------------------------------------------------------------
# Alle globalen Balancing-Koeffizienten des Spiels an EINEM Ort. Vorher
# verstreut (pve_system.py, module_system.py, skill_tree.py) - die drei
# Module importieren die Werte jetzt nur noch. HIER aendern zum
# Balancen, Werte exakt wie zuvor (nichts verschoben, nur umgezogen).

# NEU PAKET 4: Globale Balancing-Koeffizienten (wirken auch auf Excel-Werte)
BAL_PLAYER_DMG = 1.6    # Kanonenschaden x1.6  -> Grundausstattung traegt die ersten Stufen
BAL_PLAYER_RATE = 0.88  # Feuerintervall x0.88 -> schneller
BAL_PLAYER_HP = 1.4     # Huelle x1.4
BAL_ENEMY_HP = 0.85     # Gegner-HP x0.85
BAL_ENEMY_DMG = 0.7     # Gegner-Schaden x0.7
BAL_BOSS_HP = 1.25      # PAKET 8.8: Boss-HP x1.25 (vorher x0.7 - Boss viel zu leicht)

# PAKET 8.4: OEKONOMIE-BREMSKLOETZE (Ressourcen-Flut stoppen).
#   BAL_CREDITS       : ALLE Kill-Belohnungen (aktiv + idle) x0.45
#   BAL_IDLE_CREDITS  : Idle-Zusatzfaktor x0.55 (Idle-Einkommen netto x0.25)
# Grund: Kampagne 1 Erstclear spuelte ~4.300 Cr in einer Session - die
# Kanone war damit in Level 7 durchlaufbar. Mit x0.45 liegt der Erstclear
# bei ~1.900 Cr und Modul-Level 7 (Kosten x5.6, s. BAL_COST_MULT) braucht
# mehrjaehriges Farmen statt einer Session.
BAL_CREDITS = 0.45
BAL_IDLE_CREDITS = 0.55

# PAKET 8.7: KAMPAGNE-FAHRENDAEMPFUNG - Daempfung von HP/DMG ab Stufe 9,
# kumulativ je Stufe (Stufe 12: HP x0.83 / DMG x0.89). Wirkt in
# pve_system.stage_late_hp_factor / stage_late_dmg_factor.
BAL_LATE_STAGE_HP = 0.955        # HP-Faktor je Stufe UEBER Stufe 8
BAL_LATE_STAGE_DMG = 0.97        # DMG-Faktor je Stufe UEBER Stufe 8

# PAKET 8.4: GLOBALE SKILL-KOSTENBREMSE. Grund: Ein Kampagne-1-Erstclear
# brachte vorher ~130 Cores (1 je Kill) und die ersten Stufen kosteten
# nur 8 - der ganze Baum war in einer Session durchtrainiert. Jetzt:
# Core-Drops gedrosselt UND Preise x2.5 (erste 3 Stufen Basispreis,
# danach zusaetzlich x1.5 - siehe skill_tree).
SKILL_COST_MULT = 2.5

# PAKET 8.7: PREISBREMSE STUFE 2 (Nutzer-Feedback: "Upgrades gehen zu
# schnell, Preise sind immer noch zu low - Einkommen kann so bleiben").
# Alle Modul- und Schiffspreise werden mit diesem Faktor multipliziert,
# das EINKOMMEN (Kills, Quests, Idle) bleibt unveraendert. Gegenueber dem
# Original (1.0) sind Preise damit x5.6, gegenueber Paket 8.4 (2.8)
# verdoppelt: Eine Waffe auf Level 7 kostet kumuliert rund einen
# Mehr-Tage-Etat aus Kampagne + Dailies statt einer Session.
BAL_COST_MULT = 5.6

# ----------------------------------------------------------------------
# AUFTRAG 16b: KAMPAGNEN-SKALIERUNG (Sektoren 1-5)
# ----------------------------------------------------------------------
# Vorher galten fuer ALLE Sektoren dieselben Gegner-/Boss-Werte - Sektor 5
# war exakt so schwer wie Sektor 1. Jetzt wird JEDE folgende Kampagne
# spuerbar anspruchsvoller; die Beute steigt mit (bewusst weniger stark
# als die Gefahr), damit sich das Farmen im hoeheren Sektor lohnt, ohne
# das Einkommen pauschal anzuheben.
#
# GRUNDPRINZIP (Nutzer-Vorgabe): Kampagne 1 ist mit Schiff L4-5 und
# Moduln um L4-5 realistisch schaffbar -> Sektor 1 bleibt bei Faktor 1.0
# (die Bosswerte von Stufe 10/15 wurden in pve_system.BOSS_DATA direkt
# auf dieses Niveau nachjustiert). Die Werte hier heben die SEKTOREN 2-5
# darueber an. Simulierbar ueber tools/simulate_campaign.py.
CAMPAIGN_HP_MULT     = {1: 1.0, 2: 1.30, 3: 1.70, 4: 2.20, 5: 2.85}
CAMPAIGN_DMG_MULT    = {1: 1.0, 2: 1.15, 3: 1.32, 4: 1.52, 5: 1.75}
CAMPAIGN_REWARD_MULT = {1: 1.0, 2: 1.12, 3: 1.26, 4: 1.42, 5: 1.60}
# Spawn-Intervall-Faktor (multipliziert die Pause zwischen zwei Spawns;
# kleiner = Gegner kommen schneller nach). Kampagne 1 unveraendert.
CAMPAIGN_SPAWN_SPD   = {1: 1.0, 2: 0.93, 3: 0.87, 4: 0.80, 5: 0.75}

# ----------------------------------------------------------------------
# SPIELERLEVEL / XP-KURVE (zentral konfigurierbar)
# ----------------------------------------------------------------------
# XP von Stufe L auf L+1:  round(BASE * GROWTH^(L-1) + LINEAR*(L-1))
# Bewusst moderat: 1.32er Wachstum - "darf nicht zu schnell steigen".
PLAYER_XP_BASE = 300
PLAYER_XP_GROWTH = 1.32
PLAYER_XP_LINEAR = 0
PLAYER_MAX_LEVEL = 60

# ----------------------------------------------------------------------
# KAMPAGNEN-XP
# ----------------------------------------------------------------------
CAMPAIGN_XP_BASE = 60             # Grund-XP je abgeschlossener Mission
CAMPAIGN_XP_PER_STAGE = 12        # + XP je Stufe der Mission (1..15)
CAMPAIGN_XP_REPEAT_FACTOR = 0.4   # Wiederholung bringt 40 %
CAMPAIGN_XP_ELITE_MULT = 1.5      # Elite-Missionen (Stufe 5/10)
CAMPAIGN_XP_BOSS_MULT = 3.0       # Boss-Mission (Stufe 15)


def campaign_xp(stage_id, is_repeat=False):
    """XP einer abgeschlossenen Kampagnenmission (zentrale Formel)."""
    xp = CAMPAIGN_XP_BASE + CAMPAIGN_XP_PER_STAGE * max(1, int(stage_id))
    if int(stage_id) in (5, 10):
        xp *= CAMPAIGN_XP_ELITE_MULT
    elif int(stage_id) == 15:
        xp *= CAMPAIGN_XP_BOSS_MULT
    if is_repeat:
        xp *= CAMPAIGN_XP_REPEAT_FACTOR
    return max(1, int(round(xp)))


def xp_for_level(level):
    """XP, die benoetigt wird, um von `level` auf `level+1` zu kommen."""
    if level >= PLAYER_MAX_LEVEL:
        return None
    l = max(1, int(level))
    return max(1, int(round(PLAYER_XP_BASE * (PLAYER_XP_GROWTH ** (l - 1))
                            + PLAYER_XP_LINEAR * (l - 1))))


# ----------------------------------------------------------------------
# QUESTS - Metriken (Ereignisse aus dem echten Gameplay)
# ----------------------------------------------------------------------
# stages          : Kampagnenmission abgeschlossen (aktiv, nicht Idle)
# kills           : Gegner im aktiven Gefecht besiegt
# elite_kills     : Gegner auf Elite-Stufen (5/10) besiegt
# boss_kills      : Boss (Stufe 15) besiegt
# module_upgrades : Modul in der Werft verbessert
# mission_clean   : Mission abgeschlossen, ohne dabei einmal verloren zu haben
# cores_earned    : Data Cores im Gefecht erhalten (aktiv + idle)
QUEST_COUNT_IDLE_KILLS = False    # Idle-Abschuesse zaehlen fuer "kills"?

# PAKET 8.4: QUEST-OEKONOMIE GEBREMST.
# Vorher spuelten Quests ~47.000 Cr/Woche in die Kasse - 11x so viel wie
# ein kompletter Kampagne-1-Erstclear (~4.300 Cr). Das war die Haupt-
# ursache fuer "zu viele Ressourcen". Jetzt: Daily-Credits ~x0.4,
# Weekly-Credits ~x0.3, Quest-Cores leicht reduziert. XP/Quantum
# unveraendert (Spielerlevel vergibt keine Boni; Quantum ist Gacha-
# Premiumwaehrung und war nicht Teil der Beschwerde).

# Täglicher Reset: lokale Mitternacht. Wöchentlicher Reset: Montag 00:00 lokal.
DAILY_ACTIVE = 4                  # 4 von 7 Pool-Aufgaben erscheinen pro Tag
WEEKLY_ACTIVE = 5                 # 5 von 6 Pool-Aufgaben erscheinen pro Woche

DAILY_POOL = [
    {"id": "schlachtfeld", "name": "SCHLACHTFELD", "metric": "stages",
     "desc": "3 Kampagnenlevel abschliessen", "goal": 3,
     "rewards": {"xp": 250, "credits": 160}},
    {"id": "vernichtung", "name": "VERNICHTUNG", "metric": "kills",
     "desc": "40 Gegner besiegen", "goal": 40,
     "rewards": {"xp": 200, "credits": 140}},
    {"id": "elitejaeger_d", "name": "ELITEJAEGER", "metric": "elite_kills",
     "desc": "2 Elitegegner besiegen", "goal": 2,
     "rewards": {"xp": 220, "credits": 120, "quantum": 2}},
    {"id": "ingenieur_d", "name": "INGENIEUR", "metric": "module_upgrades",
     "desc": "1 Modul verbessern", "goal": 1,
     "rewards": {"xp": 180, "credits": 100}},
    {"id": "einsatzbereit", "name": "EINSATZBEREIT", "metric": "mission_clean",
     "desc": "1 Mission abschliessen, ohne zu verlieren", "goal": 1,
     "rewards": {"xp": 260, "credits": 180}},
    {"id": "sammler", "name": "SAMMLER", "metric": "cores_earned",
     "desc": "3 Data Cores erhalten", "goal": 3,
     "rewards": {"xp": 150, "cores": 2}},
    {"id": "ausdauer", "name": "AUSDAUER", "metric": "stages",
     "desc": "6 Kampagnenlevel abschliessen", "goal": 6,
     "rewards": {"xp": 420, "credits": 280, "quantum": 2}},
]

WEEKLY_POOL = [
    {"id": "kriegsveteran", "name": "KRIEGSVETERAN", "metric": "stages",
     "desc": "25 Kampagnenlevel abschliessen", "goal": 25,
     "rewards": {"xp": 3000, "credits": 1500}},
    {"id": "flottenzerstoerer", "name": "FLOTTENZERSTOERER", "metric": "kills",
     "desc": "300 Gegner besiegen", "goal": 300,
     "rewards": {"xp": 2500, "credits": 1200, "quantum": 10}},
    {"id": "elitejaeger_w", "name": "ELITEJAEGER", "metric": "elite_kills",
     "desc": "10 Elitegegner besiegen", "goal": 10,
     "rewards": {"xp": 2200, "credits": 1000, "quantum": 8}},
    {"id": "sektorbezwinger", "name": "SEKTORBEZWINGER", "metric": "boss_kills",
     "desc": "1 Boss besiegen", "goal": 1,
     "rewards": {"xp": 2800, "credits": 1400, "quantum": 12, "cores": 1}},
    {"id": "ingenieur_w", "name": "INGENIEUR", "metric": "module_upgrades",
     "desc": "10 Modul-Upgrades durchfuehren", "goal": 10,
     "rewards": {"xp": 2000, "credits": 900, "quantum": 6}},
    {"id": "eisern", "name": "EISERN", "metric": "mission_clean",
     "desc": "5 Missionen ohne Niederlage abschliessen", "goal": 5,
     "rewards": {"xp": 2600, "credits": 1100, "quantum": 8}},
]

# Abschlussboni (alle Aufgaben des Zeitraums abgeschlossen)
DAILY_BONUS = {"xp": 400, "credits": 240, "quantum": 3, "cores": 1}
WEEKLY_BONUS = {"xp": 5000, "credits": 2500, "quantum": 40, "cores": 2}

# ----------------------------------------------------------------------
# BESCHWOERUNG
# ----------------------------------------------------------------------
SUMMON_COST_SINGLE = 3            # Data Cores pro Einzelbeschoerung
SUMMON_COST_MULTI = 27            # 10x-Beschoerung (10 % Rabatt)
SUMMON_MULTI_COUNT = 10

# Offizielle Zieh-Wahrscheinlichkeiten (in der UI transparent angezeigt)
SUMMON_RATES = {"C": 0.60, "R": 0.27, "E": 0.10, "L": 0.03}

RARITY_ORDER = ["C", "R", "E", "L"]
RARITY_INFO = {
    "C": {"label": "COMMON",    "color": (168, 196, 214), "dup_credits": 150},
    "R": {"label": "RARE",      "color": (80, 180, 255),  "dup_credits": 400},
    "E": {"label": "EPIC",      "color": (190, 92, 255),  "dup_credits": 1200},
    "L": {"label": "LEGENDAER", "color": (255, 190, 76),  "dup_credits": 4000},
}

# SCHRITT 2: SAMMLUNGS-PASSIV (Champions/Einheiten wirken im Gefecht)
# Jede EINMALIG besessene Einheit/Held addiert den Bonus ihrer
# Seltenheit auf den Drohnenschaden (Modifikator "drone_dmg_pct").
# Duplikate zaehlen nicht - nur das Halten zaehlt. Bei voller
# Sammlung (5x C, 5x R, 4x E, 1x L) ergibt das +19,5 % Drohnenschaden.
# Anzeige pro Karte: "PASSIV: +1% Drohnenschaden".
PASSIV_DRONE_DMG_PCT = {"C": 0.005, "R": 0.01, "E": 0.02, "L": 0.04}

# Einheiten-Katalog: Jäger- und Unterstuetzungsdrohnen passend zur
# Hangar-Mechanik. `stats` sind definierte Werte fuer eine SPAETERE
# Integration (werden aktuell nirgendwo automatisch angewendet!).
UNITS = [
    {"key": "skimmer", "name": "SKIMMER MK-I", "rarity": "C",
     "desc": "Wendiger Aufklärungsspäher mit Weitwinkel-Scan.",
     "stats": {"dmg_mult": 1.00, "rate_mult": 1.00, "hp": 40}},
    {"key": "stichel", "name": "STICHEL D-9", "rarity": "C",
     "desc": "Leichter Jagdflieger für vordere Ketten.",
     "stats": {"dmg_mult": 1.10, "rate_mult": 0.95, "hp": 45}},
    {"key": "wachposten", "name": "WACHTPOSTEN", "rarity": "C",
     "desc": "Orbitale Geschützplattform mit standfestem Dauerfeuer.",
     "stats": {"dmg_mult": 0.95, "rate_mult": 1.10, "hp": 60}},
    {"key": "funke", "name": "FUNKE-01", "rarity": "C",
     "desc": "Stördrohne, vernebelt feindliche Zielradare.",
     "stats": {"dmg_mult": 0.90, "rate_mult": 1.05, "hp": 50}},
    {"key": "razorlight", "name": "RAZORLIGHT", "rarity": "C",
     "desc": "Schnelljäger mit Leichtbaurumpf und Klingenkanzel.",
     "stats": {"dmg_mult": 1.05, "rate_mult": 1.15, "hp": 35}},
    {"key": "vulkan", "name": "VULKAN-V2", "rarity": "R",
     "desc": "Schwerer Kanonenjäger mit Doppellauf-Turm.",
     "stats": {"dmg_mult": 1.35, "rate_mult": 0.90, "hp": 80}},
    {"key": "aegis", "name": "AEGIS-WACHTER", "rarity": "R",
     "desc": "Schild-Unterstützungsdrohne, stärkt den Defensivring.",
     "stats": {"dmg_mult": 0.90, "rate_mult": 1.00, "hp": 110}},
    {"key": "nachtfalter", "name": "NACHTFALTER", "rarity": "R",
     "desc": "Tarnaufklärer, schlüpft an Feindverbänden vorbei.",
     "stats": {"dmg_mult": 1.20, "rate_mult": 1.20, "hp": 55}},
    {"key": "ionfaenger", "name": "IONFÄNGER", "rarity": "R",
     "desc": "Ionen-Interzeptor gegen gehärtete Panzerungen.",
     "stats": {"dmg_mult": 1.40, "rate_mult": 1.00, "hp": 70}},
    {"key": "phantom", "name": "PHANTOM-X", "rarity": "E",
     "desc": "Tarnkappenjäger mit schallgedämpftem Antrieb.",
     "stats": {"dmg_mult": 1.60, "rate_mult": 1.25, "hp": 90}},
    {"key": "novakanonier", "name": "NOVA-KANONIER", "rarity": "E",
     "desc": "Artillerie-Drohne mit Plasmabatterie und Zielschleuse.",
     "stats": {"dmg_mult": 1.75, "rate_mult": 0.85, "hp": 130}},
    {"key": "leviathan", "name": "LEVIATHAN-PRIME", "rarity": "L",
     "desc": "Autonomes Flaggschiff mit eigenem Eskortenschwarm.",
     "stats": {"dmg_mult": 2.20, "rate_mult": 1.10, "hp": 220}},
]

# ----------------------------------------------------------------------
# PAKET 8.5: HELDEN-CHAMPIONS (nutzergenerierte Grafiken)
# ----------------------------------------------------------------------
# Eigene Heldentruppe NEBEN den 12 Drohnen. Die Bilder liegen in
# champions/<key>/ :  figure.png  = Sammlungs-/Ergebnis-Sprite
#                     portrait.jpg = Kopfbild (Ergebniskarte)
#                     attack.jpg / special.png / skill_icon.png = Reserve
# `stats` sind wie bei den Drohnen definiert, werden aber NICHT
# automatisch angewendet (spaetere Hangar-Anbindung kann sie lesen).
HEROES = [
    {"key": "ingenieur", "name": "INGENIEUR", "rarity": "R", "hero": True,
     "dir": "champions/ingenieur",
     "desc": "Feldtechniker der Bunker-Infanterie. Haelt Systeme unter "
             "Feuer laufend und improvisiert Waffen aus Schrott.",
     "stats": {"dmg_mult": 1.15, "rate_mult": 1.05, "hp": 95}},
    {"key": "lyra", "name": "LYRA", "rarity": "E", "hero": True,
     "dir": "champions/lyra",
     "desc": "Taktikerin mit Gefechtsfeld-Overlay. Sieht Feindbewegungen, "
             "bevor sie auf den Scannern erscheinen.",
     "stats": {"dmg_mult": 1.55, "rate_mult": 1.15, "hp": 105}},
    {"key": "nova", "name": "NOVA", "rarity": "E", "hero": True,
     "dir": "champions/nova",
     "desc": "Sturmtruppin mit Plasmakanone. Entlaedt Energiestoesse, "
             "die Panzerungen aufschmelzen.",
     "stats": {"dmg_mult": 1.70, "rate_mult": 1.20, "hp": 120}},
]

# ----------------------------------------------------------------------
# AUFTRAG 8: CHAMPIONS - AUSRUESTUNG & FAEHIGKEITEN
# ----------------------------------------------------------------------
# Drei ausruestbare Champion-Slots (SummonSystem.equipped). Ausgeruestete
# Champions UNTERSTUETZEN das Schiff, ersetzen es nicht:
#   * Aktive Stats: dmg_mult -> +x% Schaden, rate_mult -> Feuerintervall
#     (invers, 1.05 = +5% Feuer rate), hp -> +flache Huelle. Wirkung in
#     main._sync_modules_to_combat (ohne SYSTEM-SYNERGIE-Verstaerkung).
#   * Faehigkeit: EINE aktive Faehigkeit je Champion, ausloesbar im
#     Gefecht (pve_system.PvECombat.activate_champ_skill); im HUD
#     erscheinen zunaechst maximal ZWEI Skill-Buttons (CHAMPION_HUD_BUTTONS).
CHAMPION_SLOTS = 3
CHAMPION_HUD_BUTTONS = 2
# Effektfelder (mult/crit_pct/dur/heal_pct) liest pve_system.activate_champ_skill.
CHAMPION_SKILLS = {
    "nova": {"name": "PLASMASTOSS", "cd": 12.0, "mult": 4.0,
             "desc": "Energieschuss: 4x Kanonenschaden aufs vorderste Ziel"},
    "lyra": {"name": "ZIEL-OVERLAY", "cd": 18.0, "crit_pct": 0.25, "dur": 6.0,
             "desc": "6 s lang +25% Krit-Chance"},
    "ingenieur": {"name": "FELD-REPARATUR", "cd": 25.0, "heal_pct": 0.12,
                  "desc": "Heilt sofort 12% der max. Huille"},
}

# Gesamt-Pool der Beschwörung: Drohnen + Helden
ALL_PULLABLE = UNITS + HEROES

UNITS_BY_KEY = {u["key"]: u for u in ALL_PULLABLE}


def units_of_rarity(rarity):
    return [u for u in ALL_PULLABLE if u["rarity"] == rarity]


# ----------------------------------------------------------------------
# PAKET 8.6: BESCHWOERUNGS-ZEREMONIE (Inszenierung)
# ----------------------------------------------------------------------
# Ablauf in 5 Phasen: Konvergenz -> Materialisierung -> Aufladung ->
# Burst -> Offenbarung. Die Kapsel ist bewusst NICHT von Anfang an
# sichtbar: Sie materialisiert sich erst in Phase 2 auf dem Podest.
CEREMONY_MS_NORMAL = 6000          # Dauer COMMON/RARE-Zeremonie (ms)
CEREMONY_MS_EPIC = 7600            # Dauer EPIC/LEGENDAER-Zeremonie (ms)

# Phasengrenzen (Anteil der Gesamtdauer)
CEREMONY_P1_KONVERGENZ = 0.30      # Dunkelheit, Energie sammelt sich
CEREMONY_P2_MATERIAL = 0.52        # Kapsel materialisiert sich (flickert)
CEREMONY_P3_AUFLADUNG = 0.70       # Streifen glimmen, Zittern steigt
CEREMONY_P4_BURST = 0.78           # Energie-Burst, Kapsel loest sich auf
# ab 0.78: Offenbarung (Einheit steigt auf, Banner mit Name + Seltenheit)

# ----------------------------------------------------------------------
# PAKET 8.6: IDLE-OEKONOMIE (Offline-Einkommen + Idle-Bericht)
# ----------------------------------------------------------------------
# Beim Start wird die Abwesenheitszeit (Diff zur letzten Sicherung)
# verguetet: Credits + Data Cores, angelehnt an die gemessene Live-Idle-
# Rate (~0.7 Cr/s auf Stufe 1 bis ~1.9 Cr/s auf Stufe 12), aber deutlich
# abgemildert (PAKET-8.4-Geist: Oekonomie nicht fluten).
IDLE_MIN_AWAY_S = 90               # kuerzer als 90 s -> kein Bericht
IDLE_CAP_S = 8 * 3600              # max. 8 h werden verguetet
IDLE_CPS_BASE = 0.32               # seit SCHRITT 3b unbenutzt (Report rechnet Live-Formel; Wert bleibt fuer Rueckkehr)
IDLE_CPS_PER_STAGE = 0.075         # seit SCHRITT 3b unbenutzt (dto.)
# AUFTRAG 5: OFFLINE-IDLE ATTRAKTIVER (Live-Idle behaelt den Bonus).
#   IDLE_EFFICIENCY : 0.60 -> 0.85 - Offline bringt jetzt 85 % des Live-
#                     Ertrags (Live-Bonus = +17.6 %). Vorher war Offline
#                     mit 60 % fast nicht mehr lohnend.
#   IDLE_CORE_KILLS : 550 -> 200 - 1 Core je 200 virtuelle Kills (war
#                     je 550: bei 0.22 Kills/s rund 42 min/Core, das war
#                     neunmal schlechter als Live und fühlte sich leer an).
#                     Jetzt ~15 min/Core - Live bleibt klar im Vorteil
#                     (1 Core je 60 echten Kills, ~4-5 min).
#   IDLE_CORE_CAP   : 14 -> 20 - Deckel passt zum hoeheren Core-Zufluss
#                     (8 h ergeben jetzt ~32 Cores, gedeckelt bei 20).
IDLE_EFFICIENCY = 0.85             # Offline bringt 85 % des Live-Ertrags
IDLE_KPS = 0.22                    # virtuelle Abschuesse/s (Messwert Live)
IDLE_CORE_KILLS = 200              # 1 Data Core je so viele virtuelle Kills
IDLE_CORE_CAP = 20                 # Core-Deckel pro Bericht
IDLE_AUTOCOLLECT_S = 8.0           # Live: alle 8 s in die Wallet ueberweisen
IDLE_SAVE_HEARTBEAT_S = 30.0       # alle 30 s sichern (saved_at bleibt frisch)

# ----------------------------------------------------------------------
# AUFTRAG 6: NEW GAME+ (nach Kampagne 5)
# ----------------------------------------------------------------------
# Wird die Stufe 15 von Sektor 5 (die letzte Kampagne) gewonnen,
# erscheint der VICTORY-Screen und der NG+-Grad steigt um 1. Jeder
# NG+-Grad skaliert GEGNER und BELOHNUNGEN - alle anderen Mechaniken
# bleiben unveraendert. Werte bewusst moderat (ng = NG+-Grad, ab 1):
NG_HP_PCT = 0.35          # Gegner-/Boss-HP      x(1 + 0.35 * ng)
NG_DMG_PCT = 0.25         # Gegner-/Boss-Schaden x(1 + 0.25 * ng)
NG_REWARD_PCT = 0.30      # Credits/Beute        x(1 + 0.30 * ng)


def ng_hp_mult(ng):
    return 1.0 + NG_HP_PCT * max(0, int(ng))


def ng_dmg_mult(ng):
    return 1.0 + NG_DMG_PCT * max(0, int(ng))


def ng_reward_mult(ng):
    return 1.0 + NG_REWARD_PCT * max(0, int(ng))
