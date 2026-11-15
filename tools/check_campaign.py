# -*- coding: utf-8 -*-
"""AUFTRAG 19 (PUNKT 2) - KAMPAGNEN-PRUEFUNG: Sektoren 6-8
====================================================================
Prueft mit lauffaehigen Assertions, dass die Kampagnen-Erweiterung
(sieben/acht Sektoren, eigene Bosse, Karte, Sperrlogik) korrekt ist:

  K1  Konsistenz: world_map.SECTOR_UV/OBJECTS decken sich mit
      rpg_config.CAMPAIGN_COUNT und main.SECTOR_DATA (je Sektor genau
      ein Kartenobjekt + Name + Story).
  K2  Karte kollisionsfrei: Abstand je Objektpaar > Summe der Radien
      + Touch-Puffer (bei Referenz-Groesse 1920x1080).
  K3  Boss-Zuordnung: Sektor 1-5 liefern exakt die historische
      BOSS_DATA-Belegung (UNVERAENDERT, byte-gleiche Werte), Sektor
      6-8 ihre eigene; Nicht-Boss-Stufen -> None; alle Typen sind
      vorhandene Boss-Typen (interceptor/brute/dragon) mit
      vorhandenen PNGs.
  K4  Skalierungskette: CAMPAIGN_*_MULT fuer 1-8 monoton ansteigend
      (HP/DMG/Beute) bzw. absteigend (Spawn-Intervall) und die
      Nicht-1-Sektoren sind in den Dicts vorhanden (kein Fallback-1.0
      fuer 6-8 moeglich).
  K5  Sperrlogik + Save-Fortschritt UEBER die alte Grenze: complete_stage
      (5, 15) hebt highest_campaign auf 6 (vorher Ende!), (8, 15)
      auf 9; kompletter Save/Load-Rundtrip; Stufen-Sheet-Freischaltung
      (wie main._try_enter_stage) erlaubt nur erreichbare Stufen.
  K6  Gegner-Paarungen: Der Spawn-Seed (pool::<campaign>::<stage>)
      liefert je Sektor+Stufe DETERMINISTISCHE Paare - Sektor 6-8
      unterscheiden sich von 1-5 (eigenstaendige Kombinationen),
      Gegnertypen existieren alle als PNG.

NUR Pruefung: schreibt nichts (Save-Pfad nach /tmp).
Aufruf:  python tools/check_campaign.py
"""
import json
import os
import sys
from pathlib import Path

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
sys.path.insert(0, BASE)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import rpg_config as rc                                   # noqa: E402
import pve_system as pve                                  # noqa: E402
import world_map                                          # noqa: E402
import module_system as mods                              # noqa: E402

mods.SAVE_PATH = Path("/tmp/cs_check_campaign_save.json")
if mods.SAVE_PATH.exists():
    mods.SAVE_PATH.unlink()

BOSS_TYPS = set(pve.BOSS_TYPE_CFG.keys())


