# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | Skill-Tree: permanente Faehigkeiten, bezahlt mit Data Cores.

PAKET 7B - ERWEITERTER, VERZWEIGTER SKILL-BAUM:
  * 5 Spezialisierungen statt 4 Sparten: OFFENSIV / DEFENSIV / TECHNOLOGIE /
    OEKONOMIE / SPEZIALISIERUNG - jede mit eigener Spielweise.
  * 30 Knoten (vorher 20) mit echten Verzweigungen: Jeder Knoten definiert
    "reqs" = [[node_id, mindest_stufe], ...]. Die alten pauschalen
    Stufen-Schwellen (PREREQ_THRESHOLDS) sind damit entfallen - Voraussetzungen
    sind jetzt konkret und sichtbar.
  * ALTE NODE-IDs BLEIBEN ERHALTEN: corridor_slayer_skills.json von Paket 5/6/7A
    laedt unverändert weiter; neue Knoten starten bei Stufe 0.
  * Neue Effektarten wirken wirklich im Gefecht (pve_system liest sie):
    last_stand, boss_dmg_pct, salvage_flat, proj_speed_mult, drone_rate_mult,
    hp_flat, gear_amp (Modul-Bonus), cost_discount (Werft-Preise).
  * Gespeichert wird wie bisher in corridor_slayer_skills.json ("levels").
