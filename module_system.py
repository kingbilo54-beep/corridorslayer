"""Persistent module progression and clearly defined stat bonuses for CORRIDOR SLAYER.

PAKET 7B:
  * Neues Modul "reaktor" (Reaktor / Energieversorgung) - die geforderten
    5 Upgrade-Module (Waffen, Schild, Reaktor, Antrieb, Hangar) sind damit
    einzeln aufwertbar; die bestehenden Module radar/reparatur bleiben.
  * MODULE_INFO: eine zentrale Tabelle mit Wirktexten. Sie dient AUSSCHLIESSLICH
    der Anzeige ("Aktuelle Werte" / "Naechste Stufe") in der Werft; die echte
    Wirksamkeit bleibt in main._sync_modules_to_combat / pve_system.
  * cost_discount: Rabatt auf Upgrade-Preise (Skill OEkONOMIE "KONTRAKTE").
    main.py setzt das Feld beim Sync - module_system kennt skill_tree nicht.
  * cosmetic_hull: KOSMETISCHES Schiffslevel, strikt vom Gameplay getrennt.
    Es aendert NICHTS an Werten, wird nur manuell veraendert und gespeichert.
    Alle automatischen Optik-Kopplungen (Schiffskorpus, Geschützturm) sind
    entfernt - das Schiff sieht stabil aus, egal wie hoch die Module sind.

PAKET 7C:
  * Neues Modul "huelle" (SCHIFFSHUELLE): +100 max. Huelle je Stufe. Das
    Schild-Modul "schild" ist damit ein EIGENSTAENDIGES Schildsystem
    (Schadensreduktion je Stufe) und nicht mehr die Hullen-Anzeige.
  * MIGRATION: Alte Saves kennen "huelle" nicht - dort stand der Hullen-
    Bonus im "schild"-Level. Beim Laden wird "huelle" einmalig aus dem
    alten "schild"-Level uebernommen (kein Verlust!), dann gespeichert.

PAKET 7E:
  * SCHIFFSRUMPF (Feld cosmetic_hull, JSON-Key bleibt fueralte Saves
    kompatibel) ist jetzt ECHT aufwertbar: upgrade_ship() hebt das
    Schiffs-Level 1-12 (SHIP_MAX_LEVEL) gegen steigende Credit-Kosten
    (Schiffsbasis 400, Faktor 1.62, KONTRAKTE-Rabatt wirkt). Die Werft
    ruft das ueber den Button "SCHIFF AUFWERTEN" auf.
  * ECHTE WIRKUNG je Schiffs-Stufe: +80 max. Huelle und +3% Schaden
    (main._sync_modules_to_combat liest die Stufe). Das Schiffsbild
    wechselt auf fortress/ship_lvl_<Stufe>.png (Bilder 1-12).
  * ship_effect_values()/ship_next_effect(): Anzeige-Texte fuer die
    Werft (nur Anzeige - die Wirksamkeit bleibt in main.py).
"""
from dataclasses import dataclass, field
from pathlib import Path
import json
import time
import openpyxl
# SCHRITT 3: Preisbremse BAL_COST_MULT liegt zentral im BALANCE-Block
# von rpg_config.py und wird nur noch importiert (Wert identisch).
from rpg_config import BAL_COST_MULT

SAVE_PATH = Path(__file__).with_name("corridor_slayer_modules.json")

