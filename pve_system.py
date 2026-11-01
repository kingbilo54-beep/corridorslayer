"""CORRIDOR SLAYER | PvE Combat & Dynamic Upgrade Engine."""
import math
import random
import openpyxl
import os
from dataclasses import dataclass

ENEMY_DATA = {}
PLAYER_DATA = {}

try:
    wb = openpyxl.load_workbook("game_data.xlsx")
    ws_e = wb["Enemies"]
    headers_e = [cell.value for cell in ws_e[1]]
    for row in ws_e.iter_rows(min_row=2, values_only=True):
        if row[0]: ENEMY_DATA[row[0].lower()] = dict(zip(headers_e, row))
            
    ws_p = wb["Player"]
    for row in ws_p.iter_rows(min_row=2, values_only=True):
        if row[0]: PLAYER_DATA[row[0]] = row[1]
except Exception as e:
    print(f"⚠️ Fehler beim Laden der Excel-Datei: {e}")

ENEMY_FOLDER = r"C:\\\\Users\\\\bsahi\\\\Desktop\\\\corridorSlayers\\\\DS4\\\\enemys"

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

class PvECombat:
    def __init__(self, is_idle=True, campaign_id=1, stage_id=1, ship_level=1):
        self.is_idle = is_idle
        self.campaign_id = campaign_id
        self.stage_id = stage_id
        self.ship_level = ship_level
        
        self.credits = 0
        self.idle_loot_earned = 0 
        self.stage_cleared = False # NEU: Flag für abgeschlossene Stufe
        
        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.particles: list[Particle] = []
        self.muzzle_flashes = []
        
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
        self.particles.clear()
        self.muzzle_flashes.clear()
        self.stage_cleared = False
        
        # Boss-Logik: Stufe 15 ist ein einzelner Boss
        if not self.is_idle and self.stage_id == 15:
            self.spawn_queue = 1
        else:
            self.spawn_queue = 999 if self.is_idle else (3 + self.stage_id)
            
        self.spawn_timer = 2.0

    def _spawn_single_enemy(self):
        # Boss-Logik
        if not self.is_idle and self.stage_id == 15:
            e_type = "lancer" # Nutze den Lancer als Boss
            data = ENEMY_DATA.get(e_type, {})
            hp = 500 * (1.15 ** self.stage_id) # Massiv mehr HP
            speed = 20.0
            damage = 30
            reward = 500
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
                
            e_type = random.choices(available_enemies, weights=weights, k=1)[0]
            data = ENEMY_DATA.get(e_type, {"Base_HP": 20, "Base_Speed": 50, "Base_Damage": 5, "Base_Reward": 10})
            
            lane_y = random.choice([200, 270, 340]) + random.uniform(-30, 30)
            
            hp = (float(data.get("Base_HP", 20)) + (self.stage_id * float(data.get("HP_Add_Per_Stage", 10)))) * (float(data.get("HP_Mult_Per_Stage", 1.05)) ** self.stage_id)
            speed = float(data.get("Base_Speed", 50)) + (self.stage_id * float(data.get("Speed_Add_Per_Stage", 0)))
            damage = float(data.get("Base_Damage", 5)) + (self.stage_id * float(data.get("Damage_Add_Per_Stage", 2)))
            reward = int((float(data.get("Base_Reward", 10)) + (self.stage_id * 2)) * float(data.get("Idle_Reward_Mult", 1.0)))
            
            if self.is_idle:
                hp = 1.0 # One-Shot im Idle
                speed *= 0.4 
                
        self.enemies.append(Enemy(
            name=e_type.upper(), hp=hp, max_hp=hp,
            damage=int(damage), speed=speed, reward=reward,
            x=1000.0, y=lane_y,
            attack_cooldown=random.uniform(1.0, 3.0),
            enemy_type=e_type
        ))

    def _spawn_explosion(self, x, y, enemy_type):
        count = 25 if (not self.is_idle and self.stage_id == 15) else 15
        color = (255, 170, 0)
        speed = 150.0
        life = 0.6
        
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            vx = math.cos(angle) * random.uniform(0.2, 1.5) * speed
            vy = math.sin(angle) * random.uniform(0.2, 1.5) * speed
            size = random.uniform(2, 8)
            self.particles.append(Particle(x, y, vx, vy, color, size, life, life))

    def update(self, dt: float, center=(100, 270), cannon_positions=None):
        cx, cy = center
        
        for p in list(self.particles):
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.life -= dt
            if p.life <= 0: self.particles.remove(p)

        for mf in list(self.muzzle_flashes):
            mf[3] -= dt
            if mf[3] <= 0: self.muzzle_flashes.remove(mf)

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
                        Projectile(x=e.x, y=e.y, vx=dx/dist, vy=dy/dist, damage=e.damage, color=(255, 0, 0), size=5, speed=250.0, kind="enemy")
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
                        Projectile(x=kx, y=ky, vx=dx/dist, vy=dy/dist, damage=self.cannon_damage, color=(0, 255, 255), size=4, speed=600.0, kind="player", is_drone=False)
                    )
                    self.muzzle_flashes.append([kx, ky, math.atan2(dy, dx), 0.08])

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
                        Projectile(x=drone_x, y=drone_y, vx=dx/dist, vy=dy/dist, damage=drone_dmg, color=(255, 62, 177), size=3, speed=700.0, kind="player", is_drone=True)
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
                            self._spawn_explosion(e.x, e.y, e.enemy_type)
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

        # NEU: Stufe abgeschlossen, aber NICHT automatisch die nächste starten!
        if not self.is_idle and not self.enemies and self.spawn_queue == 0:
            self.stage_cleared = True

    def get_result(self):
        """Gibt das Ergebnis der Stufe zurück, damit main.py es verarbeiten kann."""
        return {
            "won": not self.is_defeated and self.stage_cleared,
            "credits_earned": self.credits
        }

    @property
    def is_defeated(self):
        return self.player_hp <= 0 and not self.is_idle