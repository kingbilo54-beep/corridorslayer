# -*- coding: utf-8 -*-
"""Persistente Spielerprogression mit robustem Laden alter RPG-Spielstaende."""
import rpg_config as rcfg


def _int_field(data, key, default=0, minimum=None, maximum=None):
    """Liest eine einzelne Zahl ohne dass ein kaputtes Feld andere Daten killt."""
    value = data.get(key, default)
    if isinstance(value, bool):
        value = default
    try:
        value = int(value)
    except (TypeError, ValueError, OverflowError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    if maximum is not None:
        value = min(maximum, value)
    return value


class PlayerProgress:
    def __init__(self):
        self.level = 1
        self.xp = 0
        self.quantum = 0
        self.total_xp = 0

    def xp_to_next(self):
        need = rcfg.xp_for_level(self.level)
        return None if need is None else max(0, need - self.xp)

    def xp_ratio(self):
        need = rcfg.xp_for_level(self.level)
        if need is None:
            return 1.0
        return max(0.0, min(1.0, self.xp / float(need)))

    def add_xp(self, amount):
        try:
            amount = int(amount)
        except (TypeError, ValueError, OverflowError):
            return 0, 0
        amount = max(0, amount)
        if amount <= 0 or self.level >= rcfg.PLAYER_MAX_LEVEL:
            return 0, 0
        self.xp += amount
        self.total_xp += amount
        ups = 0
        while self.level < rcfg.PLAYER_MAX_LEVEL:
            need = rcfg.xp_for_level(self.level)
            if self.xp < need:
                break
            self.xp -= need
            self.level += 1
            ups += 1
        if self.level >= rcfg.PLAYER_MAX_LEVEL:
            self.xp = 0
        return ups, amount

    def add_quantum(self, amount):
        try:
            amount = int(amount)
        except (TypeError, ValueError, OverflowError):
            return False
        if amount < 0:
            return False
        self.quantum += amount
        return True

    def spend_quantum(self, amount):
        if isinstance(amount, bool):
            return False
        try:
            amount = int(amount)
        except (TypeError, ValueError, OverflowError):
            return False
        if amount < 0 or self.quantum < amount:
            return False
        self.quantum -= amount
        return True

    def serialize(self):
        return {"level": int(self.level), "xp": int(self.xp),
                "quantum": int(self.quantum), "total_xp": int(self.total_xp),
                "progression_version": 2}

    def restore(self, data):
        if not isinstance(data, dict):
            return
        level = _int_field(data, "level", 1, 1, rcfg.PLAYER_MAX_LEVEL)
        xp = _int_field(data, "xp", 0, 0)
        quantum = _int_field(data, "quantum", 0, 0)
        total_xp = _int_field(data, "total_xp", 0, 0)
        version = _int_field(data, "progression_version", 0, 0)
        if version < 2 and level < rcfg.PLAYER_MAX_LEVEL:
            old_need = max(1, int(round(300 * (1.32 ** (level - 1)))))
            new_need = rcfg.xp_for_level(level)
            xp = min(new_need - 1, int(xp * new_need / old_need))
        if level >= rcfg.PLAYER_MAX_LEVEL:
            level, xp = rcfg.PLAYER_MAX_LEVEL, 0
        else:
            while level < rcfg.PLAYER_MAX_LEVEL and xp >= rcfg.xp_for_level(level):
                xp -= rcfg.xp_for_level(level)
                level += 1
            if level >= rcfg.PLAYER_MAX_LEVEL:
                xp = 0
        self.level, self.xp = level, xp
        self.quantum, self.total_xp = quantum, total_xp


class RPGBundle:
    def __init__(self, progress, quests, summon):
        self.progress, self.quests, self.summon = progress, quests, summon

    def serialize(self):
        return {"progress": self.progress.serialize(),
                "quests": self.quests.serialize(),
                "summon": self.summon.serialize()}

    def restore(self, data):
        if not isinstance(data, dict):
            return
        # Ein fehlerhafter Unterblock darf andere gueltige RPG-Daten nicht
        # verhindern. Jede Implementierung verwirft nur eigene kaputte Felder.
        for key, target in (("progress", self.progress), ("quests", self.quests),
                            ("summon", self.summon)):
            raw = data.get(key)
            if not isinstance(raw, dict):
                continue
            try:
                target.restore(raw)
            except Exception:
                # Default des betroffenen Subsystems beibehalten. Validierte
                # Einzel-Feld-Wiederherstellung bewahrt gueltige Geschwister.
                continue
