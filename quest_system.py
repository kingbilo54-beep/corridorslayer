# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 8 - QUEST-SYSTEM (DAILY / WEEKLY)
============================================================
Eigenstaendige Quest-UEbersicht mit zwei Bereichen:

  - DAILY : Reset taeglich um Mitternacht der lokalen Systemzeit,
            4 Aufgaben aus dem Pool (Rotation, deterministisch je Tag).
  - WEEKLY: Reset montags um Mitternacht lokal (ISO-Woche),
            5 Aufgaben aus dem Pool, groessere Ziele/Belohnungen.

Grundsaetze:
  - Fortschritt entsteht AUSSCHLIESSLICH durch echte Gameplay-Ereignisse
    (record(...) aus main.py: Kills, Missionsabschluesse, Upgrades...).
  - Fortschritt, Reset-Schluessel und abgeholte Belohnungen werden
    dauerhaft gespeichert (serialize/restore) - ein Neustart setzt
    nichts zurueck.
  - Innerhalb eines Zeitraums kann jede Belohnung nur EINMAL abgeholt
    werden; der Reset gibt keine abgeholten Belohnungen erneut frei
    (neuer Zeitraum = neue Aufgaben mit neuem Fortschritt).
  - Tages-/Wochenabschlussbonus einmal je Zeitraum.
