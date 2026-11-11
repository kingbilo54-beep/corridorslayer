# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | BOSS-SIMULATOR (AUFTRAG 16, 2. DURCHLAUF)
==============================================================
Prueft die Annahme des Nutzers: "Kampagne 1 muss mit einem Schiff auf
Level 4-5 realistisch schaffbar sein." Dazu werden ALLE drei
Kampagne-1-Bosse (Stufe 5 TARNJAEGER, Stufe 10 SCHLACHTSCHIFF,
Stufe 15 EISDRACHE) gegen Schiffsprofile der Stufe 4-5 simuliert.
Zusaetzlich eine Uebersicht der Bosse in den Sektoren 2-5 (mit der
Kampagnen-Skalierung CAMPAIGN_*_MULT aus rpg_config).

Modell (transparent):
  * Spieler-Werte stammen LIVE aus einem echten PvECombat-Objekt
    (Formeln werden NICHT kopiert) - Huelle wie main._sync_modules_to_combat.
  * Boss-HP/Schaden/Beute kommen aus pve_system.boss_stats_for_stage
    (die EINE Quelle, identisch zum Spiel - inkl. Kampagnen-Faktor).
  * Boss-Angriffe werden physisch simuliert (Faecher-Projektile mit
    Ausweich-Modell, Zusatz-Angriffe mit Trefferwahrscheinlichkeit,
    Flammen-Atem des Drachen mit Tick-Schaden).
  * Ausweichen: das Schiff oszilliert (Amplitude A, Frequenz f) - ein
    Faecher-Schuss trifft, wenn der Vertikalabstand beim Ankommen unter
    dem Schiffs-Trefferradius (80 px, pve_system) liegt.

NUR Analyse: liest Spielwerte, schreibt NICHTS (keine Saves, kein
Fenster). Idempotent (Auftrag 12).
Aufruf:  python tools/simulate_boss.py
"""
import math
import os
import random
import sys
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import pve_system as pve        # noqa: E402  (echte Boss-/Formel-Konstanten)
import rpg_config as rcfg       # noqa: E402

random.seed(1616)

# ----------------------------------------------------------------------
# Schiffsprofile: (Name, {Modul: Stufe}, Schiffs-Rumpf-Stufe, Skill-Punkte)
# Modulstufen-Verteilungen = typischer Spielstand beim Erreichen der Stufe.
# AUFTRAG 16b: Kampagne 1 muss mit diesen Profilen schaffbar sein -
# die Profile sind bewusst BESCHEIDEN (keine L7-Module mehr noetig).
# ----------------------------------------------------------------------
PROFILES_C1 = {
    5: [
        ("Schiff 4 - knapp",     {"kanonen": 4, "antrieb": 3, "huelle": 3,
                                  "schild": 2, "reaktor": 2, "hangar": 2,
                                  "radar": 2, "reparatur": 2}, 1, 0),
        ("Schiff 4 - Normal",    {"kanonen": 6, "antrieb": 4, "huelle": 3,
                                  "schild": 2, "reaktor": 2, "hangar": 2,
                                  "radar": 2, "reparatur": 2}, 2, 5),
        ("Schiff 5 - gewachsen", {"kanonen": 7, "antrieb": 4, "huelle": 4,
                                  "schild": 3, "reaktor": 3, "hangar": 3,
                                  "radar": 2, "reparatur": 2}, 2, 8),
    ],
    10: [
        ("Schiff 4 - knapp",     {"kanonen": 4, "antrieb": 3, "huelle": 3,
                                  "schild": 2, "reaktor": 2, "hangar": 2,
                                  "radar": 2, "reparatur": 2}, 1, 0),
        ("Schiff 4 - Normal",    {"kanonen": 6, "antrieb": 4, "huelle": 3,
                                  "schild": 2, "reaktor": 2, "hangar": 2,
                                  "radar": 2, "reparatur": 2}, 2, 5),
        ("Schiff 5 - gewachsen", {"kanonen": 7, "antrieb": 4, "huelle": 4,
                                  "schild": 3, "reaktor": 3, "hangar": 3,
                                  "radar": 2, "reparatur": 2}, 2, 8),
    ],
    15: [
        ("Schiff 4 - knapp",     {"kanonen": 4, "antrieb": 3, "huelle": 3,
                                  "schild": 2, "reaktor": 2, "hangar": 2,
                                  "radar": 2, "reparatur": 2}, 1, 0),
        ("Schiff 4 - Normal",    {"kanonen": 6, "antrieb": 4, "huelle": 3,
                                  "schild": 2, "reaktor": 2, "hangar": 2,
                                  "radar": 2, "reparatur": 2}, 2, 5),
        ("Schiff 5 - gewachsen", {"kanonen": 7, "antrieb": 4, "huelle": 4,
                                  "schild": 3, "reaktor": 3, "hangar": 3,
                                  "radar": 2, "reparatur": 2}, 2, 8),
    ],
}

# Referenz-Profile fuer die Sektor-Uebersicht 2-5 (typischer Stand,
# wenn man dorthin kommt - wird NICHT als Freigabe-Kriterium geprueft).
PROFILES_SECTORS = {
    2: ("Schiff 6-7",  {"kanonen": 8, "antrieb": 6, "huelle": 5, "schild": 4,
                        "reaktor": 4, "hangar": 4, "radar": 3, "reparatur": 3}, 3, 10),
    3: ("Schiff 8-9",  {"kanonen": 10, "antrieb": 7, "huelle": 6, "schild": 5,
                        "reaktor": 5, "hangar": 5, "radar": 4, "reparatur": 4}, 4, 14),
    4: ("Schiff 9-10", {"kanonen": 12, "antrieb": 8, "huelle": 7, "schild": 6,
                        "reaktor": 6, "hangar": 6, "radar": 5, "reparatur": 5}, 5, 18),
    5: ("Schiff 11-12", {"kanonen": 13, "antrieb": 9, "huelle": 8, "schild": 7,
                         "reaktor": 7, "hangar": 7, "radar": 6, "reparatur": 6}, 6, 22),
}

SHIP_DODGE_AMP = 70.0     # px vertikale Auslenkung (Touch-Drag)
SHIP_DODGE_F = 0.9        # Hz
SHIP_HIT_R = 80.0         # Trefferradius gegen feindliche Projektile (pve)


def build_player(mod_levels, hull_lvl, skill_points, stage, campaign=1):
    """Echtes PvECombat mit den Modul-Stufen des Profils (wie im Spiel)."""
    combat = pve.PvECombat(is_idle=False, campaign_id=campaign, stage_id=stage)
    combat.dmg_level = mod_levels["kanonen"]
    combat.speed_level = mod_levels["antrieb"]
    combat.cannon_count_level = min(8, 1 + mod_levels["kanonen"] // 2)
    combat.hangar_level = mod_levels["hangar"]
    combat.repair_level = mod_levels["reparatur"]
    # gear_mods wie main._sync_modules_to_combat (ohne SYSTEM-SYNERGIE)
    rea = mod_levels["reaktor"]
    sch = mod_levels["schild"]
    gear = {
        "crit_chance": 0.02 * max(0, rea - 1),
        "drone_dmg_pct": 0.06 * max(0, rea - 1),
        "credit_pct": 0.04 * max(0, mod_levels["radar"] - 1),
        "core_chance": 0.02 * max(0, mod_levels["radar"] - 1),
        "dr_pct": min(0.45, 0.03 * max(0, sch - 1)),
        "dmg_pct": 0.03 * max(0, hull_lvl - 1),
    }
    combat.gear_mods = gear
    base_hp = 700.0 + (mod_levels["huelle"] - 1) * 100
    base_hp += 80 * (hull_lvl - 1)
    combat.max_player_hp = base_hp
    combat.player_hp = combat.max_player_hp
    return combat


def dps_of(combat, boss_dr=0.0):
    """Gesamt-DPS auf ein Ziel mit Panzerung boss_dr (Kanonen + Drohnen)."""
    e_crit = 1.0 + combat.mod("crit_chance", 0.0) * (combat.mod("crit_mult", 2.0) - 1.0)
    dps = combat.cannon_count * combat.cannon_damage * e_crit / max(0.05, combat.attack_rate)
    n = max(0, min(6, (combat.hangar_level - 1) + int(combat.mod("extra_drones", 0))))
    if n > 0:
        drone_dmg = combat.cannon_damage * 0.5 * (1.0 + combat.mod("drone_dmg_pct", 0.0))
        rate_mult = max(0.4, combat.mod("drone_rate_mult", 1.0))
        ivg = sum((1.15 + 0.18 * (i % 3)) for i in range(n)) / n * rate_mult
        dps += n * drone_dmg / max(0.05, ivg)
    return dps * (1.0 - boss_dr) * (1.0 + combat.mod("boss_dmg_pct", 0.0))


def simulate_fight(combat, stage, campaign=1, trials=300):
    """Monte-Carlo eines Bossgefechts (Kampagne campaign).
    Liefert (sieg_quote, ttk_mean, ueberlebenszeit_der_Verlierer,
    hp_rest_mean_der_Sieger)."""
    stats = pve.boss_stats_for_stage(stage, campaign)
    if stats is None:
        raise ValueError(f"Stufe {stage} ist kein Boss (Kampagne {campaign})")
    hp0, dmg_mean, _reward = stats
    boss = pve.BOSS_DATA[stage]
    cfg = pve.BOSS_TYPE_CFG[boss["type"]]
    boss_hp_eff = hp0 / (1.0 - boss["dr"])
    dps = dps_of(combat, boss["dr"])
    dmg_per_bullet = dmg_mean

    dr = combat.mod("dr_pct", 0.0)
    regen = 1.5 + (combat.repair_level * 2.0 if combat.repair_level > 1 else 0.0)
    hp_max = combat.max_player_hp
    # AUFTRAG 16b: Zusatzangriffe unterliegen im Spiel BAL_ENEMY_DMG x
    # Kampagnen-Faktor (pve_system._boss_fx_dmg) - hier identisch.
    fx = pve.BAL_ENEMY_DMG * pve.campaign_dmg_mult(campaign)

    wins, ttks, losst, winhp = 0, [], [], []
    for _ in range(trials):
        bhp, php = hp0, hp_max
        t = 2.2                                  # Schonfrist nach Einzug
        volley_t = 1.8
        volley_n = 0                             # Salven-Zaehler (je 3. = schwer)
        atk_t = 4.0
        while t < 240.0:
            dt = 0.1
            t += dt
            bhp -= dps * dt
            if bhp <= 0:
                wins += 1
                ttks.append(t)
                winhp.append(php / max(1.0, hp_max))
                break
            # -- Faecher-Salve (interceptor/brute): Ausweichen physisch --
            volley_t -= dt
            dmg_tick = 0.0
            if volley_t <= 0:
                volley_t = random.uniform(*cfg["cadence"]) * 0.85
                volley_n += 1
                hits = 0
                for i in range(cfg["fan"]):
                    off = cfg["spread"] * (i / max(1, cfg["fan"] - 1) - 0.5)
                    flug = (520.0 - 100.0) / cfg["b_speed"]
                    abw = random.uniform(-0.35, 0.35) * SHIP_DODGE_AMP \
                        + SHIP_DODGE_AMP * math.sin(2 * math.pi * SHIP_DODGE_F * (t + flug))
                    if abs(abw) < SHIP_HIT_R * (1.0 - abs(off) / max(1.0, cfg["spread"])):
                        hits += 1
                for _ in range(hits):
                    dmg_tick += dmg_per_bullet * (1.0 - dr)
                # Schwerer Schuss jeder 3. Salve (gezielt, 45 % Ausweichchance)
                if cfg["heavy"] and volley_n % 3 == 0 \
                        and random.random() < 0.55:
                    dmg_tick += dmg_per_bullet * 1.5 * (1.0 - dr)
            # -- Zusatz-Angriffe (telegraphiert, Trefferquote geschaetzt) --
            atk_t -= dt
            if atk_t <= 0:
                atk_t = random.uniform(2.2, 3.2)
                if boss["type"] == "interceptor":
                    # EISSPIESSE: 45 % Zielchance, Spaltenbreite 104 px
                    if random.random() < 0.45 * 0.6:
                        dmg_tick += pve.SPIKE_DMG * fx * (1.0 - dr)
                elif boss["type"] == "brute":
                    # GLUTBOMBEN: 3 AoE mit sichtbaren Einschlagsmarken -
                    # aktive Spieler weichen dem Gros aus (~0.8 Treffer/Salve)
                    for _ in range(random.choice([0, 1, 1, 2])):
                        dmg_tick += pve.BOMB_DMG * fx * (1.0 - dr)
                else:
                    # EISDRACHE: Flammen-Atem - Telegraf 0.62 s, dann Strahl;
                    # wer weiterzieht, entkommt. Treffer-Ticks geschaetzt.
                    if random.random() < 0.55:
                        ticks = random.uniform(2.0, 3.8)
                        mult = 1.3 if bhp < hp0 * 0.5 else 1.0
                        dmg_tick += pve.BREATH_DPS * mult * pve.BREATH_TICK_S \
                            * ticks * fx * (1.0 - dr)
            php = min(hp_max, php + regen * dt)
            if dmg_tick > 0:
                php -= dmg_tick
                if php <= 0:
                    losst.append(t)              # Spieler gestorben
                    break
        else:
            losst.append(240.0)                  # Zeitlimit = Niederlage
    ttk = sum(ttks) / len(ttks) if ttks else float("nan")
    lost = sum(losst) / len(losst) if losst else float("nan")
    whp = sum(winhp) / len(winhp) if winhp else 0.0
    return wins / trials, ttk, lost, whp


def urteil(sieg):
    if sieg >= 0.85:
        return "OK"
    if sieg >= 0.6:
        return "hart"
    if sieg >= 0.35:
        return "sehr hart"
    return "ZU HART"


def main():
    print("CORRIDOR SLAYER - BOSS-SIMULATOR (AUFTRAG 16, 2. DURCHLAUF)")
    print(f"  BAL_BOSS_HP={rcfg.BAL_BOSS_HP}  BAL_ENEMY_DMG={rcfg.BAL_ENEMY_DMG}"
          f"  BAL_PLAYER_DMG={rcfg.BAL_PLAYER_DMG}")
    print("  Ausweich-Modell: Sinus-Strafe +-70 px @ 0.9 Hz, Trefferradius 80 px")
    print(f"  Kampagnen-HP-Faktoren: {rcfg.CAMPAIGN_HP_MULT}")

    print("")
    print("#" * 96)
    print("# ANNAHMETEST: KAMPAGNE 1 MIT SCHIFF L4-5 (alle drei Bosse)")
    print("#" * 96)
    for stage in (5, 10, 15):
        hp0, dmg_mean, reward = pve.boss_stats_for_stage(stage, 1)
        boss = pve.BOSS_DATA[stage]
        print("")
        print("=" * 96)
        print(f"STUFE {stage}: {boss['name']} ({boss['type']})  "
              f"HP={hp0:,.0f}  dr={boss['dr']:.0%}  dmg={dmg_mean:.1f}"
              f"  reward={reward}")
        print("=" * 96)
        print("  {:<22} {:>8} {:>8} {:>8} {:>10} {:>8} {:>8}".format(
            "Profil", "DPS", "TTK s", "Sieg %", "Verl.-Zeit s", "RestHP %", "Urteil"))
        for name, lvls, hull, sk in PROFILES_C1[stage]:
            combat = build_player(lvls, hull, sk, stage, campaign=1)
            sieg, ttk, lost, whp = simulate_fight(combat, stage, campaign=1)
            dps = dps_of(combat, boss["dr"])
            print("  {:<22} {:>8.0f} {:>8.1f} {:>8.0%} {:>10.1f} {:>8.0%} {:>8}".format(
                name, dps, ttk, sieg, lost, whp, urteil(sieg)))

    print("")
    print("#" * 96)
    print("# SEKTOR-UEBERSICHT (Stufe-15-Boss je Sektor, Referenz-Profile)")
    print("#" * 96)
    for camp in (2, 3, 4, 5):
        hp0, dmg_mean, reward = pve.boss_stats_for_stage(15, camp)
        name, lvls, hull, sk = PROFILES_SECTORS[camp]
        combat = build_player(lvls, hull, sk, 15, campaign=camp)
        sieg, ttk, lost, whp = simulate_fight(combat, 15, campaign=camp)
        print("  Sektor {}  Boss-HP {:>9,.0f}  dmg {:>5.1f}  |  {}: TTK {:>5.1f} s, "
              "Sieg {:>4.0%}, RestHP {:>3.0%}  [{}]".format(
                  camp, hp0, dmg_mean, name, ttk, sieg, whp, urteil(sieg)))


if __name__ == "__main__":
    main()
