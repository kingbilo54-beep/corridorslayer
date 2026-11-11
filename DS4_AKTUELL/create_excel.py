import os

# ==========================================
# 1. MODULE_SYSTEM.PY (Fügt Ship-Level hinzu)
# ==========================================
module_code = '''"""Persistent module progression and clearly defined stat bonuses for CORRIDOR SLAYER."""
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
    def cost_mult(self): return float(MODULE_DATA.get(self.key, {}).get("CostMult", 1.6))
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
    credits: int = 50000 
    data_cores: int = 0

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
        """Berechnet das Schiff-Level basierend auf der Summe aller Modul-Level."""
        total_levels = sum(m.level for m in self.modules.values())
        levels_per_ship = int(PLAYER_DATA_MOD.get("levels_per_ship_level", 5))
        # Startet bei 1. (Total 6 = Level 1. Total 11 = Level 2, etc.)
        return max(1, (total_levels // levels_per_ship))

    def get(self, key):
        return self.modules[key]

    def upgrade(self, key):
        module = self.get(key)
        self.credits = module.upgrade(self.credits)
        self.save()
        return module

    def load(self):
        try:
            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
            last_saved = float(data.get("saved_at", time.time()))
            self.offline_seconds = max(0.0, min(8*3600.0, time.time() - last_saved))
            self.credits = max(0, int(data.get("credits", self.credits)))
            self.data_cores = max(0, int(data.get("data_cores", 0)))
            for key, module in self.modules.items():
                module.level = max(1, min(module.max_level, int(data.get("levels", {}).get(key, 1))))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

    def save(self):
        try:
            payload = {
                "credits": int(self.credits),
                "data_cores": int(self.data_cores),
                "saved_at": time.time(),
                "levels": {key: int(module.level) for key, module in self.modules.items()},
            }
            SAVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass
'''

