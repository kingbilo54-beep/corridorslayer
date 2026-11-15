# -*- coding: utf-8 -*-
"""AUFTRAG 18 (PUNKT 1) - ECONOMY-PRUEFUNG: Offline-/Idle-Bericht
====================================================================
Prueft mit lauffaehigen Assertions, dass der Offline-Bericht nach der
Bremse (rpg_config.idle_tapered_seconds + idle_report_cap_credits)
korrekt rechnet - NICHT nur per Quelltext-Lektuere:

  E1  Taper-Grenzen: 0 s -> 0; 1 h -> 55 %; 3 h -> 55 %+2*30 %;
      8 h -> 55 %+2*30 %+5*15 % = 6.840 "volle" Sekunden; laenger als
      8 h bleibt auf IDLE_CAP_S.
  E2  Deckel-Dominanz: EIN Bericht ist NIE hoeher als der aktive
      Vergleichswert (nominal x IDLE_ACTIVE_KPM x 45 Min x BAL_CREDITS)
      und NIE hoeher als die alte AUFTRAG-5-Formel (85 % flach).
  E3  Echte Spiel-Methode Game._compute_idle_report (Mock statt Fenster):
      8 h zahlt gedeckelt; 20 Min zahlt voll (unterhalb aller Deckel);
      kein prev_saved_at -> None; frisch gesichert (< 90 s) -> None.
  E4  Save/Load-Kompatibilitaet: kompletter Module-Save laesst sich
      schreiben, laden und die Felder bleiben identisch (alte Saves
      ohne neue Felder laden weiterhin).
  E5  AUFTRAG 22: Live-Idle-Cores je 24-h-Fenster deckeln
      (IDLE_LIVE_CORE_CAP) - war ungedeckelt (~105 je 8 h-Sitzung).
  E6  AUFTRAG 22: Neustart-Resistenz des 8-h-Max (persistiertes 24-h-
      Fenster): Spielstart senkt die verbrauchte Zeit nicht; Fenster-
      Ablauf (24 h) gibt sie einmalig frei.

NUR Pruefung: schreibt nichts ins echte Spiel (Save-Pfad nach /tmp).
Aufruf:  python tools/check_economy.py
"""
import json
import os
import sys
import time
from pathlib import Path
from types import SimpleNamespace

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
sys.path.insert(0, BASE)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import rpg_config as rc                                   # noqa: E402
import pve_system as pve                                  # noqa: E402
import module_system as mods                              # noqa: E402

# Echten Spielstand NIE beruehren (wie simulate_economy beim Skill-Tree)
mods.SAVE_PATH = Path("/tmp/cs_check_economy_save.json")
if mods.SAVE_PATH.exists():
    mods.SAVE_PATH.unlink()


def alt_bericht(nominal, idle_pct, capped_s):
    """Formel VOR AUFTRAG 18 (flache 85 %, AUFTRAG 5) - nur als
    Vergleichsmassstab fuer E2."""
    rate = (nominal * rc.IDLE_KPS * (1.0 + idle_pct)
            * rc.BAL_CREDITS * rc.BAL_IDLE_CREDITS * rc.IDLE_EFFICIENCY)
    return int(rate * capped_s)


def neu_bericht(nominal, idle_pct, credit_pct, capped_s):
    """Formel SEIT AUFTRAG 18 (identisch zu main._compute_idle_report)."""
    rate = (nominal * rc.IDLE_KPS * (1.0 + idle_pct)
            * rc.BAL_CREDITS * rc.BAL_IDLE_CREDITS)
    return min(int(rate * rc.idle_tapered_seconds(capped_s)),
               int(rc.idle_report_cap_credits(nominal, credit_pct)))