"""
import json
from pathlib import Path
# SCHRITT 3: Globale Skill-Kostenbremse liegt zentral im BALANCE-Block
# von rpg_config.py und wird nur noch importiert (Wert identisch).
from rpg_config import SKILL_COST_MULT

SAVE_PATH = Path(__file__).with_name("corridor_slayer_skills.json")

# Sparten-Farben (skill_nexus + main.py nutzen dieselben Werte)
COLOR_OFF = (255, 62, 177)     # Magenta  - Offensive
COLOR_DEF = (0, 255, 255)      # Cyan     - Defensive
COLOR_TEC = (153, 94, 255)     # Violett  - Technologie
COLOR_EKO = (255, 190, 76)     # Amber    - Oekonomie
COLOR_SPEZ = (77, 255, 181)    # Gruen    - Spezialisierung


def _node(node_id, name, desc, max_lvl, costs, reqs=None):
    return {"id": node_id, "name": name, "desc": desc, "max": max_lvl,
            "costs": costs, "reqs": reqs or []}


SKILL_TREE = [
    {"id": "offensiv", "name": "OFFENSIV", "color": COLOR_OFF, "nodes": [
        _node("waffen_dmg", "GEWEHRVERSTÄRKER", "Erhoeht den Schaden aller Kanonen dauerhaft.", 5, [8, 16, 24, 32, 40]),
        _node("waffen_rate", "SCHNELLFEUER", "Verkuerzt das Feuerintervall der Kanonen.", 5, [8, 16, 24, 32, 40]),
        _node("waffen_krit", "ZIELRECHNER", "Chance auf kritische Treffer (Doppelschaden).", 5, [8, 16, 24, 32, 40],
              reqs=[["waffen_dmg", 1]]),
        _node("waffen_salve", "MEHRFACHLAUF", "Zusaetzlicher Projektilabwurf pro Salve.", 2, [25, 50],
              reqs=[["waffen_dmg", 2]]),
        _node("waffen_kritschaden", "PANZERBRECHER", "Verstaerkt kritischen Schaden ueber 2.0x hinaus.", 4, [10, 20, 30, 40],
              reqs=[["waffen_krit", 2]]),
        _node("off_durchschlag", "DURCHSCHLAG", "Munition durchdringt Panzer: zusaetzlicher Grundschaden.", 3, [18, 30, 45],
              reqs=[["waffen_kritschaden", 1], ["waffen_rate", 2]]),
    ]},
    {"id": "defensiv", "name": "DEFENSIV", "color": COLOR_DEF, "nodes": [
        _node("vert_panzerung", "VERSTÄRKTE HÜLLE", "Erhoeht die maximale Huellenintegritaet.", 5, [8, 16, 24, 32, 40]),
        _node("vert_nano", "NANO-REPARATUR", "Kontinuierliche Hullen-Reparatur pro Sekunde.", 5, [8, 16, 24, 32, 40]),
        _node("vert_kondensator", "SCHILDKONDENSATOR", "Zusaetzliche Hullenpunkte (flach, unabhaengig von %),", 4, [12, 22, 34, 48],
              reqs=[["vert_panzerung", 1]]),
        _node("vert_schild", "ABFANG-FELD", "Reduziert allen erlittenen Schaden.", 2, [25, 50],
              reqs=[["vert_panzerung", 2]]),
        _node("vert_kuehlung", "NOTKÜHLUNG", "Feuerrate +25% solange Huelle unter 30%.", 1, [40],
              reqs=[["vert_nano", 2]]),
        _node("vert_puls", "PULSGENERATOR", "Nach einem Treffer: 2 Gegen-Pulse auf naechste Gegner.", 4, [10, 20, 30, 40],
              reqs=[["vert_schild", 1]]),
        _node("vert_wille", "LETZER WILLE", "1x pro Gefecht: 30% Huelle statt Zerstoerung.", 1, [60],
              reqs=[["vert_puls", 2]]),
    ]},
    {"id": "technologie", "name": "TECHNOLOGIE", "color": COLOR_TEC, "nodes": [
        _node("ener_leitung", "ENERGIELEITUNG", "Erhoeht den Schaden der Hangar-Drohnen.", 5, [8, 16, 24, 32, 40]),
        _node("ener_taktik", "HANGAR-TAKTIK", "Startet zusaetzliche Drohnen.", 2, [25, 50],
              reqs=[["ener_leitung", 2]]),
        _node("tec_kuehlung", "KÜHLSYSTEM", "Drohnen-Nachschub kommt haeufiger.", 3, [15, 25, 40],
              reqs=[["ener_leitung", 1]]),
        _node("tec_tempfeld", "TEMPFELD", "Projektile fliegen schneller (weniger Fehlschuesse).", 3, [15, 25, 40],
              reqs=[["tec_kuehlung", 1]]),
        _node("tec_notstrom", "NOTSTROMZELLEN", "Zusaetzliche Grund-Reparatur pro Sekunde.", 3, [12, 20, 30],
              reqs=[["tec_tempfeld", 1]]),
        _node("tec_synergie", "SYSTEM-SYNERGIE", "Alle Werft-Modul-Boni werden um 5% je Stufe verstaerkt.", 4, [20, 35, 50, 70],
              reqs=[["ener_taktik", 1]]),
    ]},
    {"id": "oekonomie", "name": "ÖKONOMIE", "color": COLOR_EKO, "nodes": [
        _node("ener_idle", "IDLE-PROTOKOLL", "Erhoeht das Einkommen im Idle-Modus.", 5, [8, 16, 24, 32, 40]),
        _node("ener_bonus", "KRIEGSKASSE", "Erhoeht Credits aus Kampagnen-Kills.", 5, [8, 16, 24, 32, 40]),
        _node("ener_sep", "KERN-SEPARATOR", "Chance auf einen zusaetzlichen Data Core pro Kill.", 4, [10, 20, 30, 40],
              reqs=[["ener_idle", 2]]),
        _node("eko_bergung", "SCHROTTBERGUNG", "Zusaetzliche Credits pro Abschuss im Gefecht.", 4, [12, 20, 30, 45],
              reqs=[["ener_bonus", 1]]),
        _node("eko_kontrakte", "KONTRAKTE", "Rabatt auf alle Werft-Upgrade-Preise.", 5, [10, 18, 28, 40, 55],
              reqs=[["eko_bergung", 1]]),
    ]},
    {"id": "spezialisierung", "name": "SPEZIALISIERUNG", "color": COLOR_SPEZ, "nodes": [
        _node("spez_bully", "BULLY", "+Schaden gegen angeschlagene Ziele (unter 50% HP).", 4, [10, 20, 30, 40]),
        _node("spez_adrenalin", "ADRENALIN-KERN", "Mehr Schaden, je niedriger die eigene Huelle.", 3, [15, 30, 45]),
        _node("spez_exekutor", "EXEKUTOR", "Chance, Gegner unter 20% HP sofort zu eliminieren.", 2, [25, 50],
              reqs=[["spez_bully", 1]]),
        _node("spez_spreng", "SPRENGSPITZE", "Getoetete Gegner explodieren und verletzten Nachbarn.", 1, [45],
              reqs=[["spez_exekutor", 1]]),
        _node("spez_overdrive", "ÜBERTAKTUNG", "AKTIV (Taste Q im Gefecht): 8s doppelte Feuerrate, 45s Abklingzeit.", 1, [60],
              reqs=[["spez_adrenalin", 1]]),
        _node("spez_boss", "BOSS-JÄGER", "Zusaetzlicher Schaden gegen Bosse (Stufe 15).", 3, [20, 35, 50],
              reqs=[["spez_overdrive", 1]]),
    ]},
]

# ---------------- Anzeige-Effekte ----------------

def effect_text(node_id, lvl):
    """Kurztext des aktuellen Effekts fuer eine gegebene Stufe (0 = noch nicht trainiert)."""
    if node_id == "waffen_dmg": return f"+{10 * lvl}% Kanonenschaden"
    if node_id == "waffen_rate": return f"-{6 * lvl}% Feuerintervall"
    if node_id == "waffen_salve": return f"+{lvl} Projektil/Salve"
    if node_id == "waffen_krit": return f"{5 * lvl}% Krit-Chance (2.0x Schaden)"
    if node_id == "waffen_kritschaden": return f"Krit-Schaden x{2.0 + 0.25 * lvl:.2f}"
    if node_id == "off_durchschlag": return f"+{8 * lvl}% Grundschaden (Durchschlag)"
    if node_id == "vert_panzerung": return f"+{12 * lvl}% max. Huelle"
    if node_id == "vert_kondensator": return f"+{150 * lvl} max. Huelle (flach)"
    if node_id == "vert_nano": return f"+{lvl} HP/s Reparatur"
    if node_id == "vert_schild": return f"-{10 * lvl}% erlittener Schaden"
    if node_id == "vert_kuehlung": return "Feuerrate +25% unter 30% HP" if lvl else "-"
    if node_id == "vert_puls": return f"Gegen-Pulse fuer {2.0 + 0.5 * lvl:.1f}s nach Treffer"
    if node_id == "vert_wille": return "1x pro Gefecht: 30% Huelle statt Untergang" if lvl else "-"
    if node_id == "ener_leitung": return f"+{8 * lvl}% Drohnen-Schaden"
    if node_id == "ener_taktik": return f"+{lvl} zusaetzliche Drohne(n)"
    if node_id == "tec_kuehlung": return f"Drohnen-Nachschub x{0.92 ** lvl:.2f}"
    if node_id == "tec_tempfeld": return f"Projektiltempo +{8 * lvl}%"
    if node_id == "tec_notstrom": return f"+{0.5 * lvl:.1f} Huelle/s Grundreparatur"
    if node_id == "tec_synergie": return f"Werft-Modul-Boni +{5 * lvl}%"
    if node_id == "ener_idle": return f"+{15 * lvl}% Idle-Einkommen"
    if node_id == "ener_bonus": return f"+{10 * lvl}% Credits (Kampagne)"
    if node_id == "ener_sep": return f"{10 * lvl}% Chance auf doppelten Core"
    if node_id == "eko_bergung": return f"+{2 * lvl} Credits pro Abschuss (Gefecht)"
    if node_id == "eko_kontrakte": return f"-{4 * lvl}% Werft-Upgrade-Kosten"
    if node_id == "spez_bully": return f"+{12 * lvl}% Schaden bei Ziel < 50% HP"
    if node_id == "spez_exekutor": return f"{10 * lvl}% Exekution bei Ziel < 20% HP"
    if node_id == "spez_spreng": return "Kills explodieren (30% AoE-Schaden)" if lvl else "-"
    if node_id == "spez_adrenalin": return f"+{2 * lvl}% Schaden pro 10% fehlender HP"
    if node_id == "spez_overdrive": return "Taste Q: 8s x2 Feuerrate (45s CD)" if lvl else "-"
    if node_id == "spez_boss": return f"+{8 * lvl}% Schaden gegen Bosse"
    return "-"


def find_node(node_id):
    for branch in SKILL_TREE:
        for i, node in enumerate(branch["nodes"]):
            if node["id"] == node_id:
                return branch, i, node
    return None, -1, None


NODE_BY_ID = {n["id"]: (b, n) for b in SKILL_TREE for n in b["nodes"]}

# ----------------------------------------------------------------------
# PAKET 7C: KOSTEN-SKALIERUNG
# Regel: Die ersten 3 Stufen eines Knotens behalten ihren Basispreis,
# jede weitere Stufe (Index >= 3 im Kosten-Array) kostet x1.5 (kaufm.
# gerundet). Tiefe Investitionen in EINEN Knoten werden damit zur bewussten
# Entscheidung, fruehe Skills bleiben guenstig erreichbar.
# (Nur Preise - gespeicherte Level in corridor_slayer_skills.json bleiben
#  unberuehrt und voll kompatibel.)
#
# PAKET 8.4: GLOBALE SKILL-KOSTENBREMSE (SKILL_COST_MULT).
# SCHRITT 3: Die Konstante steht jetzt im BALANCE-Block von rpg_config.py
# (mit Begruendung) und wird oben importiert - Wert und Wirkung identisch.

for _b in SKILL_TREE:
    for _n in _b["nodes"]:
        _n["costs"] = [int(round(int(c) * SKILL_COST_MULT)) if _i < 3
                       else int(round(int(c) * 1.5 * SKILL_COST_MULT))
                       for _i, c in enumerate(_n["costs"])]


class SkillTree:
    """Persistenter Zustand aller Skill-Stufen + Uebersetzung in Combat-Mods."""

    def __init__(self):
        self.levels = {}
        self.load()

    # ---------- Abfragen ----------
    def level_of(self, node_id):
        return int(self.levels.get(node_id, 0))

    def prereq_ok(self, node):
        """PAKET 7B: konkrete Voraussetzungen [[node_id, min_level], ...]."""
        for req_id, req_lvl in node.get("reqs", []):
            if self.level_of(req_id) < int(req_lvl):
                return False
        return True

    def missing_req(self, node):
        """Erste nicht erfuellte Voraussetzung (fuer Anzeige) oder None."""
        for req_id, req_lvl in node.get("reqs", []):
            if self.level_of(req_id) < int(req_lvl):
                return (req_id, int(req_lvl))
        return None

    def unlock_info(self, node_id):
        """(darf_trainiert_werden, Grund-wenn-nicht)."""
        _b, _i, node = find_node(node_id)
        if node is None:
            return False, "Unbekannter Skill"
        lvl = self.level_of(node_id)
        if lvl >= node["max"]:
            return False, "MAX"
        miss = self.missing_req(node)
        if miss:
            req_b, _req_n = NODE_BY_ID.get(miss[0], (None, None))
            req_name = _req_n["name"] if _req_n else miss[0]
            return False, f"Benötigt: {req_name} Stufe {miss[1]}"
        return True, ""

    def cost_of(self, node_id):
        _b, _i, node = find_node(node_id)
        if node is None:
            return 0
        lvl = self.level_of(node_id)
        if lvl >= node["max"]:
            return 0
        return int(node["costs"][lvl])

    def total_spent(self):
        spent = 0
        for branch in SKILL_TREE:
            for node in branch["nodes"]:
                lvl = self.level_of(node["id"])
                spent += sum(node["costs"][:lvl])
        return spent

    def unlock(self, node_id):
        ok, reason = self.unlock_info(node_id)
        if not ok:
            raise ValueError(reason)
        self.levels[node_id] = self.level_of(node_id) + 1
        self.save()
        return self.level_of(node_id)

    def save(self):
        try:
            payload = {"levels": dict(self.levels)}
            SAVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass

    def load(self):
        try:
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            raw = data.get("levels", {})
            # Nur bekannte Knoten uebernehmen (Fremd-/Alt-Keys ignorieren,
            # dadurch bleiben auch zukuenftige Felder gefahrlos).
            known = set(NODE_BY_ID.keys())
            self.levels = {str(k): max(0, int(v)) for k, v in raw.items()
                           if str(k) in known}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.levels = {}

    # ---------- Bruecke zu pve_system ----------
    def modifiers(self):
        L = self.level_of
        return {
            # --- OFFENSIV ---
            "dmg_pct": 0.10 * L("waffen_dmg") + 0.08 * L("off_durchschlag"),
            "rate_mult": 0.94 ** L("waffen_rate"),
            "extra_cannons": L("waffen_salve"),
            "crit_chance": 0.05 * L("waffen_krit"),
            "crit_mult": 2.0 + 0.25 * L("waffen_kritschaden"),
            # --- DEFENSIV ---
            "hp_pct": 0.12 * L("vert_panzerung"),
            "hp_flat": 150.0 * L("vert_kondensator"),
            "regen": 1.0 * L("vert_nano") + 0.5 * L("tec_notstrom"),
            "dr_pct": 0.10 * L("vert_schild"),
            "adrenaline_cool": L("vert_kuehlung"),   # AUFTRAG 4: war "adrenaline"
            "retaliate": L("vert_puls"),
            "last_stand": L("vert_wille"),
            # --- TECHNOLOGIE ---
            "drone_dmg_pct": 0.08 * L("ener_leitung"),
            "extra_drones": L("ener_taktik"),
            "drone_rate_mult": 0.92 ** L("tec_kuehlung"),
            "proj_speed_mult": 1.0 + 0.08 * L("tec_tempfeld"),
            "gear_amp": 0.05 * L("tec_synergie"),
            # --- OEKONOMIE ---
            "idle_pct": 0.15 * L("ener_idle"),
            "credit_pct": 0.10 * L("ener_bonus"),
            "core_chance": 0.10 * L("ener_sep"),
            "salvage_flat": 2 * L("eko_bergung"),
            "cost_discount": 0.04 * L("eko_kontrakte"),
            # --- SPEZIALISIERUNG ---
            "bully": 0.12 * L("spez_bully"),
            "execute_chance": 0.10 * L("spez_exekutor"),
            "explosive": L("spez_spreng"),
            "adrenaline_dmg": 0.02 * L("spez_adrenalin"),  # AUFTRAG 4: war "adrenalin_dmg"
            "overdrive": L("spez_overdrive"),
            "boss_dmg_pct": 0.08 * L("spez_boss"),
        }

    def apply_to_combat(self, combat):
        combat.skill_mods = self.modifiers()
        return combat.skill_mods