# PAKET 7E: Schiffs-Rumpf (das Schiff SELBST) - Stufe 1-12.
SHIP_MAX_LEVEL = 12
# AUFTRAG 23 (Punkt 3): Rumpf-Kurve auf "L9 fruehestens gegen Ende von
# Sektor 3" abgestimmt (weiche Steuerung NUR ueber Preise, keine Sperren).
#   alt: Base 400, Mult 1.62 -> L9 kumuliert 167,773 Cr, L12 725,042 Cr
#        (Finanzierbarkeit erst ab ~Sektor 6-8 - die Upgrade-Praemie fehlte
#        im Mid-Game komplett).
#   neu: Base 500, Mult 1.40 -> L9 kumuliert 96,305 Cr, L12 ~276,300 Cr.
#   Simulation (tools/simulate_player_types.py, 0 Skillpunkte): kumuliertes
#   Einkommen bis Ende Sektor 3 = ~70,000-80,000 Cr (Erst ~10,400 + Offline-
#   Naechte ~60,000 bei Mid-Game-Deckeln) - Rumpf 9 faellt kurz danach
#   natuerlich an ("fruehestens Ende Sektor 3"). Der reine Offline-Rusher
#   (AUFTRAG-22-Fenster-Deckel) kommt maximal 1-2 Tage frueher dran.
#   L12 bleibt Endgame-Kauf (+3%/Stufe-DMG unveraendert).
SHIP_BASE_COST = 500       # Kosten Stufe 1 -> 2
SHIP_COST_MULT = 1.40      # Kostenfaktor je weiterer Stufe
SHIP_HP_PER_LVL = 80       # +max. Huelle je Schiffs-Stufe (Wirkung in main.py)
SHIP_DMG_PCT_PER_LVL = 0.03  # +3% Schaden je Schiffs-Stufe (Wirkung in main.py)

# SCHRITT 3: BAL_COST_MULT (PAKET 8.7 PREISBREMSE STUFE 2) steht jetzt
# im BALANCE-Block von rpg_config.py (mit der Erklaerung dazu) und wird
# oben importiert - Wert und Wirkung identisch.

MODULE_DATA = {}
PLAYER_DATA_MOD = {}
# Defaults fuer Module, die im Excel fehlen (z.B. "reaktor"; PAKET 7C "huelle")
_DEFAULT_STATS = {
    "reaktor": {"BaseCost": 180, "CostMult": 1.8, "MaxLevel": 15},
    "huelle": {"BaseCost": 220, "CostMult": 1.85, "MaxLevel": 15},
}
try:
    # SCHRITT 1c: game_data.xlsx liegt neben dieser Datei - nicht mehr im
    # Arbeitsverzeichnis. So laedt die Werft die Preise auch, wenn das
    # Spiel aus einem anderen Ordner (anderes CWD) gestartet wurde.
    wb = openpyxl.load_workbook(str(Path(__file__).parent / "game_data.xlsx"))
    ws_m = wb["Modules"]
    for row in ws_m.iter_rows(min_row=2, values_only=True):
        if row[0]:
            MODULE_DATA[row[0]] = {"Name": row[1], "BaseCost": row[2], "CostMult": row[3], "MaxLevel": row[4]}

    ws_p = wb["Player"]
    for row in ws_p.iter_rows(min_row=2, values_only=True):
        if row[0]: PLAYER_DATA_MOD[row[0]] = row[1]
except Exception as e:
    print(f"⚠️ Konnte Excel-Daten nicht laden: {e}")


@dataclass
class UpgradeModule:
    key: str
    name: str
    description: str
    level: int = 1

    @property
    def base_cost(self):
        return int(MODULE_DATA.get(self.key, _DEFAULT_STATS.get(self.key, {})).get("BaseCost", 150))
    @property
    def cost_mult(self):
        return float(MODULE_DATA.get(self.key, _DEFAULT_STATS.get(self.key, {})).get("CostMult", 1.8))
    @property
    def max_level(self):
        return int(MODULE_DATA.get(self.key, _DEFAULT_STATS.get(self.key, {})).get("MaxLevel", 15))

    @property
    def cost(self):
        # PAKET 8.4: BAL_COST_MULT wirkt auf jede Modulstufe.
        return int(round(self.base_cost * (self.cost_mult ** (self.level - 1))
                         * BAL_COST_MULT))

    def upgrade(self, credits: int) -> int:
        if self.level >= self.max_level:
            raise ValueError(f"{self.name} ist bereits auf Maximalstufe.")
        price = self.cost
        if credits < price:
            raise ValueError(f"Zu wenig Credits: {price} benötigt.")
        self.level += 1
        return credits - price


