"""Exercise the live PvE update and collision path for boss balance.

This intentionally uses PvECombat.update() for movement, attacks, projectiles,
collision, critical hits, upgrades, and damage. The small wrappers only count
transitions; they do not generate or apply attacks.
"""
import os
import sys
import math

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
sys.path.insert(0, BASE)

import pve_system as pve
import rpg_config

pve.SFX.enabled = False

DT = 1.0 / 30.0
CENTER = (100.0, 270.0)
MAX_SECONDS = 150.0
CHECKPOINTS = (10, 30, 60, 90)
PROFILES = {
    "weak-L1": {"level": 1, "hull": 1},
    "average-L7": {"level": 7, "hull": 7},
    "max-L15": {"level": 15, "hull": 12},
}


def configure_player(combat, level, hull):
    """Mirror main._sync_modules_to_combat for equal-level module profiles."""
    combat.dmg_level = level
    combat.speed_level = level
    combat.cannon_count_level = min(8, 1 + level // 2)
    combat.hangar_level = level
    combat.repair_level = level
    combat.ship_level = max(1, (level * 8) // 5)
    combat.gear_mods = {
        "crit_chance": 0.02 * (level - 1),
        "drone_dmg_pct": 0.06 * (level - 1),
        "dr_pct": min(0.45, 0.03 * (level - 1)),
        "dmg_pct": 0.03 * (hull - 1),
    }
    combat.max_player_hp = 700 + (level - 1) * 100 + (hull - 1) * 80
    combat.player_hp = combat.max_player_hp


def simulate_boss(campaign, stage, profile_name, profile):
    pve.random.seed(campaign * 10000 + stage * 100 + profile["level"])
    combat = pve.PvECombat(is_idle=False, campaign_id=campaign,
                           stage_id=stage, ship_level=profile["level"])
    configure_player(combat, profile["level"], profile["hull"])
    combat.player_hp = combat.max_player_hp
    boss = None
    engaged_at = None
    counts = {10: None, 30: None, 60: None, 90: None}
    previous = {"volley": 0, "kind": 0, "phase": 0, "rage": False}
    attacks = {"salvos": 0, "breaths": 0, "bombs": 0, "spikes": 0}

    for frame in range(int(MAX_SECONDS / DT)):
        now = frame * DT
        # A repeatable vertical dodge gives aimed attacks a real player
        # movement input while retaining the live update/collision path.
        center = (CENTER[0], CENTER[1] + 96.0 * math.sin(now * 1.15))
        live_cannons = [(center[0] + 4.0, center[1] - 14.0)] * combat.cannon_count
        combat.update(DT, center, live_cannons)
        if boss is None and combat.boss_ref is not None:
            boss = combat.boss_ref
        if boss is not None and boss in combat.enemies:
            if engaged_at is None and combat._in_player_range(boss):
                engaged_at = now
            if boss.volley > previous["volley"]:
                attacks["salvos"] += boss.volley - previous["volley"]
                previous["volley"] = boss.volley
            if boss.breath_phase == 1 and previous["phase"] == 0:
                attacks["breaths"] += 1
            previous["phase"] = boss.breath_phase
            if boss.atk_kind in (2, 3) and previous["kind"] == 0:
                if boss.atk_kind == 2:
                    attacks["bombs"] += 1
                else:
                    attacks["spikes"] += 1
            previous["kind"] = boss.atk_kind
            if boss.enraged and not previous["rage"]:
                previous["rage"] = True
        if boss is not None and engaged_at is not None and any(
                counts[second] is None for second in CHECKPOINTS):
            elapsed = now - engaged_at
            for second in CHECKPOINTS:
                if elapsed >= second and counts[second] is None:
                    counts[second] = (dict(attacks),
                                      max(0.0, boss.hp) if boss in combat.enemies else 0.0)
        if boss is None and combat.stage_cleared:
            break
        if boss is not None and boss not in combat.enemies:
            break
        if combat.player_hp <= 0:
            break

    elapsed = (frame + 1) * DT
    fight_elapsed = None if engaged_at is None else elapsed - engaged_at
    final_hp = max(0.0, boss.hp) if boss is not None else 0.0
    print(f"S{campaign} St{stage:02d} {profile_name:10s} "
          f"theoryDPS={combat.total_dps(boss.dr if boss else 0):8.1f} "
          f"bossHP={boss.max_hp if boss else 0:9.0f} "
          f"engaged={engaged_at if engaged_at is not None else -1:5.1f}s "
          f"fight={fight_elapsed if fight_elapsed is not None else -1:6.1f}s "
          f"bossLeft={final_hp:9.0f} playerHP={combat.player_hp:7.0f}/"
          f"{combat.max_player_hp:7.0f} "
          f"rage={bool(boss and boss.enraged)} attacks={attacks} checkpoints={counts}")
    return fight_elapsed, attacks, counts


def main():
    print("LIVE PvE SIMULATION: actual update(), targeting, projectiles, hits")
    print(f"dt={DT:.4f}s, center={CENTER}, max={MAX_SECONDS}s")
    for campaign in range(1, rpg_config.CAMPAIGN_COUNT + 1):
        for stage in (5, 10, 15):
            for profile_name, profile in PROFILES.items():
                simulate_boss(campaign, stage, profile_name, profile)


if __name__ == "__main__":
    main()
