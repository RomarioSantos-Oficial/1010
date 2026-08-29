import heapq
import re
import threading
import time
import unicodedata
from dataclasses import asdict, dataclass
from enum import IntEnum
from uuid import uuid4


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    return "".join(character for character in value if not unicodedata.combining(character))


class LivePriority(IntEnum):
    DIRECT_QUESTION = 0
    PRODUCT = 1
    PURCHASE = 2
    SOCIAL = 3
    SPAM = 99


@dataclass(frozen=True)
class LiveMessage:
    message_id: str
    platform: str
    user_id: str
    text: str
    category: str
    priority: int
    timestamp: float

    @property
    def scoped_user_id(self) -> str:
        return f"live.{self.platform}.{self.user_id}"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class EnqueueResult:
    accepted: bool
    code: str
    message: LiveMessage | None = None


class LiveMessageClassifier:
    product_terms = (
        "produto", "preco", "valor", "estoque", "tamanho", "sku", "vestido",
        "biquini", "lingerie", "calcado", "eletronico", "massageador", "como usar",
    )
    purchase_terms = ("quero comprar", "como compro", "link de compra", "frete", "entrega", "pagamento")

    def classify(self, text: str) -> tuple[str, LivePriority]:
        clean = normalize(text)
        if any(term in clean for term in self.product_terms) or re.search(r"\b[A-Z]+-\d{3}\b", text.upper()):
            return "product", LivePriority.PRODUCT
        if any(term in clean for term in self.purchase_terms):
            return "purchase", LivePriority.PURCHASE
        if "?" in text or re.search(r"\b(?:luna|voce|qual|como|quando|onde|por que)\b", clean):
            return "direct_question", LivePriority.DIRECT_QUESTION
        return "social", LivePriority.SOCIAL


class LiveMessageQueue:
    def __init__(self, max_size: int = 200, duplicate_window_seconds: float = 30.0):
        if max_size < 1:
            raise ValueError("max_size deve ser positivo.")
        self.max_size = max_size
        self.duplicate_window_seconds = duplicate_window_seconds
        self.classifier = LiveMessageClassifier()
        self._heap: list[tuple[int, int, LiveMessage]] = []
        self._seen: dict[tuple[str, str, str], float] = {}
        self._sequence = 0
        self._lock = threading.RLock()
        self._stats = {"accepted": 0, "duplicates": 0, "dropped": 0, "processed": 0}
        self._latency_total_ms = 0.0
        self._latency_max_ms = 0.0

    def enqueue(self, platform: str, user_id: str, text: str, now: float | None = None) -> EnqueueResult:
        timestamp = time.time() if now is None else now
        normalized_text = " ".join(normalize(text).split())
        key = (platform.casefold(), user_id.casefold(), normalized_text)
        category, priority = self.classifier.classify(text)
        message = LiveMessage(
            message_id=uuid4().hex[:12],
            platform=platform,
            user_id=user_id,
            text=text.strip(),
            category=category,
            priority=int(priority),
            timestamp=timestamp,
        )
        with self._lock:
            self._expire_seen(timestamp)
            if key in self._seen:
                self._stats["duplicates"] += 1
                return EnqueueResult(False, "duplicate")
            self._seen[key] = timestamp
            entry = (message.priority, self._sequence, message)
            self._sequence += 1
            if len(self._heap) >= self.max_size:
                worst_index = max(range(len(self._heap)), key=lambda index: self._heap[index][:2])
                worst = self._heap[worst_index]
                if entry[:2] >= worst[:2]:
                    self._stats["dropped"] += 1
                    return EnqueueResult(False, "queue_full")
                self._heap[worst_index] = entry
                heapq.heapify(self._heap)
                self._stats["dropped"] += 1
            else:
                heapq.heappush(self._heap, entry)
            self._stats["accepted"] += 1
            return EnqueueResult(True, "queued", message)

    def pop(self, now: float | None = None) -> LiveMessage | None:
        with self._lock:
            if not self._heap:
                return None
            self._stats["processed"] += 1
            message = heapq.heappop(self._heap)[2]
            current_time = time.time() if now is None else now
            latency_ms = max(0.0, (current_time - message.timestamp) * 1000)
            self._latency_total_ms += latency_ms
            self._latency_max_ms = max(self._latency_max_ms, latency_ms)
            return message

    def clear(self) -> int:
        with self._lock:
            count = len(self._heap)
            self._heap.clear()
            self._seen.clear()
            return count

    def stats(self) -> dict[str, int | float]:
        with self._lock:
            processed = self._stats["processed"]
            average = self._latency_total_ms / processed if processed else 0.0
            return {
                **self._stats,
                "queued": len(self._heap),
                "capacity": self.max_size,
                "average_latency_ms": round(average, 3),
                "max_latency_ms": round(self._latency_max_ms, 3),
            }

    def _expire_seen(self, now: float) -> None:
        cutoff = now - self.duplicate_window_seconds
        expired = [key for key, timestamp in self._seen.items() if timestamp < cutoff]
        for key in expired:
            self._seen.pop(key, None)
