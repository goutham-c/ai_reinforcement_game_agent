"""
8-Bit Retro Sound Synthesizer for Mario Bros using pure NumPy waveforms.
Zero external audio files required.
"""

import math
import numpy as np

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


class SoundManager:
    def __init__(self, sample_rate: int = 22050, enabled: bool = True):
        self.sample_rate = sample_rate
        self.enabled = enabled
        self.sounds = {}
        self.initialized = False

        if HAS_PYGAME and self.enabled:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=sample_rate, size=-16, channels=1, buffer=512)
                self.initialized = True
                self._generate_sounds()
            except Exception as e:
                print(f"[SoundManager] Warning: Audio init failed ({e}), running muted.")
                self.initialized = False

    def _generate_square_wave(self, freq: float, duration: float, volume: float = 0.3) -> np.ndarray:
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        wave = np.sign(np.sin(2 * np.pi * freq * t))
        decay = np.linspace(1.0, 0.05, n_samples)
        signal = (wave * decay * volume * 32767).astype(np.int16)
        return signal

    def _generate_freq_sweep(self, start_f: float, end_f: float, duration: float, volume: float = 0.35) -> np.ndarray:
        n_samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n_samples, False)
        # Linear frequency modulation
        freqs = np.linspace(start_f, end_f, n_samples)
        phase = 2 * np.pi * np.cumsum(freqs) / self.sample_rate
        wave = np.sign(np.sin(phase))
        decay = np.linspace(1.0, 0.1, n_samples)
        signal = (wave * decay * volume * 32767).astype(np.int16)
        return signal

    def _generate_noise_stomp(self, duration: float = 0.12, volume: float = 0.4) -> np.ndarray:
        n_samples = int(self.sample_rate * duration)
        noise = np.random.uniform(-1, 1, n_samples)
        decay = np.exp(np.linspace(0, -6, n_samples))
        signal = (noise * decay * volume * 32767).astype(np.int16)
        return signal

    def _make_sound(self, samples: np.ndarray):
        if not self.initialized:
            return None
        # Pygame requires 2D array (N, 2) if stereo or 1D array if mono
        mixer_init = pygame.mixer.get_init()
        if mixer_init and mixer_init[2] == 2:
            stereo_samples = np.column_stack((samples, samples))
            return pygame.sndarray.make_sound(stereo_samples)
        return pygame.sndarray.make_sound(samples)

    def _generate_sounds(self):
        try:
            # Jump sound: fast upward sweep
            jump_samples = self._generate_freq_sweep(180, 520, 0.14, volume=0.25)
            self.sounds["jump"] = self._make_sound(jump_samples)

            # Stomp sound: sharp noise transient + low thump
            stomp_samples = self._generate_noise_stomp(0.12, volume=0.35)
            self.sounds["stomp"] = self._make_sound(stomp_samples)

            # Coin sound: two-tone chime (B5 -> E6)
            s1 = self._generate_square_wave(987.77, 0.08, volume=0.25)
            s2 = self._generate_square_wave(1318.51, 0.22, volume=0.25)
            coin_samples = np.concatenate([s1, s2])
            self.sounds["coin"] = self._make_sound(coin_samples)

            # Bump sound (hitting brick from below)
            bump_samples = self._generate_freq_sweep(240, 100, 0.09, volume=0.3)
            self.sounds["bump"] = self._make_sound(bump_samples)

            # Death sound: descending slide
            death_samples = self._generate_freq_sweep(500, 90, 0.35, volume=0.3)
            self.sounds["death"] = self._make_sound(death_samples)

            # Victory Fanfare: ascending arpeggio (C5 -> E5 -> G5 -> C6)
            v1 = self._generate_square_wave(523.25, 0.1, volume=0.3)
            v2 = self._generate_square_wave(659.25, 0.1, volume=0.3)
            v3 = self._generate_square_wave(783.99, 0.1, volume=0.3)
            v4 = self._generate_square_wave(1046.50, 0.35, volume=0.3)
            vic_samples = np.concatenate([v1, v2, v3, v4])
            self.sounds["victory"] = self._make_sound(vic_samples)
        except Exception as e:
            print(f"[SoundManager] Waveform generation note: {e}")

    def play(self, sound_name: str):
        if not self.initialized or not self.enabled:
            return
        snd = self.sounds.get(sound_name)
        if snd:
            try:
                snd.play()
            except Exception:
                pass


# Global sound manager instance
sound_manager = SoundManager()
