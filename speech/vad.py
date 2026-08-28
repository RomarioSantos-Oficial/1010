import numpy as np


class EnergyVoiceActivityDetector:
    def __init__(self, threshold: float = 0.012, min_active_ratio: float = 0.03, frame_ms: int = 30):
        self.threshold = threshold
        self.min_active_ratio = min_active_ratio
        self.frame_ms = frame_ms

    def contains_speech(self, samples: np.ndarray, sample_rate: int) -> bool:
        audio = np.asarray(samples, dtype=np.float32).reshape(-1)
        if audio.size == 0:
            return False
        peak = float(np.max(np.abs(audio)))
        if peak > 1.0:
            audio /= 32768.0
        frame_size = max(1, int(sample_rate * self.frame_ms / 1000))
        usable = audio[: (audio.size // frame_size) * frame_size]
        if usable.size == 0:
            rms = np.sqrt(np.mean(audio * audio))
            return bool(rms >= self.threshold)
        frames = usable.reshape(-1, frame_size)
        rms = np.sqrt(np.mean(frames * frames, axis=1))
        active_ratio = float(np.mean(rms >= self.threshold))
        return active_ratio >= self.min_active_ratio
