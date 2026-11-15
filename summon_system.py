# -*- coding: utf-8 -*-
"""CORRIDOR SLAYER | PAKET 8 - BESCHWOERUNGSSYSTEM
==================================================
Data-Cores als Beschwörungsressource: Einzel- und 10x-Beschwörung,
sammelbare Jäger-/Unterstützungsdrohnen in 4 Seltenheitsstufen.

Grundsaetze:
  - Kosten und Wahrscheinlichkeiten kommen AUSSCHLIESSLICH aus
    rpg_config.py und werden in der UI transparent angezeigt.
  - Jede Ziehung wird dauerhaft gespeichert (owned-Zaehler), Restart-
    sicher via Spielstand (Schluessel "rpg" -> "summon").
  - Duplikate geben eine definierte Credit-Entschädigung (je Seltenheit)
    - es wird bewusst KEINE weitere Waehrung eingefuehrt.
  - Die Einheiten-Träger (`stats`) sind definiert, werden aber NICHT
    automatisch angewendet: eine spaetere Anbindung ans Hangar-/Drohnen-
    system kann sie lesen, ohne bestehende Drohnenmechanik zu aendern.
  - SCHRITT 2: Besessene Einheiten/Helden wirken PASSIV - je Seltenheit
    ein Bonus auf den Drohnenschaden (collection_mods(), Werte in
    rpg_config.PASSIV_DRONE_DMG_PCT). Die `stats` bleiben weiterhin
    fuer eine spaetere direkte Hangar-Anbindung reserviert.
"""
import math
import os
import random

import pygame

import rpg_config as rcfg

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SPRITE_DIR = os.path.join(_BASE_DIR, "summon", "units")
_FX_DIR = os.path.join(_BASE_DIR, "champions", "summon_fx")
_sprite_cache = {}
_portrait_cache = {}
_ceremony_cache = {}