# ==========================================
# 2. PVE_SYSTEM.PY (Gegner-Filter nach Schiff-Level)
# ==========================================
pve_code = '''"""CORRIDOR SLAYER | PvE Combat & Dynamic Upgrade Engine."""
import math
import random
import openpyxl
from dataclasses import dataclass

ENEMY_DATA = {}
PLAYER_DATA = {}
try:
    wb = openpyxl.load_workbook("game_data.xlsx")
    ws_e = wb["Enemies"]
    headers_e = [cell.value for cell in ws_e[1]]
    for row in ws_e.iter_rows(min_row=2, values_only=True):
        if row[0]:
            ENEMY_DATA[row[0].lower()] = dict(zip(headers_e, row))
            
    ws_p = wb["Player"]
    for row in ws_p.iter_rows(min_row=2, values_only=True):
        if row[0]: PLAYER_DATA[row[0]] = row[1]
except Exception as e:
    print(f"⚠️ Fehler beim Laden der Excel-Datei: {e}")

@dataclass
class Enemy:
    name: str
    hp: float
    max_hp: float
    damage: int
    speed: float
    reward: int
    x: float = 0.0
    y: float = 0.0
    attack_cooldown: float = 2.0
    hit_flash: float = 0.0
    enemy_type: str = "skitter"

@dataclass
class Projectile:
    x: float
    y: float
    vx: float
    vy: float
    damage: float
    speed: float = 550.0
    kind: str = "player"
    is_drone: bool = False

class PvECombat:
    def __init__(self, is_idle=True, campaign_stage=1, ship_level=1):
        self.is_idle = is_idle
        self.stage = campaign_stage
        self.ship_level = ship_level # NEU: Schiff-Level für Gating
        
        self.credits = 0
        self.idle_loot_earned = 0 
        
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        
        self.max_player_hp = float(PLAYER_DATA.get("base_max_hp", 500.0))
        self.player_hp = self.max_player_hp
        
        self.dmg_level = 1
        self.speed_level = 1
        self.cannon_count_level = 1
        self.hangar_level = 1
        self.repair_level = 1
        
        self.auto_fire_timer = 0.0
        self.drone_timer = 0.0
        
        self.spawn_queue = 0
        self.spawn_timer = 0.0
        self.data_cores_earned = 0
        self.spawn_stage()

    @property
    def cannon_damage(self): 
        base = float(PLAYER_DATA.get("base_cannon_damage", 12.0))
        mult = float(PLAYER_DATA.get("cannon_dmg_mult", 1.2))
        return base * (mult ** (self.dmg_level - 1))
    
    @property
    def attack_rate(self): 
        base = float(PLAYER_DATA.get("base_fire_rate", 0.8))
        mult = float(PLAYER_DATA.get("fire_rate_mult", 0.85))
        return base * (mult ** (self.speed_level - 1))
    
    @property
    def cannon_count(self): return min(8, self.cannon_count_level)

    def spawn_stage(self):
        self.enemies.clear()
        self.projectiles.clear()
        self.spawn_queue = 999 if self.is_idle else (3 + self.stage)
        self.spawn_timer = 2.0

    def _spawn_single_enemy(self):
        available_enemies = []
        weights = []
        
        # Filtere Gegner nach Schiff-Level
        for k, data in ENEMY_DATA.items():
            min_lvl = int(data.get("Min_Ship_Level", 1))
            if self.ship_level >= min_lvl:
                available_enemies.append(k)
                weights.append(data.get("Spawn_Weight", 10))
                
        # Falls das Schiff zu schwach ist (oder Daten fehlen), nimm den Skitter als Fallback
        if not available_enemies:
            available_enemies = ["skitter"]
            weights = [100]
            
        e_type = random.choices(available_enemies, weights=weights, k=1)[0]
        data = ENEMY_DATA.get(e_type, {"Base_HP": 20, "Base_Speed": 50, "Base_Damage": 5, "Base_Reward": 10})
        
        lane_y = random.choice([200, 270, 340]) + random.uniform(-30, 30)
        stage = self.stage
        
        base_hp = float(data.get("Base_HP", 20))
        add_hp = float(data.get("HP_Add_Per_Stage", 10))
        mult_hp = float(data.get("HP_Mult_Per_Stage", 1.05))
        hp = (base_hp + (stage * add_hp)) * (mult_hp ** stage)
        
        speed = float(data.get("Base_Speed", 50)) + (stage * float(data.get("Speed_Add_Per_Stage", 0)))
        damage = float(data.get("Base_Damage", 5)) + (stage * float(data.get("Damage_Add_Per_Stage", 2)))
        reward = int((float(data.get("Base_Reward", 10)) + (stage * 2)) * float(data.get("Idle_Reward_Mult", 1.0)))
        
        if self.is_idle:
            hp *= float(data.get("Idle_HP_Mult", 0.3))
            speed *= float(data.get("Idle_Speed_Mult", 0.5))
            speed *= 0.5 
            
        self.enemies.append(Enemy(
            name=e_type.upper(), hp=hp, max_hp=hp,
            damage=int(damage), speed=speed, reward=reward,
            x=1000.0, y=lane_y,
            attack_cooldown=random.uniform(1.0, 3.0),
            enemy_type=e_type
        ))

    def update(self, dt: float, center=(100, 270), cannon_positions=None):
        cx, cy = center
        
        rep_val = float(PLAYER_DATA.get("repair_per_level", 2.0))
        if self.repair_level > 1 and self.player_hp < self.max_player_hp:
            self.player_hp += (self.repair_level * rep_val) * dt 
        if self.is_idle and self.player_hp < self.max_player_hp:
            self.player_hp += 20 * dt 
            
        if self.spawn_queue > 0:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                self._spawn_single_enemy()
                self.spawn_queue -= 1
                self.spawn_timer = random.uniform(2.5, 5.0) if self.is_idle else random.uniform(1.0, 2.5)

        for e in list(self.enemies):
            e.hit_flash = max(0.0, e.hit_flash - dt)
            
            if e.x > 400:
                e.x -= e.speed * dt
            else:
                e.x = 400 
            
            dist_to_ship = math.hypot(cx - e.x, cy - e.y)
            if dist_to_ship < 550: 
                e.attack_cooldown -= dt
                if e.attack_cooldown <= 0:
                    e.attack_cooldown = random.uniform(1.5, 3.0)
                    dx, dy = cx - e.x, cy - e.y
                    dist = math.hypot(dx, dy) or 1
                    self.projectiles.append(
                        Projectile(x=e.x, y=e.y, vx=dx/dist, vy=dy/dist, damage=e.damage, speed=250.0, kind="enemy")
                    )

        visible_enemies = [e for e in self.enemies if e.x < 450]
        if visible_enemies and cannon_positions:
            target = min(visible_enemies, key=lambda e: e.x)
            self.auto_fire_timer -= dt
            if self.auto_fire_timer <= 0:
                self.auto_fire_timer = self.attack_rate
                for pos in cannon_positions[:self.cannon_count]:
                    kx, ky = pos[0], pos[1]
                    dx, dy = target.x - kx, target.y - ky
                    dist = math.hypot(dx, dy) or 1
                    self.projectiles.append(
                        Projectile(x=kx, y=ky, vx=dx/dist, vy=dy/dist, damage=self.cannon_damage, speed=600.0, kind="player", is_drone=False)
                    )

        if visible_enemies and self.hangar_level > 1:
            target = min(visible_enemies, key=lambda e: e.x)
            self.drone_timer -= dt
            if self.drone_timer <= 0:
                self.drone_timer = 1.5 - (self.hangar_level * 0.05)
                drone_dmg = self.cannon_damage * float(PLAYER_DATA.get("drone_damage_mult", 0.5))
                for i in range(min(4, self.hangar_level - 1)):
                    drone_x = cx + 20 + random.uniform(-10, 10)
                    drone_y = cy - 60 + (i * 30)
                    dx, dy = target.x - drone_x, target.y - drone_y
                    dist = math.hypot(dx, dy) or 1
                    self.projectiles.append(
                        Projectile(x=drone_x, y=drone_y, vx=dx/dist, vy=dy/dist, damage=drone_dmg, speed=700.0, kind="player", is_drone=True)
                    )

        for p in list(self.projectiles):
            p.x += p.vx * p.speed * dt
            p.y += p.vy * p.speed * dt
            
            if p.kind == "player":
                for e in list(self.enemies):
                    if math.hypot(e.x - p.x, e.y - p.y) < 30:
                        e.hp -= p.damage
                        e.hit_flash = 0.15
                        if p in self.projectiles: self.projectiles.remove(p)
                        if e.hp <= 0 and e in self.enemies:
                            self.credits += e.reward
                            if self.is_idle: self.idle_loot_earned += e.reward 
                            else: self.data_cores_earned += 1 
                            self.enemies.remove(e)
                        break
            
            elif p.kind == "enemy":
                if math.hypot(cx - p.x, cy - p.y) < 80:
                    if self.is_idle:
                        self.player_hp = max(1.0, self.player_hp - p.damage)
                    else:
                        self.player_hp = max(0.0, self.player_hp - p.damage)
                    if p in self.projectiles: self.projectiles.remove(p)

            if p.x > 650 or p.x < -100 or p.y < 0 or p.y > 600:
                if p in self.projectiles: self.projectiles.remove(p)

        if not self.is_idle and not self.enemies and self.spawn_queue == 0:
            self.stage += 1
            self.spawn_stage()
            
    @property
    def is_defeated(self):
        return self.player_hp <= 0 and not self.is_idle
'''

# ==========================================
# 3. MAIN.PY (Übergibt das Schiff-Level)
# ==========================================
try:
    with open("main.py", "r", encoding="utf-8") as f:
        main_code = f.read()

    # Sync-Methode erweitern, um das Schiff-Level zu übergeben
    main_code = main_code.replace(
        "combat.max_player_hp = 500.0 + (schild_lvl - 1) * 100",
        "combat.max_player_hp = 500.0 + (schild_lvl - 1) * 100\n            combat.ship_level = self.modules.ship_level"
    )
except Exception as e:
    print(f"Fehler beim Lesen der main.py: {e}")
    main_code = "# Fehler beim Einlesen der main.py. Bitte prüfe die Datei."

# ==========================================
# AUSFÜHRUNG
# ==========================================
def create_file(filename, content):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {filename} wurde aktualisiert.")

if __name__ == "__main__":
    print("Starte Update...")
    create_file("pve_system.py", pve_code)
    create_file("module_system.py", module_code)
    create_file("main.py", main_code)
    print("🎉 Alle Dateien wurden erfolgreich auf das Level-Gating-System umgestellt!")