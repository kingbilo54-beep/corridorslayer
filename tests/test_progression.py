import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
_data = tempfile.TemporaryDirectory(prefix="cs_progression_tests_")
os.environ["CS_DATA_DIR"] = _data.name

import main
import quest_system
import rpg_config as cfg
import rpg_progression as progression
import summon_system


class ProgressionTests(unittest.TestCase):
    def test_level_boundaries_and_max_level_xp(self):
        p = progression.PlayerProgress()
        p.restore({"level": 1, "xp": 0})
        self.assertEqual((p.level, p.xp), (1, 0))
        p.restore({"level": 59, "xp": cfg.xp_for_level(59) - 1,
                   "progression_version": 2})
        self.assertEqual(p.level, 59)
        ups, _ = p.add_xp(1)
        self.assertEqual((ups, p.level), (1, 60))
        p.restore({"level": 60, "xp": 0})
        self.assertEqual((p.level, p.xp, p.xp_to_next()), (60, 0, None))
        p.restore({"level": 60, "xp": 50000})
        self.assertEqual((p.level, p.xp), (60, 0))

    def test_invalid_and_negative_progress_values_are_safe(self):
        p = progression.PlayerProgress()
        p.restore({"level": -8, "xp": -100, "quantum": "bad",
                   "total_xp": None})
        self.assertEqual((p.level, p.xp, p.quantum, p.total_xp), (1, 0, 0, 0))
        p.restore({"level": "invalid", "xp": "oops", "quantum": 7})
        self.assertEqual((p.level, p.xp, p.quantum), (1, 0, 7))
        p.restore({"level": 999, "xp": 42})
        self.assertEqual((p.level, p.xp), (60, 0))
        self.assertEqual(p.add_xp(-50), (0, 0))

    def test_legacy_xp_is_mapped_by_progress_ratio_without_level_loss(self):
        p = progression.PlayerProgress()
        p.restore({"level": 12, "xp": 100, "total_xp": 9000})
        expected_old = round(300 * (1.32 ** 11))
        expected = int(100 * cfg.xp_for_level(12) / expected_old)
        self.assertEqual(p.level, 12)
        self.assertEqual(p.xp, expected)

    def test_xp_curve_is_increasing_and_campaign_repeats_are_reduced(self):
        needs = [cfg.xp_for_level(level) for level in range(1, 60)]
        self.assertTrue(all(a < b for a, b in zip(needs, needs[1:])))
        self.assertEqual(sum(needs), 111805)
        self.assertEqual(cfg.campaign_xp(1, True), round(cfg.campaign_xp(1) * .4))
        self.assertEqual(cfg.campaign_xp(15, True), round(cfg.campaign_xp(15) * .4))

    def test_level_rewards_grant_one_core_each_time(self):
        game = object.__new__(main.Game)
        game.modules = SimpleNamespace(data_cores=5)
        granted = game._award_level_cores(3)
        self.assertEqual(granted, 3)
        self.assertEqual(game.modules.data_cores, 8)
        self.assertEqual(game._award_level_cores(0), 0)

    def test_claiming_xp_awards_level_cores_and_save_prevents_regrant(self):
        game = object.__new__(main.Game)
        game.rpg = progression.PlayerProgress()
        game.rpg.restore({"level": 59, "xp": cfg.xp_for_level(59) - 1,
                          "progression_version": 2})
        game.modules = SimpleNamespace(data_cores=0, credits=0)
        game._save_modules = lambda: True
        game.show_message = lambda message: None
        game._apply_rewards({"xp": 1}, "TEST")
        self.assertEqual((game.rpg.level, game.modules.data_cores), (60, 1))
        saved_progress = game.rpg.serialize()
        game.rpg = progression.PlayerProgress()
        game.rpg.restore(saved_progress)
        self.assertEqual(game.rpg.add_xp(1000), (0, 0))
        self.assertEqual(game.modules.data_cores, 1)

    def test_quantum_respec_spends_currency_and_refunds_skill_cores(self):
        game = object.__new__(main.Game)
        game.skills = SimpleNamespace(levels={"node": 2})
        game.skills.total_spent = lambda: 37
        game.skills.reset_all = lambda save=True: 37
        game.modules = SimpleNamespace(data_cores=4)
        game.rpg = progression.PlayerProgress()
        game.rpg.quantum = cfg.QUANTUM_SKILL_RESET_COST
        game.nexus = SimpleNamespace(select=lambda node: None)
        game._save_modules = lambda: True
        game._sync_modules_to_combat = lambda: None
        game.show_message = lambda message: None
        game._quantum_skill_respec()
        self.assertEqual(game.rpg.quantum, 0)
        self.assertEqual(game.modules.data_cores, 41)

    def test_quantum_respec_rejects_insufficient_balance(self):
        game = object.__new__(main.Game)
        game.skills = SimpleNamespace(levels={"node": 1})
        game.skills.reset_all = lambda save=True: self.fail("should not respec")
        game.modules = SimpleNamespace(data_cores=4)
        game.rpg = progression.PlayerProgress()
        game.rpg.quantum = cfg.QUANTUM_SKILL_RESET_COST - 1
        game.show_message = lambda message: None
        game._quantum_skill_respec()
        self.assertEqual(game.rpg.quantum, cfg.QUANTUM_SKILL_RESET_COST - 1)
        self.assertEqual(game.modules.data_cores, 4)

    def test_respec_recovery_marker_survives_module_save_roundtrip(self):
        import module_system
        from pathlib import Path
        save_path = Path(_data.name) / "respec_transaction_test.json"
        with mock.patch.object(module_system, "SAVE_PATH", save_path):
            modules = module_system.FortressModules()
            modules.data_cores = 39
            modules.skill_respec_pending = True
            self.assertTrue(modules.save())
            restored = module_system.FortressModules()
        self.assertTrue(restored.skill_respec_pending)
        self.assertEqual(restored.data_cores, 39)

    def test_quantum_rejects_invalid_or_negative_amounts(self):
        p = progression.PlayerProgress()
        p.quantum = 50
        self.assertFalse(p.spend_quantum(-1))
        self.assertFalse(p.spend_quantum("bad"))
        self.assertFalse(p.spend_quantum(51))
        self.assertTrue(p.spend_quantum(20))
        self.assertEqual(p.quantum, 30)
        self.assertFalse(p.add_quantum(-3))

    def test_quest_reward_claim_is_one_time_and_applies_quantum_and_xp(self):
        q = quest_system.QuestSystem()
        daily_quantum = next(item for item in q.active_defs("daily")
                             if item["rewards"].get("quantum"))
        q.daily["prog"][daily_quantum["id"]] = daily_quantum["goal"]
        rewards = q.claim("daily", daily_quantum["id"])
        self.assertIsNotNone(rewards)
        self.assertIsNone(q.claim("daily", daily_quantum["id"]))
        restored = quest_system.QuestSystem()
        restored.restore(q.serialize())
        self.assertIsNone(restored.claim("daily", daily_quantum["id"]))
        game = object.__new__(main.Game)
        game.rpg = progression.PlayerProgress()
        game.modules = SimpleNamespace(data_cores=0, credits=0)
        game._save_modules = lambda: True
        game.show_message = lambda message: None
        game._apply_rewards(rewards, "TEST")
        self.assertEqual(game.rpg.quantum, rewards.get("quantum", 0))
        self.assertEqual(game.rpg.total_xp, rewards.get("xp", 0))

    def test_bundle_ignores_bad_child_and_keeps_valid_sibling_data(self):
        p = progression.PlayerProgress()
        p.restore({"level": 7, "progression_version": 2})
        q = quest_system.QuestSystem()
        s = summon_system.SummonSystem()
        bundle = progression.RPGBundle(p, q, s)
        bundle.restore({"progress": {"level": 9, "progression_version": 2},
                        "quests": "broken",
                        "summon": {"owned": {"skimmer": 2, "stichel": "x",
                                               "unknown": 4},
                                   "equipped": [[], 7, "nova"]}})
        self.assertEqual(p.level, 9)
        self.assertEqual(s.owned, {"skimmer": 2})
        self.assertEqual(s.equipped, [None] * cfg.CHAMPION_SLOTS)

    def test_old_save_without_rpg_subblocks_keeps_safe_defaults(self):
        p = progression.PlayerProgress()
        q = quest_system.QuestSystem()
        s = summon_system.SummonSystem()
        progression.RPGBundle(p, q, s).restore({})
        self.assertEqual((p.level, p.xp, p.quantum), (1, 0, 0))
        self.assertEqual((s.owned, s.equipped), ({}, [None] * cfg.CHAMPION_SLOTS))

    def test_quest_restore_skips_only_bad_fields(self):
        q = quest_system.QuestSystem()
        active = q.active_defs("daily")
        qid = active[0]["id"]
        q.restore({"daily": {"period": q.daily["period"],
                              "prog": {qid: "3", "bad": "x", "other": 9},
                              "claimed": [qid, []], "bonus_claimed": "yes"},
                   "weekly": "corrupt"})
        self.assertGreaterEqual(q.progress_of("daily", qid), 0)
        self.assertLessEqual(q.progress_of("daily", qid), active[0]["goal"])
        self.assertNotIn("bad", q.daily["prog"])

    def test_quantum_respec_cost_and_refund_basis(self):
        self.assertEqual(cfg.QUANTUM_SKILL_RESET_COST, 120)
        from skill_tree import SkillTree
        tree = object.__new__(SkillTree)
        tree.levels = {"waffen_dmg": 2}
        tree.save_error = None
        refund = tree.reset_all(save=False)
        self.assertEqual(refund, sum(
            __import__("skill_tree").NODE_BY_ID["waffen_dmg"][1]["costs"][:2]))
        self.assertEqual(tree.levels, {})


if __name__ == "__main__":
    unittest.main()
