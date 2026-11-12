# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | KAMPAGNEN-SIMULATOR (AUFTRAG 16b + 13)
==========================================================
Simuliert den KAMPAGNEN-VERLAUF Stufe 1-15 je Sektor und prueft die
Kern-Aussage des Nutzers: "Kampagne 1 muss mit einem Schiff auf Level
4-5 realistisch schaffbar sein - ohne Module auf annaehrend Level 7."

Modell (transparent, nah am echten Spiel):
  * Spieler-Werte stammen LIVE aus einem echten PvECombat-Objekt
    (build_player wie tools/simulate_boss.py - Formeln NICHT kopiert).
  * Gegner-Welle: exakt die Spawn-Logik aus pve_system (Min_Ship_Level-
    Gate, max. 2 Typen je Stufe mit dem deterministischen Seed
    "pool::<Sektor>::<Stufe>", HP/Dmg-Formeln inkl. Spaet-Stufen-
    Daempfung und CAMPAIGN_*_MULT).
  * Zielelogik: Kanonen/Drohnen feuern auf den LINKSesten Gegner mit
    x < 450 (wie pve_system.update); 10 % Overkill-Verlust.
  * Gegner feuern alle 1.5-3.0 s einen gezielten Schuss, sobald sie
    naeher als 550 px sind. Trefferquote passiv 0.87 (Sinus-Strafe
    +-70 px, Trefferradius 80 px), aktiv gedodst 0.45.
  * Boss-Stufen 5/10/15: Monte-Carlo aus tools/simulate_boss.py.