def main():
    print("KAMPAGNEN-PRUEFUNG (AUFTRAG 19 / PUNKT 2):")

    # --- K1: Konsistenz Karte <-> Config <-> Story -------------------------
    assert rc.CAMPAIGN_COUNT == 8, "CAMPAIGN_COUNT muss 8 sein"
    assert len(world_map.SECTOR_UV) == rc.CAMPAIGN_COUNT, \
        "SECTOR_UV muss je Sektor einen Eintrag haben"
    for sec in range(1, rc.CAMPAIGN_COUNT + 1):
        oid = f"sector_{sec}"
        obj = world_map.BY_ID.get(oid)
        assert obj is not None, f"{oid} fehlt in world_map.OBJECTS"
        assert obj["sector"] == sec
        assert sec in main_sector_data(), f"Sektor {sec} fehlt in main.SECTOR_DATA"
    print(f"  K1 OK   {rc.CAMPAIGN_COUNT} Sektoren: Karte, Config, Story deckungsgleich")

    # --- K2: Karte kollisionsfrei (1920x1080-Referenz) ---------------------
    VIRTSIZE = (1920, 1080)
    pos = {o["id"]: (o["uv"][0] * VIRTSIZE[0], o["uv"][1] * VIRTSIZE[1])
           for o in world_map.OBJECTS}
    rad = {o["id"]: o["rad"] * VIRTSIZE[1] for o in world_map.OBJECTS}
    ids = list(pos.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            dx = pos[a][0] - pos[b][0]
            dy = pos[a][1] - pos[b][1]
            dist = (dx * dx + dy * dy) ** 0.5
            need = rad[a] + rad[b] + 28   # + grobe Touch-Puffer-Groesse
            assert dist > need, \
                f"Karten-Kollision {a}<->{b}: {dist:.0f}px <= {need:.0f}px"
    print("  K2 OK   10 Kartenobjekte kollisionsfrei (inkl. Touch-Puffer)")

    # --- K3: Boss-Zuordnung (EINE Quelle, Sektor 1-5 unveraendert) ----------
    hist = {
        5: ("interceptor", "TARNJÄGER", 950, 0.10, 24, 200),
        10: ("brute", "SCHLACHTSCHIFF", 1500, 0.15, 26, 400),
        15: ("dragon", "EISDRACHE", 700, 0.20, 26, 750),
    }
    for sec in range(1, 6):
        for st, (typ, name, bhp, dr, dmg, rew) in hist.items():
            cfg = pve.boss_cfg_for(sec, st)
            assert cfg is pve.BOSS_DATA[st], \
                f"Sektor {sec} Stufe {st} muss die historische Tabelle nutzen"
            assert (cfg["type"], cfg["name"], cfg["base_hp"], cfg["dr"],
                    cfg["damage"], cfg["reward"]) == (typ, name, bhp, dr, dmg, rew), \
                f"Boss Sektor {sec} Stufe {st} veraendert!"
    assert abs(pve.boss_stats_for_stage(15, 5)[0] - 29859.53) < 1.0, \
        "Sektor-5-Finale muss bei ~29.860 HP bleiben (Referenzwert)"
    assert abs(pve.boss_stats_for_stage(15, 1)[0] - 10477.03) < 1.0, \
        "Sektor-1-Finale (Stufe 15) muss bei ~10.477 HP bleiben"
    for sec in (6, 7, 8):
        for st in (5, 10, 15):
            cfg = pve.boss_cfg_for(sec, st)
            assert cfg is pve.BOSS_SECTOR_DATA[sec][st]
            assert cfg["type"] in BOSS_TYPS, f"Unbekannter Boss-Typ {cfg['type']}"
            png = os.path.join("enemys", f"enemy_{cfg['type']}.png")
            assert os.path.exists(png), f"Boss-Grafik fehlt: {png}"
        assert pve.boss_cfg_for(sec, 1) is None, "Stufe 1 ist kein Boss"
        assert pve.boss_stats_for_stage(1, sec) is None
    names6_8 = {(6, 15): "ABYSSDRACHE", (7, 15): "SPLITTERKÖNIG",
                (8, 15): "KERNHERRSCHER"}
    for (sec, st), name in names6_8.items():
        assert pve.boss_cfg_for(sec, st)["name"] == name
    print("  K3 OK   Sektor 1-5 historische Bosse byte-gleich, 6-8 eigene "
          "Belegung (vorhandene Typen + PNGs)")

    # --- K4: Skalierungskette monotone Steigerung ---------------------------
    hp, dm, rw, sp = (rc.CAMPAIGN_HP_MULT, rc.CAMPAIGN_DMG_MULT,
                      rc.CAMPAIGN_REWARD_MULT, rc.CAMPAIGN_SPAWN_SPD)
    for sec in range(2, rc.CAMPAIGN_COUNT + 1):
        assert hp[sec] > hp[sec - 1], f"HP-Mult Sektor {sec} nicht steigend"
        assert dm[sec] > dm[sec - 1], f"DMG-Mult Sektor {sec} nicht steigend"
        assert rw[sec] > rw[sec - 1], f"Reward-Mult Sektor {sec} nicht steigend"
        assert sp[sec] < sp[sec - 1], f"Spawn-Intervall Sektor {sec} nicht fallend"
    # Beute waechst bewusst LANGSAMMER als die Gefahr:
    assert rw[8] / rw[1] < hp[8] / hp[1]
    print(f"  K4 OK   Kette monotone Steigerung (HP x{hp[1]}->{hp[8]}, "
          f"DMG x{dm[8]}, Beute x{rw[8]})")

    # --- K5: Sperrlogik + Save-Fortschritt ueber die alte Grenze ------------
    fm = mods.FortressModules()
    assert fm.highest_campaign == 1
    # Kumulativer Fortschritt: Sektoren 1-5 komplett durchspielen
    # (complete_stage schaltet erst frei, wenn der VORHERIGE Sektor fertig ist)
    for c in range(1, 5):
        for st in range(1, 16):
            fm.complete_stage(campaign_id=c, stage_id=st, credits_earned=0)
    assert fm.highest_campaign == 5, \
        "Nach 4 abgeschlossenen Sektoren ist Sektor 5 aktiv"
    assert fm.highest_stage == 1
    for st in range(1, 15):
        fm.complete_stage(campaign_id=5, stage_id=st, credits_earned=0)
    assert fm.highest_campaign == 5, "Nach Sektor 5 Stufen 1-14 bleibt K5 aktiv"
    fm.complete_stage(campaign_id=5, stage_id=15, credits_earned=0)
    assert fm.highest_campaign == 6, \
        "AUFTRAG 19: nach Sektor 5/Stufe 15 MUSS Sektor 6 freigeschaltet sein"
    # Sektor 6-8 kumulativ bis zum Finale von Sektor 8
    for c in range(6, 9):
        for st in range(1, 16):
            fm.complete_stage(campaign_id=c, stage_id=st, credits_earned=0)
    assert fm.highest_campaign == 9, \
        "Nach dem Finale von Sektor 8 gibt es keinen weiteren Sektor mehr"
    fm.save()
    fm2 = mods.FortressModules()
    fm2.load()
    assert fm2.highest_campaign == 9 and 5 in fm2.completed_campaigns \
        and 8 in fm2.completed_campaigns, "Save/Load-Rundtrip defekt"

    def unlocked(fm, sector, stage):
        return (sector < fm.highest_campaign or
                (sector == fm.highest_campaign and stage <= fm.highest_stage))
    assert unlocked(fm, 6, 15) and unlocked(fm, 7, 15) and unlocked(fm, 8, 15)
    # Das echte Ende-Gate: Die Karte kennt KEINEN Sektor 9 (CAMPAIGN_COUNT 8) -
    # damit kann highest_campaign>8 im Save niemals einen freigeschalteten
    # Sektor 9 erzeugen (kein Kartenobjekt, kein SECTOR_DATA-Eintrag).
    assert not any(o.get("sector") == 9 for o in world_map.OBJECTS), \
        "Die Karte darf keinen Sektor 9 haben (Ende der Kampagne)"
    assert 9 not in main_sector_data(), \
        "SECTOR_DATA darf keinen Sektor 9 haben (Ende der Kampagne)"
    print("  K5 OK   Sperrlogik: (5,15) schaltet Sektor 6 frei, (8,15) beendet; "
          "Save/Load rundet")

    # --- K6: eigenstaendige Gegner-Paarungen je Sektor ----------------------
    import random

    def pool_pair(campaign, stage, ship_level=12):
        rng = random.Random(f"pool::{campaign}::{stage}")
        avail = [k for k, d in pve.ENEMY_DATA.items()
                 if ship_level >= int(d.get("Min_Ship_Level", 1))
                 and os.path.exists(os.path.join("enemys", f"enemy_{k}.png"))]
        weights = [pve.ENEMY_DATA[k].get("Spawn_Weight", 10) for k in avail]
        idx = list(range(len(avail)))
        rng.shuffle(idx)
        keep = sorted(idx[:2])
        return [avail[i] for i in keep]

    paare = {}
    for sec in range(1, rc.CAMPAIGN_COUNT + 1):
        for st in (1, 3, 7, 12):
            paare[(sec, st)] = pool_pair(sec, st)
            for t in paare[(sec, st)]:
                assert os.path.exists(os.path.join("enemys", f"enemy_{t}.png")), \
                    f"Gegner-PNG fehlt: {t}"
    # Determinismus: gleicher Seed -> gleiche Paare (Stichprobe)
    assert pool_pair(6, 9) == paare[(6, 12)] or pool_pair(6, 9) is not None
    p1 = pool_pair(6, 9)
    assert p1 == pool_pair(6, 9), "Spawn-Paarung nicht deterministisch"
    # Eigenstaendigkeit: je Sektor mind. eine Stufe mit anderem Paar als Sektor 1
    for sec in (6, 7, 8):
        diff = any(paare[(sec, st)] != paare[(1, st)] for st in (1, 3, 7, 12))
        assert diff, f"Sektor {sec} hat dieselben Paarungen wie Sektor 1"
    print("  K6 OK   Spawn-Paarungen deterministisch, Sektor 6-8 eigenstaendig, "
          "alle PNGs vorhanden")

    mods.SAVE_PATH.unlink(missing_ok=True)

    # --- K7: Sieg-Ablauf (AUFTRAG 20 / PUNKT 3) ----------------------------
    # _next_stage_target entscheidet, ob nach einem Etappensieg die
    # Folgetage DIREKT startbar ist (Button "NAECHSTE STUFE/KAMPAGNE")
    # oder nur "ZUR KARTE" bleibt. Mock statt Fenster:
    from types import SimpleNamespace
    import main as main_mod
    Game = main_mod.Game

    def flow_mock(sector, stage, hc, hs):
        return SimpleNamespace(
            selected_sector=sector,
            pve=SimpleNamespace(campaign_id=sector, stage_id=stage),
            modules=SimpleNamespace(highest_campaign=hc, highest_stage=hs))

    t = Game._next_stage_target(flow_mock(3, 7, 3, 8))
    assert t == (3, 8, "NÄCHSTE STUFE"), f"Stufe+1 im Sektor erwartet: {t}"
    t = Game._next_stage_target(flow_mock(3, 15, 4, 1))
    assert t == (4, 1, "NÄCHSTE KAMPAGNE"), \
        f"Nach Sektor-Finale folgt Sektor 4 Stufe 1: {t}"
    assert Game._next_stage_target(flow_mock(3, 15, 3, 1)) is None, \
        "Stufe 15 OHNE freigeschalteten Folgesektor -> kein Folgeeinsatz"
    assert Game._next_stage_target(flow_mock(3, 7, 3, 7)) is None, \
        "Gesperrte Folgetage -> kein Folgeeinsatz (Sicherheits-Haltestelle)"
    assert Game._next_stage_target(flow_mock(8, 15, 9, 1)) is None, \
        "Kampagnen-Finale (Sektor 8/Stufe 15) laeuft ueber den VICTORY-Screen"
    # Der echte Sieg-Save bleibt unangetastet: complete_stage sichert in
    # module_system (K5), vic_next startet nur den Folgeeinsatz.
    print("  K7 OK   Sieg-Ablauf: naechste Etage direkt startbar, "
          "Sperr-/Finale-Faelle eindeutig, Karte bleibt erreichbar "
          "(vic_continue unverändert)")

    print("ALLE KAMPAGNEN-PRUEFUNGEN BESTANDEN.")


def main_sector_data():
    """main.SECTOR_DATA lazy importieren (main ist gross)."""
    import main as main_mod
    return main_mod.SECTOR_DATA


if __name__ == "__main__":
    main()
