from typing import Protocol

from .chat_queue import LiveMessage


class PlatformAdapter(Protocol):
    name: str

    def send_reply(self, message: LiveMessage, text: str) -> None: ...


class LocalPreviewAdapter:
    name = "local"

    def __init__(self):
        self.replies: list[dict[str, str]] = []

    def send_reply(self, message: LiveMessage, text: str) -> None:
        self.replies.append({"message_id": message.message_id, "user_id": message.user_id, "text": text})
