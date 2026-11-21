import unittest
from types import SimpleNamespace
import os
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
_test_data = tempfile.TemporaryDirectory(prefix="corridor_boss_anim_tests_")
os.environ.setdefault("CS_DATA_DIR", _test_data.name)
import pygame
pygame.init()
pygame.display.set_mode((1, 1))

from boss_animation import advance_boss_animation
from main import (BOSS_IDLE_SHEETS, _crop_frames_shared_alpha_bounds,
                  _dragon_extra_state, load_enemy_anim)


class BossAnimationStateTests(unittest.TestCase):
    def enemy(self, **overrides):
        values = dict(
            enemy_type="astral_centaur", hurt_t=0.0,
            boss_anim_state="idle", boss_anim_elapsed=0.0,
            boss_anim_attack_t=0.0, boss_anim_impact_t=0.0,
            boss_attack_phase="rest",
            breath_phase=0, atk_kind=0, atk_t=0.0,
        )
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_attack_phase_map(self):
        e = self.enemy(boss_attack_phase="telegraph")
        self.assertEqual(advance_boss_animation(e, .05), "anticipation")
        self.assertEqual(e.boss_anim_elapsed, 0.0)
        self.assertEqual(advance_boss_animation(e, .05), "anticipation")
        self.assertAlmostEqual(e.boss_anim_elapsed, .05)
        e.boss_attack_phase = "fire"
        self.assertEqual(advance_boss_animation(e, .05), "attack")
        self.assertEqual(e.boss_anim_elapsed, 0.0)

    def test_impact_window_and_recovery(self):
        e = self.enemy(boss_attack_phase="recovery", boss_anim_impact_t=.1)
        self.assertEqual(advance_boss_animation(e, .04), "impact")
        self.assertEqual(advance_boss_animation(e, .08), "recovery")

    def test_projectile_release_runs_attack_then_impact_before_recovery(self):
        e = self.enemy(boss_attack_phase="recovery", boss_anim_attack_t=.1)
        self.assertEqual(advance_boss_animation(e, .05), "attack")
        self.assertEqual(advance_boss_animation(e, .05), "attack")
        self.assertEqual(advance_boss_animation(e, .05), "impact")
        self.assertEqual(advance_boss_animation(e, .08), "recovery")

    def test_hurt_has_priority_and_returns_to_combat_state(self):
        e = self.enemy(hurt_t=.2, boss_attack_phase="telegraph")
        self.assertEqual(advance_boss_animation(e, .05), "hurt")
        e.hurt_t = 0.0
        self.assertEqual(advance_boss_animation(e, .05), "anticipation")

    def test_dragon_breath_states(self):
        e = self.enemy(enemy_type="dragon", breath_phase=1)
        self.assertEqual(advance_boss_animation(e, .1), "anticipation")
        e.breath_phase = 2
        self.assertEqual(advance_boss_animation(e, .1), "attack")
        e.breath_phase = 0
        self.assertEqual(advance_boss_animation(e, .1), "idle")

    def test_dragon_extra_attack_states(self):
        e = self.enemy(enemy_type="dragon", atk_kind=3, atk_t=.4)
        self.assertEqual(advance_boss_animation(e, .1), "anticipation")
        e.atk_t = 0.0
        self.assertEqual(advance_boss_animation(e, .1), "attack")

    def test_non_negative_clock_and_pause_by_no_tick(self):
        e = self.enemy(boss_attack_phase="fire")
        advance_boss_animation(e, .2)
        before = e.boss_anim_elapsed
        self.assertEqual(advance_boss_animation(e, 0.0), "attack")
        self.assertEqual(e.boss_anim_elapsed, before)
        self.assertEqual(advance_boss_animation(e, -1.0), "attack")
        self.assertEqual(e.boss_anim_elapsed, before)

    def test_alpha_crop_uses_one_shared_frame_rectangle(self):
        a = pygame.Surface((40, 30), pygame.SRCALPHA)
        b = pygame.Surface((40, 30), pygame.SRCALPHA)
        pygame.draw.rect(a, (255, 255, 255, 255), (10, 8, 8, 10))
        pygame.draw.rect(b, (255, 255, 255, 255), (14, 6, 8, 12))
        cropped = _crop_frames_shared_alpha_bounds([a, b])
        self.assertEqual(cropped[0].get_size(), cropped[1].get_size())
        rect_a = cropped[0].get_bounding_rect(min_alpha=8)
        rect_b = cropped[1].get_bounding_rect(min_alpha=8)
        self.assertEqual(rect_a.x, 2)
        self.assertEqual(rect_b.x, 6)
        self.assertGreater(cropped[0].get_width(), rect_b.right)

    def test_all_ten_boss_idle_sheets_load_as_eight_normalized_frames(self):
        for boss_type in BOSS_IDLE_SHEETS:
            with self.subTest(boss=boss_type):
                frames = load_enemy_anim(boss_type, "idle")
                self.assertEqual(len(frames), 8)
                self.assertEqual(len({frame.get_size() for frame in frames}), 1)

    def test_dragon_attack3_has_explicit_idle_animation_fallback(self):
        dragon = SimpleNamespace(atk_kind=3)
        self.assertEqual(_dragon_extra_state(dragon), "attack3_fallback")
        dragon.atk_kind = 0
        self.assertEqual(_dragon_extra_state(dragon), "attack3_fallback")


if __name__ == "__main__":
    unittest.main()
