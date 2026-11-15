"""CORRIDOR SLAYER | Prozeduraler Sound: Retro-SFX komplett ohne Asset-Dateien."""
import os
import random
import numpy as np
import pygame


class SoundSystem:
    """Erzeugt alle Effekte per Synthese - kein Download, keine WAV-Dateien."""

    def __init__(self):
        self.enabled = True
        self.muted = False
        self._built = False
        self.sounds = {}

    # ---------- interne Helfer ----------
    def _ensure_built(self):
        if self._built or not self.enabled:
            return
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
        except Exception as e:
            print(f"⚠️ Kein Audiogerät: {e}")
            self.enabled = False
            return
        try:
            self._generate_sounds()
            self._built = True
            print("✅ Sound-System bereit (Sound-Toggle in den Einstellungen).")
        except Exception as e:
            print(f"⚠️ Sound-System deaktiviert: {e}")
            self.enabled = False

    def _mixer_format(self):
        freq, _fmt, channels = pygame.mixer.get_init()
        return int(freq), max(1, int(channels))

    def _to_sound(self, wave):
        freq, channels = self._mixer_format()
        wave = np.clip(wave, -1.0, 1.0)
        pcm = (wave * 32000.0).astype(np.int16)
        if channels > 1:
            pcm = np.repeat(pcm[:, None], channels, axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(pcm))

    def _tone(self, f_start, f_end, seconds, vol=0.8, shape="sine"):
        freq, _ = self._mixer_format()
        n = int(freq * seconds)
        f = np.linspace(f_start, f_end, n)
        phase = np.cumsum(2.0 * np.pi * f / freq)
        if shape == "square":
            w = np.sign(np.sin(phase)) * 0.55
        else:
            w = np.sin(phase)
        env = np.exp(-np.linspace(0.0, 6.0, n))
        attack = max(1, int(0.004 * freq))
        env[:attack] *= np.linspace(0.0, 1.0, attack)
        return w * env * vol

    def _noise(self, seconds, vol=0.8, smooth=1):
        freq, _ = self._mixer_format()
        n = int(freq * seconds)
        w = np.random.uniform(-1.0, 1.0, n)
        for _ in range(smooth):
            w = np.convolve(w, np.ones(5) / 5.0, mode="same")
        env = np.exp(-np.linspace(0.0, 7.0, n))
        attack = max(1, int(0.002 * freq))
        env[:attack] *= np.linspace(0.0, 1.0, attack)
        return w * env * vol

    def _seq(self, notes, seconds_each, vol=0.6, shape="sine"):
        return np.concatenate([self._tone(f, f, seconds_each, vol, shape) for f in notes])

    def _generate_sounds(self):
        self.sounds["click"] = [self._to_sound(self._tone(1400, 900, 0.05, 0.45))]
        self.sounds["shoot"] = [
            self._to_sound(self._tone(random.uniform(1250, 1550), 280, 0.09, 0.55))
            for _ in range(3)
        ]
        self.sounds["hit"] = [self._to_sound(self._tone(220, 90, 0.12, 0.7) + self._noise(0.12, 0.3, 1))]
        self.sounds["explosion"] = [
            self._to_sound(self._noise(0.45, 0.85, 2) + self._tone(90, 40, 0.45, 0.45))
            for _ in range(2)
        ]
        self.sounds["upgrade"] = [self._to_sound(self._seq([523.25, 783.99], 0.09, 0.5, "square"))]
        self.sounds["victory"] = [self._to_sound(self._seq([523.25, 659.25, 783.99, 1046.50], 0.15, 0.55, "square"))]

    # ---------- öffentliche API ----------
    def play(self, name, volume=1.0):
        if not self.enabled or self.muted:
            return False
        self._ensure_built()
        pool = self.sounds.get(name)
        if not pool:
            return False
        snd = random.choice(pool)
        snd.set_volume(max(0.0, min(1.0, volume)))
        snd.play()
        return True

    def play_victory_audio(self):
        """Sieg-Sound: echte Audio-Datei, sonst synthetischer Jingle.
        AUFTRAG 3: MP4 (victory_screen.mp4) wird NICHT mehr als Audiodatei
        versucht - pygame.mixer.music kann MP4 je nach SDL_mixer-Build
        gar nicht oder nur stumm/fehlerhaft oeffnen. Nur echte Audio-
        Endungen, und nur wenn die Datei existiert (kein Exception-Flow)."""
        for name in ("victory_audio.mp3", "victory_audio.ogg", "victory_audio.wav"):
            if os.path.exists(name) and self._play_music(name):
                return True
        self.play("victory", 0.8)
        return False

    def _play_music(self, filename):
        if not self.enabled or self.muted:
            return False
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            return True
        except Exception:
            return False

    def stop_music(self, fade_ms=400):
        try:
            if pygame.mixer.get_init() is not None and pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(fade_ms)
        except Exception:
            pass

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop_music(150)
        return self.muted


SFX = SoundSystem()
