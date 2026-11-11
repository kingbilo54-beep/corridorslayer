"""Persistent module progression and clearly defined stat bonuses for CORRIDOR SLAYER."""
from dataclasses import dataclass, field
from pathlib import Path
import json
import time
import openpyxl

SAVE_PATH = Path(__file__).with_name("corridor_slayer_modules.json")

MODULE_DATA = {}
PLAYER_DATA_MOD = {}
try:
    wb = openpyxl.load_workbook("game_data.xlsx")
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
    def base_cost(self): return int(MODULE_DATA.get(self.key, {}).get("BaseCost", 150))
    @property
    def cost_mult(self): return float(MODULE_DATA.get(self.key, {}).get("CostMult", 1.8))
    @property
    def max_level(self): return int(MODULE_DATA.get(self.key, {}).get("MaxLevel", 15))
    
    @property
    def cost(self):
        return int(self.base_cost * (self.cost_mult ** (self.level - 1)))

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

    def __post_init__(self):
        self.offline_seconds = 0.0
        if not self.modules:
            self.modules = {
                "kanonen": UpgradeModule("kanonen", "Kanonen", "Erhöht den Schaden der Hauptgeschütze", 1),
                "hangar": UpgradeModule("hangar", "Hangar", "Ermöglicht den Start von Jägern", 1),
                "antrieb": UpgradeModule("antrieb", "Antrieb / Reaktor", "Erhöht die Feuerrate", 1),
                "schild": UpgradeModule("schild", "Schutzschild", "Erhöht die maximale Hüllenintegrität", 1),
                "radar": UpgradeModule("radar", "Radar", "Erhöht die Reichweite", 1),
                "reparatur": UpgradeModule("reparatur", "Reparatur-Drohnen", "Heilt die Hülle über Zeit", 1),
            }
        self.load()

    @property
    def ship_level(self):
        total_levels = sum(m.level for m in self.modules.values())
        levels_per_ship = int(PLAYER_DATA_MOD.get("levels_per_ship_level", 5))
        return max(1, (total_levels // levels_per_ship))

    def get(self, key):
        return self.modules[key]

    @property
    def max_allowed_level(self):
        """Hoechstes freigeschaltetes Modul-Level: 3 geschaffte Stufen = +1 Level."""
        return (len(self.completed_stages) // 3) + 1

    def upgrade(self, key):
        module = self.get(key)
        
        if module.level >= self.max_allowed_level:
            needed = module.level * 3
            raise ValueError(f"GESPERRT! Schaffe {needed} Kampagnen-Stufen (aktuell: {len(self.completed_stages)}).")
            
        self.credits = module.upgrade(self.credits)
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
            for key, module in self.modules.items():
                module.level = max(1, min(module.max_level, int(data.get("levels", {}).get(key, 1))))
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
                "saved_at": time.time(),
                "levels": {key: int(module.level) for key, module in self.modules.items()},
            }
            SAVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass
