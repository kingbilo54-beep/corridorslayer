# -*- coding: utf-8 -*-
"""
CORRIDOR SLAYER - PAKET 4: OVERHAUL
====================================
Victory-Fix + Damage-Numbers + Skill-Tree + Balancing

Verwendung:   py patch_paket4.py     (im DS4-Ordner ausfuehren, neben main.py)

Phasen:
  A  Basis (Paket 3 - wird automatisch uebersprungen, falls schon installiert):
     sound_system.py (Retro-SFX), Tonspur aus victory_screen.mp4 extrahieren,
     Sieg fuehrt jetzt zum STAGE_CLEAR-Screen mit deinem Victory-Video + Ton.
  B  Damage-Numbers: schwebende Schadenszahlen am Trefferpunkt
     (Gegner-Schaden=Cyan, Krit=Amber+fett, Schaden am Spieler=Rot).
  C  Skill-Tree: neue Datei skill_tree.py + TECH-TERMINAL im Hauptmenue.
     4 Sparten (Waffen/Verteidigung/Energie/Spezial), bezahlt mit Data Cores.
     UEBERTAKTUNG: Taste Q im Gefecht. Taste M: Sound an/aus.
  D  Balancing: globale Koeffizienten - Spieler x1.6 Schaden / x1.4 Huelle,
     Gegner x0.85 HP / x0.7 Schaden, Grundreparatur 1.5 HP/s, Idle liefert
     jetzt auch Data Cores (1 pro 25 Kills).

Sicherheit: Backups (*_backup_paket4.py), Assertions auf Code-Anker,
idempotent (mehrfach ausfuehrbar), bricht ab statt Dateien zu verfaelschen.
"""
import shutil
import subprocess
import py_compile
from pathlib import Path

SOUND_SYSTEM_SOURCE = '"""CORRIDOR SLAYER | Prozeduraler Sound: Retro-SFX komplett ohne Asset-Dateien."""\nimport random\nimport numpy as np\nimport pygame\n\n\nclass SoundSystem:\n    """Erzeugt alle Effekte per Synthese - kein Download, keine WAV-Dateien."""\n\n    def __init__(self):\n        self.enabled = True\n        self.muted = False\n        self._built = False\n        self.sounds = {}\n\n    # ---------- interne Helfer ----------\n    def _ensure_built(self):\n        if self._built or not self.enabled:\n            return\n        try:\n            if pygame.mixer.get_init() is None:\n                pygame.mixer.init()\n        except Exception as e:\n            print(f"⚠️ Kein Audiogerät: {e}")\n            self.enabled = False\n            return\n        try:\n            self._generate_sounds()\n            self._built = True\n            print("✅ Sound-System bereit (Taste M = stumm schalten).")\n        except Exception as e:\n            print(f"⚠️ Sound-System deaktiviert: {e}")\n            self.enabled = False\n\n    def _mixer_format(self):\n        freq, _fmt, channels = pygame.mixer.get_init()\n        return int(freq), max(1, int(channels))\n\n    def _to_sound(self, wave):\n        freq, channels = self._mixer_format()\n        wave = np.clip(wave, -1.0, 1.0)\n        pcm = (wave * 32000.0).astype(np.int16)\n        if channels > 1:\n            pcm = np.repeat(pcm[:, None], channels, axis=1)\n        return pygame.sndarray.make_sound(np.ascontiguousarray(pcm))\n\n    def _tone(self, f_start, f_end, seconds, vol=0.8, shape="sine"):\n        freq, _ = self._mixer_format()\n        n = int(freq * seconds)\n        f = np.linspace(f_start, f_end, n)\n        phase = np.cumsum(2.0 * np.pi * f / freq)\n        if shape == "square":\n            w = np.sign(np.sin(phase)) * 0.55\n        else:\n            w = np.sin(phase)\n        env = np.exp(-np.linspace(0.0, 6.0, n))\n        attack = max(1, int(0.004 * freq))\n        env[:attack] *= np.linspace(0.0, 1.0, attack)\n        return w * env * vol\n\n    def _noise(self, seconds, vol=0.8, smooth=1):\n        freq, _ = self._mixer_format()\n        n = int(freq * seconds)\n        w = np.random.uniform(-1.0, 1.0, n)\n        for _ in range(smooth):\n            w = np.convolve(w, np.ones(5) / 5.0, mode="same")\n        env = np.exp(-np.linspace(0.0, 7.0, n))\n        attack = max(1, int(0.002 * freq))\n        env[:attack] *= np.linspace(0.0, 1.0, attack)\n        return w * env * vol\n\n    def _seq(self, notes, seconds_each, vol=0.6, shape="sine"):\n        return np.concatenate([self._tone(f, f, seconds_each, vol, shape) for f in notes])\n\n    def _generate_sounds(self):\n        self.sounds["click"] = [self._to_sound(self._tone(1400, 900, 0.05, 0.45))]\n        self.sounds["shoot"] = [\n            self._to_sound(self._tone(random.uniform(1250, 1550), 280, 0.09, 0.55))\n            for _ in range(3)\n        ]\n        self.sounds["hit"] = [self._to_sound(self._tone(220, 90, 0.12, 0.7) + self._noise(0.12, 0.3, 1))]\n        self.sounds["explosion"] = [\n            self._to_sound(self._noise(0.45, 0.85, 2) + self._tone(90, 40, 0.45, 0.45))\n            for _ in range(2)\n        ]\n        self.sounds["upgrade"] = [self._to_sound(self._seq([523.25, 783.99], 0.09, 0.5, "square"))]\n        self.sounds["victory"] = [self._to_sound(self._seq([523.25, 659.25, 783.99, 1046.50], 0.15, 0.55, "square"))]\n\n    # ---------- öffentliche API ----------\n    def play(self, name, volume=1.0):\n        if not self.enabled or self.muted:\n            return False\n        self._ensure_built()\n        pool = self.sounds.get(name)\n        if not pool:\n            return False\n        snd = random.choice(pool)\n        snd.set_volume(max(0.0, min(1.0, volume)))\n        snd.play()\n        return True\n\n    def play_victory_audio(self):\n        """Sieg-Sound: echte Video-Tonspur, sonst synthetischer Jingle."""\n        for name in ("victory_audio.mp3", "victory_audio.ogg", "victory_screen.mp4", "victory_audio.wav"):\n            if self._play_music(name):\n                return True\n        self.play("victory", 0.8)\n        return False\n\n    def _play_music(self, filename):\n        if not self.enabled or self.muted:\n            return False\n        try:\n            if pygame.mixer.get_init() is None:\n                pygame.mixer.init()\n            pygame.mixer.music.load(filename)\n            pygame.mixer.music.play()\n            return True\n        except Exception:\n            return False\n\n    def stop_music(self, fade_ms=400):\n        try:\n            if pygame.mixer.get_init() is not None and pygame.mixer.music.get_busy():\n                pygame.mixer.music.fadeout(fade_ms)\n        except Exception:\n            pass\n\n    def toggle_mute(self):\n        self.muted = not self.muted\n        if self.muted:\n            self.stop_music(150)\n        return self.muted\n\n\nSFX = SoundSystem()\n'

SKILL_TREE_SOURCE = '"""CORRIDOR SLAYER | Skill-Tree: permanente Faehigkeiten, bezahlt mit Data Cores.\n\nSparten: WAFFENSYSTEME / VERTEIDIGUNG / ENERGIE & OEKONOMIE / SPEZIALSYSTEME\nDie Effekte landen als "skill_mods"-Dictionary in PvECombat (apply_to_combat)\nund werden dort von den Schadens-/Feuerraten-Formeln gelesen.\nGespeichert wird in corridor_slayer_skills.json (neben dieser Datei).\n"""\nimport json\nfrom pathlib import Path\n\nSAVE_PATH = Path(__file__).with_name("corridor_slayer_skills.json")\n\n# Voraussetzung pro Node-Position: Summe der Stufen ALLER Vorgaenger in der Sparte\nPREREQ_THRESHOLDS = [0, 1, 2, 4, 6]\n\n# Sparten-Farben (main.py nutzt dieselben Werte fuer die UI)\nCOLOR_WAFFEN = (255, 62, 177)\nCOLOR_VERT = (0, 255, 255)\nCOLOR_ENER = (255, 190, 76)\nCOLOR_SPEZ = (153, 94, 255)\n\n\ndef _node(node_id, name, desc, max_lvl, costs):\n    return {"id": node_id, "name": name, "desc": desc, "max": max_lvl, "costs": costs}\n\n\nSKILL_TREE = [\n    {"id": "waffen", "name": "WAFFENSYSTEME", "color": COLOR_WAFFEN, "nodes": [\n        _node("waffen_dmg", "GEWEHRVERSTÄRKER", "Erhoeht den Schaden aller Kanonen dauerhaft.", 5, [8, 16, 24, 32, 40]),\n        _node("waffen_rate", "SCHNELLFEUER", "Verkuerzt das Feuerintervall der Kanonen.", 5, [8, 16, 24, 32, 40]),\n        _node("waffen_salve", "MEHRFACHLAUF", "Zusaetzlicher Projektilabwurf pro Salve.", 2, [25, 50]),\n        _node("waffen_krit", "ZIELRECHNER", "Chance auf kritische Treffer (Doppelschaden).", 5, [8, 16, 24, 32, 40]),\n        _node("waffen_kritschaden", "PANZERBRECHER", "Verstaerkt kritischen Schaden ueber 2.0x hinaus.", 4, [10, 20, 30, 40]),\n    ]},\n    {"id": "verteidigung", "name": "VERTEIDIGUNG", "color": COLOR_VERT, "nodes": [\n        _node("vert_panzerung", "VERSTÄRKTE HÜLLE", "Erhoeht die maximale Huellenintegritaet.", 5, [8, 16, 24, 32, 40]),\n        _node("vert_nano", "NANO-REPARATUR", "Kontinuierliche Hullen-Reparatur pro Sekunde.", 5, [8, 16, 24, 32, 40]),\n        _node("vert_schild", "ABFANG-FELD", "Reduziert allen erlittenen Schaden.", 2, [25, 50]),\n        _node("vert_kuehlung", "NOTKÜHLUNG", "Feuerrate +25% solange Huelle unter 30%.", 1, [40]),\n        _node("vert_puls", "PULSGENERATOR", "Nach einem Treffer: 2 Gegen-Pulse auf naechste Gegner.", 4, [10, 20, 30, 40]),\n    ]},\n    {"id": "energie", "name": "ENERGIE & ÖKONOMIE", "color": COLOR_ENER, "nodes": [\n        _node("ener_leitung", "ENERGIELEITUNG", "Erhoeht den Schaden der Hangar-Drohnen.", 5, [8, 16, 24, 32, 40]),\n        _node("ener_taktik", "HANGAR-TAKTIK", "Startet zusaetzliche Drohnen.", 2, [25, 50]),\n        _node("ener_idle", "IDLE-PROTOKOLL", "Erhoeht das Einkommen im Idle-Modus.", 5, [8, 16, 24, 32, 40]),\n        _node("ener_bonus", "KRIEGSKASSE", "Erhoeht Credits aus Kampagnen-Kills.", 5, [8, 16, 24, 32, 40]),\n        _node("ener_sep", "KERN-SEPARATOR", "Chance auf einen zusaetzlichen Data Core pro Kill.", 4, [10, 20, 30, 40]),\n    ]},\n    {"id": "spezial", "name": "SPEZIALSYSTEME", "color": COLOR_SPEZ, "nodes": [\n        _node("spez_bully", "BULLY", "+Schaden gegen angeschlagene Ziele (unter 50% HP).", 4, [10, 20, 30, 40]),\n        _node("spez_exekutor", "EXEKUTOR", "Chance, Gegner unter 20% HP sofort zu eliminieren.", 2, [25, 50]),\n        _node("spez_spreng", "SPRENGSPITZE", "Getoetete Gegner explodieren und verletzten Nachbarn.", 1, [45]),\n        _node("spez_adrenalin", "ADRENALIN-KERN", "Mehr Schaden, je niedriger die eigene Huelle.", 3, [15, 30, 45]),\n        _node("spez_overdrive", "ÜBERTAKTUNG", "AKTIV (Taste Q im Gefecht): 8s doppelte Feuerrate, 45s Abklingzeit.", 1, [60]),\n    ]},\n]\n\n\ndef effect_text(node_id, lvl):\n    """Kurztext des aktuellen Effekts fuer eine gegebene Stufe (0 = noch nicht trainiert)."""\n    if node_id == "waffen_dmg": return f"+{10 * lvl}% Kanonenschaden"\n    if node_id == "waffen_rate": return f"-{6 * lvl}% Feuerintervall"\n    if node_id == "waffen_salve": return f"+{lvl} Projektil/Salve"\n    if node_id == "waffen_krit": return f"{5 * lvl}% Krit-Chance (2.0x Schaden)"\n    if node_id == "waffen_kritschaden": return f"Krit-Schaden x{2.0 + 0.25 * lvl:.2f}"\n    if node_id == "vert_panzerung": return f"+{12 * lvl}% max. Huelle"\n    if node_id == "vert_nano": return f"+{lvl} HP/s Reparatur"\n    if node_id == "vert_schild": return f"-{10 * lvl}% erlittener Schaden"\n    if node_id == "vert_kuehlung": return "Feuerrate +25% unter 30% HP" if lvl else "-"\n    if node_id == "vert_puls": return f"Gegen-Pulse fuer {2.0 + 0.5 * lvl:.1f}s nach Treffer"\n    if node_id == "ener_leitung": return f"+{8 * lvl}% Drohnen-Schaden"\n    if node_id == "ener_taktik": return f"+{lvl} zusaetzliche Drohne(n)"\n    if node_id == "ener_idle": return f"+{15 * lvl}% Idle-Einkommen"\n    if node_id == "ener_bonus": return f"+{10 * lvl}% Credits (Kampagne)"\n    if node_id == "ener_sep": return f"{10 * lvl}% Chance auf doppelten Core"\n    if node_id == "spez_bully": return f"+{12 * lvl}% Schaden bei Ziel < 50% HP"\n    if node_id == "spez_exekutor": return f"{10 * lvl}% Exekution bei Ziel < 20% HP"\n    if node_id == "spez_spreng": return "Kills explodieren (30% AoE-Schaden)" if lvl else "-"\n    if node_id == "spez_adrenalin": return f"+{2 * lvl}% Schaden pro 10% fehlender HP"\n    if node_id == "spez_overdrive": return "Taste Q: 8s x2 Feuerrate (45s CD)" if lvl else "-"\n    return "-"\n\n\ndef find_node(node_id):\n    for branch in SKILL_TREE:\n        for i, node in enumerate(branch["nodes"]):\n            if node["id"] == node_id:\n                return branch, i, node\n    return None, -1, None\n\n\nclass SkillTree:\n    """Persistenter Zustand aller Skill-Stufen + Uebersetzung in Combat-Mods."""\n\n    def __init__(self):\n        self.levels = {}\n        self.load()\n\n    # ---------- Abfragen ----------\n    def level_of(self, node_id):\n        return int(self.levels.get(node_id, 0))\n\n    def prereq_ok(self, branch, index):\n        need = PREREQ_THRESHOLDS[index]\n        if need == 0:\n            return True\n        have = sum(self.level_of(n["id"]) for n in branch["nodes"][:index])\n        return have >= need\n\n    def unlock_info(self, node_id):\n        """(darf_trainiert_werden, Grund-wenn-nicht)."""\n        branch, idx, node = find_node(node_id)\n        if node is None:\n            return False, "Unbekannter Skill"\n        lvl = self.level_of(node_id)\n        if lvl >= node["max"]:\n            return False, "MAX"\n        if not self.prereq_ok(branch, idx):\n            need = PREREQ_THRESHOLDS[idx]\n            return False, f"Benötigt {need} Stufen in {branch[\'name\']}"\n        return True, ""\n\n    def cost_of(self, node_id):\n        _b, _i, node = find_node(node_id)\n        if node is None:\n            return 0\n        lvl = self.level_of(node_id)\n        if lvl >= node["max"]:\n            return 0\n        return int(node["costs"][lvl])\n\n    def total_spent(self):\n        spent = 0\n        for branch in SKILL_TREE:\n            for node in branch["nodes"]:\n                lvl = self.level_of(node["id"])\n                spent += sum(node["costs"][:lvl])\n        return spent\n\n    def unlock(self, node_id):\n        ok, reason = self.unlock_info(node_id)\n        if not ok:\n            raise ValueError(reason)\n        self.levels[node_id] = self.level_of(node_id) + 1\n        self.save()\n        return self.level_of(node_id)\n\n    # ---------- Bruecke zu pve_system ----------\n    def modifiers(self):\n        L = self.level_of\n        return {\n            "dmg_pct": 0.10 * L("waffen_dmg"),\n            "rate_mult": 0.94 ** L("waffen_rate"),\n            "extra_cannons": L("waffen_salve"),\n            "crit_chance": 0.05 * L("waffen_krit"),\n            "crit_mult": 2.0 + 0.25 * L("waffen_kritschaden"),\n            "hp_pct": 0.12 * L("vert_panzerung"),\n            "regen": 1.0 * L("vert_nano"),\n            "dr_pct": 0.10 * L("vert_schild"),\n            "adrenaline": L("vert_kuehlung"),\n            "retaliate": L("vert_puls"),\n            "drone_dmg_pct": 0.08 * L("ener_leitung"),\n            "extra_drones": L("ener_taktik"),\n            "idle_pct": 0.15 * L("ener_idle"),\n            "credit_pct": 0.10 * L("ener_bonus"),\n            "core_chance": 0.10 * L("ener_sep"),\n            "bully": 0.12 * L("spez_bully"),\n            "execute_chance": 0.10 * L("spez_exekutor"),\n            "explosive": L("spez_spreng"),\n            "adrenalin_dmg": 0.02 * L("spez_adrenalin"),\n            "overdrive": L("spez_overdrive"),\n        }\n\n    def apply_to_combat(self, combat):\n        combat.skill_mods = self.modifiers()\n        return combat.skill_mods\n\n    # ---------- Persistenz ----------\n    def load(self):\n        try:\n            data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))\n            raw = data.get("levels", {})\n            self.levels = {str(k): max(0, int(v)) for k, v in raw.items()}\n        except (OSError, ValueError, TypeError, json.JSONDecodeError):\n            self.levels = {}\n\n    def save(self):\n        try:\n            payload = {"levels": dict(self.levels)}\n            SAVE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")\n        except OSError:\n            pass\n'


# ============ Patch-Framework (bewaehrt aus Paket 3) ============

def load_lines(path):
    text = path.read_bytes().decode("utf-8")
    crlf = "\r\n" in text
    return text.splitlines(keepends=True), crlf


def save_lines(path, lines, crlf):
    text = "".join(lines)
    if crlf:
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    path.write_bytes(text.encode("utf-8"))


def indent_of(line):
    s = line.rstrip("\r\n")
    return len(s) - len(s.lstrip())


def find_idx(lines, needle, indent=None, after=-1, before=None):
    hits = []
    for i, l in enumerate(lines):
        if i <= after:
            continue
        if before is not None and i >= before:
            break
        if needle not in l:
            continue
        if indent is not None and indent_of(l) != indent:
            continue
        hits.append(i)
    assert len(hits) == 1, (
        f"Anker fehlgeschlagen: {needle!r} (indent={indent}, after={after}) "
        f"-> {len(hits)} Treffer, erwartet genau 1")
    return hits[0]


def insert_after(lines, idx, new_lines):
    return lines[:idx + 1] + new_lines + lines[idx + 1:]


def insert_before(lines, idx, new_lines):
    return lines[:idx] + new_lines + lines[idx:]


def replace_span(lines, s, e, new_lines):
    """Ersetzt Zeilen s..e (einschlielich) durch new_lines."""
    return lines[:s] + new_lines + lines[e + 1:]


def block(text):
    return text.splitlines(keepends=True)


# ============ PHASE A: Basis aus Paket 3 (Sound + Victory) ============

def phase_a_main(path):
    lines, crlf = load_lines(path)
    print("* Phase A: Patche main.py (Sound + Victory-Flow) ...")

    # A-E1: Import
    i = find_idx(lines, "from ship_movement import ShipMovement")
    lines = insert_after(lines, i, ["from sound_system import SFX\n"])

    # A-E2: Taste M = Stummschalten
    i = find_idx(lines, "if event.key == pygame.K_F1:", indent=16)
    lines = insert_before(lines, i, [
        "                if event.key == pygame.K_m:\n",
        "                    SFX.toggle_mute()\n",
        "                    self.show_message(f\"SOUND: {'AUS' if SFX.muted else 'AN'} (Taste M)\")\n",
    ])

    # A-E3: Klick-Sound
    i = find_idx(lines, "def on_click(self, pos):", indent=4)
    lines = insert_after(lines, i, ["        SFX.play(\"click\", 0.4)\n"])

    # A-E4/E5: Upgrade-Sound an beiden Upgrade-Stellen
    for ind in (24, 28):
        i = find_idx(lines, "self.modules.upgrade(key)", indent=ind)
        j = find_idx(lines, "self._sync_modules_to_combat()", indent=ind, after=i, before=i + 3)
        lines = insert_after(lines, j, [" " * ind + "SFX.play(\"upgrade\")\n"])

    # A-E6: STAGE_CLEAR-Klickhandler ersetzen (alter Draw-Hack fliegt raus)
    s = find_idx(lines, "elif self.state == self.STAGE_CLEAR:", indent=8)
    e = find_idx(lines, "self.victory_timer = 0.0", indent=20, after=s, before=s + 25)
    assert "return" in lines[e + 1], "STAGE_CLEAR-Block endet unerwartet"
    new_block = block('''        elif self.state == self.STAGE_CLEAR:
            video_done = not self.victory_frames or self.victory_timer >= len(self.victory_frames) / 30.0
            if video_done:
                btn_continue = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
                if btn_continue.collidepoint(pos):
                    SFX.stop_music()
                    campaign = self.selected_sector if self.selected_sector > 0 else self.pve.campaign_id
                    self.state = self.STAGES
                    self.pve = PvECombat(is_idle=False, campaign_id=campaign, stage_id=1, ship_level=self.modules.ship_level)
                    self.victory_timer = 0.0
                    return
''')
    lines = lines[:s] + new_block + lines[e + 2:]

    # A-E7: Sieg -> STAGE_CLEAR (statt direkt zur Karte springen)
    s = find_idx(lines, "result = self.pve.get_result()", indent=16)
    assert "NEU" in lines[s - 1], "Kommentar vor get_result() unerwartet"
    e = -1
    for k in range(s, s + 25):
        if "ship_level=self.modules.ship_level)" in lines[k] and "stage_id=1" in lines[k]:
            e = k
            break
    assert e != -1, "Ende des Sieg-Blocks nicht gefunden"
    assert "return" in lines[e + 1], "Sieg-Block endet unerwartet"
    new_block = block('''                # NEU: Stufe gewonnen -> Victory-Screen statt Sprung zur Karte
                result = self.pve.get_result()
                if result["won"] and self.state == self.PLAYING:
                    # Credits und Fortschritt speichern
                    self.modules.complete_stage(
                        campaign_id=self.selected_sector,
                        stage_id=self.pve.stage_id,
                        credits_earned=result["credits_earned"]
                    )
                    self.last_stage_reward = result["credits_earned"]
                    self.victory_timer = 0.0
                    self.state = self.STAGE_CLEAR
                    SFX.play_victory_audio()
                    return
''')
    lines = lines[:s - 1] + new_block + lines[e + 2:]

    # A-E8: draw()-Zweig fuer STAGE_CLEAR (Video wurde bisher nie gezeichnet!)
    s = -1
    for i, l in enumerate(lines):
        if "elif self.state == self.SETTINGS:" in l and indent_of(l) == 8:
            if i + 1 < len(lines) and "self.draw_settings()" in lines[i + 1]:
                s = i
                break
    assert s != -1, "draw()-Zweig SETTINGS nicht gefunden"
    lines = insert_before(lines, s, [
        "        elif self.state == self.STAGE_CLEAR:\n",
        "            self.draw_stage_clear()\n",
    ])

    # A-E9: draw_stage_clear-Methode
    i = find_idx(lines, "def draw_settings(self):", indent=4)
    method = block('''    def draw_stage_clear(self):
        if self.victory_frames:
            frame_idx = int(self.victory_timer * 30)
            if frame_idx >= len(self.victory_frames):
                frame_idx = len(self.victory_frames) - 1
            SCREEN.blit(self.victory_frames[frame_idx], (0, 0))
            if frame_idx >= len(self.victory_frames) - 1:
                mouse = pygame.mouse.get_pos()
                btn_continue = pygame.Rect(WIDTH // 2 - 100, 400, 200, 50)
                draw_single_button(SCREEN, btn_continue, "WEITER", mouse, self.elapsed, CYAN)
                text(SCREEN, f"+{self.last_stage_reward:,} Cr", FONT_MED_BOLD, GREEN, (WIDTH // 2, 465), "center")
        else:
            self.draw_playing()
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            SCREEN.blit(overlay, (0, 0))
            panel(SCREEN, pygame.Rect(230, 140, 500, 230), fill=(5, 10, 21), border=GREEN, radius=15)
            neon_text(SCREEN, "STUFE GESCHAFFT!", FONT_BIG, GREEN, (WIDTH // 2, 175), "midtop")
            neon_text(SCREEN, f"+{self.last_stage_reward:,} CREDITS", FONT_MED_BOLD, WHITE, (WIDTH // 2, 235), "midtop")
            mouse = pygame.mouse.get_pos()
            btn_continue = pygame.Rect(WIDTH // 2 - 100, 320, 200, 50)
            draw_single_button(SCREEN, btn_continue, "WEITER", mouse, self.elapsed, CYAN)

''')
    lines = insert_before(lines, i, method)

    save_lines(path, lines, crlf)
    print("  OK: main.py Phase A abgeschlossen (9 Edits).")


def phase_a_pve(path):
    lines, crlf = load_lines(path)
    print("* Phase A: Patche pve_system.py (Sound-Hooks) ...")

    # A-P1: Import
    i = find_idx(lines, "from dataclasses import dataclass")
    lines = insert_after(lines, i, ["from sound_system import SFX\n"])

    # A-P2: Schuss-Sound
    i = find_idx(lines, "self.auto_fire_timer = self.attack_rate", indent=16)
    lines = insert_after(lines, i, [" " * 16 + "SFX.play(\"shoot\", 0.3)\n"])

    # A-P3: Explosions-Sound
    i = find_idx(lines, "self._spawn_explosion(e.x, e.y, e.enemy_type)", indent=28)
    lines = insert_after(lines, i, [" " * 28 + "SFX.play(\"explosion\", 0.5)\n"])

    # A-P4: Treffer-Sound
    i = find_idx(lines, "if p in self.projectiles: self.projectiles.remove(p)", indent=20)
    lines = insert_after(lines, i, [
        " " * 20 + "if not self.is_idle:\n",
        " " * 24 + "SFX.play(\"hit\", 0.5)\n",
    ])

    save_lines(path, lines, crlf)
    print("  OK: pve_system.py Phase A abgeschlossen (4 Edits).")


def extract_victory_audio(base):
    vid = base / "victory_screen.mp4"
    target = base / "victory_audio.mp3"
    if target.exists():
        print("* victory_audio.mp3 vorhanden - Extraktion uebersprungen.")
        return
    if not vid.exists():
        print("! victory_screen.mp4 nicht gefunden - Sieg zeigt dann den Fallback-Screen.")
        return
    try:
        import imageio_ffmpeg
        print("* Extrahiere Tonspur aus victory_screen.mp4 ...")
        subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-i", str(vid),
             "-vn", "-c:a", "libmp3lame", "-q:a", "4", str(target)],
            check=True, capture_output=True)
        print("  OK: victory_audio.mp3 erstellt - dein Sieg-Video hat jetzt Ton!")
    except ImportError:
        print("! Tipp:  pip install imageio-ffmpeg   und Skript erneut starten,")
        print("  dann wird die Tonspur des Sieg-Videos automatisch extrahiert.")
    except Exception as e:
        print(f"! Audio-Extraktion fehlgeschlagen: {e} (Spiel nutzt stattdessen den Jingle)")


# ============ PHASE B+C+D: pve_system.py ============

def patch_pve_v4(path):
    lines, crlf = load_lines(path)
    print("* Patche pve_system.py (Damage-Numbers + Skill-Hooks + Balancing) ...")

    # --- Balancing-Konstanten ---
    i = find_idx(lines, "ENEMY_FOLDER = ")
    lines = insert_after(lines, i, block('''

# NEU PAKET 4: Globale Balancing-Koeffizienten (wirken auch auf Excel-Werte)
BAL_PLAYER_DMG = 1.6    # Kanonenschaden x1.6  -> Grundausstattung traegt die ersten Stufen
BAL_PLAYER_RATE = 0.88  # Feuerintervall x0.88 -> schneller
BAL_PLAYER_HP = 1.4     # Huelle x1.4
BAL_ENEMY_HP = 0.85     # Gegner-HP x0.85
BAL_ENEMY_DMG = 0.7     # Gegner-Schaden x0.7
BAL_BOSS_HP = 0.7       # Boss-HP x0.7
'''))

    # --- DamageNumber-Datenklasse ---
    i = find_idx(lines, "class PvECombat:")
    lines = insert_before(lines, i, block('''@dataclass
class DamageNumber:
    """NEU PAKET 4: Schwebende Schadenszahl am Trefferpunkt."""
    x: float
    y: float
    value: str
    color: tuple
    life: float = 0.9
    max_life: float = 0.9
    vy: float = -46.0
    big: bool = False

'''))

    # --- Listen & Zustand in __init__ ---
    i = find_idx(lines, "self.particles: list[Particle] = []")
    lines = insert_after(lines, i, [
        "        self.damage_numbers: list[DamageNumber] = []   # NEU PAKET 4\n",
    ])
    i = find_idx(lines, "self.auto_fire_timer = 0.0")
    lines = insert_before(lines, i, block('''        self.skill_mods = {}          # NEU PAKET 4: Modifikatoren aus dem Skill-Tree
        self.retaliate_timer = 0.0    # NEU PAKET 4: PULSGENERATOR
        self.retaliate_tick = 0.0     # NEU PAKET 4
        self.overdrive_timer = 0.0    # NEU PAKET 4: UEBERTAKTUNG
        self.overdrive_cd = 0.0       # NEU PAKET 4
        self.idle_kill_counter = 0    # NEU PAKET 4: Idle liefert Data Cores
'''))

    # --- Huelle: Balancing ---
    i = find_idx(lines, 'self.max_player_hp = float(PLAYER_DATA.get("base_max_hp", 500.0))')
    lines = replace_span(lines, i, i, [
        '        self.max_player_hp = float(PLAYER_DATA.get("base_max_hp", 500.0)) * BAL_PLAYER_HP   # NEU PAKET 4: Balancing\n',
    ])

    # --- cannon_damage: Balancing + Skills + ADRENALIN-KERN (+ Hilfsmethoden) ---
    s = find_idx(lines, "def cannon_damage")
    assert "@property" in lines[s - 1], "cannon_damage: @property unerwartet"
    e = find_idx(lines, "return base * (mult ** (self.dmg_level - 1))", after=s, before=s + 6)
    lines = replace_span(lines, s - 1, e, block('''    @property
    def cannon_damage(self):
        base = float(PLAYER_DATA.get("base_cannon_damage", 12.0))
        mult = float(PLAYER_DATA.get("cannon_dmg_mult", 1.2))
        raw = base * (mult ** (self.dmg_level - 1)) * BAL_PLAYER_DMG
        raw *= 1.0 + self.mod("dmg_pct", 0.0)          # NEU PAKET 4: GEWEHRVERSTÄRKER
        return raw * self._missing_hp_factor()

    def _missing_hp_factor(self):
        """NEU PAKET 4: ADRENALIN-KERN - mehr Schaden, je niedriger die Huelle."""
        if self.max_player_hp <= 0:
            return 1.0
        missing = 1.0 - max(0.0, min(1.0, self.player_hp / self.max_player_hp))
        return 1.0 + self.mod("adrenalin_dmg", 0.0) * int(missing * 10)

    def mod(self, key, default=0.0):
        """NEU PAKET 4: Skill-Modifikator lesen (gesetzt von skill_tree.apply_to_combat)."""
        try:
            return self.skill_mods.get(key, default)
        except AttributeError:
            return default

    def activate_overdrive(self):
        """NEU PAKET 4: UEBERTAKTUNG (Spezialsparte) - 8s doppelte Feuerrate, 45s CD."""
        if self.is_idle or self.mod("overdrive", 0) < 1:
            return False
        if self.overdrive_cd > 0 or self.overdrive_timer > 0:
            return False
        self.overdrive_timer = 8.0
        self.overdrive_cd = 45.0
        return True

    def _spawn_damage(self, x, y, value, color, big=False):
        """NEU PAKET 4: schwebende Schadenszahl am Trefferpunkt."""
        try:
            self.damage_numbers.append(DamageNumber(x=x, y=y, value=str(value), color=color, big=big))
        except AttributeError:
            pass
'''))

    # --- attack_rate: Balancing + SCHNELLFEUER + UEBERTAKTUNG + NOTKUEHLUNG ---
    s = find_idx(lines, "def attack_rate")
    assert "@property" in lines[s - 1], "attack_rate: @property unerwartet"
    e = find_idx(lines, "return base * (mult ** (self.speed_level - 1))", after=s, before=s + 6)
    lines = replace_span(lines, s - 1, e, block('''    @property
    def attack_rate(self):
        base = float(PLAYER_DATA.get("base_fire_rate", 0.8))
        mult = float(PLAYER_DATA.get("fire_rate_mult", 0.85))
        rate = base * (mult ** (self.speed_level - 1)) * BAL_PLAYER_RATE
        rate *= self.mod("rate_mult", 1.0)          # NEU PAKET 4: SCHNELLFEUER
        if self.overdrive_timer > 0:                # NEU PAKET 4: UEBERTAKTUNG (x2)
            rate *= 0.5
        if self.mod("adrenaline", 0) >= 1 and self.player_hp < self.max_player_hp * 0.3:
            rate *= 0.75                            # NEU PAKET 4: NOTKUEHLUNG
        return rate
'''))

    # --- cannon_count: MEHRFACHLAUF ---
    i = find_idx(lines, "def cannon_count(self): return min(8, self.cannon_count_level)")
    lines = replace_span(lines, i, i, [
        '    def cannon_count(self): return min(8, self.cannon_count_level + int(self.mod("extra_cannons", 0)))   # NEU PAKET 4: MEHRFACHLAUF\n',
    ])

    # --- Reparatur: Grundreparatur + NANO-REPARATUR + Timer/Pulse ---
    s = find_idx(lines, 'rep_val = float(PLAYER_DATA.get("repair_per_level"')
    e = find_idx(lines, "self.player_hp += 20 * dt", after=s, before=s + 6)
    lines = replace_span(lines, s, e, block('''        rep_val = float(PLAYER_DATA.get("repair_per_level", 2.0))
        base_regen = 1.5 + self.mod("regen", 0.0)   # NEU PAKET 4: Grundreparatur + NANO-REPARATUR
        if self.player_hp < self.max_player_hp:
            self.player_hp += base_regen * dt
            if self.repair_level > 1:
                self.player_hp += (self.repair_level * rep_val) * dt
        if self.is_idle and self.player_hp < self.max_player_hp:
            self.player_hp += 20 * dt

        # NEU PAKET 4: Uebertaktungs-Timer + Vergeltungs-Pulse
        if self.overdrive_cd > 0:
            self.overdrive_cd = max(0.0, self.overdrive_cd - dt)
        if self.overdrive_timer > 0:
            self.overdrive_timer = max(0.0, self.overdrive_timer - dt)
        if self.retaliate_timer > 0 and not self.is_idle:
            self.retaliate_timer -= dt
            self.retaliate_tick -= dt
            if self.retaliate_tick <= 0 and self.enemies:
                self.retaliate_tick = 0.5
                for tgt in sorted(self.enemies, key=lambda en: en.x)[:2]:
                    dx, dy = tgt.x - cx, tgt.y - cy
                    dist = math.hypot(dx, dy) or 1
                    self.projectiles.append(Projectile(
                        x=cx, y=cy - 40, vx=dx / dist, vy=dy / dist,
                        damage=self.cannon_damage * 0.4, color=(153, 94, 255),
                        size=3, speed=650.0, kind="player", is_drone=True))
'''))

    # --- Schadenszahlen-Update-Loop ---
    i = find_idx(lines, "if mf[3] <= 0: self.muzzle_flashes.remove(mf)")
    lines = insert_after(lines, i, block('''

        for dn in list(self.damage_numbers):   # NEU PAKET 4: Schadenszahlen
            dn.y += dn.vy * dt
            dn.vy *= (1.0 - 1.5 * dt)
            dn.life -= dt
            if dn.life <= 0:
                self.damage_numbers.remove(dn)
'''))

    # --- Gegner-Spawn: Balancing (Anzahl) ---
    i = find_idx(lines, "self.spawn_queue = 999 if self.is_idle else (3 + self.stage_id)")
    lines = replace_span(lines, i, i, [
        '            self.spawn_queue = 999 if self.is_idle else (2 + self.stage_id)   # NEU PAKET 4: Balancing\n',
    ])

    # --- Gegner-Werte: Balancing (HP/Schaden) ---
    s = find_idx(lines, 'hp = (float(data.get("Base_HP", 20))')
    e = find_idx(lines, 'reward = int((float(data.get("Base_Reward", 10))', after=s, before=s + 6)
    lines = replace_span(lines, s, e, block('''            hp = (float(data.get("Base_HP", 20)) + (self.stage_id * float(data.get("HP_Add_Per_Stage", 10)))) * (float(data.get("HP_Mult_Per_Stage", 1.05)) ** self.stage_id) * BAL_ENEMY_HP   # NEU PAKET 4: Balancing
            speed = float(data.get("Base_Speed", 50)) + (self.stage_id * float(data.get("Speed_Add_Per_Stage", 0)))
            damage = (float(data.get("Base_Damage", 5)) + (self.stage_id * float(data.get("Damage_Add_Per_Stage", 2)))) * BAL_ENEMY_DMG   # NEU PAKET 4: Balancing
            reward = int((float(data.get("Base_Reward", 10)) + (self.stage_id * 2)) * float(data.get("Idle_Reward_Mult", 1.0)))
'''))

    # --- Boss: Balancing ---
    i = find_idx(lines, "hp = 500 * (1.15 ** self.stage_id)")
    lines = replace_span(lines, i, i, [
        '            hp = 500 * (1.15 ** self.stage_id) * BAL_BOSS_HP # NEU PAKET 4: Balancing (4068 -> ~2850)\n',
    ])
    i = find_idx(lines, "damage = 30")
    lines = replace_span(lines, i, i, [
        '            damage = int(30 * BAL_ENEMY_DMG)   # NEU PAKET 4: Balancing\n',
    ])

    # --- Drohnen: ENERGIELEITUNG + HANGAR-TAKTIK ---
    i = find_idx(lines, 'drone_dmg = self.cannon_damage * float(PLAYER_DATA.get("drone_damage_mult", 0.5))')
    lines = replace_span(lines, i, i, [
        '                drone_dmg = self.cannon_damage * float(PLAYER_DATA.get("drone_damage_mult", 0.5)) * (1.0 + self.mod("drone_dmg_pct", 0.0))   # NEU PAKET 4: ENERGIELEITUNG\n',
    ])
    i = find_idx(lines, "for i in range(min(4, self.hangar_level - 1)):")
    lines = replace_span(lines, i, i, [
        '                for i in range(min(4, self.hangar_level - 1) + int(self.mod("extra_drones", 0))):   # NEU PAKET 4: HANGAR-TAKTIK\n',
    ])

    # --- Treffer auf Gegner: Krit + BULLY + EXEKUTOR + Schadenszahl + Oekonomie + SPRENGSPITZE ---
    s = find_idx(lines, "e.hp -= p.damage")
    e = -1
    for k in range(s, s + 14):
        if lines[k].strip() == "break" and indent_of(lines[k]) == 24:
            e = k
            break
    assert e != -1, "Treffer-Block: break nicht gefunden"
    lines = replace_span(lines, s, e, block('''                        dmg = p.damage
                        crit = random.random() < self.mod("crit_chance", 0.0)
                        if crit:
                            dmg *= self.mod("crit_mult", 2.0)   # NEU PAKET 4: ZIELRECHNER/PANZERBRECHER
                        if self.mod("bully", 0.0) > 0 and e.hp < e.max_hp * 0.5:
                            dmg *= 1.0 + self.mod("bully", 0.0)   # NEU PAKET 4: BULLY
                        dmg = max(1, int(dmg))
                        e.hp -= dmg
                        e.hit_flash = 0.15
                        if crit:
                            self._spawn_damage(e.x, e.y - 30, dmg, (255, 190, 76), big=True)
                        else:
                            self._spawn_damage(e.x, e.y - 30, dmg, (0, 255, 255))
                        if (self.mod("execute_chance", 0.0) > 0 and 0 < e.hp <= e.max_hp * 0.2
                                and random.random() < self.mod("execute_chance", 0.0)):
                            e.hp = -1   # NEU PAKET 4: EXEKUTOR
                            self._spawn_damage(e.x, e.y - 55, "EXEK!", (255, 77, 100), big=True)
                        if p in self.projectiles: self.projectiles.remove(p)
                        if e.hp <= 0 and e in self.enemies:
                            gain_mult = (1.0 + self.mod("idle_pct", 0.0)) if self.is_idle else (1.0 + self.mod("credit_pct", 0.0))
                            reward = int(e.reward * gain_mult)   # NEU PAKET 4: IDLE-PROTOKOLL/KRIEGSKASSE
                            self.credits += reward
                            if self.is_idle:
                                self.idle_loot_earned += reward
                                self.idle_kill_counter += 1
                                if self.idle_kill_counter % 25 == 0:
                                    self.data_cores_earned += 1   # NEU PAKET 4: Idle -> Data Cores
                            else:
                                cores = 1 + (1 if random.random() < self.mod("core_chance", 0.0) else 0)
                                self.data_cores_earned += cores   # NEU PAKET 4: KERN-SEPARATOR
                            self._spawn_explosion(e.x, e.y, e.enemy_type)
                            SFX.play("explosion", 0.5)
                            if self.mod("explosive", 0) >= 1 and not self.is_idle:
                                for o in list(self.enemies):   # NEU PAKET 4: SPRENGSPITZE
                                    if o is e:
                                        continue
                                    if math.hypot(o.x - e.x, o.y - e.y) < 90:
                                        o.hp -= self.cannon_damage * 0.3
                                        self._spawn_damage(o.x, o.y - 30, int(self.cannon_damage * 0.3), (255, 190, 76))
                                        if o.hp <= 0 and o in self.enemies:
                                            self._spawn_explosion(o.x, o.y, o.enemy_type)
                                            self.enemies.remove(o)
                            self.enemies.remove(e)
                        break
'''))

    # --- Treffer auf Spieler: ABFANG-FELD + Schadenszahl + PULSGENERATOR ---
    s = find_idx(lines, "if math.hypot(cx - p.x, cy - p.y) < 80:")
    e = find_idx(lines, 'SFX.play("hit", 0.5)', after=s, before=s + 10)
    lines = replace_span(lines, s, e, block('''                if math.hypot(cx - p.x, cy - p.y) < 80:
                    applied = p.damage * (1.0 - self.mod("dr_pct", 0.0))   # NEU PAKET 4: ABFANG-FELD
                    applied = max(1, int(applied))
                    if self.is_idle:
                        self.player_hp = max(1.0, self.player_hp - applied)
                    else:
                        self.player_hp = max(0.0, self.player_hp - applied)
                    self._spawn_damage(p.x, p.y - 15, applied, (255, 77, 100))   # NEU PAKET 4: Schadenszahl (Spieler)
                    if self.mod("retaliate", 0) > 0:
                        self.retaliate_timer = 2.0 + 0.5 * self.mod("retaliate", 0)   # NEU PAKET 4: PULSGENERATOR
                    if p in self.projectiles: self.projectiles.remove(p)
                    if not self.is_idle:
                        SFX.play("hit", 0.5)
'''))

    save_lines(path, lines, crlf)
    print("  OK: pve_system.py PAKET 4 abgeschlossen (16 Edits).")