"""
import datetime
import random

import rpg_config as rcfg


def day_key(now=None):
    """Schluessel des Tages (lokal): 'YYYY-MM-DD'. Reset um Mitternacht."""
    return (now or datetime.datetime.now()).date().isoformat()


def week_key(now=None):
    """Schluessel der ISO-Woche (lokal): 'YYYY-Wnn' - ISO-Wochen beginnen
    montags, der Schluessel wechselt also exakt Montag 00:00 lokal."""
    y, w, _ = (now or datetime.datetime.now()).isocalendar()
    return "%04d-W%02d" % (y, w)


def pick_pool(pool, count, period):
    """Deterministische Rotation: derselbe Tag/Woche -> dieselben Aufgaben."""
    items = list(pool)
    random.Random("CS8::%s" % period).shuffle(items)
    return items[:max(0, min(count, len(items)))]


def _new_scope():
    return {"period": "", "prog": {}, "claimed": [], "bonus_claimed": False}


class QuestSystem:
    def __init__(self):
        self.daily = _new_scope()
        self.weekly = _new_scope()
        # Temporaerer Missionszustand (bewusst NICHT Teil des Spielstands):
        # True, solange die laufende Mission ohne Niederlage verlaeuft.
        self.mission_clean = True
        self.refresh()

    # ---------------- Reset-Logik ----------------
    def refresh(self, now=None):
        """Perioden-Schluessel pruefen (billig, jederzeit aufrufbar).
        Wechselt der Tag/die Woche, werden Fortschritt und Abhol-Marken
        des Bereichs neu aufgesetzt (neue Perioden = neue Aufgaben)."""
        now = now or datetime.datetime.now()
        dk, wk = day_key(now), week_key(now)
        if self.daily["period"] != dk:
            self.daily = {"period": dk, "prog": {}, "claimed": [],
                          "bonus_claimed": False}
        if self.weekly["period"] != wk:
            self.weekly = {"period": wk, "prog": {}, "claimed": [],
                           "bonus_claimed": False}

    # ---------------- Aktive Aufgaben ----------------
    def active_defs(self, scope_key):
        """Aktive Quest-Definitionen des Bereichs ('daily'/'weekly')."""
        if scope_key == "daily":
            return pick_pool(rcfg.DAILY_POOL, rcfg.DAILY_ACTIVE,
                             self.daily["period"])
        return pick_pool(rcfg.WEEKLY_POOL, rcfg.WEEKLY_ACTIVE,
                         self.weekly["period"])

    def progress_of(self, scope_key, qid):
        scope = self.daily if scope_key == "daily" else self.weekly
        return int(scope["prog"].get(qid, 0))

    def is_claimed(self, scope_key, qid):
        scope = self.daily if scope_key == "daily" else self.weekly
        return qid in scope["claimed"]

    # ---------------- Fortschritt (echte Gameplay-Ereignisse) ----------------
    def record(self, metric, amount=1):
        """Fortschritt fuer ALLE aktiven Aufgaben mit dieser Metrik
        buchen (Daily + Weekly gleichzeitig). amount >= 1."""
        amount = max(0, int(amount))
        if amount <= 0:
            return
        for scope_key, scope in (("daily", self.daily), ("weekly", self.weekly)):
            for q in self.active_defs(scope_key):
                if q["metric"] != metric:
                    continue
                cur = int(scope["prog"].get(q["id"], 0))
                scope["prog"][q["id"]] = min(q["goal"], cur + amount)

    def record_mission_clear(self):
        """Abschluss einer aktiven Kampagnenmission. Zaehlt als 'stages'
        und - sofern ohne Niederlage - zusaetzlich als 'mission_clean'."""
        self.record("stages", 1)
        if self.mission_clean:
            self.record("mission_clean", 1)
        self.mission_clean = True    # naechster Versuch startet sauber

    def begin_mission(self):
        """Start/Neustart einer Mission: Niederlage-Zaehler zuruecksetzen."""
        self.mission_clean = True

    def note_loss(self):
        """Niederlage erlitten - die laufende Mission ist nicht mehr 'clean'."""
        self.mission_clean = False

    # ---------------- Abholen ----------------
    def claim(self, scope_key, qid):
        """Einzelbelohnung abholen. Liefert das Reward-Dict oder None
        (bereits abgeholt / nicht abgeschlossen / nicht aktiv)."""
        self.refresh()
        scope = self.daily if scope_key == "daily" else self.weekly
        for q in self.active_defs(scope_key):
            if q["id"] != qid:
                continue
            if qid in scope["claimed"]:
                return None
            if int(scope["prog"].get(qid, 0)) < q["goal"]:
                return None
            scope["claimed"].append(qid)
            return dict(q["rewards"])
        return None

    def all_complete(self, scope_key):
        scope = self.daily if scope_key == "daily" else self.weekly
        for q in self.active_defs(scope_key):
            if int(scope["prog"].get(q["id"], 0)) < q["goal"]:
                return False
        return True

    def claim_bonus(self, scope_key):
        """Tages-/Wochenabschlussbonus (einmal je Zeitraum, nur wenn
        ALLE Aufgaben des Bereichs abgeschlossen sind)."""
        self.refresh()
        scope = self.daily if scope_key == "daily" else self.weekly
        if scope["bonus_claimed"] or not self.all_complete(scope_key):
            return None
        scope["bonus_claimed"] = True
        return dict(rcfg.DAILY_BONUS if scope_key == "daily" else rcfg.WEEKLY_BONUS)

    # ---------------- UI-Helfer ----------------
    def claimable_count(self, scope_key):
        n = 0
        scope = self.daily if scope_key == "daily" else self.weekly
        for q in self.active_defs(scope_key):
            if (q["id"] not in scope["claimed"]
                    and int(scope["prog"].get(q["id"], 0)) >= q["goal"]):
                n += 1
        if not scope["bonus_claimed"] and self.all_complete(scope_key):
            n += 1
        return n

    def any_claimable(self):
        return (self.claimable_count("daily") + self.claimable_count("weekly")) > 0

    @staticmethod
    def bonus_ready(scope_key):
        """Text-Baustein fuer die UI (welcher Bonus wartet)."""
        return "TAGESABSCHLUSSBONUS" if scope_key == "daily" else "WOCHENABSCHLUSSBONUS"

    # ---------------- Persistenz ----------------
    def serialize(self):
        return {"daily": {k: (list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v)
                          for k, v in self.daily.items()},
                "weekly": {k: (list(v) if isinstance(v, list) else dict(v) if isinstance(v, dict) else v)
                           for k, v in self.weekly.items()}}

    def restore(self, data):
        if not isinstance(data, dict):
            return
        for key, scope in (("daily", self.daily), ("weekly", self.weekly)):
            raw = data.get(key)
            if not isinstance(raw, dict):
                continue
            scope["period"] = str(raw.get("period", ""))
            prog = raw.get("prog", {})
            scope["prog"] = {str(k): max(0, int(v))
                             for k, v in prog.items()} if isinstance(prog, dict) else {}
            claimed = raw.get("claimed", [])
            scope["claimed"] = [str(x) for x in claimed] if isinstance(claimed, list) else []
            scope["bonus_claimed"] = bool(raw.get("bonus_claimed", False))
        self.refresh()   # perioden-fremde Daten (alter Tag/alte Woche) direkt umsetzen
