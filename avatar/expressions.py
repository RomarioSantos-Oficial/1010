from typing import Literal

Emotion = Literal["neutral", "happy", "sad", "surprised", "thinking"]
VisualState = Literal["neutral", "blink", "speaking", "happy"]


def visual_state(emotion: Emotion = "neutral", speaking: bool = False) -> VisualState:
    if speaking:
        return "speaking"
    if emotion == "happy":
        return "happy"
    return "neutral"
