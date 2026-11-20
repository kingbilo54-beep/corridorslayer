"""Deterministic XP / quest / currency scenario calculation from live config."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rpg_config as cfg
from rpg_progression import PlayerProgress


def _pool_xp(pool):
    return sum(int(q["rewards"].get("xp", 0)) for q in pool)


def _pool_currency(pool, currency):
    return sum(int(q["rewards"].get(currency, 0)) for q in pool)


def main():
    needs = [cfg.xp_for_level(level) for level in range(1, cfg.PLAYER_MAX_LEVEL)]
    cumulative = 0
    print("XP thresholds (cumulative to level):")
    for target in (10, 20, 30, 40, 50, 60):
        cumulative = sum(needs[:target - 1])
        print(f"  L{target}: {cumulative:,} XP")

    per_sector = sum(cfg.campaign_xp(stage) for stage in range(1, 16))
    campaign_xp = per_sector * cfg.CAMPAIGN_COUNT
    average = per_sector / 15
    repeat_average = average * cfg.CAMPAIGN_XP_REPEAT_FACTOR
    print("\nCampaign:")
    print(f"  Stage XP: {[cfg.campaign_xp(s) for s in range(1, 16)]}")
    print(f"  Average: {average:.1f} XP/mission; replay average: {repeat_average:.1f}")
    print(f"  First-clear sweep: {campaign_xp:,} XP across "
          f"{cfg.CAMPAIGN_COUNT * 15} missions")
    p = PlayerProgress()
    ups, _ = p.add_xp(campaign_xp)
    print(f"  One full sweep reaches L{p.level} ({ups} level-ups, "
          f"{ups * cfg.LEVEL_REWARD_CORES} level cores)")
    remaining = max(0, sum(needs) - campaign_xp)
    replay_missions = remaining / repeat_average
    print(f"  After that sweep, approx. {replay_missions:.0f} average replay "
          "missions reach L60 (repeat-only estimate)")

    daily_mean = _pool_xp(cfg.DAILY_POOL) * cfg.DAILY_ACTIVE / len(cfg.DAILY_POOL)
    weekly_mean = _pool_xp(cfg.WEEKLY_POOL) * cfg.WEEKLY_ACTIVE / len(cfg.WEEKLY_POOL)
    daily_quantum = (_pool_currency(cfg.DAILY_POOL, "quantum")
                     * cfg.DAILY_ACTIVE / len(cfg.DAILY_POOL))
    weekly_quantum = (_pool_currency(cfg.WEEKLY_POOL, "quantum")
                      * cfg.WEEKLY_ACTIVE / len(cfg.WEEKLY_POOL))
    full_week = 7 * (daily_mean + cfg.DAILY_BONUS["xp"]) + \
        weekly_mean + cfg.WEEKLY_BONUS["xp"]
    casual_week = 7 * daily_mean * .5 + weekly_mean * .6
    print("\nQuest scenarios (pool-selection averages; campaign XP excluded):")
    print(f"  Full completion incl. bonuses: {full_week:,.0f} XP/week; "
          f"{sum(needs) / full_week:.1f} weeks to L60")
    print(f"  2/4 daily + 3/5 weekly, no completion bonuses: "
          f"{casual_week:,.0f} XP/week; {sum(needs) / casual_week:.1f} weeks")
    print(f"  Full-task Quantum expectation: "
          f"{7 * (daily_quantum + cfg.DAILY_BONUS.get('quantum', 0)) + weekly_quantum + cfg.WEEKLY_BONUS.get('quantum', 0):.1f}/week")
    print("  Idle/offline XP: 0 (no XP grant on those payout paths)")
    print(f"  Level-up cores at L60: {(cfg.PLAYER_MAX_LEVEL - 1) * cfg.LEVEL_REWARD_CORES}; "
          f"Quantum skill reset: {cfg.QUANTUM_SKILL_RESET_COST} Q")
    print("  Wall-clock hours omitted: repository has no measured average mission duration.")


if __name__ == "__main__":
    main()
