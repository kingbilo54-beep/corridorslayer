import os
import logging
import tempfile
import unittest
from unittest import mock
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_test_data = tempfile.TemporaryDirectory(prefix="corridor_slayer_tests_")
os.environ["CS_DATA_DIR"] = _test_data.name

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

import main
import pve_system as pve
from fortress_2d import Fortress
from save_store import write_json, read_json


class RegressionTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        logger = logging.getLogger("corridor_slayer")
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

    def test_core_modules_import(self):
        import module_system
        import skill_tree
        import world_map
        self.assertTrue(module_system.FortressModules)
        self.assertTrue(skill_tree.SkillTree)
        self.assertTrue(world_map.OBJECTS)

    def test_game_constructor_starts_with_headless_video_fallbacks(self):
        game = main.Game()
        self.assertTrue(game.running)
        self.assertIn(game.state, (game.INTRO, game.MENU))

    def test_campaign_bosses_have_assets_and_configs(self):
        import campaign_system
        self.assertLessEqual(set(pve.BOSS_TYPE_CFG) - {"dragon"},
                             set(pve.BOSS_ATTACKS))
        finals = set()
        for sector in range(1, 16):
            for stage in (5, 10, 15):
                cfg = pve.boss_cfg_for(sector, stage)
                self.assertEqual(cfg["type"],
                                 campaign_system.boss_type_for(sector, stage))
                self.assertIn(cfg["type"], pve.BOSS_TYPE_CFG)
                if stage == 15:
                    finals.add(cfg["type"])
                visual = cfg.get("phase_type", cfg["type"])
                if visual == "dragon":
                    self.assertGreaterEqual(len(main.load_enemy_anim("dragon", "idle")), 2)
                    asset = None
                elif visual in main.BOSS_IDLE_SHEETS:
                    folder, filename = main.BOSS_IDLE_SHEETS[visual]
                    asset = Path(main._BASE) / "enemys" / folder / filename
                else:
                    asset = Path(main._BASE) / "enemys" / f"enemy_{visual}.png"
                if asset is not None:
                    self.assertTrue(asset.is_file(), str(asset))
        self.assertGreaterEqual(len(finals), 8)
        self.assertEqual({obj["id"] for obj in main.world_map.OBJECTS},
                         {f"sector_{sector}" for sector in range(1, 16)})
        self.assertTrue({obj["id"] for obj in main.world_map.OBJECTS}
                        <= set(main.map_locations.LOCATIONS))
        self.assertEqual(set(campaign_system.PLANETS), set(range(1, 16)))
        self.assertEqual(len({tuple(sorted(p["roster"]))
                              for p in campaign_system.PLANETS.values()}), 15)
        for profile in campaign_system.PLANETS.values():
            self.assertTrue(profile["roster"])
            self.assertEqual(set(profile["bosses"]), {5, 10, 15})
            self.assertTrue(all(name in pve.ENEMY_DATA for name in profile["roster"]))
            self.assertTrue(all((Path(main._BASE) / "enemys" / f"enemy_{name}.png").is_file()
                                for name in profile["roster"]))
        for visual in main.BOSS_IDLE_SHEETS:
            frames = main.load_enemy_anim(visual, "idle")
            self.assertEqual(len(frames), 8, visual)

    def test_all_planets_draw_as_clickable_status_markers(self):
        import ui_kit
        import world_map
        galaxy = world_map.GalaxyMap()
        galaxy.prepare(None)
        states = {
            f"sector_{sector}": {
                "name": f"PLANET {sector}",
                "status": ("AKTIV" if sector == 1 else "ABGESCHLOSSEN"
                           if sector == 2 else "GESPERRT"),
                "status_col": (main.CYAN if sector == 1 else main.GREEN
                               if sector == 2 else main.MUTED),
                "col": (main.CYAN if sector == 1 else main.GREEN
                        if sector == 2 else main.MUTED),
                "pulse": sector == 1,
            } for sector in range(1, 16)
        }
        canvas = pygame.Surface((ui_kit.W, ui_kit.H), pygame.SRCALPHA)
        galaxy.draw(canvas, None, 1.25, states)
        geometry = galaxy._geometry()
        for sector in range(1, 16):
            g = geometry[f"sector_{sector}"]
            self.assertEqual(galaxy.hit((g["hcx"], g["hcy"])),
                             f"sector_{sector}")
            self.assertGreaterEqual(g["cx"] - g["r"], 0)
            self.assertGreaterEqual(g["cy"] - g["r"], 0)
            self.assertLessEqual(g["cx"] + g["r"], ui_kit.W)
            self.assertLessEqual(g["cy"] + g["r"], ui_kit.H)
        decorative = galaxy.to_screen((.22, .15))
        self.assertIsNone(galaxy.hit(decorative))
        self.assertGreater(sum(canvas.get_at((x, y)).a > 0
                               for x in range(0, ui_kit.W, 24)
                               for y in range(0, ui_kit.H, 24)), 0)
        later = pygame.Surface((ui_kit.W, ui_kit.H), pygame.SRCALPHA)
        galaxy.draw(later, None, 2.25, states)
        self.assertNotEqual(pygame.image.tostring(canvas, "RGBA"),
                            pygame.image.tostring(later, "RGBA"))
        galaxy.set_hover("sector_2")
        hover = pygame.Surface((ui_kit.W, ui_kit.H), pygame.SRCALPHA)
        galaxy.draw(hover, None, 2.25, states)
        galaxy.select("sector_2")
        selected = pygame.Surface((ui_kit.W, ui_kit.H), pygame.SRCALPHA)
        galaxy.draw(selected, None, 2.25, states)
        self.assertNotEqual(pygame.image.tostring(later, "RGBA"),
                            pygame.image.tostring(hover, "RGBA"))
        self.assertNotEqual(pygame.image.tostring(hover, "RGBA"),
                            pygame.image.tostring(selected, "RGBA"))

    def test_campaign_track_toggle_and_fifteen_stage_layout(self):
        import ui_kit
        old_size = (ui_kit.W, ui_kit.H)
        try:
            ui_kit.set_screen(1280, 720)
            game = main.Game()
            game.state = game.STAGES
            game._fire("map_track")
            self.assertEqual(game.campaign_track, "ship")
            game._fire("map_track")
            self.assertEqual(game.campaign_track, "planet")
            game.selected_sector = 1
            layout = game._layout_stages()
            stage_buttons = [b for key, b in layout.items()
                             if key.startswith("stage_")]
            self.assertEqual(len(stage_buttons), 15)
            for button in stage_buttons:
                self.assertTrue(pygame.Rect(0, 0, 1280, 720).contains(button.rect))
            game.selected_sector = 1
            with mock.patch.object(game, "_try_enter_stage") as enter_stage:
                for stage in range(1, 16):
                    game._fire(f"stage_{stage}")
                self.assertEqual([call.args[0] for call in enter_stage.call_args_list],
                                 list(range(1, 16)))
        finally:
            ui_kit.set_screen(*old_size)

    def test_ship_campaign_starts_real_unlocked_planet_mission(self):
        game = main.Game()
        game.campaign_track = "ship"
        game.active_ship_id = "fortress"
        game.modules.ship_campaign_progress = {}
        game.modules.highest_campaign = 1
        game.modules.highest_stage = 5
        game.modules.cosmetic_hull = 1
        game.map_sel = "sector_1"
        game.gmap.select("sector_1")
        game._map_action()
        self.assertEqual(game.state, game.PLAYING)
        self.assertEqual(game.pve.campaign_id, 1)
        self.assertEqual(game.pve.stage_id, 5)
        self.assertEqual(game.active_ship_mission_id, "earth_guard")

    def test_hangar_render_changes_with_equipped_module_levels(self):
        import ui_kit
        old_size = (ui_kit.W, ui_kit.H)
        old_screen = main.SCREEN
        try:
            ui_kit.set_screen(1280, 720)
            main.SCREEN = pygame.display.set_mode((1280, 720))
            game = main.Game()
            for key in game.modules.modules:
                game.modules.get(key).level = 1
            game.modules.cosmetic_hull = 1
            game.fortress.set_level(1)
            game._layout_research()
            game.draw_research()
            starter = pygame.image.tostring(main.SCREEN, "RGB")

            for key, level in (("kanonen", 12), ("schild", 10), ("huelle", 15),
                               ("reaktor", 15), ("antrieb", 12), ("hangar", 12),
                               ("radar", 14), ("reparatur", 15)):
                game.modules.get(key).level = level
            game.modules.cosmetic_hull = 12
            game.fortress.set_level(12)
            game._layout_research()
            game.elapsed = 1.4
            game.draw_research()
            upgraded = pygame.image.tostring(main.SCREEN, "RGB")
            self.assertNotEqual(starter, upgraded)
            self.assertIsNotNone(main.load_hangar_image(12))
            self.assertIsNotNone(main.load_drone_image(12))
            self.assertIsNotNone(main.load_radar_image(14))
            self.assertIsNotNone(main.load_kanonen_crop(12))
            self.assertIsNotNone(main.shield_gfx.image_for(10))
        finally:
            main.SCREEN = old_screen
            ui_kit.set_screen(*old_size)

    def test_boss_attack_patterns_fire_expected_projectile_count(self):
        for kind, cfg in pve.BOSS_TYPE_CFG.items():
            if kind == "dragon":
                continue
            combat = pve.PvECombat(is_idle=False)
            enemy = pve.Enemy(kind, 1000, 1000, 20, 25, 1, kind,
                              x=700, y=260, is_boss=True)
            combat._boss_shoot(enemy, 100, 270)
            self.assertEqual(len(combat.projectiles), cfg["fan"], kind)
            self.assertTrue(all(projectile.kind == "enemy"
                                for projectile in combat.projectiles))

    def test_dragon_breath_bombs_and_spikes_are_executable(self):
        combat = pve.PvECombat(is_idle=False)
        dragon = pve.Enemy("dragon", 1000, 1000, 20, 25, 1, "dragon",
                           x=600, y=270, is_boss=True)
        dragon.boss_cd = 0
        combat._dragon_breath(dragon, 100, 270, 0.01, 500)
        self.assertEqual(dragon.breath_phase, 1)
        self.assertEqual(main._dragon_atk_state(dragon), "telegraph")
        combat._dragon_breath(dragon, 100, 270, 1.0, 500)
        self.assertEqual(dragon.breath_phase, 2)
        self.assertEqual(main._dragon_atk_state(dragon), "fire")

        dragon.breath_phase = 0
        dragon.last_atk = 3
        dragon.atk_cd = 0
        combat._boss_extra_attack(dragon, 100, 270, 0, 500)
        self.assertEqual(dragon.atk_kind, 2)
        self.assertEqual(main._dragon_extra_state(dragon), "attack2")
        combat._boss_extra_attack(dragon, 100, 270, 1.0, 500)
        self.assertTrue(combat.boss_bombs)

        dragon.last_atk = 2
        dragon.atk_cd = 0
        combat._boss_extra_attack(dragon, 100, 270, 0, 500)
        self.assertEqual(dragon.atk_kind, 3)
        combat._boss_extra_attack(dragon, 100, 270, 1.0, 500)
        self.assertTrue(combat.boss_spikes)

    def test_boss_fire_does_not_change_player_weapon_cooldown(self):
        combat = pve.PvECombat(is_idle=False)
        original_rate = combat.attack_rate
        boss = pve.Enemy("boss", 100, 100, 10, 10, 1,
                         "astral_centaur", x=600, y=270, is_boss=True)
        combat._boss_shoot(boss, 100, 270)
        self.assertEqual(combat.attack_rate, original_rate)

    def test_upgrade_changes_module_level_and_keeps_level_fifteen_cap(self):
        import module_system
        manager = module_system.FortressModules()
        manager.credits = 10**9
        module = manager.get("antrieb")
        module.level = 1
        before = module.level
        with mock.patch.object(
                module_system, "SAVE_PATH", Path(_test_data.name) / "upgrade.json"):
            manager.upgrade("antrieb")
        self.assertEqual(module.level, before + 1)
        self.assertEqual(manager.max_allowed_level, 15)
        self.assertIsNotNone(main.load_module_image("antrieb", 15))

    def test_player_target_and_enemy_attack_ranges_are_separate(self):
        combat = pve.PvECombat(is_idle=False)
        normal = pve.Enemy("normal", 1, 1, 1, 1, 1, "skitter", x=500)
        boss = pve.Enemy("boss", 1, 1, 1, 1, 1, "void_lurker",
                         x=900, is_boss=True)
        self.assertFalse(combat._in_player_range(normal))
        self.assertFalse(combat._in_player_range(boss))
        normal.x = 449
        self.assertTrue(combat._in_player_range(normal))
        boss.x = pve.BOSS_HOLD_X["void_lurker"] + 1
        self.assertFalse(combat._in_player_range(boss))
        boss.x = pve.BOSS_HOLD_X["void_lurker"]
        self.assertTrue(combat._in_player_range(boss))

    def test_live_update_blocks_all_player_fire_during_boss_approach(self):
        combat = pve.PvECombat(is_idle=False, stage_id=5)
        boss = pve.Enemy("boss", 10000, 10000, 20, 34, 1,
                         "interceptor", x=1000, y=270, is_boss=True)
        combat.enemies = [boss]
        combat.boss_ref = boss
        combat.projectiles.append(pve.Projectile(
            x=boss.x, y=boss.y, vx=0, vy=0, damage=500,
            color=(255, 255, 255), size=5, speed=0, kind="player"))
        combat.hangar_level = 4
        combat.retaliate_timer = 2.0
        starting_hp = boss.hp
        for _ in range(30):
            combat.update(1 / 30, center=(100, 270),
                          cannon_positions=[(104, 256)] * 3)
        self.assertGreater(boss.x, pve.BOSS_HOLD_X["interceptor"])
        self.assertTrue(all(projectile.kind == "enemy"
                            for projectile in combat.projectiles))
        self.assertFalse(combat._in_player_range(boss))
        self.assertEqual(boss.hp, starting_hp)

    def test_each_normal_enemy_uses_its_own_live_projectile_mechanic(self):
        for enemy_type, attack in pve.ENEMY_ATTACKS.items():
            with self.subTest(enemy_type=enemy_type):
                combat = pve.PvECombat(is_idle=False)
                enemy = pve.Enemy(enemy_type, 1000, 1000, 8, 0, 1,
                                  enemy_type, x=400, y=270)
                enemy.attack_cooldown = 0
                enemy.dash_cd = 100
                combat.enemies = [enemy]
                combat.update(.01, center=(100, 270))
                shots = [p for p in combat.projectiles if p.kind == "enemy"]
                self.assertEqual(len(shots), attack["count"])
                self.assertEqual({p.projectile_type for p in shots},
                                 {attack["projectile"]})
                self.assertEqual({p.motion for p in shots},
                                 {attack.get("motion", "straight")})

    def test_live_boss_attack_state_machines_fire_multiple_telegraphed_waves(self):
        import campaign_system
        for campaign in range(1, 16):
            for stage in (5, 10, 15):
                enemy_type = campaign_system.boss_type_for(campaign, stage)
                attacks = pve.BOSS_ATTACKS.get(enemy_type)
                if not attacks:
                    continue  # The dragon's breath/bomb/spike runtime is tested below.
                with self.subTest(campaign=campaign, stage=stage,
                                  enemy_type=enemy_type):
                    combat = pve.PvECombat(is_idle=False,
                                           campaign_id=campaign, stage_id=stage)
                    combat._spawn_single_enemy()
                    boss = combat.enemies[-1]
                    self.assertEqual(boss.enemy_type, enemy_type)
                    # Keep the actual spawned boss alive long enough to observe
                    # both attacks after its approach and the normal cooldowns.
                    boss.hp = boss.max_hp = 1e12
                    combat.player_hp = combat.max_player_hp = 1e12
                    phases = set()
                    fired = 0
                    attack_starts = []
                    last_phase = "rest"
                    used_attacks = set()
                    for frame in range(800):
                        before = boss.volley
                        combat.update(.05, center=(100, 270))
                        phases.add(boss.boss_attack_phase)
                        fired += boss.volley - before
                        if boss.boss_attack_phase == "telegraph" and last_phase != "telegraph":
                            attack_starts.append(frame * .05)
                            used_attacks.add(boss.boss_attack_key)
                        last_phase = boss.boss_attack_phase
                    self.assertGreaterEqual(fired, 3)
                    self.assertTrue({"telegraph", "fire", "recovery"}.issubset(phases))
                    self.assertGreaterEqual(len(used_attacks), 2)
                    self.assertTrue(all(b - a > 1.0
                                        for a, b in zip(attack_starts, attack_starts[1:])))
                    self.assertEqual(used_attacks, {a["name"] for a in attacks})

    def test_projectile_visual_types_render_on_live_fx_path(self):
        from combat_fx import CombatFX
        combat = pve.PvECombat(is_idle=False)
        kinds = {attack["projectile"] for attack in pve.ENEMY_ATTACKS.values()}
        kinds.update(a["projectile"] for rows in pve.BOSS_ATTACKS.values()
                     for a in rows)
        combat.projectiles = [pve.Projectile(
            x=80 + index * 24, y=100, vx=1, vy=.15, damage=5,
            color=(100, 210, 255), size=5, kind="enemy",
            projectile_type=kind, impact_radius=24 if kind == "rocket" else 0)
            for index, kind in enumerate(sorted(kinds))]
        surface = pygame.Surface((640, 540), pygame.SRCALPHA)
        CombatFX().draw(surface, combat, lambda x, y: (x, y), 1.0, 0.0)
        self.assertGreater(sum(surface.get_at((x, 100)).a > 0
                               for x in range(640)), 0)

    def test_live_dragon_cycles_breath_secondary_attacks_and_rage(self):
        prior = pve.random.getstate()
        pve.random.seed(4421)
        try:
            combat = pve.PvECombat(is_idle=False, stage_id=15)
            dragon = pve.Enemy("dragon", 100000, 100000, 26, 30, 1,
                               "dragon", x=pve.BOSS_HOLD_X["dragon"],
                               y=270, is_boss=True)
            dragon.boss_cd = .1
            dragon.atk_cd = .1
            combat.enemies = [dragon]
            combat.boss_ref = dragon
            breaths = bombs = spikes = 0
            previous_breath = previous_kind = 0
            for frame in range(900):
                combat.update(1 / 30, center=(100, 270))
                if dragon.breath_phase == 1 and previous_breath == 0:
                    breaths += 1
                previous_breath = dragon.breath_phase
                if dragon.atk_kind in (2, 3) and previous_kind == 0:
                    bombs += dragon.atk_kind == 2
                    spikes += dragon.atk_kind == 3
                previous_kind = dragon.atk_kind
                if frame == 420:
                    dragon.hp = dragon.max_hp * .49
            self.assertGreaterEqual(breaths, 2)
            self.assertGreater(bombs, 0)
            self.assertGreater(spikes, 0)
            self.assertTrue(dragon.enraged)
            self.assertTrue(combat.boss_bombs or combat.boss_spikes or breaths >= 2)
        finally:
            pve.random.setstate(prior)

    def test_boss_spawn_uses_stage_assignment_and_phase_sprite(self):
        combat = pve.PvECombat(is_idle=False, campaign_id=8, stage_id=15)
        combat._spawn_single_enemy()
        boss = combat.enemies[-1]
        self.assertEqual(boss.enemy_type, "void_lurker")
        self.assertEqual(boss.visual_type, "void_lurker")
        self.assertEqual(boss.phase_visual, "lich_dragon")

    def test_final_boss_switches_to_phase_sprite_below_half_health(self):
        combat = pve.PvECombat(is_idle=False, campaign_id=8, stage_id=15)
        combat._spawn_single_enemy()
        boss = combat.enemies[-1]
        boss.hp = boss.max_hp * 0.49
        combat.update(0.01, center=(100, 270))
        self.assertTrue(boss.enraged)
        self.assertEqual(boss.visual_type, "lich_dragon")

    def test_engine_levels_one_through_fifteen_load(self):
        for level in range(1, 16):
            data = main._load_engine_sprite_data(level)
            self.assertIsNotNone(data, f"engine level {level}")
            self.assertEqual(len(data["frames"]), 8)

    def test_fortress_assets_resolve_independent_of_working_directory(self):
        original = os.getcwd()
        try:
            with tempfile.TemporaryDirectory(prefix="cs_cwd_") as cwd:
                os.chdir(cwd)
                ship = Fortress(100, 270, level=12)
                self.assertIsNotNone(ship._base_image)
                self.assertGreater(ship._base_image.get_width(), 0)
                self.assertEqual(ship.level, 12)
                os.chdir(original)
        finally:
            os.chdir(original)

    def test_save_store_round_trip_is_atomic_json(self):
        path = Path(_test_data.name) / "round_trip.json"
        write_json(path, {"credits": 42, "levels": {"antrieb": 15}})
        self.assertEqual(read_json(path),
                         {"credits": 42, "levels": {"antrieb": 15}})

    def test_ship_campaign_progress_migrates_and_saves_separately(self):
        import module_system
        path = Path(_test_data.name) / "legacy_campaign_save.json"
        write_json(path, {"credits": 321, "highest_campaign": 2,
                          "highest_stage": 4, "completed_stages": [[1, 3]]})
        with mock.patch.object(module_system, "SAVE_PATH", path):
            manager = module_system.FortressModules()
            manager.load()
            self.assertEqual(manager.ship_campaign_progress, {})
            self.assertEqual(manager.highest_campaign, 2)
            self.assertIn((1, 3), manager.completed_stages)
            self.assertTrue(manager.complete_ship_mission("fortress", "earth_guard"))
            self.assertFalse(manager.complete_ship_mission("fortress", "earth_guard"))
            reloaded = module_system.FortressModules()
            reloaded.load()
        self.assertEqual(reloaded.ship_campaign_progress,
                         {"fortress": ["earth_guard"]})
        self.assertEqual(reloaded.highest_campaign, 2)
        self.assertEqual(reloaded.completed_stages, [(1, 3)])

    def test_player_regeneration_never_exceeds_max_hp(self):
        combat = pve.PvECombat(is_idle=True)
        combat.repair_level = 15
        combat.player_hp = combat.max_player_hp - .01
        combat.update(.1, center=(100, 270))
        self.assertEqual(combat.player_hp, combat.max_player_hp)


if __name__ == "__main__":
    unittest.main()
