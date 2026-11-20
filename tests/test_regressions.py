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
        for sector in range(6, 9):
            for stage in (5, 10, 15):
                cfg = pve.boss_cfg_for(sector, stage)
                self.assertIn(cfg["type"], pve.BOSS_TYPE_CFG)
                visual = cfg.get("phase_type", cfg["type"])
                folder, filename = main.BOSS_IDLE_SHEETS[visual]
                self.assertTrue((Path(main._BASE) / "enemys" / folder / filename).is_file())
        for visual in main.BOSS_IDLE_SHEETS:
            frames = main.load_enemy_anim(visual, "idle")
            self.assertEqual(len(frames), 8, visual)

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
        boss.x = pve.BOSS_TARGET_X - 1
        self.assertTrue(combat._in_player_range(normal))
        self.assertTrue(combat._in_player_range(boss))

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


if __name__ == "__main__":
    unittest.main()