class SummonSystem:

    def __init__(self):
        self.owned = {}          # unit_key -> Anzahl gezogen
        # AUFTRAG 8: drei ausruestbare Champion-Slots (Champion-Key oder None).
        # Ausgeruestete Helden wirken mit ihren Stats + Faehigkeit im
        # Gefecht (main._sync_modules_to_combat / pve_system). Nur
        # BESSENE Helden sind ausruestbar; ein Key sitzt nur EINMAL.
        self.equipped = [None] * rcfg.CHAMPION_SLOTS

    # ---------------- AUFTRAG 8: Champion-Ausruestung ----------------
    def equip(self, slot, key):
        """Champion `key` in Slot `slot` ausruesten (0-basiert).
        Nur besessene Helden; ein bereits ausgeruesteter Key wechselt
        automatisch den Slot (kein Doppelsitz). Wirft ValueError bei
        ungueltigem Slot/Key oder wenn der Held nicht besessen ist."""
        if not (0 <= int(slot) < rcfg.CHAMPION_SLOTS):
            raise ValueError("Ungueltiger Champion-Slot.")
        unit = rcfg.UNITS_BY_KEY.get(key)
        if unit is None or not unit.get("hero"):
            raise ValueError("Nur Helden sind ausruestbar.")
        if key not in self.owned:
            raise ValueError("Champion nicht besessen - erst beschwoeren.")
        for i in range(len(self.equipped)):
            if self.equipped[i] == key:
                self.equipped[i] = None      # kein Doppelsitz
        self.equipped[int(slot)] = key

    def unequip(self, slot):
        """Slot freigeben (kein Fehler, wenn er leer ist)."""
        if 0 <= int(slot) < len(self.equipped):
            self.equipped[int(slot)] = None

    def equipped_heroes(self):
        """Ausgeruestete Helden als (key, Unit-Dict)-Paare (Slot-Reihenfolge,
        ohne Luecken - d.h. nur gueltige, besessene Helden). Den Key braucht
        main.py fuer rpg_config.CHAMPION_SKILLS (AUFTRAG 8)."""
        out = []
        for key in self.equipped:
            unit = rcfg.UNITS_BY_KEY.get(key) if key else None
            if unit and unit.get("hero") and key in self.owned:
                out.append((key, unit))
        return out

    # ---------------- Kosten / Chancen ----------------
    @staticmethod
    def cost(kind="single"):
        return (rcfg.SUMMON_COST_MULTI if kind == "multi"
                else rcfg.SUMMON_COST_SINGLE)

    @staticmethod
    def pull_count(kind="single"):
        return rcfg.SUMMON_MULTI_COUNT if kind == "multi" else 1

    @staticmethod
    def rates():
        """Chancen in fester Reihenfolge fuer die UI-Anzeige."""
        return [(r, rcfg.SUMMON_RATES[r]) for r in rcfg.RARITY_ORDER]

    # ---------------- Ziehen ----------------
    def _roll(self, rng):
        r = rng.random()
        acc = 0.0
        chosen = rcfg.RARITY_ORDER[-1]
        for rar in rcfg.RARITY_ORDER:
            acc += float(rcfg.SUMMON_RATES.get(rar, 0.0))
            if r < acc:
                chosen = rar
                break
        pool = rcfg.units_of_rarity(chosen)
        return pool[rng.randrange(len(pool))] if pool else rcfg.UNITS[0]

    def pull(self, cores, kind="single", rng=None):
        """Beschwörung ausfuehren. `cores` = verfuegbare Data Cores.
        Liefert Ergebnis-Dict oder wirft ValueError (zu wenig Cores).
        Gutschreiben von Credits (Duplikate) und Abzug der Cores sind
        Aufgabe des Aufrufers (main.py) - Rueckgabe enthaelt beide Werte."""
        rng = rng if rng is not None else random
        cost = self.cost(kind)
        if cores < cost:
            raise ValueError("Zu wenig Data Cores: %d benötigt." % cost)
        results = []
        credits_back = 0
        for _ in range(self.pull_count(kind)):
            unit = self._roll(rng)
            is_new = unit["key"] not in self.owned
            self.owned[unit["key"]] = self.owned.get(unit["key"], 0) + 1
            dup = 0 if is_new else int(
                rcfg.RARITY_INFO[unit["rarity"]]["dup_credits"])
            credits_back += dup
            results.append({"key": unit["key"], "new": is_new,
                            "dup_credits": dup})
        return {"spent": cost, "results": results,
                "credits_back": credits_back}

    # ---------------- Sammlung ----------------
    def collection(self):
        """Alle Einheiten + Helden mit Besitzstand (Sammlungs-Ansicht)."""
        return [{"unit": u, "count": int(self.owned.get(u["key"], 0)),
                 "owned": u["key"] in self.owned} for u in rcfg.ALL_PULLABLE]

    def unique_owned(self):
        return sum(1 for k in rcfg.UNITS_BY_KEY if k in self.owned)

    def total_owned(self):
        return sum(self.owned.values())

    # ---------------- SCHRITT 2: Sammlungs-Passiv ----------------
    def collection_mods(self):
        """Passiv-Boni der SAMMLUNG als Modifikator-Dict.
        Jede EINMALIG besessene Einheit/Held addiert den Passiv-Bonus
        ihrer Seltenheit (rpg_config.PASSIV_DRONE_DMG_PCT). Duplikate
        zaehlen nicht - nur das Halten. main._sync_modules_to_combat
        kombiniert das Dict mit dem Modifikator "drone_dmg_pct".
        Aktuell enthalten: "drone_dmg_pct" (Drohnenschaden)."""
        dmg = 0.0
        for key, n in self.owned.items():
            if n <= 0:
                continue
            unit = rcfg.UNITS_BY_KEY.get(key)
            if unit:
                dmg += float(rcfg.PASSIV_DRONE_DMG_PCT.get(unit["rarity"], 0.0))
        return {"drone_dmg_pct": dmg}

    @staticmethod
    def passiv_label(rarity):
        """Anzeige-Text des Passiv-Bonus einer Seltenheit, z. B.
        'PASSIV: +1% Drohnenschaden' (deutsches Dezimalkomma)."""
        v = float(rcfg.PASSIV_DRONE_DMG_PCT.get(rarity, 0.0))
        s = ("%g" % (v * 100.0)).replace(".", ",")
        return "PASSIV: +%s%% Drohnenschaden" % s

    @staticmethod
    def champion_stats_text(unit):
        """AUFTRAG 8: Bonus-Text der aktiven Stats eines Champions,
        z. B. 'Schaden +15% - Feuerrate +5% - +95 Huelle'.
        Mapping wie main._sync_modules_to_combat (rate invers)."""
        st = unit.get("stats") or {}
        dmg = int(round((float(st.get("dmg_mult", 1.0)) - 1.0) * 100))
        rate = int(round((1.0 - 1.0 / max(0.5, float(st.get("rate_mult", 1.0)))) * 100))
        hp = int(float(st.get("hp", 0.0)))
        teile = []
        if dmg:
            teile.append("Schaden +%d%%" % dmg)
        if rate:
            teile.append("Feuerrate +%d%%" % rate)
        if hp:
            teile.append("+%d Huille" % hp)
        return " - ".join(teile) if teile else "keine Bonuswerte"

    # ---------------- Persistenz ----------------
    def serialize(self):
        return {"owned": {k: int(v) for k, v in self.owned.items()},
                "equipped": list(self.equipped)}

    def restore(self, data):
        if not isinstance(data, dict):
            return
        raw = data.get("owned", {})
        if isinstance(raw, dict):
            known = rcfg.UNITS_BY_KEY
            self.owned = {str(k): max(0, int(v)) for k, v in raw.items()
                          if k in known and v > 0}
        # AUFTRAG 8: Champion-Slots zuruecklesen - nur gueltige, besessene
        # Helden (alte Saves ohne den Key behalten die Leer-Slots).
        eq = data.get("equipped")
        if isinstance(eq, list):
            slots = [None] * rcfg.CHAMPION_SLOTS
            for i, key in enumerate(eq[:rcfg.CHAMPION_SLOTS]):
                unit = rcfg.UNITS_BY_KEY.get(key) if key else None
                if unit and unit.get("hero") and key in self.owned \
                        and key not in slots:
                    slots[i] = key
            self.equipped = slots

    # ---------------- Sprites ----------------
    @staticmethod
    def sprite(key, size=None):
        """Sprite einer Einheit/Helden. Drohnen: PNG aus summon/units/,
        Helden: figure.png aus champions/<key>/ (seitenverhaeltnis-treu).
        Bei fehlender Datei prozeduraler Fallback - wie bei den Szenenbildern."""
        ck = (key, size)
        if ck in _sprite_cache:
            return _sprite_cache[ck]
        unit = rcfg.UNITS_BY_KEY.get(key)
        img = None
        if unit and unit.get("hero"):
            img = _hero_sprite(unit, size)
        if img is None:
            path = os.path.join(_SPRITE_DIR, "unit_%s.png" % key)
            try:
                img = pygame.image.load(path).convert_alpha()
                if size:
                    img = pygame.transform.smoothscale(img, (size, size))
            except Exception:
                if unit:
                    img = _procedural_sprite(unit, size or 128)
        _sprite_cache[ck] = img
        return img

    @staticmethod
    def portrait(key, height=None):
        """Kopfbild eines Helden (portrait.jpg) fuer Ergebniskarten.
        Liefert None bei Drohnen oder fehlender Datei."""
        unit = rcfg.UNITS_BY_KEY.get(key)
        if not unit or not unit.get("hero"):
            return None
        ck = ("portrait", key, height)
        if ck in _portrait_cache:
            return _portrait_cache[ck]
        img = None
        try:
            path = os.path.join(_BASE_DIR, unit["dir"], "portrait.jpg")
            img = pygame.image.load(path).convert()
            if height:
                w = max(1, int(img.get_width() * height / img.get_height()))
                img = pygame.transform.smoothscale(img, (w, height))
        except Exception:
            img = None
        _portrait_cache[ck] = img
        return img


