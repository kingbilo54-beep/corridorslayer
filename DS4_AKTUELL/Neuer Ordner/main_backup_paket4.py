import math
import sys
import pygame
import os
import random
from fortress_2d import Fortress
from module_system import FortressModules
from pve_system import PvECombat
from effects.engine_effect import EngineEffect
from ship_movement import ShipMovement

pygame.init()

WIDTH, HEIGHT = 960, 540
FPS = 60

SCREEN = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("CORRIDOR SLAYER // MOBILE LANDSCAPE")
CLOCK = pygame.time.Clock()

VOID = (3, 6, 14)
PANEL = (8, 15, 29)
LINE = (25, 48, 70)
CYAN = (0, 255, 255)
CYAN_SOFT = (23, 145, 177)
ICE = (203, 247, 255)
WHITE = (232, 242, 250)
MUTED = (91, 119, 145)
DIM = (46, 68, 91)
VIOLET = (153, 94, 255)
MAGENTA = (255, 62, 177)
GREEN = (77, 255, 181)
RED = (255, 77, 100)
AMBER = (255, 190, 76)

FONT_TINY = pygame.font.SysFont("segoeui", 12, bold=True)
FONT_SMALL = pygame.font.SysFont("segoeui", 14, bold=True)
FONT_MED_BOLD = pygame.font.SysFont("segoeui", 20, bold=True)
FONT_BIG = pygame.font.SysFont("segoeui", 36, bold=True)
FONT_HUGE = pygame.font.SysFont("segoeui", 48, bold=True)

ENEMY_FOLDER = r"C:\\Users\\bsahi\\Desktop\\corridorSlayers\\DS4\\enemys"
MODULE_FOLDER = r"C:\\Users\\bsahi\\Desktop\\corridorSlayers\\DS4\\modules"
KANONEN_FOLDER = r"C:\\Users\\bsahi\\Desktop\\corridorSlayers\\DS4\\kanonen"

enemy_images = {}
module_images = {}
kanonen_images = {}

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
        pass # Transparent lassen
        kanonen_images[level] = surf
        return surf

CANNON_OFFSETS = [(4, -14)]

def text(surface, value, font, color, pos, anchor="topleft"):
    image = font.render(str(value), True, color)
    rect = image.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(image, rect)
    return rect

def neon_text(surface, value, font, color, pos, anchor="topleft", glow_strength=2):
    glow_surf = font.render(str(value), True, color)
    for alpha in [120, 80, 40]:
        glow_surf.set_alpha(alpha)
        for dx in range(-glow_strength, glow_strength + 1):
            for dy in range(-glow_strength, glow_strength + 1):
                if dx == 0 and dy == 0: continue
                rect = glow_surf.get_rect()
                setattr(rect, anchor, (pos[0]+dx, pos[1]+dy))
                surface.blit(glow_surf, rect)
    image = font.render(str(value), True, WHITE)
    rect = image.get_rect()
    setattr(rect, anchor, pos)
    surface.blit(image, rect)
    return rect

def panel(surface, rect, fill=PANEL, border=LINE, radius=12, corner=18):
    if fill:
        pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=radius)