@dataclass
class FortressModules:
    modules: dict = field(default_factory=dict)
    credits: int = 500 # Startkapital 500
    data_cores: int = 0
    highest_campaign: int = 1
    highest_stage: int = 1
    completed_stages: list = field(default_factory=list)
    completed_campaigns: list = field(default_factory=list)
    # PAKET 7B: kosmetisches Schiffslevel (STRIKT vom Gameplay getrennt).
    # Wird NIE automatisch veraendert - nur ein spaeteres Skin-Menue darf es
    # umschalten. Gameplay-Upgrades beruehren diese Zahl nicht.
    cosmetic_hull: int = 1
    # PAKET 7B: Upgrade-Rabatt (0..0.5), gesetzt von main.py (Oekonomie-Skill).
    cost_discount: float = 0.0

    def __post_init__(self):
        self.offline_seconds = 0.0
        # PAKET 8.6: saved_at des VORHERIGEN Programmlaufs. main.py liest
        # das beim Start, um das Offline-Einkommen (Idle-Bericht) zu
        # berechnen. 0.0 = erster Start / alter Save ohne Zeitstempel.
        self.prev_saved_at = 0.0
        # PAKET 8: RPG-Block (Spielerlevel/XP, QUANTUM, Quests, Beschoerung)
        # im selben Spielstand. rpg_raw = beim Laden gelesener Alt-Block,
        # rpg_ref = von main.py gesetzte Live-Objekte (RPGBundle).
        self.rpg_raw = None
        self.rpg_ref = None
        # AUFTRAG 22: LIVE-IDLE-FENSTER (Neustart-resistent). Rollierendes
        # 24-h-Fenster: max 8 h Idle-Einkommen und 20 Cores je Fenster.
        # Persistiert im Save; alte Saves ohne die Keys starten sauber mit
        # einem frischen Fenster (Defaults 0).
        self.idle_window_start = 0.0     # Unix-Zeit des Fenster-Starts (0 = frisch)
        self.idle_session_used_s = 0.0   # verbrauchte Idle-Einkommens-Sekunden
        self.idle_live_cores_used = 0    # verbrauchte Idle-Cores im Fenster
        # AUFTRAG 6: NEW GAME+ Grad (0 = erster Durchlauf). Steigt bei jedem
        # Sieg gegen die letzte Kampagne (Sektor 5, Stufe 15) - siehe
        # rpg_config.NG_* und main.py (VICTORY-Screen). Alte Saves ohne den
        # Key starten sauber bei 0.
        self.ng_plus = 0
        if not self.modules:
            self.modules = {
                "kanonen": UpgradeModule("kanonen", "Waffen / Kanonen", "Erhöht den Schaden der Hauptgeschütze", 1),
                "schild": UpgradeModule("schild", "Schildsystem", "Energieschild: reduziert erlittenen Schaden", 1),
                # PAKET 7C: eigenstaendiges Huellen-Modul (war frueher an
                # "schild" gekoppelt - siehe MIGRATION in load())
                "huelle": UpgradeModule("huelle", "Schiffshülle", "Verstärkte Panzerung: +100 max. Hülle je Stufe", 1),
                "reaktor": UpgradeModule("reaktor", "Reaktor / Energie", "Versorgt alle Systeme: Krit-Chance & Drohnen-Schaden", 1),
                "antrieb": UpgradeModule("antrieb", "Antrieb", "Erhöht die Feuerrate", 1),
                "hangar": UpgradeModule("hangar", "Hangar", "Startet Jäger-Drohnen im Gefecht", 1),
                "radar": UpgradeModule("radar", "Radar", "Aufklaerung: mehr Credits & Core-Chance", 1),
                "reparatur": UpgradeModule("reparatur", "Reparatur-Drohnen", "Heilt die Hülle über Zeit", 1),
            }
        self.load()

    @property
    def ship_level(self):
        """GAMEPLAY-Schiffslevel (Gegner-Spawning) - KEIN Optikwert mehr."""
        total_levels = sum(m.level for m in self.modules.values())
        levels_per_ship = int(PLAYER_DATA_MOD.get("levels_per_ship_level", 5))
        return max(1, (total_levels // levels_per_ship))

    # ---------------- PAKET 7E: SCHIFFSRUMPF (Stufe 1-12) ----------------
    @property
    def ship_hull_level(self):
        """Stufe des Schiffs SELBST (Rumpfklasse 1-12). Bestimmt das
        Schiffsbild (fortress/ship_lvl_x.png), +80 Huelle und +3% Schaden
        je Stufe. JSON-Key bleibt 'cosmetic_hull' (alte Saves kompatibel)."""
        return max(1, int(self.cosmetic_hull))

    def ship_upgrade_cost(self, level=None):
        """Credit-Kosten der naechsten Schiffs-Stufe (mit KONTRAKTE-Rabatt);
        None auf Maximalstufe."""
        lvl = self.ship_hull_level if level is None else max(1, int(level))
        if lvl >= SHIP_MAX_LEVEL:
            return None
        # PAKET 8.4: BAL_COST_MULT wirkt auch auf den Schiffs-Rumpf.
        price = int(round(SHIP_BASE_COST * (SHIP_COST_MULT ** (lvl - 1))
                          * BAL_COST_MULT))
        return max(1, int(round(price * (1.0 - min(0.5, max(0.0, self.cost_discount))))))

    def upgrade_ship(self):
        """Schiff auf die naechste Stufe heben (max. 12). Wirft ValueError
        bei Maximalstufe oder zu wenig Credits; zieht Credits ab und
        speichert. Liefert den gezahlten Preis."""
        if self.ship_hull_level >= SHIP_MAX_LEVEL:
            raise ValueError("Das Schiff ist bereits auf Maximalstufe 12.")
        price = self.ship_upgrade_cost()
        if self.credits < price:
            raise ValueError(f"Zu wenig Credits: {price} benötigt.")
        self.credits -= price
        self.cosmetic_hull = self.ship_hull_level + 1
        self.save()
        return price

    def get(self, key):
        return self.modules[key]

    @property
    def max_allowed_level(self):
        """PAKET 7D: Weiches Limit - die Kreditkosten (Kostenkurve mit
        x1.8/x1.85 pro Stufe) sind das eigentliche Tor. Der fruehere
        Kampagnen-Gate (3 Stufen = +1 Modul-Level) hat Spieler komplett
        ausgesperrt (alle Upgrades 'GESPERRT') und ist entfernt."""
        return 15

    def upgrade(self, key):
        module = self.get(key)

        if module.level >= module.max_level:
            raise ValueError(f"{module.name} ist bereits auf Maximalstufe (15).")

        # PAKET 7B: Oekonomie-Rabatt auf den Preis (Mindestpreis 1).
        price = max(1, int(round(module.cost * (1.0 - min(0.5, max(0.0, self.cost_discount))))))
        if self.credits < price:
            raise ValueError(f"Zu wenig Credits: {price} benötigt.")
        self.credits -= price
        module.level += 1
        self.save()
        return module

    def complete_stage(self, campaign_id, stage_id, credits_earned):
        self.credits += credits_earned

        stage_tuple = (campaign_id, stage_id)
        if stage_tuple not in self.completed_stages:
            self.completed_stages.append(stage_tuple)

        if campaign_id == self.highest_campaign:
            if stage_id == 15:
                if campaign_id not in self.completed_campaigns:
                    self.completed_campaigns.append(campaign_id)
                self.highest_campaign += 1
                self.highest_stage = 1
            else:
                self.highest_stage = max(self.highest_stage, stage_id + 1)

        self.save()

    def load(self):
        try:
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            self.credits = max(0, int(data.get("credits", self.credits)))
            self.data_cores = max(0, int(data.get("data_cores", 0)))
            self.highest_campaign = max(1, int(data.get("highest_campaign", 1)))
            self.highest_stage = max(1, int(data.get("highest_stage", 1)))
            self.completed_stages = [tuple(s) for s in data.get("completed_stages", [])]
            self.completed_campaigns = data.get("completed_campaigns", [])
            # PAKET 7B: neue Felder mit sicheren Defaults (alte Saves bleiben
            # voll kompatibel - fehlende Keys werden einfach ergaenzt).
            self.cosmetic_hull = max(1, int(data.get("cosmetic_hull", 1)))
            # AUFTRAG 6: NG+-Grad aus dem Spielstand (fehlt in alten Saves
            # -> 0, keine Migration noetig).
            self.ng_plus = max(0, int(data.get("ng_plus", 0)))
            levels = dict(data.get("levels", {}))
            # PAKET 7C MIGRATION: Vor 7C erhoehte "schild" die max. Huelle.
            # Alte Saves bekommen ihr Hullen-Level EINMALIG auf das neue
            # "huelle"-Modul uebertragen (kein Verlust); "schild" wirkt ab
            # jetzt als Schildsystem (Schadensreduktion) ab Level 1.
            if "huelle" not in levels and "schild" in levels:
                levels["huelle"] = levels["schild"]
                levels["schild"] = 1
            for key, module in self.modules.items():
                module.level = max(1, min(module.max_level, int(levels.get(key, 1))))
            # PAKET 8: RPG-Block erst einmal nur einlesen - die Live-
            # Objekte (rpg_ref) restauriert main.py nach dem Aufbau.
            self.rpg_raw = data.get("rpg")
            # PAKET 8.6: Zeitstempel der letzten Sicherung merken (Basis
            # fuer das Offline-Einkommen). Kein Schreiben noetig - save()
            # pflegt "saved_at" bereits bei jeder Sicherung.
            try:
                self.prev_saved_at = max(0.0, float(data.get("saved_at", 0.0)))
            except (TypeError, ValueError):
                self.prev_saved_at = 0.0
            # AUFTRAG 22: Idle-Fenster laden (fehlt in alten Saves -> Defaults,
            # main.py startet dann mit einem frischen 24-h-Fenster).
            try:
                self.idle_window_start = max(0.0, float(data.get("idle_window_start", 0.0)))
                self.idle_session_used_s = max(0.0, float(data.get("idle_session_used_s", 0.0)))
                self.idle_live_cores_used = max(0, int(data.get("idle_live_cores_used", 0)))
            except (TypeError, ValueError):
                self.idle_window_start = 0.0
                self.idle_session_used_s = 0.0
                self.idle_live_cores_used = 0
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def save(self):
        try:
            payload = {
                "credits": int(self.credits),
                "data_cores": int(self.data_cores),
                "highest_campaign": int(self.highest_campaign),
                "highest_stage": int(self.highest_stage),
                "completed_stages": self.completed_stages,
                "completed_campaigns": self.completed_campaigns,
                "cosmetic_hull": int(self.cosmetic_hull),
                "ng_plus": int(getattr(self, "ng_plus", 0)),
                "saved_at": time.time(),
                "levels": {key: int(module.level) for key, module in self.modules.items()},
                # AUFTRAG 22: Live-Idle-Fenster persistieren (Neustart-
                # resistente 24-h-Deckelung).
                "idle_window_start": float(getattr(self, "idle_window_start", 0.0)),
                "idle_session_used_s": float(getattr(self, "idle_session_used_s", 0.0)),
                "idle_live_cores_used": int(getattr(self, "idle_live_cores_used", 0)),
            }
            # PAKET 8: RPG-Block anhaengen, sobald die Systeme leben.
            if self.rpg_ref is not None:
                payload["rpg"] = self.rpg_ref.serialize()
            SAVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass


# ----------------------------------------------------------------------
# PAKET 7B: ANZEIGE-PROFILE DER MODULEFFEKTE (Werft-Panel)
# ----------------------------------------------------------------------
# Muss inhaltlich mit main._sync_modules_to_combat / pve_system uebereinstimmen.
# Jede Funktion liefert (aktueller_Stand, naechste_Stufe) als Textlisten.

def module_effect_values(key, lvl):
    """Aktuelle Werte eines Moduls (fuer das Werft-Panel)."""
    lvl = max(1, int(lvl))
    if key == "kanonen":
        # PUNKT 3: Deckel 8 wie cannon_count in pve_system (Salvo-Zahl)
        return [f"Schaden: +{12 * (lvl - 1)}%",
                f"Projektile/Salve: {min(8, 1 + lvl // 2)}"]
    if key == "schild":
        # PAKET 7C: Schildsystem = Schadensreduktion (Huelle jetzt in "huelle")
        return [f"Schadensreduktion: {3 * (lvl - 1)}%",
                "Schildring im Gefecht sichtbar"]
    if key == "huelle":
        return [f"Max. Hülle: {700 + (lvl - 1) * 100}",
                "Hüllenpanzerung am Schiff sichtbar"]
    if key == "reaktor":
        return [f"Krit-Chance: +{2 * (lvl - 1)}%",
                f"Drohnen-Schaden: +{6 * (lvl - 1)}%"]
    if key == "antrieb":
        return [f"Feuerintervall: x{0.85 ** (lvl - 1):.2f}"]
    if key == "hangar":
        return [f"Drohnen gleichzeitig: {max(0, min(6, lvl - 1))}",
                "Jede Stufe: mehr & schnellere Drohnen"]
    if key == "radar":
        return [f"Credits-Bonus: +{4 * (lvl - 1)}%",
                f"Data-Core-Chance: +{2 * (lvl - 1)}%"]
    if key == "reparatur":
        return [f"Reparatur: {lvl * 2.0:.0f} Hülle/s"]
    return []


def module_next_effect(key):
    """Wirkung der naechsten Stufe (eine Zeile)."""
    if key == "kanonen":
        return "+12% Kanonenschaden"
    if key == "schild":
        return "-3% erlittener Schaden"
    if key == "huelle":
        return "+100 maximale Hülle"
    if key == "reaktor":
        return "+2% Krit-Chance, +6% Drohnen-Schaden"
    if key == "antrieb":
        return "Kürzeres Feuerintervall"
    if key == "hangar":
        return "Mehr / schnellere Drohnen"
    if key == "radar":
        return "+4% Credits, +2% Core-Chance"
    if key == "reparatur":
        return "+2 Hülle/s Reparatur"
    return "-"


# ----------------------------------------------------------------------
# PAKET 7E: ANZEIGE-PROFIL DES SCHIFFSRUMPF-UPGRADES (Werft)
# ----------------------------------------------------------------------
# Muss inhaltlich mit main._sync_modules_to_combat uebereinstimmen:
# +SHIP_HP_PER_LVL Huelle und +SHIP_DMG_PCT_PER_LVL Schaden je Stufe.

def ship_effect_values(level):
    """Aktuelle Werte des Schiffs-Rumpfs (fuer die Werft-Anzeige)."""
    lvl = max(1, int(level))
    return [f"Max. Hülle: +{SHIP_HP_PER_LVL * (lvl - 1)}",
            f"Schaden: +{int(round(SHIP_DMG_PCT_PER_LVL * 100)) * (lvl - 1)}%",
            f"Rumpfklasse: Schiff Stufe {lvl} / {SHIP_MAX_LEVEL}"]


def ship_next_effect():
    """Wirkung der naechsten Schiffs-Stufe (eine Zeile)."""
    return (f"+{SHIP_HP_PER_LVL} maximale Hülle, "
            f"+{int(round(SHIP_DMG_PCT_PER_LVL * 100))}% Schaden, neues Schiffsbild")