# ----------------------------------------------------------------------
# Helden-Sprites + Beschoerungs-Zeremonie (PAKET 8.5)
# ----------------------------------------------------------------------
def _hero_sprite(unit, size=None):
    """figure.png eines Helden, proportional in das size-Quadrat passt
    (keine Verzerrung der schmalen Charakter-Formate)."""
    try:
        path = os.path.join(_BASE_DIR, unit["dir"], "figure.png")
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        return None
    if size:
        w0, h0 = img.get_size()
        s = size / max(1, max(w0, h0))
        img = pygame.transform.smoothscale(
            img, (max(1, int(w0 * s)), max(1, int(h0 * s))))
    return img


def ceremony_assets(tier, size):
    """PAKET 8.6: Alle Bausteine der Beschwörungs-Zeremonie.
    tier: "epic" (pink Portal) oder "normal" (cyan Kammer).

    Bewusste Inszenierung: Bei "normal" dient die KAMMER OHNE KAPSEL
    (no_backdrop_empty.jpg) als Kulisse - die geschlossene Kapsel
    (cap_normal_a/b) materialisiert sich erst waehrend der Zeremonie
    auf dem Podest. Bei "epic" bleibt das Portal-Artwork die Quelle:
    Dort laedt der Swirl (ep_05 -> ep_04 -> ep_06/ep_07) auf und die
    Einheit tritt am Ende aus dem Portal.

    Liefert: backdrop, capsules (2 Frames), energy (Schwaden, klein->
    gross), embers (Funken), flash, glow (weicher Schein), accent."""
    ck = (tier, size)
    if ck in _ceremony_cache:
        return _ceremony_cache[ck]
    W, H = size

    def load(name, alpha=True):
        try:
            img = pygame.image.load(os.path.join(_FX_DIR, name))
            return img.convert_alpha() if alpha else img.convert()
        except Exception:
            return None

    def tint(s, color):
        if s is None:
            return None
        t = s.copy()
        t.fill(color, special_flags=pygame.BLEND_MULT)
        return t

    epic = (tier == "epic")
    accent = (226, 80, 255) if epic else (90, 220, 255)

    # --- Kulisse: normal NUR die leere Kammer (keine Kapsel sichtbar!) ---
    bname = "ep_backdrop.jpg" if epic else "no_backdrop_empty.jpg"
    bg = load(bname, alpha=False)
    if bg is None and not epic:
        bg = load("no_backdrop.jpg", alpha=False)      # Rueckfallebene
    if bg is None:
        bg = pygame.Surface((W, H))
        bg.fill((10, 6, 18) if epic else (5, 12, 17))
    if (bg.get_width(), bg.get_height()) != (W, H):
        bg = pygame.transform.smoothscale(bg, (W, H))

    # --- Geschlossene Kapseln (nutzergenerierte Sprites) ---
    capsules = []
    if epic:
        cap = load("cap_epic_b.png")
        if cap is not None:
            capsules.append(cap)
            capsules.append(pygame.transform.flip(cap, True, False))
    else:
        for n in ("cap_normal_a.png", "cap_normal_b.png"):
            cap = load(n)
            if cap is not None:
                capsules.append(cap)
    if not capsules:
        # Prozeduraler Fallback: dunkle Punktkapsel mit Streifen
        s = pygame.Surface((200, 260), pygame.SRCALPHA)
        pygame.draw.rect(s, (24, 30, 40), (30, 20, 140, 220),
                         border_radius=26)
        pygame.draw.rect(s, accent, (44, 40, 16, 180), border_radius=8)
        pygame.draw.rect(s, accent, (140, 40, 16, 180), border_radius=8)
        capsules = [s]

    # --- Energie-Schwaden (Portal/Saeule): klein -> gross ---
    energy = []
    for n in ("ep_05.png", "ep_04.png", "ep_06.png", "ep_07.png"):
        s = load(n)
        if s is not None:
            energy.append(s if epic else tint(s, (120, 228, 255)))
    if not energy:
        f = pygame.Surface((120, 170), pygame.SRCALPHA)
        pygame.draw.ellipse(f, accent, f.get_rect().inflate(-24, -30))
        energy = [f]

    # --- Funken / Glutpartikel ---
    embers = []
    for n in ("ep_21.png", "ep_22.png", "ep_23.png", "ep_24.png"):
        s = load(n)
        if s is not None:
            embers.append(s if epic else tint(s, (150, 230, 255)))
    if not embers:
        embers = energy

    # --- Burst-Flash (Energie-Blitz aus dem Sheet) ---
    flash = load("ep_17.png")
    if flash is not None and not epic:
        flash = tint(flash, (170, 235, 255))
    if flash is None:
        flash = pygame.Surface((260, 260), pygame.SRCALPHA)
        pygame.draw.circle(flash, accent, (130, 130), 108)
        pygame.draw.circle(flash, (255, 255, 255), (130, 130), 66)

    def premultiply(s):
        """Additiv-Bleiting braucht opake, prae-multiplizierte Quellen
        (BLEND_ADD addiert sonst die volle RGB-Flaeche und ignoriert die
        weichen Alpha-Kanten). RGB wird mit Alpha skaliert und auf ein
        schwarzes, opakes Surface kopiert. Ohne numpy: Alpha einfach
        verwerfen (Transparenz wird Schwarz - bleibt additiv harmlos)."""
        if s is None:
            return None
        opaque = pygame.Surface(s.get_size()).convert()
        opaque.fill((0, 0, 0))
        try:
            import numpy as np
            arr = pygame.surfarray.pixels3d(s)          # W x H x 3 (Ref!)
            al = pygame.surfarray.pixels_alpha(s)       # W x H
            mult = al.astype(np.uint16)[:, :, None]
            arr[:] = (arr.astype(np.uint16) * mult // 255).astype(np.uint8)
            del arr, al
            opaque.blit(s, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        except Exception:
            opaque = s.convert()    # Fallback: Alpha weg -> schwarz drauf
        return opaque

    # --- Weicher additiver Schein (prozedural, einmalig gebaut) ---
    glow = pygame.Surface((256, 256)).convert()
    glow.fill((0, 0, 0))
    for r in range(128, 0, -2):
        k = (1.0 - r / 128.0) ** 1.7
        pygame.draw.circle(glow,
                           tuple(int(c * k * 0.62) for c in accent),
                           (128, 128), r)

    out = {"backdrop": bg, "capsules": capsules, "energy": energy,
           "embers": embers, "flash": flash, "glow": glow, "accent": accent,
           "energy_pm": [premultiply(s) for s in energy],
           "flash_pm": premultiply(flash)}
    _ceremony_cache[ck] = out
    return out


# ----------------------------------------------------------------------
# Prozeduraler Fallback (kein PNG noetig, sieht trotzdem gut aus)
# ----------------------------------------------------------------------
def _procedural_sprite(unit, size=128):
    rng = random.Random("cs8::" + unit["key"])
    rar_col = rcfg.RARITY_INFO[unit["rarity"]]["color"]
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    hull = tuple(min(255, int(c * 0.55)) for c in rar_col)
    dark = tuple(max(0, int(c * 0.28)) for c in rar_col)

    def poly(points, color):
        pygame.draw.polygon(s, color, points)

    n_wings = rng.choice((2, 3))
    span = int(size * rng.uniform(0.34, 0.46))
    body_w = int(size * rng.uniform(0.13, 0.19))
    # Tragflaechen / Ausleger
    for i in range(n_wings):
        off = -span + (2 * span) * (i / max(1, n_wings - 1)) if n_wings > 1 else 0
        tilt = rng.randint(-14, 14)
        poly([(cx + off - body_w // 2, size * 0.52 + tilt),
              (cx + off + body_w // 2, size * 0.50 + tilt),
              (cx + int(off * 0.55), size * 0.30)], dark)
        poly([(cx + off - body_w // 2, size * 0.52 + tilt),
              (cx + off + body_w // 2, size * 0.50 + tilt),
              (cx + int(off * 0.55), size * 0.76)], hull)
    # Rumpf (gestrecktes Sechseck)
    bw = body_w
    poly([(cx, size * 0.16), (cx + bw, size * 0.38), (cx + int(bw * 0.7), size * 0.74),
          (cx, size * 0.88), (cx - int(bw * 0.7), size * 0.74), (cx - bw, size * 0.38)],
         hull)
    # Cockpit-Glow
    glow_r = max(6, size // 12)
    pygame.draw.circle(s, rar_col, (cx, int(size * 0.34)), glow_r)
    pygame.draw.circle(s, (255, 255, 255),
                       (cx, int(size * 0.34)), max(2, glow_r // 3))
    # Triebwerke
    for i in range(n_wings + 1):
        ex = cx - span + (2 * span) * (i / n_wings)
        ey = int(size * 0.80)
        pygame.draw.circle(s, rar_col, (int(ex), ey), max(3, size // 22))
    # Raritaets-Rahmen
    pygame.draw.rect(s, rar_col, s.get_rect().inflate(-2, -2), 2, border_radius=10)
    # dezente Scanlinie
    for y in range(0, size, 6):
        pygame.draw.line(s, (255, 255, 255, 10), (0, y), (size, y))
    return s
