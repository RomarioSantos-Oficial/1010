from dataclasses import asdict, dataclass
from threading import Lock
from time import time

from avatar.expressions import Emotion, visual_state


@dataclass
class AvatarState:
    emotion: Emotion = "neutral"
    speaking: bool = False
    updated_at: float = 0.0


class AvatarController:
    def __init__(self, sprite_url: str = "/assets/avatar/luna_sprite_v1_1.png"):
        self.sprite_url = sprite_url
        self._state = AvatarState(updated_at=time())
        self._lock = Lock()

    def react(self, emotion: Emotion) -> dict:
        with self._lock:
            self._state.emotion = emotion
            self._state.updated_at = time()
            return self.snapshot()

    def set_speaking(self, speaking: bool) -> dict:
        with self._lock:
            self._state.speaking = speaking
            self._state.updated_at = time()
            return self.snapshot()

    def snapshot(self) -> dict:
        state = asdict(self._state)
        state["visual_state"] = visual_state(self._state.emotion, self._state.speaking)
        state["sprite_url"] = self.sprite_url
        return state
