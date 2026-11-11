# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 8 - SPIELERPROGRESSION (XP / LEVEL / QUANTUM)
========================================================================
Eigenstaendiges Spielerlevel ueber den Modul- und Skill-Systemen:

  - XP aus Kampagnenmissionen und Quests
  - Levelaufstieg ueber die zentrale Kurve (rpg_config.xp_for_level)
  - Premium-Waehrung QUANTUM (neu, getrennt von Credits/Data Cores)

WICHTIG: Das Spielerlevel veraendert bewusst KEINE bestehenden Modul-,
Schiffs- oder Gefechtswerte. Es dient der langfristigen Progression und
spaeteren Freischaltungen (Architektur dafuer: `level` abfragbar).

Persistenz: der Spielstand (corridor_slayer_modules.json) wird um den
Schluessel "rpg" erweitert; alte Saves ohne diesen Schluessel erhalten
sichere Defaults (siehe module_system.FortressModules).
"""
import rpg_config as rcfg


class PlayerProgress:
    """Spielerlevel + XP + Premium-Waehrung."""

    def __init__(self):
        self.level = 1
        self.xp = 0
        self.quantum = 0
        self.total_xp = 0

    # ---------------- XP ----------------
    def xp_to_next(self):
        """XP, die zum naechsten Level fehlen (None auf Maximallevel)."""
        need = rcfg.xp_for_level(self.level)
        if need is None:
            return None
        return max(0, need - self.xp)

    def xp_ratio(self):
        """Fortschritt zum naechsten Level als 0..1 (1.0 = aufgestiegen)."""
        need = rcfg.xp_for_level(self.level)
        if need is None:
            return 1.0
        return max(0.0, min(1.0, self.xp / float(need)))

    def add_xp(self, amount):
        """XP gutschreiben; liefert (new_levels, total_gained).
        Mehrfachaufstiege in einem Ruf werden korrekt verarbeitet."""
        amount = max(0, int(amount))
        if amount <= 0:
            return 0, 0
        self.xp += amount
        self.total_xp += amount
        ups = 0
        while True:
            need = rcfg.xp_for_level(self.level)
            if need is None or self.xp < need:
                break
            self.xp -= need
            self.level += 1
            ups += 1
        return ups, amount

    # ---------------- QUANTUM (Premium) ----------------
    def add_quantum(self, amount):
        self.quantum = max(0, self.quantum + int(amount))

    def spend_quantum(self, amount):
        amount = int(amount)
        if self.quantum < amount:
            return False
        self.quantum -= amount
        return True

    # ---------------- Persistenz ----------------
    def serialize(self):
        return {"level": int(self.level), "xp": int(self.xp),
                "quantum": int(self.quantum), "total_xp": int(self.total_xp)}

    def restore(self, data):
        if not isinstance(data, dict):
            return
        self.level = max(1, int(data.get("level", 1)))
        self.xp = max(0, int(data.get("xp", 0)))
        self.quantum = max(0, int(data.get("quantum", 0)))
        self.total_xp = max(0, int(data.get("total_xp", 0)))
        # Konsistenz-Klammer: Level nie ueber die Kurve hinaus fuettern
        while self.level > 1 and rcfg.xp_for_level(self.level - 1) is not None \
                and self.xp >= rcfg.xp_for_level(self.level):
            need = rcfg.xp_for_level(self.level)
            if need is None:
                break
            self.xp -= need
            self.level += 1


class RPGBundle:
    """Vereint Progress, Quests und Beschoerung zu EINEM Serialisierungs-
    block fuer den Spielstand (Schluessel "rpg" in corridor_slayer_modules.json)."""

    def __init__(self, progress, quests, summon):
        self.progress = progress
        self.quests = quests
        self.summon = summon

    def serialize(self):
        return {
            "progress": self.progress.serialize(),
            "quests": self.quests.serialize(),
            "summon": self.summon.serialize(),
        }

    def restore(self, data):
        if not isinstance(data, dict):
            return
        self.progress.restore(data.get("progress", {}))
        self.quests.restore(data.get("quests", {}))
        self.summon.restore(data.get("summon", {}))
