# -*- coding: utf-8 -*-
"""BUG-VERIFIKATION (Auftrag: "Noch offene Bugs" - Nachweis pro Bug)
====================================================================
Prueft mit lauffaehigen Assertions, dass die vier gemeldeten Bugs im
Code tatsaechlich behoben sind - NICHT nur per Quelltext-Lektuere:

  Bug 1  skill_nexus._branch_layout : ein req-Zyklus (a -> b -> a) darf
         die Rekursion NICHT mehr zum Absturz bringen.
  Bug 2  pve_system._missing_hp_factor : dezimalstetig (keine
         Ganzzahl-Trunkierung mehr) - 47 % fehlende Huelle wirken wie
         47 %, nicht wie 40 %.
  Bug 3  sound_system.play_victory_audio : MP4 wird nicht mehr als
         Audiodatei versucht; fehlende Audio-Datei -> sauberer Fallback.
  Bug 4  Namenskonflikt adrenaline/adrenalin_dmg : im Spiel sind nur
         noch "adrenaline_dmg" und "adrenaline_cool" registriert.

NUR Pruefung: schreibt nichts, aendert nichts. Idempotent (Auftrag 12).
Aufruf:  python tools/check_bugs.py
"""
import inspect
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE)
sys.path.insert(0, BASE)

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def check_bug1():
    import skill_nexus
    nexus = skill_nexus.NexusUI.__new__(skill_nexus.NexusUI)
    branch = {
        "id": "test", "nodes": [
            {"id": "a", "reqs": [("b", 1)]},
            {"id": "b", "reqs": [("a", 1)]},     # ZYKLUS a <-> b
            {"id": "c", "reqs": [("c", 1)]},     # Selbst-Zyklus
            {"id": "d", "reqs": []},
        ]}
    tiers, leaves = nexus._branch_layout(branch)   # darf NICHT rekursiv explodieren
    assert set(tiers) == {"a", "b", "c", "d"}, tiers
    assert "d" in leaves, leaves
    print("  Bug 1 OK  - Zyklus (a<->b, c->c) bricht deterministisch ab, Baum wird gebaut")


def check_bug2():
    import pve_system
    c = pve_system.PvECombat(is_idle=False, campaign_id=1, stage_id=1)
    c.skill_mods = {"adrenaline_dmg": 0.02}
    c.max_player_hp = 1000.0
    f40 = None
    f47 = None
    f50 = None
    for hp, store in ((600, "f40"), (527, "f47"), (500, "f50")):
        c.player_hp = float(hp)
        val = c._missing_hp_factor()
        if store == "f40":
            f40 = val
        elif store == "f47":
            f47 = val
        else:
            f50 = val
    # stetig: 47.3 % fehlend liegt streng zwischen 40 % und 50 %
    assert f40 < f47 < f50, (f40, f47, f50)
    # exakt: 1 + 0.02 * 4.73 = 1.0946 (Trunkierung waere 1.08)
    assert abs(f47 - (1.0 + 0.02 * 4.73)) < 1e-9, f47
    print("  Bug 2 OK  - dezimalstetig: 40%% -> %.4f, 47.3%% -> %.4f, 50%% -> %.4f"
          % (f40, f47, f50))


def check_bug3():
    import ast
    import sound_system
    mod = sound_system.SoundSystem if hasattr(sound_system, "SoundSystem") \
        else sound_system.SFX
    fn = getattr(mod, "play_victory_audio", None)
    assert fn is not None, "play_victory_audio fehlt"
    src = inspect.getsource(fn)
    tree = ast.parse(src.lstrip())
    # Nur echte String-Konstanten im CODE zaehlen (Funktions-Docstring
    # ausnehmen - er dokumentiert nur den Fix, er ist kein Kandidat).
    literals = []
    fdef = tree.body[0]
    for node in ast.walk(fdef):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node is fdef.body[0].value and isinstance(fdef.body[0], ast.Expr):
                continue          # Docstring
            literals.append(node.value)
    assert not any(".mp4" in s for s in literals), \
        "play_victory_audio versucht weiterhin MP4 zu laden"
    assert any(".mp3" in s or ".ogg" in s or ".wav" in s for s in literals), \
        "keine echten Audio-Endungen mehr in der Kandidatenliste"
    sfx = getattr(sound_system, "SFX", None)
    if sfx is not None and hasattr(sfx, "play_victory_audio"):
        try:
            sfx.play_victory_audio()     # darf nie eine Exception werfen
        except Exception as e:           # noqa: BLE001
            raise AssertionError(f"play_victory_audio warf {e!r}")
    print("  Bug 3 OK  - MP4 wird nicht als Audio versucht, Fallback greift ohne Fehler")


def check_bug4():
    import ast
    with open(os.path.join(BASE, "skill_tree.py"), encoding="utf-8") as fh:
        src = fh.read()
    # Nur CODE-Strings zaehlen (Kommentare dokumentieren den alten Namen)
    keys = set()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            keys.add(node.value)
    assert "adrenaline_dmg" in keys and "adrenaline_cool" in keys, \
        "neue Schluessel fehlen"
    assert "adrenalin_dmg" not in keys, \
        "alter Schluessel adrenalin_dmg noch in Benutzung"
    assert "adrenaline" not in keys, \
        "nackter Schluessel 'adrenaline' noch in Benutzung"
    print("  Bug 4 OK  - nur adrenaline_dmg / adrenaline_cool, keine Konflikte")


def main():
    print("BUG-VERIFIKATION (alle vier gemeldeten Bugs):")
    check_bug1()
    check_bug2()
    check_bug3()
    check_bug4()
    print("ALLE 4 BUGS VERIFIZIERT BEHOBEN.")


if __name__ == "__main__":
    main()
