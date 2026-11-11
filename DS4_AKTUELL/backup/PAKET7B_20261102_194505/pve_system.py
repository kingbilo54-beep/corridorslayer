"""CORRIDOR SLAYER | PvE Combat & Dynamic Upgrade Engine."""
import math
import random
import openpyxl
import os
from dataclasses import dataclass
from sound_system import SFX

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


# NEU PAKET 4: Globale Balancing-Koeffizienten (wirken auch auf Excel-Werte)
BAL_PLAYER_DMG = 1.6    # Kanonenschaden x1.6  -> Grundausstattung traegt die ersten Stufen
BAL_PLAYER_RATE = 0.88  # Feuerintervall x0.88 -> schneller
BAL_PLAYER_HP = 1.4     # Huelle x1.4
BAL_ENEMY_HP = 0.85     # Gegner-HP x0.85
BAL_ENEMY_DMG = 0.7     # Gegner-Schaden x0.7
BAL_BOSS_HP = 0.7       # Boss-HP x0.7

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
        self.damage_numbers: list[DamageNumber] = []   # NEU PAKET 4
        self.muzzle_flashes = []
        
        self.max_player_hp = float(PLAYER_DATA.get("base_max_hp", 500.0)) * BAL_PLAYER_HP   # NEU PAKET 4: Balancing
        self.player_hp = self.max_player_hp
        
        self.dmg_level = 1
        self.speed_level = 1
        self.cannon_count_level = 1
        self.hangar_level = 1
        self.repair_level = 1
        
        self.skill_mods = {}          # NEU PAKET 4: Modifikatoren aus dem Skill-Tree
        self.retaliate_timer = 0.0    # NEU PAKET 4: PULSGENERATOR
        self.retaliate_tick = 0.0     # NEU PAKET 4
        self.overdrive_timer = 0.0    # NEU PAKET 4: UEBERTAKTUNG
        self.overdrive_cd = 0.0       # NEU PAKET 4
        self.idle_kill_counter = 0    # NEU PAKET 4: Idle liefert Data Cores
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
        raw = base * (mult ** (self.dmg_level - 1)) * BAL_PLAYER_DMG
        raw *= 1.0 + self.mod("dmg_pct", 0.0)          # NEU PAKET 4: GEWEHRVERSTÄRKER
        return raw * self._missing_hp_factor()

    def _missing_hp_factor(self):
        """NEU PAKET 4: ADRENALIN-KERN - mehr Schaden, je niedriger die Huelle."""
        if self.max_player_hp <= 0:
            return 1.0
        missing = 1.0 - max(0.0, min(1.0, self.player_hp / self.max_player_hp))
        return 1.0 + self.mod("adrenalin_dmg", 0.0) * int(missing * 10)

    def mod(self, key, default=0.0):
        """NEU PAKET 4: Skill-Modifikator lesen (gesetzt von skill_tree.apply_to_combat)."""
        try:
            return self.skill_mods.get(key, default)
        except AttributeError:
            return default

    def activate_overdrive(self):
        """NEU PAKET 4: UEBERTAKTUNG (Spezialsparte) - 8s doppelte Feuerrate, 45s CD."""
        if self.is_idle or self.mod("overdrive", 0) < 1:
            return False
        if self.overdrive_cd > 0 or self.overdrive_timer > 0:
            return False
        self.overdrive_timer = 8.0
        self.overdrive_cd = 45.0
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
        if self.mod("adrenaline", 0) >= 1 and self.player_hp < self.max_player_hp * 0.3:
            rate *= 0.75                            # NEU PAKET 4: NOTKUEHLUNG
        return rate
    
    @property
    def cannon_count(self): return min(8, self.cannon_count_level + int(self.mod("extra_cannons", 0)))   # NEU PAKET 4: MEHRFACHLAUF

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
            self.spawn_queue = 999 if self.is_idle else (2 + self.stage_id)   # NEU PAKET 4: Balancing
            
        self.spawn_timer = 2.0

    def _spawn_single_enemy(self):
        # Boss-Logik
        if not self.is_idle and self.stage_id == 15:
            e_type = "lancer" # Nutze den Lancer als Boss
            data = ENEMY_DATA.get(e_type, {})
            hp = 500 * (1.15 ** self.stage_id) * BAL_BOSS_HP # NEU PAKET 4: Balancing (4068 -> ~2850)
            speed = 20.0
            damage = int(30 * BAL_ENEMY_DMG)   # NEU PAKET 4: Balancing
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
            
            hp = (float(data.get("Base_HP", 20)) + (self.stage_id * float(data.get("HP_Add_Per_Stage", 10)))) * (float(data.get("HP_Mult_Per_Stage", 1.05)) ** self.stage_id) * BAL_ENEMY_HP   # NEU PAKET 4: Balancing
            speed = float(data.get("Base_Speed", 50)) + (self.stage_id * float(data.get("Speed_Add_Per_Stage", 0)))
            damage = (float(data.get("Base_Damage", 5)) + (self.stage_id * float(data.get("Damage_Add_Per_Stage", 2)))) * BAL_ENEMY_DMG   # NEU PAKET 4: Balancing
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


        for dn in list(self.damage_numbers):   # NEU PAKET 4: Schadenszahlen
            dn.y += dn.vy * dt
            dn.vy *= (1.0 - 1.5 * dt)
            dn.life -= dt
            if dn.life <= 0:
                self.damage_numbers.remove(dn)

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
                SFX.play("shoot", 0.3)
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
                drone_dmg = self.cannon_damage * float(PLAYER_DATA.get("drone_damage_mult", 0.5)) * (1.0 + self.mod("drone_dmg_pct", 0.0))   # NEU PAKET 4: ENERGIELEITUNG
                for i in range(min(4, self.hangar_level - 1) + int(self.mod("extra_drones", 0))):   # NEU PAKET 4: HANGAR-TAKTIK
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
                        dmg = p.damage
                        crit = random.random() < self.mod("crit_chance", 0.0)
                        if crit:
                            dmg *= self.mod("crit_mult", 2.0)   # NEU PAKET 4: ZIELRECHNER/PANZERBRECHER
                        if self.mod("bully", 0.0) > 0 and e.hp < e.max_hp * 0.5:
                            dmg *= 1.0 + self.mod("bully", 0.0)   # NEU PAKET 4: BULLY
                        dmg = max(1, int(dmg))
                        e.hp -= dmg
                        e.hit_flash = 0.15
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
                            gain_mult = (1.0 + self.mod("idle_pct", 0.0)) if self.is_idle else (1.0 + self.mod("credit_pct", 0.0))
                            reward = int(e.reward * gain_mult)   # NEU PAKET 4: IDLE-PROTOKOLL/KRIEGSKASSE
                            self.credits += reward
                            if self.is_idle:
                                self.idle_loot_earned += reward
                                self.idle_kill_counter += 1
                                if self.idle_kill_counter % 25 == 0:
                                    self.data_cores_earned += 1   # NEU PAKET 4: Idle -> Data Cores
                            else:
                                cores = 1 + (1 if random.random() < self.mod("core_chance", 0.0) else 0)
                                self.data_cores_earned += cores   # NEU PAKET 4: KERN-SEPARATOR
                            self._spawn_explosion(e.x, e.y, e.enemy_type)
                            SFX.play("explosion", 0.5)
                            if self.mod("explosive", 0) >= 1 and not self.is_idle:
                                for o in list(self.enemies):   # NEU PAKET 4: SPRENGSPITZE
                                    if o is e:
                                        continue
                                    if math.hypot(o.x - e.x, o.y - e.y) < 90:
                                        o.hp -= self.cannon_damage * 0.3
                                        self._spawn_damage(o.x, o.y - 30, int(self.cannon_damage * 0.3), (255, 190, 76))
                                        if o.hp <= 0 and o in self.enemies:
                                            self._spawn_explosion(o.x, o.y, o.enemy_type)
                                            self.enemies.remove(o)
                            self.enemies.remove(e)
                        break
            
            elif p.kind == "enemy":
                if math.hypot(cx - p.x, cy - p.y) < 80:
                    applied = p.damage * (1.0 - self.mod("dr_pct", 0.0))   # NEU PAKET 4: ABFANG-FELD
                    applied = max(1, int(applied))
                    if self.is_idle:
                        self.player_hp = max(1.0, self.player_hp - applied)
                    else:
                        self.player_hp = max(0.0, self.player_hp - applied)
                    self._spawn_damage(p.x, p.y - 15, applied, (255, 77, 100))   # NEU PAKET 4: Schadenszahl (Spieler)
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

    def get_result(self):
        """Gibt das Ergebnis der Stufe zurück, damit main.py es verarbeiten kann."""
        return {
            "won": not self.is_defeated and self.stage_cleared,
            "credits_earned": self.credits
        }

    @property
    def is_defeated(self):
        return self.player_hp <= 0 and not self.is_idle