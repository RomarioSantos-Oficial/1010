from datetime import UTC, datetime

from safety.content_policy import ContentSafetyPolicy

from .chat_queue import EnqueueResult, LiveMessage, LiveMessageQueue
from .moderation import LiveModeration, ModerationDecision
from .obs_controller import OBSController


class LiveAgent:
    def __init__(
        self,
        safety: ContentSafetyPolicy,
        obs: OBSController,
        queue: LiveMessageQueue | None = None,
    ):
        self.queue = queue or LiveMessageQueue()
        self.moderation = LiveModeration(safety)
        self.obs = obs
        self.running = False
        self.started_at: str | None = None

    def start(self, connect_obs: bool = False) -> dict:
        if connect_obs:
            self.obs.connect()
        self.running = True
        self.started_at = datetime.now(UTC).isoformat()
        return self.status()

    def stop(self, clear_queue: bool = True) -> dict:
        self.running = False
        if clear_queue:
            self.queue.clear()
        self.obs.disconnect()
        return self.status()

    def ingest(self, platform: str, user_id: str, text: str) -> tuple[ModerationDecision, EnqueueResult | None]:
        if not self.running:
            return ModerationDecision(False, "live_offline", "A live não está ativa."), None
        scoped_user_id = f"live.{platform}.{user_id}"
        moderation = self.moderation.evaluate(scoped_user_id, text)
        if not moderation.allowed:
            return moderation, None
        return moderation, self.queue.enqueue(platform, user_id, text)

    def next_message(self) -> LiveMessage | None:
        if not self.running:
            return None
        return self.queue.pop()

    def status(self) -> dict:
        return {
            "running": self.running,
            "started_at": self.started_at,
            "queue": self.queue.stats(),
            "obs": self.obs.status(),
        }