def draw_grid(surface, elapsed):
    surface.fill(VOID)
    spacing = 40
    for x in range(0, WIDTH, spacing):
        pygame.draw.line(surface, (8, 17, 30), (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, spacing):
        pygame.draw.line(surface, (8, 17, 30), (0, y), (WIDTH, y), 1)

def draw_scanline(surface, elapsed):
    y = int((elapsed * 38) % (HEIGHT + 80)) - 40
    if 0 <= y < HEIGHT:
        pygame.draw.rect(surface, (12, 35, 50), (0, y, WIDTH, 4))

def draw_button(surface, rect, label, subtitle, mouse_pos, elapsed, accent=CYAN, enabled=True):
    hovered = enabled and rect.collidepoint(mouse_pos)
    fill = (5, 17, 29) if hovered else (3, 10, 20)
    pygame.draw.rect(surface, fill, rect, border_radius=7)
    border = accent if hovered else tuple(max(18, int(c * 0.52)) for c in accent)
    pygame.draw.rect(surface, border, rect, 2 if hovered else 1, border_radius=7)
    
    if hovered:
        neon_text(surface, label, FONT_MED_BOLD, accent, (rect.centerx, rect.centery - 8), "center", glow_strength=1)
        text(surface, subtitle, FONT_TINY, WHITE, (rect.centerx, rect.centery + 10), "center")
    else:
        text(surface, label, FONT_MED_BOLD, WHITE, (rect.centerx, rect.centery - 8), "center")
        text(surface, subtitle, FONT_TINY, accent, (rect.centerx, rect.centery + 10), "center")

def draw_single_button(surface, rect, label, mouse_pos, elapsed, accent=CYAN, enabled=True):
    hovered = enabled and rect.collidepoint(mouse_pos)
    fill = (5, 17, 29) if hovered else (3, 10, 20)
    pygame.draw.rect(surface, fill, rect, border_radius=7)
    border = accent if hovered else tuple(max(18, int(c * 0.52)) for c in accent)
    pygame.draw.rect(surface, border, rect, 2 if hovered else 1, border_radius=7)
    if hovered:
        neon_text(surface, label, FONT_MED_BOLD, accent, (rect.centerx, rect.centery), "center", glow_strength=1)
    else:
        text(surface, label, FONT_MED_BOLD, WHITE, (rect.centerx, rect.centery), "center")

class Game:
    STAGE_CLEAR = "stage_clear"
    INTRO = "intro"
    LOADING = "loading"
    MENU = "menu"
    PLAYING = "playing"
    STAGES = "stages"
    SETTINGS = "settings"
    RESEARCH = "research"
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
        
        self.video_frames = []
        self.final_frame_surface = None
        self.intro_timer = 0.0
        self.defeat_frames = []
        self.defeat_timer = 0.0
        self.settings_return_state = self.MENU 
        
        self.selected_sector = 0 
        self.message = ""
        self.message_timer = 0.0
        
        try:
            self.menu_bg = pygame.image.load("menu_bg.png").convert()
            self.menu_bg = pygame.transform.smoothscale(self.menu_bg, (WIDTH, HEIGHT))
        except Exception:
            self.menu_bg = None
        try:
            self.world_bg = pygame.image.load('bg_world.jpg').convert()
            self.world_bg = pygame.transform.smoothscale(self.world_bg, (WIDTH, HEIGHT))
        except Exception as e:
            print(f'bg_world.jpg nicht gefunden: {e}')
            self.world_bg = None
            
        try:
            self.logo_img = pygame.image.load("logo.png").convert_alpha()
            logo_w = 500
            logo_h = int(self.logo_img.get_height() * (logo_w / self.logo_img.get_width()))
            self.logo_img = pygame.transform.smoothscale(self.logo_img, (logo_w, logo_h))
        except Exception:
            self.logo_img = None
        
        try:
            import cv2
            cap = cv2.VideoCapture("intro2.mp4")
            while True:
                ret, frame = cap.read()
                if not ret: break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surf = pygame.image.frombuffer(frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB")
                surf = pygame.transform.smoothscale(surf, (WIDTH, HEIGHT))
                self.video_frames.append(surf)
            cap.release()
            if self.video_frames:
                self.final_frame_surface = self.video_frames[-1]
            
            cap = cv2.VideoCapture("defeat_animation.mp4")
            while True:
                ret, frame = cap.read()
                if not ret: break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surf = pygame.image.frombuffer(frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB")
                surf = pygame.transform.smoothscale(surf, (WIDTH, HEIGHT))
                self.defeat_frames.append(surf)
            cap.release()
        except Exception:
            self.state = self.MENU

        
        # Lade die Hintergründe (stellen sicher, dass sie im selben Ordner liegen)
        try:
            self.bg_chapter_1_part_1 = pygame.transform.smoothscale(pygame.image.load("bg_chapter_1_part_1.jpg").convert(), (WIDTH, HEIGHT))
            self.bg_chapter_1_part_2 = pygame.transform.smoothscale(pygame.image.load("bg_chapter_1_part_2.jpg").convert(), (WIDTH, HEIGHT))
            self.bg_chapter_1_part_3 = pygame.transform.smoothscale(pygame.image.load("bg_chapter_1_part_3.jpg").convert(), (WIDTH, HEIGHT))
            print("✅ Hintergründe erfolgreich geladen!")
        except Exception as e:
            print(f"⚠️ FEHLER beim Laden der Hintergründe: {e}")
            print("Stelle sicher, dass die Dateien bg_chapter_1_part_1.jpg, bg_chapter_1_part_2.jpg und bg_chapter_1_part_3.jpg im Ordner liegen!")
            self.bg_chapter_1_part_1 = None
            self.bg_chapter_1_part_2 = None
            self.bg_chapter_1_part_3 = None

        
        # Victory Video laden
        self.victory_frames = []
        self.victory_timer = 0.0
        try:
            import cv2
            cap = cv2.VideoCapture("victory_screen.mp4")
            while True:
                ret, frame = cap.read()
                if not ret: break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                surf = pygame.image.frombuffer(frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB")
                surf = pygame.transform.smoothscale(surf, (WIDTH, HEIGHT))
                self.victory_frames.append(surf)
            cap.release()
            if self.victory_frames:
                print(f"✅ Victory Video geladen ({len(self.victory_frames)} Frames).")
        except Exception as e:
            print(f"⚠️ Victory Video nicht gefunden: {e}")

        self.fortress = Fortress(120, 270, level=1) 
        self.modules = FortressModules()
        self.engine_effect = EngineEffect(0, 0)
        self.movement = ShipMovement()
        
        self.idle_combat = PvECombat(is_idle=True, campaign_id=1, stage_id=1, ship_level=self.modules.ship_level)
        self.pve = PvECombat(is_idle=False, campaign_id=1, stage_id=1, ship_level=self.modules.ship_level)

        self.idle_mode = True
        self.stage_deployed = False
        self.show_upgrades = False

        btn_w = 360
        btn_h = 38
        start_y = 250
        spacing = 44
        cx = WIDTH // 2

        self.start_idle_button = pygame.Rect(cx - btn_w//2, start_y, btn_w, btn_h)
        self.research_button = pygame.Rect(cx - btn_w//2, start_y + spacing, btn_w, btn_h)
        self.stages_button = pygame.Rect(cx - btn_w//2, start_y + spacing*2, btn_w, btn_h)
        self.settings_button = pygame.Rect(cx - btn_w//2, start_y + spacing*3, btn_w, btn_h)
        self.quit_button = pygame.Rect(cx - btn_w//2, start_y + spacing*4, btn_w, btn_h)
        
        self.btn_back = pygame.Rect(280, 460, 400, 50)
        self.btn_back_settings = pygame.Rect(280, 460, 400, 50)
        
        self.stage_cards = {i: pygame.Rect(280, 120 + (i - 1) * 65, 400, 50) for i in range(1, 6)}
        
        self.btn_open_upgrades = pygame.Rect(20, 480, 160, 40)
        self.btn_back_play = pygame.Rect(780, 480, 160, 40)
        
        self.pause_rect = pygame.Rect(280, 120, 400, 300)
        self.btn_resume = pygame.Rect(330, 200, 300, 40)
        self.btn_pause_settings = pygame.Rect(330, 260, 300, 40)
        self.btn_give_up = pygame.Rect(330, 320, 300, 40)

        self.popup_rect = pygame.Rect(180, 70, 600, 400)
        self.btn_close_popup = pygame.Rect(self.popup_rect.right - 40, self.popup_rect.top + 10, 30, 30)
        
        self.research_slots = {}
        keys = list(self.modules.modules.keys())
        for i, key in enumerate(keys):
            col = i % 3
            row = i // 3
            rect = pygame.Rect(40 + col * 300, 120 + row * 180, 280, 160)
            self.research_slots[key] = rect

        self.btn_defeat_restart = pygame.Rect(50, 400, 400, 140) 
        self.btn_defeat_menu = pygame.Rect(510, 400, 400, 140)    

        self._sync_modules_to_combat()

    def _sync_modules_to_combat(self):
        for combat in (self.idle_combat, self.pve):
            combat.dmg_level = self.modules.get("kanonen").level
            combat.speed_level = self.modules.get("antrieb").level
            combat.cannon_count_level = min(8, 1 + self.modules.get("kanonen").level // 2)
            combat.max_player_hp = 500.0 + (self.modules.get("schild").level - 1) * 100
            combat.player_hp = min(combat.player_hp, combat.max_player_hp)
            combat.hangar_level = self.modules.get("hangar").level
            combat.repair_level = self.modules.get("reparatur").level
            combat.ship_level = self.modules.ship_level

    def _collect_idle_loot(self):
        """Überweist gesammelte Idle-Credits in die persistente Wallet."""
        if self.idle_combat.credits > 0:
            self.modules.credits += self.idle_combat.credits
            self.idle_combat.credits = 0
            self.modules.save()

    def _restart_stage(self):
        """Startet die zuletzt gespielte Kampagnen-Stufe neu (nach Niederlage)."""
        campaign = self.selected_sector if self.selected_sector > 0 else self.pve.campaign_id
        stage = self.pve.stage_id
        self.pve = PvECombat(is_idle=False, campaign_id=campaign, stage_id=stage,
                             ship_level=self.modules.ship_level)
        self._sync_modules_to_combat()
        self.state = self.PLAYING

    def show_message(self, msg, duration=3.0):
        """Zeigt eine sichtbare Hinweiszeile unten am Bildschirm."""
        self.message = msg
        self.message_timer = duration

    def _draw_message(self):
        if self.message_timer <= 0 or not self.message:
            return
        surf = FONT_MED_BOLD.render(self.message, True, WHITE)
        pad = 20
        rect = surf.get_rect(center=(WIDTH // 2, HEIGHT - 105))
        bg = pygame.Rect(rect.x - pad, rect.y - 10, rect.width + pad * 2, rect.height + 20)
        panel(SCREEN, bg, fill=(5, 10, 21), border=AMBER, radius=10)
        SCREEN.blit(surf, rect)

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

    def handle_events(self):
        mouse = pygame.mouse.get_pos()
        
        if self.state == self.DEFEAT:
            if pygame.mouse.get_pressed()[0]:
                if self.btn_defeat_restart.collidepoint(mouse):
                    self._restart_stage()
                    return
                elif self.btn_defeat_menu.collidepoint(mouse):
                    self.state = self.MENU
                    return
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self._restart_stage()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = self.MENU
            return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._collect_idle_loot()
                self.running = False
                return

            if self.state == self.INTRO:
                if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                    self.state = self.MENU
                continue

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1: 
                    self.debug_mode = not self.debug_mode
                    print(f"DEBUG MODUS: {'AN' if self.debug_mode else 'AUS'}")
                    
                if event.key == pygame.K_ESCAPE:
                    if self.state == self.PLAYING:
                        self.state = self.PAUSED
                    elif self.show_upgrades:
                        self.show_upgrades = False
                    elif self.state in (self.STAGES, self.SETTINGS, self.RESEARCH):
                        if self.state == self.SETTINGS:
                            self.state = self.settings_return_state
                        else:
                            self.state = self.MENU

                if self.debug_mode and self.state == self.PLAYING:
                    if event.key == pygame.K_TAB:
                        self.debug_target = "engine" if self.debug_target == "cannon" else "cannon"
                        print(f"Debug-Ziel: {self.debug_target.upper()}")
                    
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                        dx = -1 if event.key == pygame.K_LEFT else (1 if event.key == pygame.K_RIGHT else 0)
                        dy = -1 if event.key == pygame.K_UP else (1 if event.key == pygame.K_DOWN else 0)
                        if self.debug_target == "cannon":
                            self.debug_cannon_offset[0] += dx
                            self.debug_cannon_offset[1] += dy
                            print(f"Kanone: ({self.debug_cannon_offset[0]}, {self.debug_cannon_offset[1]})")
                        else:
                            self.debug_engine_offset[0] += dx
                            self.debug_engine_offset[1] += dy
                            print(f"Antrieb: ({self.debug_engine_offset[0]}, {self.debug_engine_offset[1]})")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.debug_mode and self.state == self.PLAYING:
                    if event.button == 1: # Linksklick = Kanone
                        cx = self.fortress.x + self.debug_cannon_offset[0]
                        cy = self.fortress.y + self.debug_cannon_offset[1]
                        if math.hypot(mouse[0] - cx, mouse[1] - cy) < 35:
                            self.is_dragging_cannon = True
                            self.debug_target = "cannon"
                            print("Kanone angefasst.")
                            continue
                    elif event.button == 3: # Rechtsklick = Antrieb (großer Radius!)
                        ex = self.fortress.x + self.debug_engine_offset[0]
                        ey = self.fortress.y + self.debug_engine_offset[1]
                        if math.hypot(mouse[0] - ex, mouse[1] - ey) < 60:
                            self.is_dragging_engine = True
                            self.debug_target = "engine"
                            print("Antrieb angefasst.")
                            continue
                self.on_click(mouse)
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if self.is_dragging_cannon:
                    self.is_dragging_cannon = False
                    print(f"Kanone FINAL: ({self.debug_cannon_offset[0]}, {self.debug_cannon_offset[1]})")
                if self.is_dragging_engine:
                    self.is_dragging_engine = False
                    print(f"Antrieb FINAL: ({self.debug_engine_offset[0]}, {self.debug_engine_offset[1]})")
            
            elif event.type == pygame.MOUSEMOTION:
                if self.is_dragging_cannon:
                    self.debug_cannon_offset[0] = mouse[0] - self.fortress.x
                    self.debug_cannon_offset[1] = mouse[1] - self.fortress.y
                if self.is_dragging_engine:
                    self.debug_engine_offset[0] = mouse[0] - self.fortress.x
                    self.debug_engine_offset[1] = mouse[1] - self.fortress.y

    def on_click(self, pos):
        if self.state == self.MENU:
            if self.start_idle_button.collidepoint(pos):
                self.idle_mode = True
                self.idle_combat.stage_id = self.modules.highest_stage
                self._sync_modules_to_combat()
                self.state = self.PLAYING
            elif self.research_button.collidepoint(pos):
                self.state = self.RESEARCH
            elif self.stages_button.collidepoint(pos):
                self.state = self.STAGES
            elif self.settings_button.collidepoint(pos):
                self.settings_return_state = self.MENU
                self.state = self.SETTINGS
            elif self.quit_button.collidepoint(pos):
                self._collect_idle_loot()
                self.running = False

        elif self.state == self.RESEARCH:
            if self.btn_back.collidepoint(pos):
                self.state = self.MENU
                return
            for key, rect in self.research_slots.items():
                if rect.collidepoint(pos):
                    try:
                        self.modules.upgrade(key)
                        self._sync_modules_to_combat()
                    except ValueError as e:
                        self.show_message(str(e))
                    return

        elif self.state == self.STAGES:
            click_x, click_y = pos
            
            sector_data = {
                1: {"pos": (480, 400)},
                2: {"pos": (250, 250)},
                3: {"pos": (750, 280)},
                4: {"pos": (200, 100)},
                5: {"pos": (800, 120)}
            }
            
            if self.selected_sector == 0:
                for sector, data in sector_data.items():
                    sx, sy = data["pos"]
                    if math.hypot(click_x - sx, click_y - sy) < 30:
                        if sector <= self.modules.highest_campaign:
                            self.selected_sector = sector
                            return
                        else:
                            self.show_message(f"Sektor {sector} ist gesperrt! Schalte erst fruehere Sektoren frei.")
                            return
                            
                btn_back_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 60, 200, 40)
                if btn_back_rect.collidepoint((click_x, click_y)):
                    self.state = self.MENU
                    
            else:
                panel_rect = pygame.Rect(50, 80, 860, 400)
                btn_close = pygame.Rect(panel_rect.right - 50, panel_rect.y + 15, 30, 30)
                if btn_close.collidepoint((click_x, click_y)):
                    self.selected_sector = 0
                    return
                    
                # Klick auf eine Stufe (Rechteck-Logik)
                for i in range(15):
                    stage = i + 1
                    col = i % 5
                    row = i // 5
                    
                    rect_x = panel_rect.x + 35 + col * 165
                    rect_y = panel_rect.y + 70 + row * 95
                    stage_rect = pygame.Rect(rect_x, rect_y, 130, 70)
                    
                    if stage_rect.collidepoint((click_x, click_y)):
                        is_unlocked = False
                        if self.selected_sector < self.modules.highest_campaign:
                            is_unlocked = True
                        elif self.selected_sector == self.modules.highest_campaign and stage <= self.modules.highest_stage:
                            is_unlocked = True
                            
                        if is_unlocked:
                            self._collect_idle_loot()
                            self.idle_mode = False
                            self.pve = PvECombat(is_idle=False, campaign_id=self.selected_sector, stage_id=stage, ship_level=self.modules.ship_level)
                            self._sync_modules_to_combat()
                            self.state = self.PLAYING
                            return
                        else:
                            self.show_message(f"Stufe {stage} ist gesperrt! Schaffe erst fruehere Stufen.")
                            return

        elif self.state == self.PLAYING:
            if self.show_upgrades:
                if self.btn_close_popup.collidepoint(pos):
                    self.show_upgrades = False
                    return
                if not self.popup_rect.collidepoint(pos):
                    self.show_upgrades = False
                    return
                
                keys = list(self.modules.modules.keys())
                for i, key in enumerate(keys):
                    col = i % 2
                    row = i // 2
                    btn_rect = pygame.Rect(self.popup_rect.x + 40 + col * 260, self.popup_rect.y + 70 + row * 90, 240, 80)
                    if btn_rect.collidepoint(pos):
                        try:
                            self.modules.upgrade(key)
                            self._sync_modules_to_combat()
                        except ValueError as e:
                            self.show_message(str(e))
                        return
            else:
                if self.btn_open_upgrades.collidepoint(pos):
                    self.show_upgrades = True
                elif self.btn_back_play.collidepoint(pos):
                    self.state = self.PAUSED

        elif self.state == self.PAUSED:
            if self.btn_resume.collidepoint(pos):
                self.state = self.PLAYING
            elif self.btn_pause_settings.collidepoint(pos):
                self.settings_return_state = self.PAUSED
                self.state = self.SETTINGS
            elif self.btn_give_up.collidepoint(pos):
                self._collect_idle_loot()
                self.state = self.MENU

        elif self.state == self.STAGE_CLEAR:
            if hasattr(self, 'victory_frames') and self.victory_frames:
                frame_idx = int(self.victory_timer * 30.0)
                if frame_idx >= len(self.victory_frames): frame_idx = len(self.victory_frames) - 1
                SCREEN.blit(self.victory_frames[frame_idx], (0, 0))
                if frame_idx == len(self.victory_frames) - 1:
                    mouse = pygame.mouse.get_pos()
                    btn_continue = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
                    draw_single_button(SCREEN, btn_continue, "WEITER", mouse, self.elapsed, CYAN)
            else:
                self.draw_playing()
                self.draw_stage_clear()
            if not hasattr(self, 'victory_frames') or not self.victory_frames or self.victory_timer >= len(self.victory_frames) / 30.0:
                btn_continue = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
                if btn_continue.collidepoint(pos):
                    self.state = self.STAGES
                    self.pve = PvECombat(is_idle=False, campaign_id=self.selected_sector, stage_id=1, ship_level=self.modules.ship_level)
                    self.victory_timer = 0.0
                    return
        elif self.state == self.SETTINGS:
            if self.btn_back_settings.collidepoint(pos):
                self.state = self.settings_return_state

    def update(self, dt):
        if self.state == self.INTRO:
            if self.video_frames:
                self.intro_timer += dt
                if self.intro_timer >= len(self.video_frames) / 30.0:
                    self.state = self.MENU
            return

        # NEU: STAGE_CLEAR blockiert das Update (verhindert doppelte Belohnung)
        if self.state == self.STAGE_CLEAR:
            if hasattr(self, 'victory_frames') and self.victory_frames:
                self.victory_timer += dt * 2.0 # 2x Geschwindigkeit
                if self.victory_timer >= len(self.victory_frames) / 30.0:
                    self.victory_timer = len(self.victory_frames) / 30.0 # Am Ende anhalten
            return

        if self.state == self.LOADING:
            self.loading_time += dt
            if self.loading_time >= 2.5:
                self.state = self.MENU
            return

        if self.state == self.DEFEAT:
            if self.defeat_frames:
                self.defeat_timer += dt
                if self.defeat_timer >= len(self.defeat_frames) / 30.0:
                    self.defeat_timer = len(self.defeat_frames) / 30.0 
            return

        if self.state == self.PAUSED:
            return

        self.fortress.update(dt)
        self.movement.update(dt) # NEU: Idle-Bewegung updaten
        
        center = (self.fortress.x, self.fortress.y)

        # Antrieb-Update (Position wird in draw_playing gesetzt)
        engine_lvl = self.modules.get("antrieb").level
        self.engine_effect.update(dt, engine_lvl)
        
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
                
                # NEU: Prüfen, ob die Stufe gewonnen wurde
                result = self.pve.get_result()
                if result["won"] and self.state == self.PLAYING:
                    # Credits und Fortschritt speichern
                    self.modules.complete_stage(
                        campaign_id=self.selected_sector, 
                        stage_id=self.pve.stage_id, 
                        credits_earned=result["credits_earned"]
                    )
                    print(f"🎉 STUFE {self.pve.stage_id} ABGESCHLOSSEN! + {result['credits_earned']} Cr")
                    # Zurück zur Karte
                    self.state = self.STAGES
                    self.pve = PvECombat(is_idle=False, campaign_id=self.selected_sector, stage_id=1, ship_level=self.modules.ship_level)
                    return

    def draw(self):
        if self.state == self.INTRO:
            if self.video_frames:
                frame_idx = int(self.intro_timer * 30)
                if frame_idx < len(self.video_frames):
                    SCREEN.blit(self.video_frames[frame_idx], (0, 0))
            else:
                SCREEN.fill((0, 0, 0))
            pygame.display.flip()
            return

        if self.state == self.DEFEAT:
            if self.defeat_frames:
                frame_idx = int(self.defeat_timer * 30)
                if frame_idx < len(self.defeat_frames):
                    SCREEN.blit(self.defeat_frames[frame_idx], (0, 0))
            else:
                SCREEN.fill((50, 0, 0))
                text(SCREEN, "SCHIFF ZERSTÖRT", FONT_HUGE, RED, (WIDTH//2, HEIGHT//2), "center")
            
            pygame.display.flip()
            return

        if self.state in (self.MENU, self.RESEARCH, self.SETTINGS, self.STAGES):
            if self.menu_bg:
                SCREEN.blit(self.menu_bg, (0, 0))
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 140))
                SCREEN.blit(overlay, (0, 0))
            elif self.final_frame_surface:
                SCREEN.blit(self.final_frame_surface, (0, 0))
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160)) 
                SCREEN.blit(overlay, (0, 0))
            else:
                SCREEN.fill(VOID)
        elif self.state in (self.PLAYING, self.PAUSED, self.STAGE_CLEAR):
            combat = self.idle_combat if self.idle_mode else self.pve
            if not self.idle_mode and hasattr(self, 'bg_stage_1_5') and self.bg_chapter_1_part_1:
                if combat.stage_id <= 5: SCREEN.blit(self.bg_chapter_1_part_1, (0, 0))
                elif combat.stage_id <= 10: SCREEN.blit(self.bg_chapter_1_part_2, (0, 0))
                else: SCREEN.blit(self.bg_chapter_1_part_3, (0, 0))
                
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 50))
                SCREEN.blit(overlay, (0, 0))
            else:
                draw_grid(SCREEN, self.elapsed)
            
        draw_scanline(SCREEN, self.elapsed)

        if self.state == self.LOADING:
            self.draw_loading()
        elif self.state == self.MENU:
            self.draw_menu()
        elif self.state == self.RESEARCH:
            self.draw_research()
        elif self.state == self.STAGES:
            self.draw_stages()
        elif self.state in (self.PLAYING, self.PAUSED):
            self.draw_playing()
            if self.state == self.PAUSED:
                self.draw_pause_menu()
        elif self.state == self.SETTINGS:
            self.draw_settings()

        if self.debug_mode and self.state == self.PLAYING:
            cx, cy = self.fortress.x, self.fortress.y
            pygame.draw.line(SCREEN, RED, (cx - 20, cy), (cx + 20, cy), 2)
            pygame.draw.line(SCREEN, RED, (cx, cy - 20), (cx, cy + 20), 2)
            
            if self.debug_target == "cannon":
                tx, ty = cx + self.debug_cannon_offset[0], cy + self.debug_cannon_offset[1]
                pygame.draw.circle(SCREEN, GREEN, (int(tx), int(ty)), 25, 2)
            else:
                tx, ty = cx + self.debug_engine_offset[0], cy + self.debug_engine_offset[1]
                pygame.draw.circle(SCREEN, AMBER, (int(tx), int(ty)), 25, 2)
            
            debug_txt = f"TAB = Wechseln | Ziel: {self.debug_target.upper()}"
            text(SCREEN, debug_txt, FONT_MED_BOLD, RED, (WIDTH // 2, 20), "midtop")
            text(SCREEN, "Pfeiltasten = Feinjustieren | Linksklick = Kanone | Rechtsklick = Antrieb", FONT_SMALL, WHITE, (WIDTH // 2, 50), "midtop")

        self._draw_message()
        pygame.display.flip()

    def draw_pause_menu(self):
        mouse = pygame.mouse.get_pos()
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        SCREEN.blit(overlay, (0, 0))
        panel(SCREEN, self.pause_rect, fill=(5, 10, 21), border=CYAN, radius=15)
        neon_text(SCREEN, "SPIEL PAUSIERT", FONT_BIG, WHITE, (self.pause_rect.centerx, self.pause_rect.y + 20), "midtop")
        draw_single_button(SCREEN, self.btn_resume, "FORTSETZEN", mouse, self.elapsed, GREEN)
        draw_single_button(SCREEN, self.btn_pause_settings, "EINSTELLUNGEN", mouse, self.elapsed, VIOLET)
        draw_single_button(SCREEN, self.btn_give_up, "ZUM HAUPTMENÜ", mouse, self.elapsed, RED)

    def draw_loading(self):
        frame = pygame.Rect(180, 200, 600, 150)
        panel(SCREEN, frame, fill=(3, 8, 17), border=(16, 42, 60), radius=12)
        neon_text(SCREEN, "SYSTEM INITIALIZATION", FONT_MED_BOLD, WHITE, (WIDTH // 2, 220), "midtop")
        prog = min(1.0, self.loading_time / 2.5)
        bar_bg = pygame.Rect(230, 280, 500, 15)
        bar_fg = pygame.Rect(230, 280, int(500 * prog), 15)
        pygame.draw.rect(SCREEN, (10, 25, 40), bar_bg, border_radius=4)
        pygame.draw.rect(SCREEN, CYAN, bar_fg, border_radius=4)
        pygame.draw.rect(SCREEN, LINE, bar_bg, 2, border_radius=4)
        text(SCREEN, f"LOADING... {int(prog * 100)}%", FONT_TINY, CYAN, (WIDTH // 2, 310), "midtop")

    def draw_menu(self):
        mouse = pygame.mouse.get_pos()
        t = self.elapsed
        if self.logo_img:
            logo_rect = self.logo_img.get_rect(center=(WIDTH // 2, 140))
            SCREEN.blit(self.logo_img, logo_rect)
        else:
            neon_text(SCREEN, "CORRIDOR", FONT_HUGE, CYAN, (WIDTH // 2, 70), "midtop", glow_strength=3)
            neon_text(SCREEN, "SLAYER", FONT_HUGE, MAGENTA, (WIDTH // 2, 120), "midtop", glow_strength=3)
        banner_rect = pygame.Rect(WIDTH // 2 - 190, 200, 380, 30)
        banner_surf = pygame.Surface((banner_rect.width, banner_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(banner_surf, (10, 5, 0, 200), banner_surf.get_rect(), border_radius=4)
        pygame.draw.rect(banner_surf, AMBER, banner_surf.get_rect(), 1, border_radius=4)
        SCREEN.blit(banner_surf, (banner_rect.x, banner_rect.y))
        text(SCREEN, "COMMAND INTERFACE", FONT_MED_BOLD, AMBER, (banner_rect.centerx, banner_rect.centery), "center")
        draw_button(SCREEN, self.start_idle_button, "IDLE MODUS", "Automatischer Abwehrbetrieb", mouse, t, CYAN)
        draw_button(SCREEN, self.research_button, "UPGRADES", "Module & Schiff upgraden", mouse, t, MAGENTA)
        draw_button(SCREEN, self.stages_button, "STUFENKAMPAGNE", "Gezielter Sektor-Einsatz", mouse, t, AMBER)
        draw_button(SCREEN, self.settings_button, "EINSTELLUNGEN", "System Konfiguration", mouse, t, VIOLET)
        draw_button(SCREEN, self.quit_button, "BEENDEN", "Verbindung trennen", mouse, t, RED)

    def draw_research(self):
        mouse = pygame.mouse.get_pos()
        panel(SCREEN, pygame.Rect(20, 80, 920, 440), fill=(2, 5, 12), border=(22, 71, 91))
        neon_text(SCREEN, "FORSCHUNGSLABOR", FONT_BIG, WHITE, (WIDTH // 2, 90), "midtop")
        neon_text(SCREEN, f"CREDITS: {self.modules.credits:,} Cr", FONT_MED_BOLD, GREEN, (WIDTH // 2, 130), "midtop")
        for key, rect in self.research_slots.items():
            mod = self.modules.get(key)
            hovered = rect.collidepoint(mouse)
            fill = (5, 17, 29) if hovered else (3, 10, 20)
            pygame.draw.rect(SCREEN, fill, rect, border_radius=12)
            border = CYAN if hovered else LINE
            pygame.draw.rect(SCREEN, border, rect, 2 if hovered else 1, border_radius=12)
            mod_img = load_module_image(key, mod.level)
            img_rect = mod_img.get_rect(center=(rect.centerx, rect.y + 50))
            SCREEN.blit(mod_img, img_rect)
            text(SCREEN, mod.name.upper(), FONT_MED_BOLD, WHITE, (rect.centerx, rect.y + 100), "center")
            text(SCREEN, f"LVL {mod.level}", FONT_SMALL, CYAN, (rect.centerx, rect.y + 120), "center")
            if mod.level >= self.modules.max_allowed_level and mod.level < mod.max_level:
                need = mod.level * 3 - len(self.modules.completed_stages)
                cost_color = RED
                cost_text = f"GESPERRT: noch {need} Stufen"
            else:
                cost_color = GREEN if self.modules.credits >= mod.cost and mod.level < mod.max_level else RED
                cost_text = f"{mod.cost} Cr" if mod.level < mod.max_level else "MAX"
            text(SCREEN, cost_text, FONT_SMALL, cost_color, (rect.centerx, rect.y + 140), "center")
        draw_button(SCREEN, self.btn_back, "ZURÜCK", "", mouse, self.elapsed, MUTED)

    def draw_stages(self):
        mouse = pygame.mouse.get_pos()
        
        # 1. Hintergrundbild zeichnen
        if hasattr(self, 'world_bg') and self.world_bg:
            SCREEN.blit(self.world_bg, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 60))
            SCREEN.blit(overlay, (0, 0))
        else:
            SCREEN.fill(VOID)
            
        neon_text(SCREEN, "GALAXY MAP", FONT_BIG, WHITE, (WIDTH // 2, 20), "midtop")
        
        # 2. Sektoren
        sector_data = {
            1: {"pos": (480, 400), "name": "ERDE"},
            2: {"pos": (250, 250), "name": "RAUMSTATION"},
            3: {"pos": (750, 280), "name": "ASTEROIDENGÜRTEL"},
            4: {"pos": (200, 100), "name": "MARS"},
            5: {"pos": (800, 120), "name": "DUNKLER SEKTOR"}
        }
        
        for sector, data in sector_data.items():
            pos = data["pos"]
            name = data["name"]
            
            if sector < self.modules.highest_campaign: color = GREEN
            elif sector == self.modules.highest_campaign: color = CYAN
            else: color = MUTED
                
            if self.selected_sector == sector:
                pygame.draw.circle(SCREEN, color, pos, 35, 4)
                pygame.draw.circle(SCREEN, color, pos, 25, 2)
            else:
                pygame.draw.circle(SCREEN, color, pos, 25, 2)
                pygame.draw.circle(SCREEN, color, pos, 5, 0)
                
            text(SCREEN, name, FONT_SMALL, color, (pos[0], pos[1] + 30), "midtop")
            
        # 3. Rolldown-Menü (Größer und mechanischer)
        if self.selected_sector > 0:
            # Panel vergrößert
            panel_rect = pygame.Rect(50, 80, 860, 400)
            panel(SCREEN, panel_rect, fill=(2, 5, 12, 240), border=VIOLET, radius=15)
            
            # Mechanischer Panel-Rahmen (Dicke Linien an den Ecken)
            pygame.draw.rect(SCREEN, VIOLET, panel_rect, 4, border_radius=15)
            pygame.draw.rect(SCREEN, DIM, panel_rect.inflate(-10, -10), 2, border_radius=12)

            sector_name = sector_data[self.selected_sector]["name"]
            neon_text(SCREEN, f"SEKTOR {self.selected_sector} - {sector_name}", FONT_BIG, VIOLET, (WIDTH // 2, panel_rect.y + 15), "midtop")
            
            # 15 Stufen (3 Reihen, 5 Spalten)
            # Breite: 130, Höhe: 70, Abstand: 35
            for i in range(15):
                stage = i + 1
                col = i % 5
                row = i // 5
                
                rect_x = panel_rect.x + 35 + col * 165
                rect_y = panel_rect.y + 70 + row * 95
                stage_rect = pygame.Rect(rect_x, rect_y, 130, 70)
                
                # Status bestimmen
                stage_key = (self.selected_sector, stage)
                is_completed = stage_key in self.modules.completed_stages
                
                is_unlocked = False
                if self.selected_sector < self.modules.highest_campaign: is_unlocked = True
                elif self.selected_sector == self.modules.highest_campaign and stage <= self.modules.highest_stage: is_unlocked = True
                    
                # Farben & Boss-Logik
                if is_completed:
                    border_color = GREEN
                    fill_color = (10, 30, 20, 255)
                    inner_color = (5, 15, 10, 255)
                elif is_unlocked:
                    border_color = VIOLET
                    fill_color = (20, 10, 35, 255)
                    inner_color = (10, 5, 20, 255)
                else:
                    border_color = DIM
                    fill_color = (5, 5, 10, 255)
                    inner_color = (2, 2, 5, 255)
                    
                is_boss = (stage == 15)
                is_semi_boss = (stage == 5 or stage == 10)
                
                if is_boss:
                    border_color = RED if not is_unlocked else AMBER
                elif is_semi_boss:
                    border_color = MAGENTA if not is_unlocked else VIOLET
                
                # --- MECHANISCHES ACHTECK ZEICHNEN ---
                # Eckpunkte für das Achteck berechnen (abgeschrägte Ecken)
                cut = 12 # Wie stark die Ecken abgeschrägt sind
                x, y, w, h = stage_rect.x, stage_rect.y, stage_rect.width, stage_rect.height
                
                # 8 Punkte für das äußere Achteck
                outer_points = [
                    (x + cut, y), (x + w - cut, y),          # Oben
                    (x + w, y + cut), (x + w, y + h - cut),  # Rechts
                    (x + w - cut, y + h), (x + cut, y + h),  # Unten
                    (x, y + h - cut), (x, y + cut)           # Links
                ]
                
                # 1. Füllung (Dunkler Hintergrund)
                pygame.draw.polygon(SCREEN, fill_color, outer_points)
                
                # 2. Äußerer dicker Rand
                pygame.draw.polygon(SCREEN, border_color, outer_points, 6)
                
                # 3. Innerer dünner Rand (leicht nach innen versetzt)
                inner_rect = stage_rect.inflate(-12, -12)
                ix, iy, iw, ih = inner_rect.x, inner_rect.y, inner_rect.width, inner_rect.height
                inner_cut = cut - 2
                
                inner_points = [
                    (ix + inner_cut, iy), (ix + iw - inner_cut, iy),
                    (ix + iw, iy + inner_cut), (ix + iw, iy + ih - inner_cut),
                    (ix + iw - inner_cut, iy + ih), (ix + inner_cut, iy + ih),
                    (ix, iy + ih - inner_cut), (ix, iy + inner_cut)
                ]
                pygame.draw.polygon(SCREEN, inner_color, inner_points, 2)
                
                # 4. "Schrauben" an den schrägen Ecken (Optional, für den Mech-Look)
                for point in [outer_points[0], outer_points[1], outer_points[4], outer_points[5]]:
                    # Ein kleiner Punkt etwas innerhalb der Kante
                    px = point[0] + (x + w/2 - point[0]) * 0.15
                    py = point[1] + (y + h/2 - point[1]) * 0.15
                    pygame.draw.circle(SCREEN, border_color, (int(px), int(py)), 3)

                # 5. Text (Zentriert)                # 5. Text (Zentriert)
                if is_boss or is_semi_boss:
                    label = "BOSS" if is_boss else "ELITE"
                    label_color = AMBER if is_boss and is_unlocked else (RED if is_boss else MAGENTA)
                    # Label oben
                    text(SCREEN, label, FONT_TINY, label_color, (stage_rect.centerx, stage_rect.y + 18), "center")
                    # Stufennummer unten
                    text(SCREEN, str(stage), FONT_MED_BOLD, WHITE if is_unlocked else MUTED, (stage_rect.centerx, stage_rect.y + 46), "center")
                else:
                    # Normale Stufe: Nur die Nummer
                    text(SCREEN, str(stage), FONT_BIG, WHITE if is_unlocked else MUTED, (stage_rect.centerx, stage_rect.centery), "center")

            # Schließen-Button
            btn_close = pygame.Rect(panel_rect.right - 50, panel_rect.y + 15, 30, 30)
            draw_single_button(SCREEN, btn_close, "X", mouse, self.elapsed, RED)
            
        else:
            btn_back_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 60, 200, 40)
            draw_single_button(SCREEN, btn_back_rect, "HAUPTMENÜ", mouse, self.elapsed, MUTED)

    def draw_playing(self):
        # --- HINTERGRUND ZEICHNEN (Hier eingefügt, um das Gitter zu überdecken) ---
        if not self.idle_mode and hasattr(self, 'bg_chapter_1_part_1') and self.bg_chapter_1_part_1:
            combat_bg = self.idle_combat if self.idle_mode else self.pve
            if combat_bg.stage_id <= 5: SCREEN.blit(self.bg_chapter_1_part_1, (0, 0))
            elif combat_bg.stage_id <= 10: SCREEN.blit(self.bg_chapter_1_part_2, (0, 0))
            else: SCREEN.blit(self.bg_chapter_1_part_3, (0, 0))
            
            overlay_bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay_bg.fill((0, 0, 0, 50))
            SCREEN.blit(overlay_bg, (0, 0))
        # -------------------------------------------------------------------------
        mouse = pygame.mouse.get_pos()
        combat = self.idle_combat if self.idle_mode else self.pve
        
        # --- Idle-Bewegung berechnen ---
        ship_x, ship_y = self.movement.get_position(self.fortress.x, self.fortress.y)
        angle = self.movement.get_angle()
        
        center = (ship_x, ship_y)

        # 1. Antrieb zeichnen (bewegt sich mit)
        engine_x = ship_x + self.debug_engine_offset[0]
        engine_y = ship_y + self.debug_engine_offset[1]
        self.engine_effect.set_position(engine_x, engine_y)
        self.engine_effect.draw(SCREEN)
        
        # 2. Schiff zeichnen (bewegt & rotiert)
        orig_x, orig_y = self.fortress.x, self.fortress.y
        self.fortress.x = ship_x
        self.fortress.y = ship_y
        
        # Schild-Visualisierung (Ring um das Schiff)
        schild_lvl = self.modules.get("schild").level
        if schild_lvl > 1:
            shield_radius = 60 + (schild_lvl * 5)
            pulse = math.sin(self.elapsed * 4) * 3
            pygame.draw.circle(SCREEN, (0, 255, 255, 100), (int(ship_x), int(ship_y)), int(shield_radius + pulse), 2)
            pygame.draw.circle(SCREEN, (0, 255, 255, 50), (int(ship_x), int(ship_y)), int(shield_radius + pulse + 5), 1)

        # Schiff zeichnen
        if hasattr(self.fortress, '_base_image') and self.fortress._base_image:
            rotated_ship = pygame.transform.rotate(self.fortress._base_image, angle)
            ship_rect = rotated_ship.get_rect(center=(int(ship_x), int(ship_y)))
            SCREEN.blit(rotated_ship, ship_rect)
        else:
            self.fortress.draw(SCREEN)
            
        self.fortress.x, self.fortress.y = orig_x, orig_y

        # 3. Gegner zeichnen
        for enemy in combat.enemies:
            e_img = load_enemy_image(enemy.enemy_type)
            ang_deg = math.degrees(math.atan2(ship_y - enemy.y, ship_x - enemy.x))
            rot_enemy = pygame.transform.rotate(e_img, -ang_deg)
            SCREEN.blit(rot_enemy, rot_enemy.get_rect(center=(int(enemy.x), int(enemy.y))))
            hp_bar = pygame.Rect(int(enemy.x - 20), int(enemy.y - 35), 40, 4)
            pygame.draw.rect(SCREEN, (30, 30, 30), hp_bar)
            pygame.draw.rect(SCREEN, GREEN, (hp_bar.x, hp_bar.y, max(0, int(40 * enemy.hp / enemy.max_hp)), 4))

        # 4. Kanone zeichnen
        target = min(combat.enemies, key=lambda e: e.x) if combat.enemies else None
        kanonen_lvl = self.modules.get("kanonen").level
        current_offset = self.debug_cannon_offset if self.debug_mode else CANNON_OFFSETS[0]
        
        for i, (ox, oy) in enumerate([current_offset]):
            cx, cy = center[0] + ox, center[1] + oy
            if target:
                ang_deg = math.degrees(math.atan2(target.y - cy, target.x - cx))
            else:
                ang_deg = 0 
            turret_img = load_kanonen_image(kanonen_lvl)
            rot_turret = pygame.transform.rotate(turret_img, -ang_deg)
            shadow = pygame.Surface((30, 15), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow, (0, 0, 0, 100), (0, 0, 30, 15))
            SCREEN.blit(shadow, (cx - 15, cy + 5))
            SCREEN.blit(rot_turret, rot_turret.get_rect(center=(int(cx), int(cy))))
            if self.debug_mode:
                pygame.draw.circle(SCREEN, RED, (int(cx), int(cy)), 20, 1)

        # 5. Projektile
        for p in combat.projectiles:
            end_x, end_y = p.x, p.y
            start_x = p.x - p.vx * 20
            start_y = p.y - p.vy * 20
            glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(glow, (*p.color, 120), (start_x, start_y), (end_x, end_y), p.size * 3)
            pygame.draw.line(glow, (*p.color, 200), (start_x, start_y), (end_x, end_y), p.size)
            SCREEN.blit(glow, (0, 0))
            pygame.draw.line(SCREEN, (255, 255, 255), (start_x, start_y), (end_x, end_y), max(1, p.size // 2))
            pygame.draw.circle(SCREEN, (255, 255, 255), (int(p.x), int(p.y)), p.size)

        # 6. Partikel
        for part in combat.particles:
            alpha = part.life / part.max_life
            r = int(part.size * alpha)
            if r > 0:
                pygame.draw.circle(SCREEN, part.color, (int(part.x), int(part.y)), r)

        # 7. Mündungsfeuer
        for mf in combat.muzzle_flashes:
            mx, my, ang, timer = mf
            flash_radius = 8 + (timer * 100)
            pygame.draw.circle(SCREEN, (255, 255, 200), (int(mx), int(my)), int(flash_radius))
            pygame.draw.circle(SCREEN, (255, 255, 255), (int(mx), int(my)), int(flash_radius / 2))
            for i in range(3):
                angle = ang + random.uniform(-0.5, 0.5)
                end_x = mx + math.cos(angle) * flash_radius * 2
                end_y = my + math.sin(angle) * flash_radius * 2
                pygame.draw.line(SCREEN, (255, 255, 150), (mx, my), (end_x, end_y), 2)

        # HUD
        if not self.idle_mode:
            hp_ratio = combat.player_hp / combat.max_player_hp
            bar_rect = pygame.Rect(20, 350, 160, 12)
            pygame.draw.rect(SCREEN, (20, 30, 45), bar_rect, border_radius=6)
            hp_color = GREEN if hp_ratio > 0.3 else RED
            pygame.draw.rect(SCREEN, hp_color, (bar_rect.x, bar_rect.y, int(bar_rect.width * hp_ratio), bar_rect.height), border_radius=6)
            pygame.draw.rect(SCREEN, CYAN_SOFT, bar_rect, 2, border_radius=6)
            text(SCREEN, f"{int(combat.player_hp)} / {int(combat.max_player_hp)}", FONT_TINY, WHITE, (bar_rect.centerx, bar_rect.centery), "center")
            neon_text(SCREEN, f"CREDITS: {combat.credits:,} Cr", FONT_SMALL, GREEN, (WIDTH - 20, 20), "topright")
            neon_text(SCREEN, f"SEKTOR {combat.campaign_id} - STUFE {combat.stage_id:02d}", FONT_SMALL, AMBER, (WIDTH - 20, 45), "topright")
        else:
            neon_text(SCREEN, f"IDLE LOOT: +{combat.idle_loot_earned:,} Cr", FONT_SMALL, GREEN, (WIDTH - 20, 20), "topright")
            neon_text(SCREEN, f"CREDITS GESAMT: {self.modules.credits + combat.credits:,} Cr", FONT_TINY, MUTED, (WIDTH - 20, 45), "topright")

        draw_single_button(SCREEN, self.btn_open_upgrades, "UPGRADES", mouse, self.elapsed, MAGENTA)
        draw_single_button(SCREEN, self.btn_back_play, "MENÜ", mouse, self.elapsed, MUTED)

        if self.show_upgrades:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            SCREEN.blit(overlay, (0, 0))
            panel(SCREEN, self.popup_rect, fill=(5, 10, 21), border=MAGENTA, radius=15)
            neon_text(SCREEN, "MODULE & UPGRADES", FONT_MED_BOLD, MAGENTA, (self.popup_rect.centerx, self.popup_rect.y + 20), "midtop")
            pygame.draw.rect(SCREEN, RED, self.btn_close_popup, border_radius=5)
            text(SCREEN, "X", FONT_MED_BOLD, WHITE, (self.btn_close_popup.centerx, self.btn_close_popup.centery), "center")
            keys = list(self.modules.modules.keys())
            for i, key in enumerate(keys):
                mod = self.modules.get(key)
                col = i % 2
                row = i // 2
                btn_rect = pygame.Rect(self.popup_rect.x + 40 + col * 260, self.popup_rect.y + 70 + row * 90, 240, 80)
                pygame.draw.rect(SCREEN, (3, 10, 20), btn_rect, border_radius=8)
                pygame.draw.rect(SCREEN, LINE, btn_rect, 1, border_radius=8)
                mod_img = load_module_image(key, mod.level)
                SCREEN.blit(mod_img, (btn_rect.x + 10, btn_rect.y + 20))
                text(SCREEN, mod.name.upper(), FONT_SMALL, WHITE, (btn_rect.x + 60, btn_rect.y + 15))
                text(SCREEN, f"LVL {mod.level}", FONT_TINY, CYAN, (btn_rect.x + 60, btn_rect.y + 35))
                if mod.level < mod.max_level:
                    cost_color = GREEN if self.modules.credits >= mod.cost else RED
                    text(SCREEN, f"{mod.cost} Cr", FONT_SMALL, cost_color, (btn_rect.x + 60, btn_rect.y + 55))
                else:
                    text(SCREEN, "MAX", FONT_SMALL, AMBER, (btn_rect.x + 60, btn_rect.y + 55))

    def draw_settings(self):
        mouse = pygame.mouse.get_pos()
        panel(SCREEN, pygame.Rect(180, 100, 600, 340), fill=(5, 10, 21), border=(24, 59, 82))
        neon_text(SCREEN, "EINSTELLUNGEN", FONT_BIG, WHITE, (WIDTH // 2, 130), "midtop")
        text(SCREEN, "Helligkeit & Sound folgen in Kürze...", FONT_SMALL, MUTED, (WIDTH // 2, 250), "center")
        draw_button(SCREEN, self.btn_back_settings, "ZURÜCK", "", mouse, self.elapsed, CYAN)

if __name__ == "__main__":
    Game().run()