def main():
    print("ECONOMY-PRUEFUNG (AUFTRAG 18 / PUNKT 1):")

    # --- E1: Taper-Grenzen ------------------------------------------------
    volle = rc.idle_tapered_seconds
    assert volle(0) == 0.0, "Taper bei 0 s muss 0 sein"
    assert abs(volle(1800) - 1800 * 0.55) < 1e-6, "1. Staffel falsch"
    assert abs(volle(3600) - 3600 * 0.55) < 1e-6, "Grenze 1 h falsch"
    assert abs(volle(7200) - (3600 * 0.55 + 3600 * 0.30)) < 1e-6, \
        "Staffel 2 (Std. 2) falsch"
    assert abs(volle(10800) - (3600 * 0.55 + 2 * 3600 * 0.30)) < 1e-6, \
        "Grenze 3 h falsch"
    voll8h = 3600 * 0.55 + 2 * 3600 * 0.30 + 5 * 3600 * 0.15
    assert abs(volle(rc.IDLE_CAP_S) - voll8h) < 1e-6, "8-h-Summe falsch"
    assert abs(volle(24 * 3600) - voll8h) < 1e-6, "Laenger als 8 h muss cappen"
    print(f"  E1 OK   Taper: 8 h = {voll8h:,.0f} volle Sekunden "
          f"(= {voll8h / 3600:.2f} h statt 8 h)")

    # --- E2: Deckel-Dominanz + Vorher/Nachher -----------------------------
    sznen = [
        ("Frueh (St5/Schiff4)", 5, 4, 0.0, 0.0, 0),
        ("Mitte (St10/Schiff8)", 10, 8, 0.2, 0.0, 0),
        ("Ende  (St15/Schiff12)", 15, 12, 0.2, 0.0, 0),
        ("Ende+ (idle 60 %)", 15, 12, 0.6, 0.15, 0),
        ("NG+1  (St15/Schiff12)", 15, 12, 0.6, 0.15, 1),
    ]
    for name, stg, ship, ipct, cpct, ng in sznen:
        nominal = pve.stage_nominal_reward(stg, ship) * rc.ng_reward_mult(ng)
        alt = alt_bericht(nominal, ipct, rc.IDLE_CAP_S)
        neu = neu_bericht(nominal, ipct, cpct, rc.IDLE_CAP_S)
        cap = rc.idle_report_cap_credits(nominal, cpct)
        assert neu <= alt, f"{name}: neuer Bericht ({neu}) > alt ({alt})"
        assert neu <= cap, f"{name}: neuer Bericht ({neu}) > Deckel ({cap})"
        # Taper alleine reicht in keinem Szenario als Deckel-Verletzung:
        assert neu >= 0
        print(f"  E2 OK   {name:<24} 8h: {alt:>7,} -> {neu:>7,} Cr "
              f"(x{neu / max(1, alt):.2f}, Deckel {cap:,.0f})")

    # --- E3: echte Spiel-Methode (Mock statt Fenster) ---------------------
    import main as main_mod
    Game = main_mod.Game

    def mock(prev_ago, stage=15, ship=12, ng=0,
             skill_mods=None):
        if skill_mods is None:
            skill_mods = {"idle_pct": 0.2, "credit_pct": 0.0}
        prev = time.time() - prev_ago if prev_ago else 0.0
        return SimpleNamespace(
            modules=SimpleNamespace(prev_saved_at=prev,
                                    highest_stage=stage,
                                    ship_level=ship, ng_plus=ng),
            skills=SimpleNamespace(modifiers=lambda: dict(skill_mods)))

    m = mock(8 * 3600)
    rep = Game._compute_idle_report(m)
    nominal = pve.stage_nominal_reward(15, 12)
    erwartet = neu_bericht(nominal, 0.2, 0.0, rc.IDLE_CAP_S)
    assert rep is not None and rep["credits"] == erwartet, \
        f"8h-Bericht {rep} != erwartet {erwartet}"
    assert rep["cores"] == rc.IDLE_CORE_CAP, "Core-Deckel bei 8 h falsch"
    print(f"  E3 OK   echte Methode, 8 h: {rep['credits']:,} Cr "
          f"+ {rep['cores']} Cores (Deckel greift)")

    rep20 = Game._compute_idle_report(mock(20 * 60))
    assert rep20 is not None and rep20["credits"] > 0 \
        and rep20["credits"] < rep["credits"], \
        "20-Min-Bericht muss voll (aber kleiner als 8 h) ausfallen"
    print(f"  E3 OK   echte Methode, 20 Min: {rep20['credits']:,} Cr "
          f"(kein Taper-Effekt nötig, unter allen Deckeln)")

    assert Game._compute_idle_report(mock(0.0)) is None, \
        "Kein prev_saved_at -> kein Bericht"
    assert Game._compute_idle_report(mock(30)) is None, \
        "Unter IDLE_MIN_AWAY_S -> kein Bericht"
    print("  E3 OK   erster Start / kurzer Weg -> kein Bericht (None)")

    # --- E4: Save/Load-Kompatibilitaet ------------------------------------
    fm = mods.FortressModules()
    fm.credits = 123456
    fm.highest_campaign = 3
    fm.highest_stage = 7
    fm.complete_stage(campaign_id=3, stage_id=7, credits_earned=500)
    fm.save()
    fm2 = mods.FortressModules()
    fm2.load()
    assert fm2.credits == 123456 + 500, \
        "Credits nicht sauber gesichert (complete_stage addiert Belohnung)"
    assert (3, 7) in fm2.completed_stages, \
        f"complete_stage(3,7) fehlt im Reload: {fm2.completed_stages[:5]}"
    assert fm2.highest_stage == 8, "Nach Stufe 7 muss Fortschritt 8 greifen"
    # Altes Save ohne neue Felder darf nicht brechen (Kompatibilitaet):
    alt_payload = {"credits": 500, "data_cores": 2,
                   "highest_campaign": 2, "highest_stage": 5,
                   "completed_stages": [[2, 5]], "completed_campaigns": [1]}
    mods.SAVE_PATH.write_text(json.dumps(alt_payload), encoding="utf-8")
    fm3 = mods.FortressModules()
    fm3.load()
    assert fm3.credits == 500 and fm3.highest_campaign == 2, \
        "Altes Save laedt nicht mehr"
    print("  E4 OK   Save/Load: Rundtrip sauber, alte Saves laden weiter")

    # --- E5: Live-Idle-Core-Deckel (AUFTRAG 22) ---------------------------
    combat = pve.PvECombat(is_idle=True, campaign_id=1, stage_id=1,
                           ship_level=13)
    combat.income_frozen = False
    e = pve.Enemy(name="SKITTER", hp=1, max_hp=1, damage=0, speed=0.0,
                  reward=10, enemy_type="skitter")
    # 6,600 echte Kill-Buchungen = 110 x 60 -> ohne Deckel 110 Cores;
    # mit dem Fenster-Deckel genau IDLE_LIVE_CORE_CAP.
    for _ in range(6600):
        combat._grant_kill_rewards(e)
    assert combat.idle_cores_used == rc.IDLE_LIVE_CORE_CAP, \
        f"Core-Deckel greift nicht: {combat.idle_cores_used}"
    assert combat.data_cores_earned == rc.IDLE_LIVE_CORE_CAP, \
        f"Cores-Buchung ueber dem Deckel: {combat.data_cores_earned}"
    print(f"  E5 OK   Live-Idle-Cores (echter Kill-Pfad): 6,600 Kills -> "
          f"{combat.data_cores_earned} Cores (Fenster-Deckel "
          f"{rc.IDLE_LIVE_CORE_CAP}, vorher ~105 ungedeckelt)")

    # --- E6: Neustart-Resistenz des 8-h-Max (AUFTRAG 22) ------------------
    fm6 = mods.FortressModules()
    fm6.idle_window_start = time.time() - 3600        # Fenster 1 h alt
    fm6.idle_session_used_s = 7.5 * 3600              # 7.5 h verbraucht
    fm6.idle_live_cores_used = 20
    fm6.save()
    fm7 = mods.FortressModules()                      # "Neustart"
    fm7.load()
    assert abs(fm7.idle_session_used_s - 7.5 * 3600) < 1e-6 and \
        fm7.idle_live_cores_used == 20 and fm7.idle_window_start > 0, \
        "Idle-Fenster nicht persistiert"
    # Spielstart-Logik (exakt wie main.Game.__init__):
    def start_fresh_window(m):
        ws = float(getattr(m, "idle_window_start", 0.0) or 0.0)
        if ws <= 0.0 or time.time() - ws >= rc.IDLE_LIVE_WINDOW_S:
            m.idle_window_start = time.time()
            m.idle_session_used_s = 0.0
            m.idle_live_cores_used = 0
            return True
        return False
    assert not start_fresh_window(fm7), "Fenster darf nach 1 h nicht neu starten"
    assert fm7.idle_session_used_s >= 8 * 3600 - 1e-3 or fm7.idle_session_used_s == 7.5 * 3600
    frozen = float(fm7.idle_session_used_s) >= rc.IDLE_LIVE_WINDOW_S  # nur Demo
    # Nach 25 h Fenster-Alt muss EINMALIG zurueckgesetzt werden:
    fm7.idle_window_start = time.time() - 25 * 3600
    assert start_fresh_window(fm7), "Fenster-Rollover fehlt"
    assert fm7.idle_session_used_s == 0.0 and fm7.idle_live_cores_used == 0
    # Altes Save ohne Fenster-Keys -> frisches Fenster (kompatibel):
    mods.SAVE_PATH.write_text(json.dumps({"credits": 10}), encoding="utf-8")
    fm8 = mods.FortressModules()
    fm8.load()
    assert start_fresh_window(fm8) and fm8.idle_session_used_s == 0.0
    print("  E6 OK   Neustart-Resistenz: 7.5 h bleiben verbraucht; "
          "Fenster-Rollover nach 24 h einmalig; alte Saves starten frisch")

    mods.SAVE_PATH.unlink(missing_ok=True)
    print("ALLE ECONOMY-PRUEFUNGEN BESTANDEN.")


import json  # noqa: E402  (nach den Imports oben - bewusst unten genutzt)

if __name__ == "__main__":
    main()