# ============ PHASE B+C+D: main.py ============

def patch_main_v4(path):
    lines, crlf = load_lines(path)
    print("* Patche main.py (Damage-Numbers + Skill-Tree-UI + Balancing) ...")

    # --- Import + State ---
    i = find_idx(lines, "from sound_system import SFX")
    lines = insert_after(lines, i, ["from skill_tree import SkillTree   # NEU PAKET 4\n"])
    i = find_idx(lines, 'RESEARCH = "research"')
    lines = insert_after(lines, i, ['    SKILLTREE = "skilltree"   # NEU PAKET 4\n'])

    # --- skills vor dem ersten _sync anlegen ---
    i = find_idx(lines, "self.fortress = Fortress(120, 270, level=1)")
    lines = insert_before(lines, i, [
        "        self.skills = SkillTree()   # NEU PAKET 4\n",
    ])

    # --- Menue: 6 Buttons ---
    s = find_idx(lines, "start_y = 250")
    e = find_idx(lines, "self.quit_button = pygame.Rect(", after=s, before=s + 10)
    lines = replace_span(lines, s, e, block('''        start_y = 226   # NEU PAKET 4: 6 Menuepunkte
        spacing = 40
        cx = WIDTH // 2
        self.start_idle_button = pygame.Rect(cx - btn_w//2, start_y, btn_w, btn_h)
        self.research_button = pygame.Rect(cx - btn_w//2, start_y + spacing, btn_w, btn_h)
        self.skill_button = pygame.Rect(cx - btn_w//2, start_y + spacing*2, btn_w, btn_h)   # NEU PAKET 4
        self.stages_button = pygame.Rect(cx - btn_w//2, start_y + spacing*3, btn_w, btn_h)
        self.settings_button = pygame.Rect(cx - btn_w//2, start_y + spacing*4, btn_w, btn_h)
        self.quit_button = pygame.Rect(cx - btn_w//2, start_y + spacing*5, btn_w, btn_h)
'''))

    # --- Menue-Zeichnung: Button dazwischen ---
    s = find_idx(lines, "draw_button(SCREEN, self.start_idle_button")
    e = find_idx(lines, "draw_button(SCREEN, self.quit_button", after=s, before=s + 10)
    lines = replace_span(lines, s, e, block('''        draw_button(SCREEN, self.start_idle_button, "IDLE MODUS", "Automatischer Abwehrbetrieb", mouse, t, CYAN)
        draw_button(SCREEN, self.research_button, "UPGRADES", "Module & Schiff upgraden", mouse, t, MAGENTA)
        draw_button(SCREEN, self.skill_button, "SKILL-TREE", "Data Cores investieren", mouse, t, AMBER)
        draw_button(SCREEN, self.stages_button, "STUFENKAMPAGNE", "Gezielter Sektor-Einsatz", mouse, t, GREEN)
        draw_button(SCREEN, self.settings_button, "EINSTELLUNGEN", "System Konfiguration", mouse, t, VIOLET)
        draw_button(SCREEN, self.quit_button, "BEENDEN", "Verbindung trennen", mouse, t, RED)
'''))

    # --- on_click Menue: Skill-Tree oeffnen ---
    i = find_idx(lines, "elif self.stages_button.collidepoint(pos):")
    lines = insert_before(lines, i, block('''            elif self.skill_button.collidepoint(pos):   # NEU PAKET 4
                self.state = self.SKILLTREE
'''))

    # --- ESC reicht jetzt auch aus dem Skill-Tree zurueck ---
    i = find_idx(lines, "elif self.state in (self.STAGES, self.SETTINGS, self.RESEARCH):")
    lines = replace_span(lines, i, i, [
        "                    elif self.state in (self.STAGES, self.SETTINGS, self.RESEARCH, self.SKILLTREE):   # NEU PAKET 4\n",
    ])

    # --- Idle-Beute: jetzt auch Data Cores ---
    s = find_idx(lines, "def _collect_idle_loot(self):")
    e = find_idx(lines, "self.modules.save()", after=s, before=s + 9)
    lines = replace_span(lines, s, e, block('''    def _collect_idle_loot(self):
        """Überweist gesammelte Idle-Credits (und Data Cores) in die Wallet."""
        if self.idle_combat.credits > 0:
            self.modules.credits += self.idle_combat.credits
            self.idle_combat.credits = 0
        if self.idle_combat.data_cores_earned > 0:   # NEU PAKET 4: Idle -> Data Cores
            self.modules.data_cores += self.idle_combat.data_cores_earned
            self.idle_combat.data_cores_earned = 0
        self.modules.save()
'''))

    # --- Sync: Skills anwenden + neue Huellen-Basis (500 -> 700) ---
    s = find_idx(lines, "def _sync_modules_to_combat(self):")
    e = find_idx(lines, "combat.ship_level = self.modules.ship_level", after=s, before=s + 12)
    lines = replace_span(lines, s, e, block('''    def _sync_modules_to_combat(self):
        for combat in (self.idle_combat, self.pve):
            combat.dmg_level = self.modules.get("kanonen").level
            combat.speed_level = self.modules.get("antrieb").level
            combat.cannon_count_level = min(8, 1 + self.modules.get("kanonen").level // 2)
            combat.hangar_level = self.modules.get("hangar").level
            combat.repair_level = self.modules.get("reparatur").level
            combat.ship_level = self.modules.ship_level
            if hasattr(self, "skills"):
                self.skills.apply_to_combat(combat)   # NEU PAKET 4: Skill-Mods auf jeden Kampf
            base_hp = 700.0 + (self.modules.get("schild").level - 1) * 100   # NEU PAKET 4: 500 -> 700
            combat.max_player_hp = base_hp * (1.0 + combat.mod("hp_pct", 0.0))   # NEU PAKET 4: VERSTÄRKTE HÜLLE
'''))
    # player_hp-Clamp war Teil des alten Blocks -> neu anhaengen:
    # (der alte Block endete mit dem Clamp; wir haengen ihn an die neue Schleife an)
    # Suche das Ende der for-Schleife (die Zeile nach combat.max_player_hp...)
    idx_maxhp = find_idx(lines, 'combat.max_player_hp = base_hp * (1.0 + combat.mod("hp_pct", 0.0))')
    lines = insert_after(lines, idx_maxhp, [
        "            combat.player_hp = min(combat.player_hp, combat.max_player_hp)\n",
    ])

    # --- Hintergrund-Bugfix (bg_stage_1_5 existierte nie -> Kapitel-BGs wurden nie gezeichnet) ---
    i = find_idx(lines, "hasattr(self, 'bg_stage_1_5')")
    lines = replace_span(lines, i, i, [
        "            if not self.idle_mode and hasattr(self, 'bg_chapter_1_part_1') and self.bg_chapter_1_part_1:   # NEU PAKET 4: Bugfix\n",
    ])

    # --- Taste Q: UEBERTAKTUNG ---
    i = find_idx(lines, "if event.key == pygame.K_F1:", indent=16)
    lines = insert_before(lines, i, block('''                if event.key == pygame.K_q and self.state == self.PLAYING and not self.idle_mode:   # NEU PAKET 4
                    if self.pve.activate_overdrive():
                        self.show_message("ÜBERTAKTUNG AKTIV: doppelte Feuerrate (8s)")
                    elif self.pve.mod("overdrive", 0) < 1:
                        self.show_message("Übertaktung nicht trainiert (Skill-Tree, Sparte SPEZIAL)")
                    else:
                        self.show_message("Übertaktung nicht bereit (Abklingzeit)")
'''))

    # --- Schadenszahlen zeichnen (vor Mündungsfeuer) ---
    i = find_idx(lines, "Mündungsfeuer")
    lines = insert_before(lines, i, block('''        # 6b. NEU PAKET 4: Schadenszahlen (Gegner=Cyan, Krit=Amber, Spieler=Rot)
        for dn in getattr(combat, "damage_numbers", []):
            alpha = max(0, min(255, int(255 * dn.life / dn.max_life)))
            font = FONT_MED_BOLD if dn.big else FONT_SMALL
            surf = font.render(str(dn.value), True, dn.color)
            surf.set_alpha(alpha)
            SCREEN.blit(surf, surf.get_rect(center=(int(dn.x), int(dn.y))))

'''))

    # --- draw(): SKILLTREE-Hintergrund + Verzweigung ---
    i = find_idx(lines, "if self.state in (self.MENU, self.RESEARCH, self.SETTINGS, self.STAGES):")
    lines = replace_span(lines, i, i, [
        "        if self.state in (self.MENU, self.RESEARCH, self.SETTINGS, self.STAGES, self.SKILLTREE):   # NEU PAKET 4\n",
    ])
    i = find_idx(lines, "self.draw_settings()")
    lines = insert_before(lines, i - 1, block('''        elif self.state == self.SKILLTREE:   # NEU PAKET 4
            self.draw_skill_tree()
'''))

    # --- on_click(): Skill-Tree-Handler einhaengen ---
    i = find_idx(lines, "if self.btn_back_settings.collidepoint(pos):")
    lines = insert_before(lines, i - 1, block('''        elif self.state == self.SKILLTREE:   # NEU PAKET 4
            self.on_click_skill_tree(pos)
'''))

    # --- Neue Methoden: draw_skill_tree + on_click_skill_tree (vor draw_settings) ---
    i = find_idx(lines, "def draw_settings(self):", indent=4)
    lines = insert_before(lines, i, block('''    def draw_skill_tree(self):
        """NEU PAKET 4: TECH-TERMINAL - Skill-Tree mit 4 Sparten (Data Cores)."""
        from skill_tree import SKILL_TREE, effect_text
        mouse = pygame.mouse.get_pos()
        self._skill_rects = {}
        if not hasattr(self, "skill_selected"):
            self.skill_selected = SKILL_TREE[0]["nodes"][0]["id"]   # NEU PAKET 4: Vorauswahl wie in Referenz-UIs
        cores = self.modules.data_cores

        # Kopfzeile
        neon_text(SCREEN, "TECH-TERMINAL // SKILL-TREE", FONT_BIG, WHITE, (WIDTH // 2, 14), "midtop")
        core_color = GREEN if cores > 0 else RED
        neon_text(SCREEN, f"DATA CORES: {cores}", FONT_MED_BOLD, core_color, (WIDTH - 20, 18), "topright")
        text(SCREEN, "Klick = auswaehlen | TRAIN = freischalten | ESC = zurueck", FONT_TINY, MUTED, (WIDTH - 20, 46), "topright")

        # 4 Spalten mit je 5 Nodes
        for bi, branch in enumerate(SKILL_TREE):
            bx = 40 + bi * 225
            bcolor = branch["color"]
            pygame.draw.line(SCREEN, bcolor, (bx, 76), (bx + 205, 76), 2)
            text(SCREEN, branch["name"], FONT_SMALL, bcolor, (bx + 102, 80), "midtop")
            for ni, node in enumerate(branch["nodes"]):
                lvl = self.skills.level_of(node["id"])
                max_l = node["max"]
                ny = 104 + ni * 66
                rect = pygame.Rect(bx, ny, 205, 58)
                self._skill_rects[node["id"]] = rect
                ok, _reason = self.skills.unlock_info(node["id"])
                cost = self.skills.cost_of(node["id"])
                selected = (self.skill_selected == node["id"])
                if selected:
                    border, bwidth = bcolor, 3
                elif lvl >= max_l:
                    border, bwidth = GREEN, 1
                elif ok and cores >= cost:
                    border, bwidth = bcolor, 2
                elif ok:
                    border, bwidth = AMBER, 1
                else:
                    border, bwidth = DIM, 1
                fill = (10, 14, 24) if selected else (3, 10, 20)
                pygame.draw.rect(SCREEN, fill, rect, border_radius=8)
                pygame.draw.rect(SCREEN, border, rect, bwidth, border_radius=8)
                for cxy in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright):
                    pygame.draw.circle(SCREEN, border, cxy, 2)
                status = f"{lvl}/{max_l}"
                status_color = GREEN if lvl >= max_l else (bcolor if lvl > 0 else MUTED)
                text(SCREEN, node["name"], FONT_TINY, WHITE if (lvl > 0 or ok) else MUTED, (rect.x + 10, rect.y + 8))
                info = effect_text(node["id"], lvl) if lvl > 0 else node["desc"][:34]
                text(SCREEN, info, FONT_TINY, CYAN_SOFT if lvl > 0 else MUTED, (rect.x + 10, rect.y + 24))
                if lvl >= max_l:
                    text(SCREEN, "MAX", FONT_TINY, GREEN, (rect.right - 10, rect.y + 8), "topright")
                elif not ok:
                    text(SCREEN, "GESPERRT", FONT_TINY, DIM, (rect.right - 10, rect.y + 8), "topright")
                else:
                    text(SCREEN, f"{cost} Cores", FONT_TINY, GREEN if cores >= cost else RED, (rect.right - 10, rect.y + 8), "topright")
                text(SCREEN, status, FONT_TINY, status_color, (rect.right - 10, rect.y + 24), "topright")

        # Detail-Panel unten
        panel(SCREEN, pygame.Rect(40, 438, 880, 92), fill=(2, 5, 12), border=LINE, radius=10)
        if self.skill_selected:
            branch = None
            node = None
            for br in SKILL_TREE:
                for nd in br["nodes"]:
                    if nd["id"] == self.skill_selected:
                        branch, node = br, nd
            lvl = self.skills.level_of(node["id"])
            bcolor = branch["color"]
            ok, reason = self.skills.unlock_info(node["id"])
            cost = self.skills.cost_of(node["id"])
            text(SCREEN, node["name"], FONT_MED_BOLD, bcolor, (60, 448))
            text(SCREEN, f"Stufe {lvl}/{node['max']}", FONT_SMALL, WHITE, (60, 470))
            text(SCREEN, node["desc"], FONT_TINY, MUTED, (60, 492))
            text(SCREEN, f"Aktuell: {effect_text(node['id'], lvl)}", FONT_TINY, CYAN_SOFT, (420, 450))
            if lvl < node["max"]:
                text(SCREEN, f"Naechste: {effect_text(node['id'], lvl + 1)}", FONT_TINY, WHITE, (420, 468))
                text(SCREEN, f"Kosten: {cost} Data Cores", FONT_TINY, GREEN if cores >= cost else RED, (420, 486))
                if not ok:
                    text(SCREEN, reason, FONT_TINY, RED, (420, 504))
            train_rect = pygame.Rect(760, 452, 140, 44)
            self._skill_train_rect = train_rect
            can_train = ok and cores >= cost and lvl < node["max"]
            draw_single_button(SCREEN, train_rect, "TRAIN", mouse, self.elapsed, bcolor if can_train else DIM, enabled=can_train)
        else:
            self._skill_train_rect = None
            text(SCREEN, "Faehigkeit auswaehlen ...", FONT_SMALL, MUTED, (WIDTH // 2, 480), "center")

    def on_click_skill_tree(self, pos):
        """NEU PAKET 4: Klicks im TECH-TERMINAL (Node waehlen / TRAIN kaufen)."""
        for node_id, rect in self._skill_rects.items():
            if rect.collidepoint(pos):
                self.skill_selected = node_id
                return
        train_rect = getattr(self, "_skill_train_rect", None)
        if train_rect and train_rect.collidepoint(pos):
            node_id = self.skill_selected
            if not node_id:
                return
            ok, reason = self.skills.unlock_info(node_id)
            if not ok:
                self.show_message(f"Nicht moeglich: {reason}")
                return
            cost = self.skills.cost_of(node_id)
            if self.modules.data_cores < cost:
                self.show_message(f"Zu wenig Data Cores: {cost} benoetigt")
                return
            self.modules.data_cores -= cost
            self.skills.unlock(node_id)
            self._sync_modules_to_combat()
            self.modules.save()
            SFX.play("upgrade")
            self.show_message(f"Skill trainiert: {node_id}")

'''))

    save_lines(path, lines, crlf)
    print("  OK: main.py PAKET 4 abgeschlossen (18 Edits).")


