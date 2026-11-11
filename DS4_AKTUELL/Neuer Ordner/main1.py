# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | MOBILE EDITION (PAKET 5)
=============================================
Vollstaendige Mobile-Optimierung:

  * Responsive UI: jede Oberflaeche wird aus der aktuellen Bildschirmmasse
    berechnet (Hoch- UND Querformat, jede Aufloesung). Draw und Touch-Hit-
    Test benutzen dieselben Layout-Objekte -> keine Überlappungen mehr.
  * Touch-Steuerung durchgehend: Pause/Sound/Zurueck/Upgrades/Overdrive
    sind Buttons, ESC/M/Q/R funktionieren weiterhin als OPTIONALE Abkuerzung.
  * SKILL-NEXUS ersetzt das alte Spaltenraster (gleiche Daten/Speicherdatei,
    kaufte Faehigkeiten bleiben erhalten).
  * Kampfgeschehen laeuft in einer skalierten Arena (Weltkoordinaten 960x540
    bleiben unveraendert -> pve_system/ship_movement/fortress_2d unberuehrt).
  * Alle bisherigen Features erhalten: Victory-Video + Ton, Damage Numbers,
    Idle-Modus + Data Cores, Balancing aus Paket 4.
"""
import math
import os
import sys
import json
import random
import pygame

from module_system import FortressModules
from pve_system import PvECombat
from effects.engine_effect import EngineEffect
from fortress_2d import Fortress
from ship_movement import ShipMovement
from sound_system import SFX
from skill_tree import SkillTree, SKILL_TREE
import ui_kit
from ui_kit import (set_screen, u, fs, F, margin, btn_h, text, neon_text, panel,
                    overlay, grid_bg, draw_btn, draw_btns, first_hit, Btn,
                    draw_toggle, wrap_text,
                    VOID, PANEL, LINE, CYAN, CYAN_SOFT, ICE, WHITE, MUTED,
                    DIM, VIOLET, MAGENTA, GREEN, RED, AMBER)
import skill_nexus

pygame.init()

# ---------- Anzeige: Handy = Vollbild, Desktop = resizesbares Hochformat-Fenster ----------
IS_ANDROID = any(k in os.environ for k in
                 ("ANDROID_ARGUMENT", "ANDROID_PRIVATE", "ANDROID_ENTRYPOINT",
                  "PYDROID3", "PYDROID"))
FORCE_FULLSCREEN = IS_ANDROID or os.environ.get("CS_FULLSCREEN") == "1"

if FORCE_FULLSCREEN:
    try:
        SCREEN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    except Exception:
        SCREEN = pygame.display.set_mode((540, 960), pygame.RESIZABLE)
else:
    SCREEN = pygame.display.set_mode((540, 960), pygame.RESIZABLE)
pygame.display.set_caption("CORRIDOR SLAYER // MOBILE EDITION")
CLOCK = pygame.time.Clock()
FPS = 60

# ---------- Weltkonstanten (unveraendert -> Gameplay-Balance bleibt) ----------
WORLD_W, WORLD_H = 960.0, 540.0
FORTRESS_POS = (120.0, 270.0)
CANNON_OFFSETS = [(4, -14)]

VERSION = "MOBILE EDITION v5.0"
_BASE = os.path.dirname(os.path.abspath(__file__))
_PREFS_PATH = os.path.join(_BASE, "ui_prefs.json")

# ---------- Asset-Ordner: erst neben dieser Datei, dann alter Hartpfad ----------
def _folder(name, old_abs):
    p = os.path.join(_BASE, name)
    if os.path.isdir(p):
        return p
    if os.path.isdir(old_abs):
        return old_abs
    return p

ENEMY_FOLDER = _folder("enemys", r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\enemys")
MODULE_FOLDER = _folder("modules", r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\modules")
KANONEN_FOLDER = _folder("kanonen", r"C:\Users\bsahi\Desktop\corridorSlayers\DS4\kanonen")

enemy_images = {}
module_images = {}
kanonen_images = {}
_enemy_scaled = {}
_module_scaled = {}
_kanonen_scaled = {}


def _scaled(cache, key, img, s):
    """Skaliert ein Image mit s (Viertel-Pixel-Buckets gecacht)."""
    b = max(1, int(round(s * 8)))
    k = (key, b)
    out = cache.get(k)
    if out is None:
        nw = max(2, int(img.get_width() * b / 8))
        nh = max(2, int(img.get_height() * b / 8))
        out = pygame.transform.smoothscale(img, (nw, nh))
        if len(cache) > 60:
            cache.clear()
        cache[k] = out
    return out


def load_enemy_image(enemy_type):
    if enemy_type in enemy_images:
        return enemy_images[enemy_type]
    path = os.path.join(ENEMY_FOLDER, f"enemy_{enemy_type}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), rect)
        target_w = 50 if enemy_type == "skitter" else 70
        target_h = int(cropped.get_height() * (target_w / cropped.get_width()))
        scaled = pygame.transform.smoothscale(cropped, (target_w, target_h))
        enemy_images[enemy_type] = scaled
        return scaled
    except Exception:
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(surf, MAGENTA, (20, 20), 20)
        enemy_images[enemy_type] = surf
        return surf


def load_module_image(module_key, level):
    cache_key = f"{module_key}_{level}"
    if cache_key in module_images:
        return module_images[cache_key]
    path = os.path.join(MODULE_FOLDER, f"{module_key}_lvl_{level}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), rect)
        target_w = 40
        target_h = int(cropped.get_height() * (target_w / cropped.get_width()))
        scaled = pygame.transform.smoothscale(cropped, (target_w, target_h))
        module_images[cache_key] = scaled
        return scaled
    except Exception:
        surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.rect(surf, (40, 50, 70), (0, 0, 40, 40), border_radius=5)
        module_images[cache_key] = surf
        return surf


def load_kanonen_image(level):
    if level in kanonen_images:
        return kanonen_images[level]
    path = os.path.join(KANONEN_FOLDER, f"kanonen_lvl_{level}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        rect = img.get_bounding_rect()
        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(img, (0, 0), rect)
        target_w = 25
        target_h = int(cropped.get_height() * (target_w / cropped.get_width()))
        scaled = pygame.transform.smoothscale(cropped, (target_w, target_h))
        kanonen_images[level] = scaled
        return scaled
    except Exception:
        surf = pygame.Surface((25, 25), pygame.SRCALPHA)
        kanonen_images[level] = surf
        return surf


def load_video_frames(path):
    """Liest ein Video NATIV ein (Skalierung erst beim Zeichnen, resize-fest)."""
    frames = []
    try:
        import cv2
        cap = cv2.VideoCapture(path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            surf = pygame.image.frombuffer(frame.tobytes(),
                                           (frame.shape[1], frame.shape[0]), "RGB")
            frames.append(surf)
        cap.release()
    except Exception:
        return []
    return frames


SECTOR_DATA = {
    1: {"uv": (0.50, 0.78), "name": "ERDE"},
    2: {"uv": (0.22, 0.55), "name": "RAUMSTATION"},
    3: {"uv": (0.78, 0.52), "name": "ASTEROIDENGUERTEL"},
    4: {"uv": (0.28, 0.30), "name": "MARS"},
    5: {"uv": (0.75, 0.17), "name": "DUNKLER SEKTOR"},
}


class Game:
    STAGE_CLEAR = "stage_clear"
    INTRO = "intro"
    LOADING = "loading"
    MENU = "menu"
    PLAYING = "playing"
    STAGES = "stages"
    SETTINGS = "settings"
    RESEARCH = "research"
    SKILLTREE = "skilltree"
    DEFEAT = "defeat"
    PAUSED = "paused"

    def __init__(self):
        self.running = True
        self.state = self.INTRO
        self.elapsed = 0.0
        self.loading_time = 0.0

        self.debug_mode = False
        self.last_stage_reward = 0
        self.debug_target = "cannon"
        self.is_dragging_cannon = False
        self.is_dragging_engine = False
        self.debug_cannon_offset = [4, -14]
        self.debug_engine_offset = [-106, -24]
        self.rumble_x = 0.0
        self.rumble_y = 0.0

        self.intro_timer = 0.0
        self.defeat_timer = 0.0
        self.victory_timer = 0.0
        self.settings_return_state = self.MENU

        self.selected_sector = 0
        self.message = ""
        self.message_timer = 0.0

        self.intro_frames = load_video_frames(os.path.join(_BASE, "intro2.mp4"))
        self.defeat_frames = load_video_frames(os.path.join(_BASE, "defeat_animation.mp4"))
        self.victory_frames = load_video_frames(os.path.join(_BASE, "victory_screen.mp4"))
        if self.victory_frames:
            print(f"OK: Victory Video geladen ({len(self.victory_frames)} Frames).")
        if not self.intro_frames:
            self.state = self.MENU

        # Hintergrundbilder (nativ halten, beim Zeichnen einpassen)
        self.menu_bg = self._try_img("menu_bg.png", conv=True)
        self.world_bg = self._try_img("bg_world.jpg", conv=True)
        self.logo_img = None
        logo = self._try_img("logo.png", conv=False)
        if logo is not None:
            self.logo_img = logo
        self.bg_chapter = [self._try_img(f"bg_chapter_1_part_{i}.jpg", conv=True)
                           for i in (1, 2, 3)]
        self._fit_cache = {}
        self._vcache = {}

        self.skills = SkillTree()
        self.nexus = skill_nexus.NexusUI()
        self.fortress = Fortress(FORTRESS_POS[0], FORTRESS_POS[1], level=1)
        self.modules = FortressModules()
        self.engine_effect = EngineEffect(0, 0)
        self.movement = ShipMovement()

        self.idle_combat = PvECombat(is_idle=True, campaign_id=1, stage_id=1,
                                     ship_level=self.modules.ship_level)
        self.pve = PvECombat(is_idle=False, campaign_id=1, stage_id=1,
                             ship_level=self.modules.ship_level)

        self.idle_mode = True
        self.show_upgrades = False

        # Eingabe-Zustand (Touch & Maus, Feuer beim Loslassen)
        self._ptr = None
        self._touch_guard = 0.0

        self._load_prefs()
        self._ui = {}
        self._sync_modules_to_combat()

    # ---------------- Hilfs-Loader / Prefs ----------------
    def _try_img(self, name, conv=True):
        path = os.path.join(_BASE, name)
        try:
            img = pygame.image.load(path)
            return img.convert() if conv else img.convert_alpha()
        except Exception:
            return None

    def _fit_surf(self, img, key):
        """Skaliert ein Hintergrundbild auf Vollbild (Cover), gecacht pro Groesse."""
        W, H = ui_kit.W, ui_kit.H
        k = (key, W, H)
        out = self._fit_cache.get(k)
        if out is None:
            iw, ih = img.get_size()
            s = max(W / iw, H / ih)
            out = pygame.transform.smoothscale(img, (max(1, int(iw * s)), max(1, int(ih * s))))
            if len(self._fit_cache) > 12:
                self._fit_cache.clear()
            self._fit_cache[k] = out
        return out

    def _video_frame(self, frames, idx):
        """Skaliert das Videoframe bildschirmfuellend (kleiner Cache)."""
        W, H = ui_kit.W, ui_kit.H
        k = (W, H, idx)
        c = self._vcache
        out = c.get(k)
        if out is None:
            if len(c) > 3:
                c.clear()
            f = frames[idx]
            fw, fh = f.get_size()
            s = max(W / fw, H / fh)
            out = pygame.transform.smoothscale(f, (max(1, int(fw * s)), max(1, int(fh * s))))
            c[k] = out
        return out

    def _load_prefs(self):
        self.prefs = {}
        try:
            with open(_PREFS_PATH, "r", encoding="utf-8") as fh:
                self.prefs = json.load(fh)
        except Exception:
            self.prefs = {}
        if self.prefs.get("muted"):
            SFX.muted = True

    def _save_prefs(self):
        try:
            with open(_PREFS_PATH, "w", encoding="utf-8") as fh:
                json.dump(self.prefs, fh)
        except Exception:
            pass

    # ---------------- Bruecken (unveraendert aus Paket 3/4) ----------------
    def _sync_modules_to_combat(self):
        for combat in (self.idle_combat, self.pve):
            combat.dmg_level = self.modules.get("kanonen").level
            combat.speed_level = self.modules.get("antrieb").level
            combat.cannon_count_level = min(8, 1 + self.modules.get("kanonen").level // 2)
            combat.hangar_level = self.modules.get("hangar").level
            combat.repair_level = self.modules.get("reparatur").level
            combat.ship_level = self.modules.ship_level
            if hasattr(self, "skills"):
                self.skills.apply_to_combat(combat)
            base_hp = 700.0 + (self.modules.get("schild").level - 1) * 100
            combat.max_player_hp = base_hp * (1.0 + combat.mod("hp_pct", 0.0))
            combat.player_hp = min(combat.player_hp, combat.max_player_hp)

    def _collect_idle_loot(self):
        """Überweist gesammelte Idle-Credits (und Data Cores) in die Wallet."""
        if self.idle_combat.credits > 0:
            self.modules.credits += self.idle_combat.credits
            self.idle_combat.credits = 0
        if self.idle_combat.data_cores_earned > 0:
            self.modules.data_cores += self.idle_combat.data_cores_earned
            self.idle_combat.data_cores_earned = 0
        self.modules.save()

    def _restart_stage(self):
        campaign = self.selected_sector if self.selected_sector > 0 else self.pve.campaign_id
        stage = self.pve.stage_id
        self.pve = PvECombat(is_idle=False, campaign_id=campaign, stage_id=stage,
                             ship_level=self.modules.ship_level)
        self._sync_modules_to_combat()
        self.state = self.PLAYING

    def show_message(self, msg, duration=3.0):
        self.message = msg
        self.message_timer = duration

    def _toggle_sound(self):
        SFX.toggle_mute()
        self.prefs["muted"] = bool(SFX.muted)
        self._save_prefs()
        self.show_message(f"SOUND: {'AUS' if SFX.muted else 'AN'}")

    def _overdrive(self):
        if self.idle_mode:
            return
        if self.pve.activate_overdrive():
            self.show_message("ÜBERTAKTUNG AKTIV: doppelte Feuerrate (8s)")
        elif self.pve.mod("overdrive", 0) < 1:
            self.show_message("Übertaktung nicht trainiert (Skill-Nexus, Sparte SPEZIAL)")
        else:
            self.show_message("Übertaktung nicht bereit (Abklingzeit)")

    def _skill_train(self):
        node_id = self.nexus.selected
        if not node_id:
            return
        ok, reason = self.skills.unlock_info(node_id)
        if not ok:
            self.show_message(f"Nicht moeglich: {reason}")
            return
        cost = self.skills.cost_of(node_id)
        if self.modules.data_cores < cost:
            self.show_message(f"Zu wenig Data Cores: {cost} benoetigt")
            return
        self.modules.data_cores -= cost
        self.skills.unlock(node_id)
        self._sync_modules_to_combat()
        self.modules.save()
        SFX.play("upgrade")
        pos = self.nexus.nodes.get(node_id)
        if pos:
            branch, _i, _n = None, -1, None
            for br in SKILL_TREE:
                for nd in br["nodes"]:
                    if nd["id"] == node_id:
                        branch = br
            self.nexus.fire(pos[0], pos[1], branch["color"] if branch else CYAN)
        self.show_message(f"Skill trainiert: {node_id}")

    def _quit(self):
        self._collect_idle_loot()
        self.running = False

    # ---------------- Hauptschleife ----------------
    def run(self):
        while self.running:
            dt = min(CLOCK.tick(FPS) / 1000.0, 0.05)
            if self.message_timer > 0:
                self.message_timer -= dt
            self.elapsed += dt
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()

    # ---------------- Eingabe (Touch + Maus, Tastatur optional) ----------------
    def _fpos(self, event):
        W, H = ui_kit.W, ui_kit.H
        return (int(event.x * W), int(event.y * H))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._quit()
                return

            if event.type == pygame.FINGERDOWN:
                self._touch_guard = self.elapsed + 0.45
                self._press(self._fpos(event))

            elif event.type == pygame.FINGERUP:
                self._release(self._fpos(event))

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.elapsed < self._touch_guard:
                    continue                     # synthetisches Touch-Maus-Event
                if event.button == 1 and self._debug_drag_start(event.pos):
                    continue
                if event.button == 1:
                    self._press(event.pos)
                elif event.button == 3 and self.debug_mode and self.state == self.PLAYING:
                    ex = self.fortress.x + self.debug_engine_offset[0]
                    ey = self.fortress.y + self.debug_engine_offset[1]
                    if math.hypot(event.pos[0] - ex, event.pos[1] - ey) < 60:
                        self.is_dragging_engine = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.elapsed < self._touch_guard:
                    continue
                if event.button == 1:
                    self._release(event.pos)
                self.is_dragging_cannon = False
                self.is_dragging_engine = False

            elif event.type == pygame.MOUSEMOTION:
                self._debug_drag_move(event.pos)

            elif event.type == pygame.KEYDOWN:
                self._key(event)

    def _debug_drag_start(self, pos):
        """Desktop-Debug: Kanone/Antrieb ziehen (rechte Maustaste = Antrieb)."""
        if not (self.debug_mode and self.state == self.PLAYING):
            return False
        cx = self.fortress.x + self.debug_cannon_offset[0]
        cy = self.fortress.y + self.debug_cannon_offset[1]
        if math.hypot(pos[0] - cx, pos[1] - cy) < 35:
            self.is_dragging_cannon = True
            self.debug_target = "cannon"
            return True
        return False

    def _debug_drag_move(self, pos):
        if self.is_dragging_cannon:
            self.debug_cannon_offset[0] = pos[0] - self.fortress.x
            self.debug_cannon_offset[1] = pos[1] - self.fortress.y
        if self.is_dragging_engine:
            self.debug_engine_offset[0] = pos[0] - self.fortress.x
            self.debug_engine_offset[1] = pos[1] - self.fortress.y

    def _press(self, pos):
        self._ptr = None
        if self.state == self.SKILLTREE:
            nid = self.nexus.hit(pos)
            if nid:
                self._ptr = {"kind": "node", "id": nid}
                return
        b = first_hit(self._ui, pos)
        if b:
            self._ptr = {"kind": "btn", "id": b.id}

    def _release(self, pos):
        p, self._ptr = self._ptr, None
        if not p:
            return
        if p["kind"] == "node":
            if self.state == self.SKILLTREE and self.nexus.hit(pos) == p["id"]:
                self.nexus.select(p["id"])
                SFX.play("click", 0.4)
            return
        b = self._ui.get(p["id"])
        if b and b.hit(pos):
            self._fire(b.id)

    def _key(self, event):
        k = event.key
        if k == pygame.K_AC_BACK:            # Android-Zurueck-Taste
            k = pygame.K_ESCAPE
        if k == pygame.K_F1:
            self.debug_mode = not self.debug_mode
            print(f"DEBUG MODUS: {'AN' if self.debug_mode else 'AUS'}")
            return
        if k == pygame.K_m:
            self._toggle_sound()
            return
        if k == pygame.K_q and self.state == self.PLAYING and not self.idle_mode:
            self._overdrive()
            return
        if self.state == self.INTRO:
            self.state = self.MENU
            return
        if self.state == self.DEFEAT and k == pygame.K_r:
            self._restart_stage()
            return
        if k == pygame.K_ESCAPE:
            if self.state == self.PLAYING:
                self.state = self.PAUSED
            elif self.show_upgrades:
                self.show_upgrades = False
            elif self.state in (self.STAGES, self.SETTINGS, self.RESEARCH, self.SKILLTREE):
                if self.state == self.SETTINGS:
                    self.state = self.settings_return_state
                else:
                    self.state = self.MENU
            return
        if self.debug_mode and self.state == self.PLAYING:
            if k == pygame.K_TAB:
                self.debug_target = "engine" if self.debug_target == "cannon" else "cannon"
            dx = -1 if k == pygame.K_LEFT else (1 if k == pygame.K_RIGHT else 0)
            dy = -1 if k == pygame.K_UP else (1 if k == pygame.K_DOWN else 0)
            if dx or dy:
                if self.debug_target == "cannon":
                    self.debug_cannon_offset[0] += dx
                    self.debug_cannon_offset[1] += dy
                else:
                    self.debug_engine_offset[0] += dx
                    self.debug_engine_offset[1] += dy

    # ---------------- Update (Logik unveraendert) ----------------
    def update(self, dt):
        if self.state == self.INTRO:
            if self.intro_frames:
                self.intro_timer += dt
                if self.intro_timer >= len(self.intro_frames) / 30.0:
                    self.state = self.MENU
            return

        if self.state == self.STAGE_CLEAR:
            if self.victory_frames:
                self.victory_timer += dt * 2.0
                full = len(self.victory_frames) / 30.0
                if self.victory_timer >= full:
                    self.victory_timer = full
            return

        if self.state == self.LOADING:
            self.loading_time += dt
            if self.loading_time >= 2.5:
                self.state = self.MENU
            return

        if self.state == self.DEFEAT:
            if self.defeat_frames:
                self.defeat_timer += dt
                full = len(self.defeat_frames) / 30.0
                if self.defeat_timer >= full:
                    self.defeat_timer = full
            return

        if self.state == self.PAUSED:
            return

        self.fortress.update(dt)
        self.movement.update(dt)

        engine_lvl = self.modules.get("antrieb").level
        self.engine_effect.update(dt, engine_lvl)

        center = (self.fortress.x, self.fortress.y)
        mounted_cannons = []
        current_offset = self.debug_cannon_offset if self.debug_mode else CANNON_OFFSETS[0]
        for ox, oy in [current_offset]:
            mounted_cannons.append((center[0] + ox, center[1] + oy))

        if self.state == self.PLAYING:
            if self.idle_mode:
                self.idle_combat.update(dt, center, mounted_cannons)
            else:
                self.pve.update(dt, center, mounted_cannons)

                if hasattr(self.pve, 'data_cores_earned') and self.pve.data_cores_earned > 0:
                    self.modules.data_cores += self.pve.data_cores_earned
                    self.pve.data_cores_earned = 0
                    self.modules.save()

                if self.pve.is_defeated:
                    self.state = self.DEFEAT
                    return

                result = self.pve.get_result()
                if result["won"] and self.state == self.PLAYING:
                    self.modules.complete_stage(
                        campaign_id=self.selected_sector,
                        stage_id=self.pve.stage_id,
                        credits_earned=result["credits_earned"]
                    )
                    self.last_stage_reward = result["credits_earned"]
                    self.victory_timer = 0.0
                    self.state = self.STAGE_CLEAR
                    SFX.play_victory_audio()
                    return

    # ---------------- Aktionen (Fire-on-Release) ----------------
    def _fire(self, bid):
        SFX.play("click", 0.4)
        if bid in ("snd_menu", "snd_res", "snd_stg"):
            self._toggle_sound()
            return
        st = self.state

        if st == self.INTRO:
            self.state = self.MENU
            return

        if st == self.MENU:
            if bid == "btn_idle":
                self.idle_mode = True
                self.idle_combat.stage_id = self.modules.highest_stage
                self._sync_modules_to_combat()
                self.state = self.PLAYING
            elif bid == "btn_research":
                self.state = self.RESEARCH
            elif bid == "btn_skills":
                self.nexus.select(None)
                self.state = self.SKILLTREE
            elif bid == "btn_stages":
                self.selected_sector = 0
                self.state = self.STAGES
            elif bid == "btn_settings":
                self.settings_return_state = self.MENU
                self.state = self.SETTINGS
            elif bid == "btn_quit":
                self._quit()
            elif bid == "snd_menu":
                self._toggle_sound()
            return

        if st == self.RESEARCH:
            if bid == "res_back":
                self.state = self.MENU
            elif bid.startswith("res_"):
                self._buy_module(bid[4:])
            return

        if st == self.STAGES:
            if bid == "stg_back":
                self.state = self.MENU
            elif bid == "stg_close":
                self.selected_sector = 0
            elif bid.startswith("sec_"):
                sector = int(bid[4:])
                if sector <= self.modules.highest_campaign:
                    self.selected_sector = sector
                else:
                    self.show_message(f"Sektor {sector} ist gesperrt! Schalte erst fruehere Sektoren frei.")
            elif bid.startswith("stage_"):
                self._try_enter_stage(int(bid[6:]))
            return

        if st == self.SKILLTREE:
            if bid == "nex_back":
                self.state = self.MENU
            elif bid == "nex_train":
                self._skill_train()
            elif bid == "nex_close":
                self.nexus.select(None)
            return

        if st == self.SETTINGS:
            if bid == "set_back":
                self.state = self.settings_return_state
            elif bid == "set_sound":
                self._toggle_sound()
            elif bid == "set_full":
                self._toggle_fullscreen()
            elif bid == "set_debug":
                self.debug_mode = not self.debug_mode
                self.show_message(f"DEBUG MODUS: {'AN' if self.debug_mode else 'AUS'}")
            return

        if st == self.PLAYING:
            if self.show_upgrades:
                if bid == "upg_close":
                    self.show_upgrades = False
                elif bid.startswith("upg_"):
                    self._buy_module(bid[4:])
                return
            if bid == "hud_pause":
                self.state = self.PAUSED
            elif bid == "hud_sound":
                self._toggle_sound()
            elif bid == "hud_upgrades":
                self.show_upgrades = True
            elif bid == "hud_overdrive":
                self._overdrive()
            return

        if st == self.PAUSED:
            if bid == "pau_resume":
                self.state = self.PLAYING
            elif bid == "pau_settings":
                self.settings_return_state = self.PAUSED
                self.state = self.SETTINGS
            elif bid == "pau_sound":
                self._toggle_sound()
            elif bid == "pau_giveup":
                self._collect_idle_loot()
                self.state = self.MENU
            return

        if st == self.DEFEAT:
            if bid == "def_skip":
                if self.defeat_frames:
                    self.defeat_timer = len(self.defeat_frames) / 30.0
            elif bid == "def_restart":
                self._restart_stage()
            elif bid == "def_menu":
                self.state = self.MENU
            return

        if st == self.STAGE_CLEAR:
            if bid == "vic_skip":
                if self.victory_frames:
                    self.victory_timer = len(self.victory_frames) / 30.0
            elif bid == "vic_continue":
                SFX.stop_music()
                campaign = self.selected_sector if self.selected_sector > 0 else self.pve.campaign_id
                self.state = self.STAGES
                self.pve = PvECombat(is_idle=False, campaign_id=campaign, stage_id=1,
                                     ship_level=self.modules.ship_level)
                self.victory_timer = 0.0
            return

    def _buy_module(self, key):
        try:
            self.modules.upgrade(key)
            self._sync_modules_to_combat()
            SFX.play("upgrade")
        except ValueError as e:
            self.show_message(str(e))

    def _try_enter_stage(self, stage):
        sector = self.selected_sector
        unlocked = (sector < self.modules.highest_campaign or
                    (sector == self.modules.highest_campaign and stage <= self.modules.highest_stage))
        if unlocked:
            self._collect_idle_loot()
            self.idle_mode = False
            self.pve = PvECombat(is_idle=False, campaign_id=sector, stage_id=stage,
                                 ship_level=self.modules.ship_level)
            self._sync_modules_to_combat()
            self.state = self.PLAYING
        else:
            self.show_message(f"Stufe {stage} ist gesperrt! Schaffe erst fruehere Stufen.")

    def _toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
            self.show_message("VOLLBILD umgeschaltet")
        except Exception as e:
            self.show_message(f"Vollbild nicht moeglich: {e}")

    # ---------------- Layouts (einzige Quelle fuer Rects) ----------------
    def _layout_menu(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = max(u(40), min(W, H) // 14)
        ui["snd_menu"] = Btn("snd_menu", pygame.Rect(W - m - isz, m, isz, isz),
                             icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        items = [
            ("btn_idle", "IDLE MODUS", "Automatischer Abwehrbetrieb", CYAN),
            ("btn_research", "UPGRADES", "Module & Schiff ausbauen", MAGENTA),
            ("btn_skills", "SKILL-NEXUS", "Data Cores investieren", AMBER),
            ("btn_stages", "STUFENKAMPAGNE", "Sektor-Einsatz waehlen", GREEN),
            ("btn_settings", "EINSTELLUNGEN", "Sound & System", VIOLET),
            ("btn_quit", "BEENDEN", "Verbindung trennen", RED),
        ]
        bh, gap = btn_h(), max(u(8), int(H * 0.011))
        total = len(items) * bh + (len(items) - 1) * gap
        y0 = H - m - total - u(46)
        for i, (bid, lab, sub, acc) in enumerate(items):
            ui[bid] = Btn(bid, pygame.Rect(m, y0 + i * (bh + gap), W - 2 * m, bh), lab, sub, acc)
        return ui

    def _layout_hud(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = max(u(40), min(W, H) // 14)
        ui["hud_pause"] = Btn("hud_pause", pygame.Rect(m, m, isz, isz), icon="pause", accent=CYAN)
        ui["hud_sound"] = Btn("hud_sound", pygame.Rect(m + isz + u(10), m, isz, isz),
                              icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        bh = btn_h()
        yb = H - bh - m
        od_learned = self.skills.level_of("spez_overdrive") > 0
        if not self.idle_mode and od_learned:
            bw = (W - 2 * m - u(12)) // 2
            ui["hud_upgrades"] = Btn("hud_upgrades", pygame.Rect(m, yb, bw, bh),
                                     "UPGRADES", "Module ausbauen", MAGENTA)
            cd = float(getattr(self.pve, "overdrive_cd", 0.0) or 0.0)
            ui["hud_overdrive"] = Btn("hud_overdrive",
                                      pygame.Rect(m + bw + u(12), yb, bw, bh),
                                      "ÜBERTAKTUNG",
                                      "BEREIT – 8s x2 Feuerrate" if cd <= 0 else f"ABKLINGZEIT {int(cd)}s",
                                      VIOLET, enabled=(cd <= 0))
        else:
            ui["hud_upgrades"] = Btn("hud_upgrades", pygame.Rect(m, yb, W - 2 * m, bh),
                                     "UPGRADES", "Module ausbauen", MAGENTA)
        return ui

    def _layout_upgrades(self):
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        sh = int(H * 0.62)
        rect = pygame.Rect(u(8), H - sh - u(8), W - u(16), sh)
        cs = max(u(40), u(38))
        ui["upg_close"] = Btn("upg_close", pygame.Rect(rect.right - cs - u(10), rect.y + u(10), cs, cs),
                              icon="close", accent=RED)
        keys = list(self.modules.modules.keys())
        cols = 2
        rows = (len(keys) + cols - 1) // cols
        gap = u(10)
        head = u(54)
        cw = (rect.w - u(24) - gap * (cols - 1)) // cols
        ch = (rect.h - head - u(16) - gap * (rows - 1)) // rows
        for i, key in enumerate(keys):
            r = pygame.Rect(rect.x + u(12) + (i % cols) * (cw + gap),
                            rect.y + head + (i // cols) * (ch + gap), cw, ch)
            ui["upg_" + key] = Btn("upg_" + key, r, accent=CYAN)
        return ui, rect

    def _layout_research(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = max(u(40), min(W, H) // 14)
        ui["res_back"] = Btn("res_back", pygame.Rect(m, m, isz, isz), icon="back", accent=CYAN)
        ui["snd_res"] = Btn("snd_res", pygame.Rect(W - m - isz, m, isz, isz),
                            icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        keys = list(self.modules.modules.keys())
        top = m + isz + u(46)
        cols = 2
        rows = (len(keys) + 1) // 2
        gap = u(10)
        cw = (W - 2 * m - gap) // cols
        ch = (H - top - m - u(6) - gap * (rows - 1)) // rows
        for i, key in enumerate(keys):
            r = pygame.Rect(m + (i % cols) * (cw + gap), top + (i // cols) * (ch + gap), cw, ch)
            ui["res_" + key] = Btn("res_" + key, r, accent=CYAN)
        return ui

    def _stage_positions(self):
        W, H = ui_kit.W, ui_kit.H
        top = u(78)
        bottom = H - margin() - u(6)
        out = {}
        for sector, data in SECTOR_DATA.items():
            uvx, uvy = data["uv"]
            out[sector] = (int(uvx * W * 0.86 + W * 0.07),
                           int(top + uvy * (bottom - top)))
        return out

    def _layout_stages(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = max(u(40), min(W, H) // 14)
        ui["stg_back"] = Btn("stg_back", pygame.Rect(m, m, isz, isz), icon="back", accent=CYAN)
        ui["snd_stg"] = Btn("snd_stg", pygame.Rect(W - m - isz, m, isz, isz),
                            icon=("sound_off" if SFX.muted else "sound_on"), accent=MUTED)
        r = max(u(26), int(min(W, H) * 0.055))
        if self.selected_sector == 0:
            # Sektoren nur waehlbar, solange kein Stufen-Sheet offen ist (modal)
            for sector, (sx, sy) in self._stage_positions().items():
                ui[f"sec_{sector}"] = Btn(f"sec_{sector}",
                                          pygame.Rect(sx - r * 1.5, sy - r * 1.5, r * 3, r * 3),
                                          accent=CYAN)
        if self.selected_sector > 0:
            rect = pygame.Rect(u(8), int(H * 0.16), W - u(16), int(H * 0.80))
            cs = max(u(40), u(38))
            head = max(u(50), cs + u(24))
            ui["stg_close"] = Btn("stg_close",
                                  pygame.Rect(rect.right - cs - u(10), rect.y + u(10), cs, cs),
                                  icon="close", accent=RED)
            cols, rows = 3, 5
            gap = u(8)
            cw = (rect.w - u(24) - gap * (cols - 1)) // cols
            ch = (rect.h - head - u(14) - gap * (rows - 1)) // rows
            for i in range(15):
                stage = i + 1
                rr = pygame.Rect(rect.x + u(12) + (i % cols) * (cw + gap),
                                 rect.y + head + (i // cols) * (ch + gap), cw, ch)
                ui[f"stage_{stage}"] = Btn(f"stage_{stage}", rr, accent=VIOLET)
            self._stage_sheet_rect = rect
        return ui

    def _layout_skilltree(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = max(u(40), min(W, H) // 14)
        ui["nex_back"] = Btn("nex_back", pygame.Rect(m, m, isz, isz), icon="back", accent=AMBER)
        top = m + isz + u(12)
        bottom = H - int(H * 0.24) - u(14)
        self._nex_area = (top, bottom)
        for nid, rect in self.nexus.hitmap.items():
            ui["node_" + nid] = Btn("node_" + nid, rect, accent=AMBER)
        if self.nexus.selected:
            if self.nexus.train_rect:
                ui["nex_train"] = Btn("nex_train", self.nexus.train_rect, accent=AMBER)
            if self.nexus.close_rect:
                ui["nex_close"] = Btn("nex_close", self.nexus.close_rect, accent=MUTED)
        return ui

    def _layout_settings(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        isz = max(u(40), min(W, H) // 14)
        ui["set_back"] = Btn("set_back", pygame.Rect(m, m, isz, isz), icon="back", accent=VIOLET)
        bh = int(btn_h() * 1.15)
        y = m + isz + u(40)
        rows = [("set_sound", "SOUND", "Effekte & Sieg-Musik")]
        if not IS_ANDROID:
            rows.append(("set_full", "VOLLBILD", "Fenster / Vollbild umschalten"))
        rows.append(("set_debug", "DEBUG MODUS", "Entwicklerwerkzeuge (Desktop)"))
        for bid, lab, sub in rows:
            ui[bid] = Btn(bid, pygame.Rect(m, y, W - 2 * m, bh), lab, sub, VIOLET)
            y += bh + u(12)
        self._settings_rows_end = y
        return ui

    def _layout_pause(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        pw = min(W - 2 * m, u(430))
        bh = btn_h()
        gap = u(12)
        head = u(56)
        ph = head + 4 * bh + 5 * gap
        px, py = (W - pw) // 2, (H - ph) // 2
        labels = [
            ("pau_resume", "FORTSETZEN", "", GREEN),
            ("pau_settings", "EINSTELLUNGEN", "", VIOLET),
            ("pau_sound", "SOUND: " + ("AUS" if SFX.muted else "AN"), "", CYAN),
            ("pau_giveup", "ZUM HAUPTMENÜ" if self.idle_mode else "AUFGEBEN", "", RED),
        ]
        for i, (bid, lab, sub, acc) in enumerate(labels):
            ui[bid] = Btn(bid, pygame.Rect(px + u(20), py + head + i * (bh + gap), pw - u(40), bh),
                          lab, sub, acc)
        self._pause_rect = pygame.Rect(px, py, pw, ph)
        return ui

    def _layout_defeat(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        ui = {}
        ended = (not self.defeat_frames) or self.defeat_timer >= len(self.defeat_frames) / 30.0
        if not ended:
            ui["def_skip"] = Btn("def_skip", pygame.Rect(0, 0, W, H))
            return ui
        bh = btn_h()
        bw = (W - 2 * m - u(12)) // 2
        yb = H - bh - m - u(12)
        ui["def_restart"] = Btn("def_restart", pygame.Rect(m, yb, bw, bh),
                                "NEUSTART", "Stufe erneut", GREEN)
        ui["def_menu"] = Btn("def_menu", pygame.Rect(m + bw + u(12), yb, bw, bh),
                             "HAUPTMENÜ", "Zurück zur Basis", RED)
        return ui

    def _layout_clear(self):
        W, H = ui_kit.W, ui_kit.H
        ui = {}
        ended = (not self.victory_frames) or self.victory_timer >= len(self.victory_frames) / 30.0
        if not ended:
            ui["vic_skip"] = Btn("vic_skip", pygame.Rect(0, 0, W, H))
            return ui
        bw = int(W * 0.62)
        bh = int(btn_h() * 1.25)
        ui["vic_continue"] = Btn("vic_continue",
                                 pygame.Rect((W - bw) // 2, int(H * 0.66), bw, bh),
                                 "WEITER", "", CYAN)
        return ui

    def _layout_intro(self):
        W, H = ui_kit.W, ui_kit.H
        return {"intro_skip": Btn("intro_skip", pygame.Rect(0, 0, W, H))}

    def _pressed(self, bid):
        return bool(self._ptr and self._ptr["id"] == bid)

    # ---------------- Zeichnen ----------------
    def _draw_menu_backdrop(self):
        W, H = ui_kit.W, ui_kit.H
        SCREEN.fill(VOID)
        if self.menu_bg is not None:
            img = self._fit_surf(self.menu_bg, "menu_bg")
            SCREEN.blit(img, ((W - img.get_width()) // 2, (H - img.get_height()) // 2))
            overlay(SCREEN, 140)
        else:
            grid_bg(SCREEN, self.elapsed)
            overlay(SCREEN, 40)

    def _draw_header(self, title, title_color=WHITE):
        """Titel + Icons sind Teil der Layouts; hier nur der Titeltext."""
        W, H = ui_kit.W, ui_kit.H
        isz = max(u(40), min(W, H) // 14)
        neon_text(SCREEN, title, F(17), title_color, (W // 2, margin() + isz // 2), "center", 1)

    def draw_menu(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        self._draw_menu_backdrop()
        self._ui = self._layout_menu()
        top = u(16)
        banner_h = u(30)
        if self.logo_img is not None:
            iw, ih = self.logo_img.get_size()
            lw = int(W * 0.62)
            lh = int(ih * lw / iw)
            maxh = int(H * (0.20 if H >= W else 0.13))
            if lh > maxh:
                lh = maxh
                lw = int(ih * lh / ih)
            key = ("logo", lw, lh)
            img = self._fit_cache.get(key)
            if img is None:
                img = pygame.transform.smoothscale(self.logo_img, (lw, lh))
                self._fit_cache[key] = img
            SCREEN.blit(img, ((W - lw) // 2, top))
            header_end = top + lh + u(10) + banner_h + u(8)
        else:
            neon_text(SCREEN, "CORRIDOR", F(34), CYAN, (W // 2, top), "midtop", 2)
            neon_text(SCREEN, "SLAYER", F(34), MAGENTA, (W // 2, top + u(44)), "midtop", 2)
            header_end = top + u(96) + u(10) + banner_h + u(8)
        bw = min(W - 2 * m, u(330))
        brect = pygame.Rect((W - bw) // 2, header_end - banner_h - u(8), bw, banner_h)
        pygame.draw.rect(SCREEN, (10, 5, 0), brect, border_radius=u(5))
        pygame.draw.rect(SCREEN, AMBER, brect, 1, border_radius=u(5))
        text(SCREEN, "COMMAND INTERFACE", F(11), AMBER, brect.center, "center")
        text(SCREEN, f"CREDITS: {self.modules.credits:,}   DATA CORES: {self.modules.data_cores}",
             F(11), MUTED, (W // 2, header_end + u(2)), "midtop")
        # Buttons: vertikal zwischen Header und Fusszeile verteilen
        items = [k for k in self._ui if k.startswith("btn_")]
        n = len(items)
        avail_top = header_end + u(26)
        avail_bot = H - m - u(40)
        gap = max(u(8), int(H * 0.011))
        bh = min(btn_h(), int((avail_bot - avail_top - (n - 1) * gap) / n))
        bh = max(u(34), bh)
        gap = min(gap, max(4, (avail_bot - avail_top - n * bh) // max(1, n - 1)))
        total = n * bh + (n - 1) * gap
        y0 = avail_top + max(0, (avail_bot - avail_top - total) // 2)
        for i, bid in enumerate(items):
            self._ui[bid].rect = pygame.Rect(m, y0 + i * (bh + gap), W - 2 * m, bh)
            draw_btn(SCREEN, self._ui[bid], pressed=self._pressed(bid))
        draw_btn(SCREEN, self._ui["snd_menu"], pressed=self._pressed("snd_menu"))
        text(SCREEN, VERSION, F(9), DIM, (W // 2, H - m - u(20)), "midtop")

    def _draw_module_card(self, rect, key, pressed=False, big=False):
        mod = self.modules.get(key)
        fill = (10, 26, 42) if pressed else (4, 12, 24)
        pygame.draw.rect(SCREEN, fill, rect, border_radius=u(12))
        pygame.draw.rect(SCREEN, CYAN if pressed else LINE, rect, 2 if pressed else 1,
                         border_radius=u(12))
        img = load_module_image(key, mod.level)
        isz = u(46) if big else u(38)
        img_s = _scaled(_module_scaled, (key, mod.level, isz), img, isz / max(1, img.get_width()))
        SCREEN.blit(img_s, img_s.get_rect(center=(rect.centerx, rect.y + u(10) + isz // 2)))
        y = rect.y + u(12) + isz + u(4)
        text(SCREEN, mod.name.upper(), F(12), WHITE, (rect.centerx, y), "midtop")
        text(SCREEN, f"LVL {mod.level}", F(11), CYAN, (rect.centerx, y + u(18)), "midtop")
        if mod.level >= mod.max_level:
            text(SCREEN, "MAX", F(11), AMBER, (rect.centerx, y + u(34)), "midtop")
        elif mod.level >= self.modules.max_allowed_level:
            need = mod.level * 3 - len(self.modules.completed_stages)
            text(SCREEN, f"GESPERRT: noch {need} Stufen", F(9), RED,
                 (rect.centerx, y + u(34)), "midtop")
        else:
            col = GREEN if self.modules.credits >= mod.cost else RED
            text(SCREEN, f"{mod.cost} Cr", F(12), col, (rect.centerx, y + u(34)), "midtop")

    def draw_research(self):
        self._draw_menu_backdrop()
        self._ui = self._layout_research()
        W, H = ui_kit.W, ui_kit.H
        self._draw_header("FORSCHUNGSLABOR", CYAN)
        text(SCREEN, f"CREDITS: {self.modules.credits:,} Cr", F(13), GREEN,
             (W // 2, margin() + max(u(40), min(W, H) // 14) + u(10)), "midtop")
        for bid, b in self._ui.items():
            if bid.startswith("res_") and bid != "res_back":
                self._draw_module_card(b.rect, bid[4:], pressed=self._pressed(bid), big=True)
        draw_btn(SCREEN, self._ui["res_back"], pressed=self._pressed("res_back"))
        draw_btn(SCREEN, self._ui["snd_res"], pressed=self._pressed("snd_res"))

    def draw_stages(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        self._ui = self._layout_stages()
        if self.world_bg is not None:
            img = self._fit_surf(self.world_bg, "world_bg")
            SCREEN.blit(img, ((W - img.get_width()) // 2, (H - img.get_height()) // 2))
            overlay(SCREEN, 70)
        else:
            SCREEN.fill(VOID)
            grid_bg(SCREEN, self.elapsed)
        self._draw_header("GALAXY MAP", ICE)
        draw_btn(SCREEN, self._ui["stg_back"], pressed=self._pressed("stg_back"))
        draw_btn(SCREEN, self._ui["snd_stg"], pressed=self._pressed("snd_stg"))
        pos = self._stage_positions()
        r = max(u(26), int(min(W, H) * 0.055))
        order = sorted(pos.keys())
        for a, b2 in zip(order, order[1:]):
            pygame.draw.line(SCREEN, LINE, pos[a], pos[b2], max(1, u(2)))
        for sector, (sx, sy) in pos.items():
            if sector < self.modules.highest_campaign:
                color = GREEN
            elif sector == self.modules.highest_campaign:
                color = CYAN
            else:
                color = MUTED
            if self.selected_sector == sector:
                pygame.draw.circle(SCREEN, color, (sx, sy), r + u(8), max(2, u(3)))
                pygame.draw.circle(SCREEN, color, (sx, sy), r, 2)
            else:
                pygame.draw.circle(SCREEN, color, (sx, sy), r, 2)
                pygame.draw.circle(SCREEN, color, (sx, sy), max(2, u(5)))
            text(SCREEN, SECTOR_DATA[sector]["name"], F(10), color, (sx, sy + r + u(8)), "midtop")
        if self.selected_sector > 0:
            overlay(SCREEN, 110)
            rect = self._stage_sheet_rect
            panel(SCREEN, rect, fill=(2, 5, 12), border=VIOLET, radius=u(16), width=max(2, u(3)))
            pygame.draw.rect(SCREEN, DIM, rect.inflate(-u(10), -u(10)), 1, border_radius=u(12))
            name = SECTOR_DATA[self.selected_sector]["name"]
            neon_text(SCREEN, f"SEKTOR {self.selected_sector} · {name}", F(15), VIOLET,
                      (rect.centerx, rect.y + u(10)), "midtop", 1)
            for bid, b in self._ui.items():
                if bid.startswith("stage_"):
                    self._draw_stage_cell(b.rect, int(bid[6:]), pressed=self._pressed(bid))
            draw_btn(SCREEN, self._ui["stg_close"], pressed=self._pressed("stg_close"))

    def _draw_stage_cell(self, rect, stage, pressed=False):
        sector = self.selected_sector
        is_completed = (sector, stage) in self.modules.completed_stages
        is_unlocked = (sector < self.modules.highest_campaign or
                       (sector == self.modules.highest_campaign and stage <= self.modules.highest_stage))
        is_boss = stage == 15
        is_semi = stage in (5, 10)
        if is_completed:
            border, fill, inner = GREEN, (10, 30, 20), (5, 15, 10)
        elif is_unlocked:
            border, fill, inner = VIOLET, (20, 10, 35), (10, 5, 20)
        else:
            border, fill, inner = DIM, (5, 5, 10), (2, 2, 5)
        if is_boss:
            border = AMBER if is_unlocked else RED
        elif is_semi:
            border = VIOLET if is_unlocked else MAGENTA
        if pressed:
            border = WHITE
        cut = max(4, int(min(rect.w, rect.h) * 0.16))
        x, y, w, h = rect.x, rect.y, rect.w, rect.h
        outer = [(x + cut, y), (x + w - cut, y), (x + w, y + cut), (x + w, y + h - cut),
                 (x + w - cut, y + h), (x + cut, y + h), (x, y + h - cut), (x, y + cut)]
        pygame.draw.polygon(SCREEN, fill, outer)
        pygame.draw.polygon(SCREEN, border, outer, max(2, u(3)))
        ix, iy, iw, ih = rect.inflate(-u(10), -u(10))
        ic = max(3, cut - u(2))
        innerp = [(ix + ic, iy), (ix + iw - ic, iy), (ix + iw, iy + ic), (ix + iw, iy + ih - ic),
                  (ix + iw - ic, iy + ih), (ix + ic, iy + ih), (ix, iy + ih - ic), (ix, iy + ic)]
        pygame.draw.polygon(SCREEN, inner, innerp, 1)
        if is_boss or is_semi:
            label = "BOSS" if is_boss else "ELITE"
            lab_col = AMBER if (is_boss and is_unlocked) else (RED if is_boss else MAGENTA)
            text(SCREEN, label, F(9), lab_col, (rect.centerx, rect.y + u(8)), "midtop")
            text(SCREEN, str(stage), F(14), WHITE if is_unlocked else MUTED,
                 (rect.centerx, rect.centery + u(6)), "center")
        else:
            text(SCREEN, str(stage), F(16), WHITE if is_unlocked else MUTED,
                 rect.center, "center")

    def draw_skill_tree(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        self._draw_menu_backdrop()
        isz = max(u(40), min(W, H) // 14)
        top = m + isz + u(12)
        bottom = H - int(H * 0.24) - u(14)
        cores = self.modules.data_cores
        self.nexus.draw(SCREEN, self.elapsed, self.skills, cores, SKILL_TREE, top, bottom)
        self._ui = self._layout_skilltree()
        draw_btn(SCREEN, self._ui["nex_back"], pressed=self._pressed("nex_back"))
        neon_text(SCREEN, "SKILL-NEXUS", F(17), AMBER, (W // 2, m + isz // 2), "center", 1)
        text(SCREEN, f"DATA CORES: {cores}", F(12), GREEN if cores > 0 else RED,
             (W - m - u(6), m + isz // 2), "midright")
        if not self.nexus.selected:
            text(SCREEN, "Knoten antippen, um Details zu sehen", F(10), MUTED,
                 (W // 2, H - int(H * 0.24) - u(24)), "midtop")

    def draw_settings(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        self._draw_menu_backdrop()
        self._ui = self._layout_settings()
        self._draw_header("EINSTELLUNGEN", VIOLET)
        toggles = {"set_sound": not SFX.muted,
                   "set_full": bool(pygame.display.is_fullscreen()),
                   "set_debug": self.debug_mode}
        for bid, b in self._ui.items():
            if bid.startswith("set_") and bid != "set_back":
                draw_btn(SCREEN, b, pressed=self._pressed(bid))
                trect = pygame.Rect(b.rect.right - u(66) - u(12), b.rect.centery - u(14), u(56), u(28))
                draw_toggle(SCREEN, trect, toggles.get(bid, False))
        draw_btn(SCREEN, self._ui["set_back"], pressed=self._pressed("set_back"))
        info_y = getattr(self, "_settings_rows_end", H // 2) + u(10)
        info = [VERSION,
                "Optimiert fuer Touch & Hochformat.",
                "Tastatur ist optional: ESC = Pause · M = Sound · Q = Uebertaktung."]
        f = F(10)
        y = info_y
        for ln in info:
            text(SCREEN, ln, f, MUTED, (W // 2, y), "midtop")
            y += int(f.get_height() * 1.4)

    def draw_pause_menu(self):
        overlay(SCREEN, 185)
        self._ui = self._layout_pause()
        rect = self._pause_rect
        panel(SCREEN, rect, fill=(5, 10, 21), border=CYAN, radius=u(16))
        neon_text(SCREEN, "PAUSIERT", F(19), WHITE, (rect.centerx, rect.y + u(14)), "midtop", 1)
        for bid, b in self._ui.items():
            draw_btn(SCREEN, b, pressed=self._pressed(bid))

    def _view(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        isz = max(u(40), min(W, H) // 14)
        top = m + isz + u(12)
        if not self.idle_mode:
            top += u(18) + u(10)
        deck = btn_h() + m + u(16)
        avail_w = W - u(10)
        avail_h = max(50, H - top - deck)
        s = min(avail_w / WORLD_W, avail_h / WORLD_H)
        aw, ah = int(WORLD_W * s), int(WORLD_H * s)
        ox, oy = (W - aw) // 2, top + (avail_h - ah) // 2
        return s, ox, oy, aw, ah

    def draw_playing(self):
        W, H = ui_kit.W, ui_kit.H
        SCREEN.fill(VOID)          # Full-Flush: keine Restpixel aus dem Vorbild-Screen
        combat = self.idle_combat if self.idle_mode else self.pve
        s, ox, oy, aw, ah = self._view()
        rect = pygame.Rect(ox, oy, aw, ah)
        ch_bg = None
        if not self.idle_mode and self.bg_chapter[0] is not None:
            idx = 0 if combat.stage_id <= 5 else (1 if combat.stage_id <= 10 else 2)
            ch_bg = self.bg_chapter[idx]
        if ch_bg is not None:
            key = ("chap", idx, aw, ah)
            img = self._fit_cache.get(key)
            if img is None:
                img = pygame.transform.smoothscale(ch_bg, (aw, ah))
                self._fit_cache[key] = img
            SCREEN.blit(img, rect.topleft)
            dim = self._fit_cache.get(("dim", aw, ah))
            if dim is None:
                dim = pygame.Surface((aw, ah), pygame.SRCALPHA)
                dim.fill((0, 0, 0, 50))
                self._fit_cache[("dim", aw, ah)] = dim
            SCREEN.blit(dim, rect.topleft)
        else:
            SCREEN.set_clip(rect)
            grid_bg(SCREEN, self.elapsed)
            SCREEN.set_clip(None)
        SCREEN.set_clip(rect)
        try:
            self._draw_world(combat, s, ox, oy)
        finally:
            SCREEN.set_clip(None)
        col = (30, 60, 88)
        cl, lw = u(16), max(2, u(2))
        for (cx, cy, dx, dy) in ((rect.left, rect.top, 1, 1), (rect.right, rect.top, -1, 1),
                                 (rect.left, rect.bottom, 1, -1), (rect.right, rect.bottom, -1, -1)):
            pygame.draw.line(SCREEN, col, (cx, cy + dy * cl), (cx, cy), lw)
            pygame.draw.line(SCREEN, col, (cx, cy), (cx + dx * cl, cy), lw)
        m = margin()
        isz = max(u(40), min(W, H) // 14)
        if not self.idle_mode:
            hp_ratio = combat.player_hp / max(1.0, combat.max_player_hp)
            bar = pygame.Rect(m, m + isz + u(10), W - 2 * m, u(16))
            pygame.draw.rect(SCREEN, (20, 30, 45), bar, border_radius=u(8))
            hpc = GREEN if hp_ratio > 0.3 else RED
            pygame.draw.rect(SCREEN, hpc, (bar.x, bar.y, int(bar.w * hp_ratio), bar.h),
                             border_radius=u(8))
            pygame.draw.rect(SCREEN, CYAN_SOFT, bar, 2, border_radius=u(8))
            text(SCREEN, f"HÜLLE {int(combat.player_hp)} / {int(combat.max_player_hp)}",
                 F(10), WHITE, bar.center, "center")
            neon_text(SCREEN, f"CREDITS: {combat.credits:,}", F(12), GREEN,
                      (W - m, m + u(2)), "topright")
            neon_text(SCREEN, f"SEKTOR {combat.campaign_id} · STUFE {combat.stage_id:02d}",
                      F(10), AMBER, (W - m, m + u(24)), "topright")
        else:
            neon_text(SCREEN, f"IDLE-BEUTE: +{combat.idle_loot_earned:,} Cr", F(12), GREEN,
                      (W - m, m + u(2)), "topright")
            neon_text(SCREEN, f"GESAMT: {self.modules.credits + combat.credits:,} Cr", F(10),
                      MUTED, (W - m, m + u(24)), "topright")
        self._ui = self._layout_hud()
        draw_btns(SCREEN, self._ui, self._ptr["id"] if self._ptr else None)
        if self.show_upgrades:
            overlay(SCREEN, 185)
            ui_sheet, sheet_rect = self._layout_upgrades()
            self._ui = ui_sheet
            panel(SCREEN, sheet_rect, fill=(5, 10, 21), border=MAGENTA, radius=u(16))
            neon_text(SCREEN, "MODULE & UPGRADES", F(15), MAGENTA,
                      (sheet_rect.centerx, sheet_rect.y + u(12)), "midtop", 1)
            text(SCREEN, f"CREDITS: {self.modules.credits:,} Cr", F(11), GREEN,
                 (sheet_rect.x + u(14), sheet_rect.y + u(18)))
            for bid, b in ui_sheet.items():
                if bid.startswith("upg_") and bid != "upg_close":
                    self._draw_module_card(b.rect, bid[4:], pressed=self._pressed(bid))
            draw_btn(SCREEN, ui_sheet["upg_close"], pressed=self._pressed("upg_close"))

    def _draw_world(self, combat, s, ox, oy):
        def T(x, y):
            return (ox + x * s, oy + y * s)

        ship_x, ship_y = self.movement.get_position(self.fortress.x, self.fortress.y)
        angle = self.movement.get_angle()
        ex, ey = T(ship_x + self.debug_engine_offset[0], ship_y + self.debug_engine_offset[1])
        self.engine_effect.set_position(ex, ey)
        self.engine_effect.draw(SCREEN)

        sx, sy = T(ship_x, ship_y)
        schild_lvl = self.modules.get("schild").level
        if schild_lvl > 1:
            rad = (60 + schild_lvl * 5) * s
            pulse = math.sin(self.elapsed * 4) * 3
            pygame.draw.circle(SCREEN, (0, 255, 255), (int(sx), int(sy)), int(rad + pulse), 2)
            pygame.draw.circle(SCREEN, (0, 180, 200), (int(sx), int(sy)), int(rad + pulse + 5 * s), 1)

        base = getattr(self.fortress, "_base_image", None)
        if base:
            img = _scaled(_ship_scaled, "ship", base, s)
            rot = pygame.transform.rotate(img, angle)
            SCREEN.blit(rot, rot.get_rect(center=(int(sx), int(sy))))
        else:
            orig = (self.fortress.x, self.fortress.y)
            self.fortress.x, self.fortress.y = sx, sy
            self.fortress.draw(SCREEN)
            self.fortress.x, self.fortress.y = orig

        for enemy in combat.enemies:
            img0 = load_enemy_image(enemy.enemy_type)
            img = _scaled(_enemy_scaled, enemy.enemy_type, img0, s)
            ang_deg = math.degrees(math.atan2(ship_y - enemy.y, ship_x - enemy.x))
            rot = pygame.transform.rotate(img, -ang_deg)
            ex, ey = T(enemy.x, enemy.y)
            SCREEN.blit(rot, rot.get_rect(center=(int(ex), int(ey))))
            bw, bh = 40 * s, 4 * s
            bar = pygame.Rect(int(ex - bw / 2), int(ey - 35 * s), max(2, int(bw)), max(2, int(bh)))
            pygame.draw.rect(SCREEN, (30, 30, 30), bar)
            pygame.draw.rect(SCREEN, GREEN, (bar.x, bar.y,
                                             max(0, int(bar.w * enemy.hp / max(1, enemy.max_hp))),
                                             bar.h))

        target = min(combat.enemies, key=lambda e: e.x) if combat.enemies else None
        kanonen_lvl = self.modules.get("kanonen").level
        current_offset = self.debug_cannon_offset if self.debug_mode else CANNON_OFFSETS[0]
        cox, coy = current_offset
        cx, cy = T(ship_x + cox, ship_y + coy)
        ang_deg = math.degrees(math.atan2(target.y - ship_y - coy, target.x - ship_x - cox)) if target else 0
        turret0 = load_kanonen_image(kanonen_lvl)
        turret = _scaled(_kanonen_scaled, kanonen_lvl, turret0, s)
        rot = pygame.transform.rotate(turret, -ang_deg)
        sw, sh = int(30 * s), int(15 * s)
        shadow = pygame.Surface((max(2, sw), max(2, sh)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 100), (0, 0, sw, sh))
        SCREEN.blit(shadow, (cx - sw // 2, cy + int(5 * s)))
        SCREEN.blit(rot, rot.get_rect(center=(int(cx), int(cy))))

        for p in combat.projectiles:
            x1, y1 = T(p.x - p.vx * 20, p.y - p.vy * 20)
            x2, y2 = T(p.x, p.y)
            pygame.draw.line(SCREEN, p.color, (x1, y1), (x2, y2), max(1, int(p.size * 2.5 * s)))
            pygame.draw.line(SCREEN, (255, 255, 255), (x1, y1), (x2, y2),
                             max(1, int(p.size * 0.6 * s)))
            pygame.draw.circle(SCREEN, (255, 255, 255), (int(x2), int(y2)), max(1, int(p.size * s)))

        for part in combat.particles:
            alpha = part.life / max(0.001, part.max_life)
            r = int(part.size * alpha * s)
            if r > 0:
                px, py = T(part.x, part.y)
                pygame.draw.circle(SCREEN, part.color, (int(px), int(py)), r)

        for mf in combat.muzzle_flashes:
            mx, my, ang, timer = mf
            mpx, mpy = T(mx, my)
            fr = (8 + timer * 100) * s
            pygame.draw.circle(SCREEN, (255, 255, 200), (int(mpx), int(mpy)), int(fr))
            pygame.draw.circle(SCREEN, (255, 255, 255), (int(mpx), int(mpy)), int(fr / 2))

        for dn in getattr(combat, "damage_numbers", []):
            alpha = max(0, min(255, int(255 * dn.life / max(0.001, dn.max_life))))
            f = F((20 if dn.big else 14) * s)
            surf = f.render(str(dn.value), True, dn.color)
            surf.set_alpha(alpha)
            dx, dy = T(dn.x, dn.y)
            SCREEN.blit(surf, surf.get_rect(center=(int(dx), int(dy))))

    def _draw_debug(self):
        s, ox, oy, aw, ah = self._view()
        cx, cy = ox + (self.fortress.x + 0) * s, oy + self.fortress.y * s
        ship_x, ship_y = self.movement.get_position(self.fortress.x, self.fortress.y)
        cx, cy = ox + ship_x * s, oy + ship_y * s
        pygame.draw.line(SCREEN, RED, (cx - 20, cy), (cx + 20, cy), 2)
        pygame.draw.line(SCREEN, RED, (cx, cy - 20), (cx, cy + 20), 2)
        tx, ty = ox + (ship_x + self.debug_cannon_offset[0]) * s, oy + (ship_y + self.debug_cannon_offset[1]) * s
        pygame.draw.circle(SCREEN, GREEN, (int(tx), int(ty)), 20, 1)
        text(SCREEN, "DEBUG: TAB = Ziel · Pfeile = justieren", F(9), RED,
             (ui_kit.W // 2, ui_kit.H - btn_h() - margin() - u(26)), "midtop")

    def _video_overlay(self, frames, timer, speed=1.0):
        """Zeichnet das aktuelle Videoframe; True, wenn beendet."""
        W, H = ui_kit.W, ui_kit.H
        if not frames:
            return True
        full = len(frames) / 30.0
        idx = min(int(timer * 30), len(frames) - 1)
        frame = self._video_frame(frames, idx)
        SCREEN.fill((0, 0, 0))
        SCREEN.blit(frame, ((W - frame.get_width()) // 2, (H - frame.get_height()) // 2))
        return timer >= full

    def draw_defeat(self):
        W, H = ui_kit.W, ui_kit.H
        self._ui = self._layout_defeat()
        ended = self._video_overlay(self.defeat_frames, self.defeat_timer)
        if not ended:
            self._draw_skip_hint()
            return
        if not self.defeat_frames:
            SCREEN.fill((40, 0, 8))
        overlay(SCREEN, 130)
        neon_text(SCREEN, "SCHIFF ZERSTÖRT", F(24), RED, (W // 2, int(H * 0.34)), "midtop", 2)
        text(SCREEN, f"SEKTOR {self.pve.campaign_id} · STUFE {self.pve.stage_id:02d}",
             F(13), WHITE, (W // 2, int(H * 0.34) + u(40)), "midtop")
        for bid, b in self._ui.items():
            draw_btn(SCREEN, b, pressed=self._pressed(bid))

    def draw_stage_clear(self):
        W, H = ui_kit.W, ui_kit.H
        self._ui = self._layout_clear()
        if self.victory_frames:
            ended = self._video_overlay(self.victory_frames, self.victory_timer)
            if not ended:
                self._draw_skip_hint()
                return
            overlay(SCREEN, 90)
        else:
            overlay(SCREEN, 150)
        neon_text(SCREEN, "STUFE GESCHAFFT!", F(26), GREEN, (W // 2, int(H * 0.44)), "midtop", 2)
        neon_text(SCREEN, f"+{self.last_stage_reward:,} CREDITS", F(16), WHITE,
                  (W // 2, int(H * 0.44) + u(48)), "midtop", 1)
        for bid, b in self._ui.items():
            draw_btn(SCREEN, b, pressed=self._pressed(bid))

    def draw_intro(self):
        W, H = ui_kit.W, ui_kit.H
        self._ui = self._layout_intro()
        ended = self._video_overlay(self.intro_frames, self.intro_timer)
        if not ended:
            self._draw_skip_hint()

    def _draw_skip_hint(self):
        W, H = ui_kit.W, ui_kit.H
        f = F(11)
        label = "TIPPEN = ÜBERSPRINGEN"
        rect = f.size(label)
        bar = pygame.Rect((W - rect[0]) // 2 - u(14), H - u(54) - u(10), rect[0] + u(28), u(34))
        pygame.draw.rect(SCREEN, (0, 0, 0), bar, border_radius=u(8))
        pygame.draw.rect(SCREEN, (60, 80, 100), bar, 1, border_radius=u(8))
        text(SCREEN, label, f, ICE, bar.center, "center")

    def draw_loading(self):
        W, H = ui_kit.W, ui_kit.H
        m = margin()
        pw = min(W - 2 * m, u(460))
        rect = pygame.Rect((W - pw) // 2, int(H * 0.38), pw, u(120))
        panel(SCREEN, rect, fill=(3, 8, 17), border=(16, 42, 60), radius=u(12))
        neon_text(SCREEN, "SYSTEM INITIALIZATION", F(14), WHITE,
                  (rect.centerx, rect.y + u(14)), "midtop", 1)
        prog = min(1.0, self.loading_time / 2.5)
        bar = pygame.Rect(rect.x + u(30), rect.y + u(64), pw - u(60), u(14))
        pygame.draw.rect(SCREEN, (10, 25, 40), bar, border_radius=u(6))
        pygame.draw.rect(SCREEN, CYAN, (bar.x, bar.y, int(bar.w * prog), bar.h), border_radius=u(6))
        pygame.draw.rect(SCREEN, LINE, bar, 2, border_radius=u(6))
        text(SCREEN, f"LOADING… {int(prog * 100)}%", F(10), CYAN,
             (rect.centerx, rect.y + u(90)), "midtop")

    def _draw_message(self):
        W, H = ui_kit.W, ui_kit.H
        if self.message_timer <= 0 or not self.message:
            return
        f = F(12)
        lines = wrap_text(self.message, f, W - 2 * margin() - u(30))
        h = int(f.get_height() * 1.3) * len(lines) + u(18)
        rect = pygame.Rect(0, 0, W - 2 * margin(), h)
        rect.center = (W // 2, H - btn_h() - margin() - u(44))
        panel(SCREEN, rect, fill=(5, 10, 21), border=AMBER, radius=u(10))
        y = rect.y + u(9)
        for ln in lines:
            text(SCREEN, ln, f, WHITE, (rect.centerx, y), "midtop")
            y += int(f.get_height() * 1.3)

    def draw(self):
        W, H = SCREEN.get_size()
        set_screen(W, H)
        st = self.state
        if st == self.INTRO:
            self.draw_intro()
            pygame.display.flip()
            return
        if st == self.DEFEAT:
            self.draw_defeat()
            pygame.display.flip()
            return
        if st in (self.MENU, self.RESEARCH, self.SETTINGS, self.STAGES,
                  self.SKILLTREE, self.LOADING):
            self._draw_menu_backdrop()
        if st == self.LOADING:
            self.draw_loading()
        elif st == self.MENU:
            self.draw_menu()
        elif st == self.RESEARCH:
            self.draw_research()
        elif st == self.SETTINGS:
            self.draw_settings()
        elif st == self.STAGES:
            self.draw_stages()
        elif st == self.SKILLTREE:
            self.draw_skill_tree()
        elif st in (self.PLAYING, self.PAUSED) or (st == self.STAGE_CLEAR and not self.victory_frames):
            self.draw_playing()
        if st == self.PAUSED:
            self.draw_pause_menu()
        if st == self.STAGE_CLEAR:
            self.draw_stage_clear()
        if self.debug_mode and st == self.PLAYING:
            self._draw_debug()
        self._draw_message()
        pygame.display.flip()


_ship_scaled = {}

if __name__ == "__main__":
    Game().run()
