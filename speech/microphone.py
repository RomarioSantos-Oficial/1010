import io

import numpy as np
import sounddevice as sd
import soundfile as sf


class MicrophoneRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, device: int | None = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device

    @staticmethod
    def input_devices() -> list[dict]:
        devices = []
        for index, device in enumerate(sd.query_devices()):
            if int(device["max_input_channels"]) > 0:
                devices.append(
                    {
                        "index": index,
                        "name": str(device["name"]),
                        "channels": int(device["max_input_channels"]),
                        "default_sample_rate": int(device["default_samplerate"]),
                    }
                )
        return devices

    def record(self, seconds: float = 5.0) -> np.ndarray:
        frames = max(1, int(seconds * self.sample_rate))
        recording = sd.rec(
            frames,
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            device=self.device,
        )
        sd.wait()
        return np.asarray(recording).reshape(-1)

    def to_wav(self, samples: np.ndarray) -> bytes:
        output = io.BytesIO()
        sf.write(output, samples, self.sample_rate, format="WAV", subtype="PCM_16")
        return output.getvalue()