# ============ Hauptprogramm ============

def main():
    base = Path(__file__).resolve().parent
    main_py = base / "main.py"
    pve_py = base / "pve_system.py"
    snd_py = base / "sound_system.py"
    skill_py = base / "skill_tree.py"

    if not main_py.exists() or not pve_py.exists():
        print("X  main.py / pve_system.py nicht gefunden. Skript in den DS4-Ordner legen!")
        return 1

    print("=" * 60)
    print(" CORRIDOR SLAYER - PAKET 4 (Victory + Damage + Skills + Balance)")
    print("=" * 60)

    # 0) Backups
    for p in (main_py, pve_py):
        bak = p.with_name(p.stem + "_backup_paket4.py")
        if bak.exists():
            print(f"* Backup existiert bereits: {bak.name}")
        else:
            shutil.copy2(p, bak)
            print(f"  OK: Backup {bak.name}")

    # A) sound_system.py anlegen (falls fehlend)
    if snd_py.exists():
        print("* sound_system.py existiert bereits - uebersprungen.")
    else:
        snd_py.write_text(SOUND_SYSTEM_SOURCE.replace("\n", "\r\n"), encoding="utf-8", newline="")
        print("  OK: sound_system.py angelegt (Retro-SFX ohne Assets).")

    # A) Tonspur aus dem Victory-Video extrahieren (optional)
    extract_victory_audio(base)

    # A) Victory-Flow + Sound-Hooks (nur wenn noch nicht vorhanden)
    if "from sound_system import SFX" in main_py.read_text(encoding="utf-8"):
        print("* main.py: Phase A bereits installiert - uebersprungen.")
    else:
        phase_a_main(main_py)
    if "from sound_system import SFX" in pve_py.read_text(encoding="utf-8"):
        print("* pve_system.py: Phase A bereits installiert - uebersprungen.")
    else:
        phase_a_pve(pve_py)

    # B/C/D) Overhaul-Edits (nur wenn noch nicht vorhanden)
    if "BAL_PLAYER_DMG" in pve_py.read_text(encoding="utf-8"):
        print("* pve_system.py: PAKET 4 bereits installiert - uebersprungen.")
    else:
        patch_pve_v4(pve_py)
    if "SKILLTREE" in main_py.read_text(encoding="utf-8"):
        print("* main.py: PAKET 4 bereits installiert - uebersprungen.")
    else:
        patch_main_v4(main_py)

    # C) skill_tree.py anlegen
    if skill_py.exists():
        print("* skill_tree.py existiert bereits - uebersprungen.")
    else:
        skill_py.write_text(SKILL_TREE_SOURCE.replace("\n", "\r\n"), encoding="utf-8", newline="")
        print("  OK: skill_tree.py angelegt (4 Sparten, 20 Faehigkeiten).")

    # Verifikation
    print()
    print("Verifikation:")
    for p in (main_py, pve_py, snd_py, skill_py):
        py_compile.compile(str(p), doraise=True)
        print(f"  OK: {p.name} kompiliert fehlerfrei")

    print()
    print("Fertig! Starten mit:  py main.py")
    print("  Hauptmenue -> SKILL-TREE (Data Cores investieren)")
    print("  Gefecht: Q = Uebertaktung | M = Sound an/aus")
    print("  Sieg = Victory-Video mit Ton (bei installiertem imageio-ffmpeg)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
