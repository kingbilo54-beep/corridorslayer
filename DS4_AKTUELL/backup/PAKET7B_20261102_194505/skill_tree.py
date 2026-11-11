"""CORRIDOR SLAYER | Skill-Tree: permanente Faehigkeiten, bezahlt mit Data Cores.

Sparten: WAFFENSYSTEME / VERTEIDIGUNG / ENERGIE & OEKONOMIE / SPEZIALSYSTEME
Die Effekte landen als "skill_mods"-Dictionary in PvECombat (apply_to_combat)
und werden dort von den Schadens-/Feuerraten-Formeln gelesen.
Gespeichert wird in corridor_slayer_skills.json (neben dieser Datei).
"""
import json
from pathlib import Path

SAVE_PATH = Path(__file__).with_name("corridor_slayer_skills.json")

# Voraussetzung pro Node-Position: Summe der Stufen ALLER Vorgaenger in der Sparte
PREREQ_THRESHOLDS = [0, 1, 2, 4, 6]

# Sparten-Farben (main.py nutzt dieselben Werte fuer die UI)
COLOR_WAFFEN = (255, 62, 177)
COLOR_VERT = (0, 255, 255)
COLOR_ENER = (255, 190, 76)
COLOR_SPEZ = (153, 94, 255)


def _node(node_id, name, desc, max_lvl, costs):
    return {"id": node_id, "name": name, "desc": desc, "max": max_lvl, "costs": costs}


SKILL_TREE = [
    {"id": "waffen", "name": "WAFFENSYSTEME", "color": COLOR_WAFFEN, "nodes": [
        _node("waffen_dmg", "GEWEHRVERSTÄRKER", "Erhoeht den Schaden aller Kanonen dauerhaft.", 5, [8, 16, 24, 32, 40]),
        _node("waffen_rate", "SCHNELLFEUER", "Verkuerzt das Feuerintervall der Kanonen.", 5, [8, 16, 24, 32, 40]),
        _node("waffen_salve", "MEHRFACHLAUF", "Zusaetzlicher Projektilabwurf pro Salve.", 2, [25, 50]),
        _node("waffen_krit", "ZIELRECHNER", "Chance auf kritische Treffer (Doppelschaden).", 5, [8, 16, 24, 32, 40]),
        _node("waffen_kritschaden", "PANZERBRECHER", "Verstaerkt kritischen Schaden ueber 2.0x hinaus.", 4, [10, 20, 30, 40]),
    ]},
    {"id": "verteidigung", "name": "VERTEIDIGUNG", "color": COLOR_VERT, "nodes": [
        _node("vert_panzerung", "VERSTÄRKTE HÜLLE", "Erhoeht die maximale Huellenintegritaet.", 5, [8, 16, 24, 32, 40]),
        _node("vert_nano", "NANO-REPARATUR", "Kontinuierliche Hullen-Reparatur pro Sekunde.", 5, [8, 16, 24, 32, 40]),
        _node("vert_schild", "ABFANG-FELD", "Reduziert allen erlittenen Schaden.", 2, [25, 50]),
        _node("vert_kuehlung", "NOTKÜHLUNG", "Feuerrate +25% solange Huelle unter 30%.", 1, [40]),
        _node("vert_puls", "PULSGENERATOR", "Nach einem Treffer: 2 Gegen-Pulse auf naechste Gegner.", 4, [10, 20, 30, 40]),
    ]},
    {"id": "energie", "name": "ENERGIE & ÖKONOMIE", "color": COLOR_ENER, "nodes": [
        _node("ener_leitung", "ENERGIELEITUNG", "Erhoeht den Schaden der Hangar-Drohnen.", 5, [8, 16, 24, 32, 40]),
        _node("ener_taktik", "HANGAR-TAKTIK", "Startet zusaetzliche Drohnen.", 2, [25, 50]),
        _node("ener_idle", "IDLE-PROTOKOLL", "Erhoeht das Einkommen im Idle-Modus.", 5, [8, 16, 24, 32, 40]),
        _node("ener_bonus", "KRIEGSKASSE", "Erhoeht Credits aus Kampagnen-Kills.", 5, [8, 16, 24, 32, 40]),
        _node("ener_sep", "KERN-SEPARATOR", "Chance auf einen zusaetzlichen Data Core pro Kill.", 4, [10, 20, 30, 40]),
    ]},
    {"id": "spezial", "name": "SPEZIALSYSTEME", "color": COLOR_SPEZ, "nodes": [
        _node("spez_bully", "BULLY", "+Schaden gegen angeschlagene Ziele (unter 50% HP).", 4, [10, 20, 30, 40]),
        _node("spez_exekutor", "EXEKUTOR", "Chance, Gegner unter 20% HP sofort zu eliminieren.", 2, [25, 50]),
        _node("spez_spreng", "SPRENGSPITZE", "Getoetete Gegner explodieren und verletzten Nachbarn.", 1, [45]),
        _node("spez_adrenalin", "ADRENALIN-KERN", "Mehr Schaden, je niedriger die eigene Huelle.", 3, [15, 30, 45]),
        _node("spez_overdrive", "ÜBERTAKTUNG", "AKTIV (Taste Q im Gefecht): 8s doppelte Feuerrate, 45s Abklingzeit.", 1, [60]),
    ]},
]


