import io
from threading import Lock

import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    def __init__(self):
        self._lock = Lock()

    def play(self, wav_data: bytes, blocking: bool = True) -> None:
        samples, sample_rate = sf.read(io.BytesIO(wav_data), dtype="float32")
        with self._lock:
            sd.play(samples, sample_rate)
            if blocking:
                sd.wait()

    def stop(self) -> None:
        sd.stop()