NUR Analyse: liest Spielwerte, schreibt NICHTS (keine Saves, kein
Fenster, kein pygame-Display). Idempotent (Auftrag 12).
Aufruf:  python tools/simulate_campaign.py
"""
import os
import random
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))

import pve_system as pve          # noqa: E402
import rpg_config as rcfg         # noqa: E402
import simulate_boss as sb        # noqa: E402  (build_player, dps_of, MC)

random.seed(1616)

# Schiffsnahkeit: Profile der Werft (wie simulate_boss.PROFILES_C1)
PROFILES = {
    "Schiff 4 - knapp":     {"kanonen": 4, "antrieb": 3, "huelle": 3, "schild": 2,
                             "reaktor": 2, "hangar": 2, "radar": 2, "reparatur": 2},
    "Schiff 4 - Normal":    {"kanonen": 6, "antrieb": 4, "huelle": 3, "schild": 2,
                             "reaktor": 2, "hangar": 2, "radar": 2, "reparatur": 2},
    "Schiff 5 - gewachsen": {"kanonen": 7, "antrieb": 4, "huelle": 4, "schild": 3,
                             "reaktor": 3, "hangar": 3, "radar": 2, "reparatur": 2},
    "Schiff 6-7":           {"kanonen": 8, "antrieb": 6, "huelle": 5, "schild": 4,
                             "reaktor": 4, "hangar": 4, "radar": 3, "reparatur": 3},
    "Schiff 8-9":           {"kanonen": 10, "antrieb": 7, "huelle": 6, "schild": 5,
                             "reaktor": 5, "hangar": 5, "radar": 4, "reparatur": 4},
    "Schiff 9-10":          {"kanonen": 12, "antrieb": 8, "huelle": 7, "schild": 6,
                             "reaktor": 6, "hangar": 6, "radar": 5, "reparatur": 5},
    "Schiff 11-12":         {"kanonen": 13, "antrieb": 9, "huelle": 8, "schild": 7,
                             "reaktor": 7, "hangar": 7, "radar": 6, "reparatur": 6},
    # AUFTRAG 19 (PUNKT 2): Endstufen-Profile fuer die Sektoren 6-8.
    # Kanonen/Rumpf nahe am Maximum (15/12) - die neuen Sektoren sind das
    # Ende der Progressionsleiter, erreichbar erst mit weitgehend
    # ausgebautem Schiff (Gegene-HP x3.7-x6.25 gegenueber Sektor 1).
    "Schiff 12 - Endstufe": {"kanonen": 15, "antrieb": 10, "huelle": 9, "schild": 8,
                             "reaktor": 8, "hangar": 8, "radar": 7, "reparatur": 7},
}
PROFILE_HULL = {"Schiff 4 - knapp": 1, "Schiff 4 - Normal": 2,
                "Schiff 5 - gewachsen": 2, "Schiff 6-7": 3, "Schiff 8-9": 4,
                "Schiff 9-10": 5, "Schiff 11-12": 6, "Schiff 12 - Endstufe": 7}

# Referenzprofil je Sektor (was ein Spieler dort typischerweise hat)
SEKTOR_PROFILE = {1: ["Schiff 4 - Normal", "Schiff 5 - gewachsen"],
                  2: ["Schiff 6-7"],
                  3: ["Schiff 8-9"],
                  4: ["Schiff 9-10"],
                  5: ["Schiff 11-12"],
                  6: ["Schiff 11-12", "Schiff 12 - Endstufe"],
                  7: ["Schiff 12 - Endstufe"],
                  8: ["Schiff 12 - Endstufe"]}

SHIP_X = 150.0            # typische Schiffsposition (Welt-px)
TARGET_X = 450.0          # ab hier ist ein Gegner zielbar (pve_system)
RANGE_X = 550.0           # ab hier schiesst ein Gegner (dist_to_ship < 550)
ENTER_X = SHIP_X + RANGE_X     # = 700
P_HIT_PASSIVE = 0.87      # Sinus-Strafe +-70 px, Trefferradius 80 px
P_HIT_AKTIV = 0.45        # Spieler weicht bewusst aus
OVERKILL = 0.10           # Projektil-Verlust (Ziel stirbt im Flug)


def stage_pool(campaign, stage, ship_level):
    """Exakte Nachbildung der Pool-Auswahl aus pve_system._spawn_single_enemy."""
    rng = random.Random(f"pool::{campaign}::{stage}")
    available, weights = [], []
    for k, data in pve.ENEMY_DATA.items():
        if ship_level >= int(data.get("Min_Ship_Level", 1)):
            available.append(k)
            weights.append(data.get("Spawn_Weight", 10))
    if not available:
        return [("skitter", pve.ENEMY_DATA.get("skitter", {}))] * 2
    if len(available) > 2:
        idx = list(range(len(available)))
        rng.shuffle(idx)
        keep = sorted(idx[:2])
        available = [available[i] for i in keep]
        weights = [weights[i] for i in keep]
    types = rng.choices(available, weights=weights, k=2)   # Stichprobe der 2 Typen
    return [(t, pve.ENEMY_DATA[t]) for t in set(types)]


def stage_enemies(campaign, stage, ship_level):
    """Alle Gegner der Welle: (Typ, HP, Schaden, Speed, Reward)."""
    n = pve.stage_enemy_count(stage)
    rng = random.Random(f"wave::{campaign}::{stage}")
    pool = stage_pool(campaign, stage, ship_level)
    out = []
    for _ in range(n):
        t, data = pool[rng.randrange(len(pool))]
        late_hp = pve.stage_late_hp_factor(stage)
        late_dmg = pve.stage_late_dmg_factor(stage)
        hp = (float(data.get("Base_HP", 20)) + stage * float(data.get("HP_Add_Per_Stage", 10))) \
            * (float(data.get("HP_Mult_Per_Stage", 1.05)) ** stage) \
            * pve.BAL_ENEMY_HP * late_hp * pve.campaign_hp_mult(campaign)
        speed = float(data.get("Base_Speed", 50)) + stage * float(data.get("Speed_Add_Per_Stage", 0))
        dmg = (float(data.get("Base_Damage", 5)) + stage * float(data.get("Damage_Add_Per_Stage", 2))) \
            * pve.BAL_ENEMY_DMG * late_dmg * pve.campaign_dmg_mult(campaign)
        rew = (float(data.get("Base_Reward", 10)) + stage * 2) \
            * float(data.get("Idle_Reward_Mult", 1.0)) * pve.campaign_reward_mult(campaign)
        out.append({"type": t, "hp": hp, "dmg": dmg, "speed": speed,
                    "reward": rew})
    return out


def simulate_wave(combat, campaign, stage):
    """Wellen-Kampf: liefert (clear_s, intake_passiv, intake_aktiv,
    sieg_passiv, totzeit_s). Sequential-Kill-Modell, siehe Kopf."""
    dps = sb.dps_of(combat, 0.0) * (1.0 - OVERKILL)
    enemies = stage_enemies(campaign, stage, combat.ship_level)
    spd = pve.campaign_spawn_mult(campaign)
    t = 2.0                                   # erster Spawn nach 2 s
    spawn_ivg = 1.75 * spd                    # Mittel aus uniform(1.0, 2.5)
    kill_t = 0.0
    intake_p = 0.0
    intake_a = 0.0
    for e in enemies:
        t += spawn_ivg
        arrive_target = t + max(0.0, (1000.0 - TARGET_X) / max(1.0, e["speed"]))
        arrive_range = t + max(0.0, (1000.0 - ENTER_X) / max(1.0, e["speed"]))
        start = max(arrive_target, kill_t)
        kill_t = start + e["hp"] / max(1.0, dps)
        alive_in_range = max(0.0, kill_t - max(arrive_range, t))
        shots = alive_in_range / 2.25          # Mittel aus uniform(1.5, 3.0)
        intake_p += shots * e["dmg"] * P_HIT_PASSIVE
        intake_a += shots * e["dmg"] * P_HIT_AKTIV
    clear_s = kill_t
    return clear_s, intake_p, intake_a


def hp_after(combat, intake, duration):
    """Rest-HP nach einer Stufe (Regeneration eingerechnet, min. 0)."""
    regen = 1.5 + (combat.repair_level * 2.0 if combat.repair_level > 1 else 0.0)
    return max(0.0, combat.max_player_hp + regen * duration - intake)


def main():
    print("CORRIDOR SLAYER - KAMPAGNEN-SIMULATOR (AUFTRAG 16b/13)")
    print(f"  BAL_ENEMY_HP={rcfg.BAL_ENEMY_HP}  BAL_ENEMY_DMG={rcfg.BAL_ENEMY_DMG}"
          f"  BAL_PLAYER_DMG={rcfg.BAL_PLAYER_DMG}")
    print(f"  Kampagnen-HP-Faktoren: {rcfg.CAMPAIGN_HP_MULT}")
    print(f"  Kampagnen-Beute-Faktoren: {rcfg.CAMPAIGN_REWARD_MULT}")
    print("  Trefferquoten gegnerischer Schuesse: passiv 0.87 / aktiv 0.45")

    for camp in range(1, rcfg.CAMPAIGN_COUNT + 1):
        profiles = SEKTOR_PROFILE[camp]
        print("")
        print("#" * 100)
        print(f"# SEKTOR {camp}   (Referenz-Profile: {', '.join(profiles)})")
        print("#" * 100)
        head = ("  {:>5} {:<22} {:>6} {:>8} {:>10} {:>10} {:>8} {:>8}".format(
            "Stufe", "Profil", "DPS", "Gegner", "Welle HP", "Clear s",
            "HP rest a", "Urteil"))
        print(head)
        for pname in profiles:
            lvls = PROFILES[pname]
            combat = sb.build_player(lvls, PROFILE_HULL[pname], 0, 1, campaign=camp)
            ship_l = combat.ship_level
            for stage in range(1, 16):
                stats = pve.boss_stats_for_stage(stage, camp)
                if stats is not None:
                    sieg, ttk, lost, whp = sb.simulate_fight(
                        combat, stage, campaign=camp, trials=120)
                    urt = sb.urteil(sieg)
                    print("  {:>5} {:<22} {:>6.0f} {:>8} {:>8.0f} {:>8.1f} {:>8.0%} {:>8}"
                          .format(stage, pname, sb.dps_of(combat, 0.0), "BOSS",
                                  stats[0], ttk, whp, urt))
                    continue
                clear_s, ip, ia = simulate_wave(combat, camp, stage)
                rest_a = hp_after(combat, ia, clear_s)
                ratio = min(1.0, rest_a / max(1.0, combat.max_player_hp))
                urt = ("OK" if ratio >= 0.5 else
                       "knapp" if ratio >= 0.2 else
                       "hart" if ratio > 0.0 else "ZU HART")
                es = stage_enemies(camp, stage, combat.ship_level)
                wave_hp = sum(e["hp"] for e in es)
                print("  {:>5} {:<22} {:>6.0f} {:>8} {:>8.0f} {:>8.1f} {:>8.0%} {:>8}"
                      .format(stage, pname, sb.dps_of(combat, 0.0),
                              len(es), wave_hp, clear_s, ratio, urt))
            #Credits-Abschaetzung je Sektor-Durchlauf (Kill-Beute):
            total_rew = 0.0
            for stage in range(1, 16):
                stats = pve.boss_stats_for_stage(stage, camp)
                if stats is not None:
                    total_rew += stats[2]
                else:
                    es = stage_enemies(camp, stage, combat.ship_level)
                    total_rew += sum(e["reward"] for e in es)
            print("  -> Sektor {} Kill-Beute netto (x BAL_CREDITS, ohne Radar-/Skill-Boni): ~{:,.0f} Cr"
                  .format(camp, total_rew * rcfg.BAL_CREDITS))


if __name__ == "__main__":
    main()