def effect_text(node_id, lvl):
    """Kurztext des aktuellen Effekts fuer eine gegebene Stufe (0 = noch nicht trainiert)."""
    if node_id == "waffen_dmg": return f"+{10 * lvl}% Kanonenschaden"
    if node_id == "waffen_rate": return f"-{6 * lvl}% Feuerintervall"
    if node_id == "waffen_salve": return f"+{lvl} Projektil/Salve"
    if node_id == "waffen_krit": return f"{5 * lvl}% Krit-Chance (2.0x Schaden)"
    if node_id == "waffen_kritschaden": return f"Krit-Schaden x{2.0 + 0.25 * lvl:.2f}"
    if node_id == "vert_panzerung": return f"+{12 * lvl}% max. Huelle"
    if node_id == "vert_nano": return f"+{lvl} HP/s Reparatur"
    if node_id == "vert_schild": return f"-{10 * lvl}% erlittener Schaden"
    if node_id == "vert_kuehlung": return "Feuerrate +25% unter 30% HP" if lvl else "-"
    if node_id == "vert_puls": return f"Gegen-Pulse fuer {2.0 + 0.5 * lvl:.1f}s nach Treffer"
    if node_id == "ener_leitung": return f"+{8 * lvl}% Drohnen-Schaden"
    if node_id == "ener_taktik": return f"+{lvl} zusaetzliche Drohne(n)"
    if node_id == "ener_idle": return f"+{15 * lvl}% Idle-Einkommen"
    if node_id == "ener_bonus": return f"+{10 * lvl}% Credits (Kampagne)"
    if node_id == "ener_sep": return f"{10 * lvl}% Chance auf doppelten Core"
    if node_id == "spez_bully": return f"+{12 * lvl}% Schaden bei Ziel < 50% HP"
    if node_id == "spez_exekutor": return f"{10 * lvl}% Exekution bei Ziel < 20% HP"
    if node_id == "spez_spreng": return "Kills explodieren (30% AoE-Schaden)" if lvl else "-"
    if node_id == "spez_adrenalin": return f"+{2 * lvl}% Schaden pro 10% fehlender HP"
    if node_id == "spez_overdrive": return "Taste Q: 8s x2 Feuerrate (45s CD)" if lvl else "-"
    return "-"


def find_node(node_id):
    for branch in SKILL_TREE:
        for i, node in enumerate(branch["nodes"]):
            if node["id"] == node_id:
                return branch, i, node
    return None, -1, None


class SkillTree:
    """Persistenter Zustand aller Skill-Stufen + Uebersetzung in Combat-Mods."""

    def __init__(self):
        self.levels = {}
        self.load()

    # ---------- Abfragen ----------
    def level_of(self, node_id):
        return int(self.levels.get(node_id, 0))

    def prereq_ok(self, branch, index):
        need = PREREQ_THRESHOLDS[index]
        if need == 0:
            return True
        have = sum(self.level_of(n["id"]) for n in branch["nodes"][:index])
        return have >= need

    def unlock_info(self, node_id):
        """(darf_trainiert_werden, Grund-wenn-nicht)."""
        branch, idx, node = find_node(node_id)
        if node is None:
            return False, "Unbekannter Skill"
        lvl = self.level_of(node_id)
        if lvl >= node["max"]:
            return False, "MAX"
        if not self.prereq_ok(branch, idx):
            need = PREREQ_THRESHOLDS[idx]
            return False, f"Benötigt {need} Stufen in {branch['name']}"
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

    # ---------- Bruecke zu pve_system ----------
    def modifiers(self):
        L = self.level_of
        return {
            "dmg_pct": 0.10 * L("waffen_dmg"),
            "rate_mult": 0.94 ** L("waffen_rate"),
            "extra_cannons": L("waffen_salve"),
            "crit_chance": 0.05 * L("waffen_krit"),
            "crit_mult": 2.0 + 0.25 * L("waffen_kritschaden"),
            "hp_pct": 0.12 * L("vert_panzerung"),
            "regen": 1.0 * L("vert_nano"),
            "dr_pct": 0.10 * L("vert_schild"),
            "adrenaline": L("vert_kuehlung"),
            "retaliate": L("vert_puls"),
            "drone_dmg_pct": 0.08 * L("ener_leitung"),
            "extra_drones": L("ener_taktik"),
            "idle_pct": 0.15 * L("ener_idle"),
            "credit_pct": 0.10 * L("ener_bonus"),
            "core_chance": 0.10 * L("ener_sep"),
            "bully": 0.12 * L("spez_bully"),
            "execute_chance": 0.10 * L("spez_exekutor"),
            "explosive": L("spez_spreng"),
            "adrenalin_dmg": 0.02 * L("spez_adrenalin"),
            "overdrive": L("spez_overdrive"),
        }

    def apply_to_combat(self, combat):
        combat.skill_mods = self.modifiers()
        return combat.skill_mods

    # ---------- Persistenz ----------
    def load(self):
        try:
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            raw = data.get("levels", {})
            self.levels = {str(k): max(0, int(v)) for k, v in raw.items()}
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.levels = {}

    def save(self):
        try:
            payload = {"levels": dict(self.levels)}
            SAVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass
