# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | OEKONOMIE-SIMULATOR (SCHRITT 4)
====================================================
Simuliert Kampagne + Idle-Oekonomie fuer die Stufen 1-15 und druckt
eine Tabelle: TTK, Kills/min, Credits/min, Modul-Kumuliative-Preise,
Core-Einkommen/min - fuer drei Skill-Szenarien (0 / 10 / 20 Punkte).

NUR fuer Analyse: liest Spielwerte, schreibt NICHTS (keine Saves,
kein Fenster, kein pygame-Display-Init).

Modell (transparent, nahe am echten Spiel):
  * Modul-Stufen = runde(1.5 x Stufe), gedeckelt auf MaxLevel 15
    (alle 8 Werft-Module gleich hoch; Schiffsrumpf = min(12, dto.)).
  * Schiffslevel (Gegner-Pool-Gate) = Summe Modul-Stufen // 5
    (exakte Spiel-Formel, module_system.FortressModules.ship_level).
  * Skills 0/10/20 = round-robin ueber die OFFENSIV-Sparte
    (Waffen-Knoten in Reihenfolge, max-Stufen respektiert).
  * DPS = Kanonen (Anzahl x Schaden x Krit-Erwartung / Feuerintervall)
    + Hangar-Drohnen. Kanonen-/Drohnen-/Raten-Formeln stammen LIVE aus
    einem echten PvECombat-Objekt (keine Kopie der Formeln).
  * Gegner-HP = Spawn-Formel aus pve_system ((Base_HP + Stufe*HP_Add)
    x HP_Mult^Stufe x BAL_ENEMY_HP x Fahrendaempfung). TTK-Spalte =
    PANZERSTER Pool-Gegner der Stufe; Kill-Rate rechnet mit dem
    gewichteten Mittel (Spawn_Weight). Boss-Stufen 5/10/15 = Boss-HP
    (inkl. Panzerung dr). PNG-Existenz wird IGNORIERT (Simulation
    ohne Assets).
  * Kill-Rate = min(Spawn-Rate 1/1.75 s, DPS / mittlere Gegner-HP)
    (alle Kanonen fokussieren im Spiel dasselbe Ziel).
  * Credits/min = Kill-Rate x 60 x Nominal-Reward (gewichtetes
    Spawn-Pool-Mittel, pve_system.stage_nominal_reward) x
    (1 + credit_pct) x BAL_CREDITS (+ SCHROTTBERGUNG flat je Kill).
  * Cores/min = Kill-Rate x 60 x Core-Wurf (Erstbeendung 30 %, Farm
    10 % / Elite 25 % / Boss 15 garantiert; + core_chance).
  * Modul-Preise = exakte Spiel-Preisformel (BaseCost x CostMult^(Lvl-1)
    x BAL_COST_MULT). QUELLE: game_data.xlsx falls vorhanden, sonst
    eingebaute Defaults (wird im Kopf der Ausgabe angezeigt).

Aufruf:  python tools/simulate_economy.py
"""
import sys
from pathlib import Path

# pve_system / module_system / skill_tree liegen eine Ebene ueber tools/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pve_system as pve
import rpg_config as rcfg
import module_system as mods
import skill_tree

# ----------------------------------------------------------------------------
# SkillTree nur LESEN: Save-Pfad nach /tmp umgeleitet, damit der echte
# Spielstand corridor_slayer_skills.json NIEMALS beruehrt wird.
skill_tree.SAVE_PATH = Path("/tmp/cs_sim_skills_nur_simulation.json")


def offensive_levels(total):
    """Verteilt `total` Skill-Stufen round-robin auf die OFFENSIV-Sparte."""
    st = skill_tree.SkillTree()          # leer (kein Save unter /tmp-Pfad)
    if total <= 0:
        return st
    branch = next((b for b in skill_tree.SKILL_TREE
                   if "OFFENSIV" in b["name"].upper()), skill_tree.SKILL_TREE[0])
    verteilt = 0
    runde = 0
    while verteilt < total:
        progress = False
        for node in branch["nodes"]:
            if verteilt >= total:
                break
            cur = st.level_of(node["id"])
            if cur < node["max"]:
                st.levels[node["id"]] = cur + 1
                verteilt += 1
                progress = True
        if not progress:                 # alle Knoten auf max
            break
        runde += 1
        if runde > 100:
            break
    return st


def module_target(stage):
    """Modul-Stufe im Szenario: runde(1.5 x Stufe), Deckel MaxLevel 15."""
    return max(1, int(round(1.5 * stage)))


def module_price_sum(key, target_level):
    """Kumulierte Credit-Kosten, um Modul `key` von Stufe 1 auf
    `target_level` zu bringen (exakte Spiel-Preisformel inkl. BAL_COST_MULT)."""
    data = mods.MODULE_DATA.get(key, mods._DEFAULT_STATS.get(key, {}))
    base = int(data.get("BaseCost", 150))
    mult = float(data.get("CostMult", 1.8))
    max_l = int(data.get("MaxLevel", 15))
    total = 0
    for lvl in range(1, min(target_level, max_l)):
        total += int(round(base * (mult ** (lvl - 1)) * rcfg.BAL_COST_MULT))
    return total


def pool_for(stage, ship_level):
    """Spawn-Pool einer Stufe (ohne PNG-Pruefung) -> list[(key, data, w)]."""
    pool = []
    for k, d in pve.ENEMY_DATA.items():
        w = float(d.get("Spawn_Weight", 10))
        if ship_level >= int(d.get("Min_Ship_Level", 1)) and w > 0:
            pool.append((k, d, w))
    if not pool:
        pool = [("skitter", pve.ENEMY_DATA.get(
            "skitter", {"Base_HP": 20, "HP_Add_Per_Stage": 6,
                        "HP_Mult_Per_Stage": 1.04}), 100.0)]
    return pool


def enemy_hp(data, stage):
    """Spawn-Formel HP (pve_system._spawn_single_enemy, normaler Gegner)."""
    late = pve.stage_late_hp_factor(stage)
    return ((float(data.get("Base_HP", 20))
             + stage * float(data.get("HP_Add_Per_Stage", 10)))
            * (float(data.get("HP_Mult_Per_Stage", 1.05)) ** stage)
            * pve.BAL_ENEMY_HP * late)


def combat_setup(stage, st):
    """Baut ein ECHTES PvECombat-Objekt im Szenario und liefert
    (combat, kan_l, schiffslevel)."""
    target = module_target(stage)
    kan_l = min(15, target)              # Kanonen/Antrieb/Hangar = 1.5x Stufe
    combat = pve.PvECombat(is_idle=False, campaign_id=1, stage_id=stage)
    combat.dmg_level = kan_l
    combat.speed_level = kan_l           # Antrieb gleiche Stufe
    combat.cannon_count_level = min(8, 1 + kan_l // 2)
    combat.hangar_level = kan_l
    combat.repair_level = 1
    # Schiffslevel = exakte Spiel-Formel (Summe aller 8 Module // 5)
    total_levels = 8 * module_target(stage)
    ship_lvl = max(1, total_levels // 5)
    combat.ship_level = ship_lvl
    combat.skill_mods = st.modifiers()
    # gear_mods wie main._sync_modules_to_combat (REAKTOR/RADAR/RUMPF)
    gear = {
        "crit_chance": 0.02 * max(0, kan_l - 1),
        "drone_dmg_pct": 0.06 * max(0, kan_l - 1),
        "credit_pct": 0.04 * max(0, kan_l - 1),
        "core_chance": 0.02 * max(0, kan_l - 1),
        "dr_pct": 0.0,
        "dmg_pct": mods.SHIP_DMG_PCT_PER_LVL * max(0, min(12, target) - 1),
    }
    combat.gear_mods = gear
    return combat, kan_l, ship_lvl


def dps_of(combat):
    """Gesamt-DPS: Kanonen (alle fokussieren ein Ziel) + Hangar-Drohnen."""
    e_crit = 1.0 + combat.mod("crit_chance", 0.0) * (combat.mod("crit_mult", 2.0) - 1.0)
    dps = combat.cannon_count * combat.cannon_damage * e_crit / max(0.05, combat.attack_rate)
    # Drohnen (PAKET 7C): Anzahl = (hangar-1) + extra, Deckel 6
    n = max(0, min(6, (combat.hangar_level - 1) + int(combat.mod("extra_drones", 0))))
    if n > 0:
        drone_dmg = combat.cannon_damage * 0.5 * (1.0 + combat.mod("drone_dmg_pct", 0.0))
        rate_mult = max(0.4, combat.mod("drone_rate_mult", 1.0))
        ivg = sum((1.15 + 0.18 * (i % 3)) for i in range(n)) / n * rate_mult
        dps += n * drone_dmg / max(0.05, ivg)
    return dps


def sim_stage(stage, st):
    """Simuliert EINE Stufe -> dict mit allen Tabellenwerten."""
    combat, kan_l, ship_lvl = combat_setup(stage, st)
    dps = dps_of(combat)

    if stage in pve.BOSS_DATA:
        b = pve.BOSS_DATA[stage]
        # AUFTRAG 16b: Boss-Werte ueber die zentrale Quelle (identisch zum
        # Spiel, inkl. Kampagnen-Faktor; Idle/Kampagne 1 bleibt x1.0).
        hp = pve.boss_stats_for_stage(stage, 1)[0]
        eff_dps = dps * (1.0 - b["dr"]) * (1.0 + combat.mod("boss_dmg_pct", 0.0))
        ttk = hp / max(1.0, eff_dps)
        fight_s = ttk + 2.0                 # Einzug/Puffer
        kills_min = 60.0 / fight_s          # ein Boss je Gefecht
        reward = pve.boss_stats_for_stage(stage, 1)[2]
        core_farm = 1.0 + combat.mod("core_chance", 0.0)   # Boss 15: garantiert
        core_first = core_farm
    else:
        pool = pool_for(stage, ship_lvl)
        hp_list = [enemy_hp(d, stage) for _k, d, _w in pool]
        weights = [w for _k, _d, w in pool]
        tank = max(hp_list)
        wavg = sum(h * w for h, w in zip(hp_list, weights)) / sum(weights)
        ttk = tank / max(1.0, dps)
        spawn_rate = 1.0 / 1.75             # Spawn alle 1.0-2.5 s (Mittel)
        kill_rate = min(spawn_rate, dps / max(1.0, wavg))
        kills_min = kill_rate * 60.0
        reward = float(pve.stage_nominal_reward(stage, ship_lvl))
        core_base = 0.25 if stage in (5, 10) else 0.10
        core_farm = core_base + combat.mod("core_chance", 0.0)
        core_first = 0.30 + combat.mod("core_chance", 0.0)

    credit_mult = (1.0 + combat.mod("credit_pct", 0.0)) * pve.BAL_CREDITS
    cr_min = kills_min * reward * credit_mult \
        + kills_min * combat.mod("salvage_flat", 0)
    return {
        "stage": stage, "kan": kan_l, "ship": ship_lvl,
        "ttk": ttk, "dps": dps, "kills_min": kills_min,
        "cr_min": cr_min,
        "sum_kan": module_price_sum("kanonen", module_target(stage)),
        "sum_all": sum(module_price_sum(k, module_target(stage))
                       for k in ("kanonen", "schild", "huelle", "reaktor",
                                 "antrieb", "hangar", "radar", "reparatur")),
        "cores_farm": kills_min * core_farm,
        "cores_first": kills_min * core_first,
    }


TITEL = ("Stufe", "Kan", "Schiff", "Gegner", "TTK s", "DPS", "Kills/min",
         "Credits/min", "Kanonen-Σ Cr", "Σ Module Cr",
         "Cores/min Farm", "Cores/min Erst")


def druck_tabelle(skill_punkte):
    st = offensive_levels(skill_punkte)
    mo = st.modifiers()
    kopf = f"  SKILLS: {skill_punkte} PUNKTE (Offensiv-Sparte, round-robin)"
    if skill_punkte > 0:
        kopf += (f"  -> dmg_pct +{mo['dmg_pct']:.2f}, "
                 f"crit {mo['crit_chance']:.2f}, "
                 f"rate x{mo['rate_mult']:.3f}, "
                 f"+{mo['extra_cannons']} Kanone(n)")
    print("")
    print("=" * 104)
    print(kopf)
    print("=" * 104)
    print("  {:>5} {:>4} {:>6} {:>6} {:>8} {:>8} {:>9} {:>12} {:>13} {:>12} {:>14} {:>14}".format(*TITEL))
    print("  " + "-" * 108)
    for stage in range(1, 16):
        r = sim_stage(stage, st)
        print("  {:>5} {:>4} {:>6} {:>6} {:>8.1f} {:>8.0f} {:>9.1f} {:>12,.0f} "
              "{:>13,.0f} {:>12,.0f} {:>14.1f} {:>14.1f}".format(
                  r["stage"], r["kan"], r["ship"],
                  pve.stage_enemy_count(stage) if stage not in pve.BOSS_DATA else 1,
                  r["ttk"], r["dps"],
                  r["kills_min"], r["cr_min"], r["sum_kan"], r["sum_all"],
                  r["cores_farm"], r["cores_first"]))
    print("  " + "-" * 108)
    print("  TTK = panzerster Pool-Gegner (Boss-Stufen: Boss mit Panzerung). "
          "Gegner = Kills je Stufenlauf (stage_enemy_count / Boss = 1).")
    print("  Alle /min-Raten sind DAUERBETRIEBS-Werte (Stufe sofort wieder "
          "starten, keine Menue-Pausen). Ein realer Lauf einer Stufe "
          "bringt nur 'Gegner' Kills:")
    print("  z. B. Erst-Cores je Lauf = Gegner x Cores/min Erst / Kills-min. "
          "Ohne KONTRAKTE-Rabatt, ohne UEBERTAKTUNG, ohne SPRENGSPITZE-Kettenkills.")


def main():
    quelle = ("game_data.xlsx" if mods.MODULE_DATA
              else "EINGEBAUTE DEFAULTS (keine game_data.xlsx gefunden - "
                   "im echten DS4-Ordner ausfuehren fuer die Excel-Preise!)")
    print("CORRIDOR SLAYER - OEKONOMIE-SIMULATOR (SCHRITT 4)")
    print(f"  Modul-Preise Quelle : {quelle}")
    print(f"  Modul-Stufen        : runde(1.5 x Stufe), alle 8 Module; "
          f"Preisfaktor BAL_COST_MULT = {rcfg.BAL_COST_MULT}")
    print(f"  Idle-Referenz       : Live-Formel seit Schritt 3b "
          f"(Nominal x {rcfg.IDLE_KPS} Kills/s x BAL_CREDITS x "
          f"BAL_IDLE_CREDITS x {rcfg.IDLE_EFFICIENCY})")
    # Offline-Idle-Vergleich je Stufe (kleine Zusatztabelle).
    # AUFTRAG 13: Label jetzt dynamisch - der Wert kommt aus
    # rpg_config.IDLE_EFFICIENCY (0.85 seit AUFTRAG 5, vorher 0.60).
    print("")
    print(f"  OFFLINE-IDLE (IDLE-BERICHT, "
          f"{int(round(rcfg.IDLE_EFFICIENCY * 100))} %): Stufe -> Credits/h "
          f"(Live: x{1.0 / max(0.01, rcfg.IDLE_EFFICIENCY):.3f})")
    zeilen = []
    for stage in range(1, 16):
        nom = pve.stage_nominal_reward(stage, 12)
        rate = (nom * rcfg.IDLE_KPS * rcfg.BAL_CREDITS
                * rcfg.BAL_IDLE_CREDITS * rcfg.IDLE_EFFICIENCY)
        zeilen.append(f"{stage:>2}:{rate * 3600:>7,.0f} Cr/h")
    for i in range(0, len(zeilen), 5):
        print("    " + "  ".join(zeilen[i:i + 5]))
    for punkte in (0, 10, 20):
        druck_tabelle(punkte)
    print("")
    print("HINWEISE: Alle Werte sind Naeherungen (siehe Modellkopf). "
          "Das Spiel selbst bleibt massgeblich.")


if __name__ == "__main__":
    main()
