from collections.abc import Sequence

from brain.llm_provider import Message


class ContextManager:
    def __init__(self, history_limit: int = 16, memory_limit: int = 6, max_chars: int = 24_000):
        self.history_limit = history_limit
        self.memory_limit = memory_limit
        self.max_chars = max_chars

    def select_history(self, history: Sequence[Message]) -> list[Message]:
        selected: list[Message] = []
        used = 0
        for message in reversed(history[-self.history_limit:]):
            size = len(message["content"])
            if used + size > self.max_chars:
                break
            selected.append(message)
            used += size
        return list(reversed(selected))

    def select_memories(self, memories: Sequence[str]) -> list[str]:
        return list(memories[: self.memory_limit])
