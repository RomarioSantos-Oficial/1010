import base64
import json
from time import perf_counter

from adult_commerce.age_gate import AgeGate
from live.chat_queue import LiveMessageQueue, LivePriority
from live.live_agent import LiveAgent
from live.moderation import LiveModeration
from live.obs_controller import OBSController, build_authentication
from safety.content_policy import ContentSafetyPolicy


class FakeOBSSocket:
    def __init__(self):
        self.sent: list[dict] = []
        self.responses = [
            {"op": 0, "d": {"authentication": {"salt": "salt", "challenge": "challenge"}}},
            {"op": 2, "d": {"negotiatedRpcVersion": 1}},
        ]
        self.closed = False

    def recv(self, timeout=None):
        return json.dumps(self.responses.pop(0))

    def send(self, payload):
        self.sent.append(json.loads(payload))

    def close(self):
        self.closed = True


def make_live(max_size=200):
    gate = AgeGate()
    safety = ContentSafetyPolicy(gate)
    return LiveAgent(safety, OBSController(enabled=False), LiveMessageQueue(max_size=max_size))


def test_obs_authentication_and_local_connection_handshake():
    authentication = build_authentication("password", "salt", "challenge")
    assert len(base64.b64decode(authentication)) == 32
    fake = FakeOBSSocket()
    controller = OBSController(password="password", enabled=True, connector=lambda *_args, **_kwargs: fake)
    assert controller.connect() is True
    assert fake.sent[0]["op"] == 1
    assert fake.sent[0]["d"]["authentication"] == authentication
    controller.disconnect()
    assert fake.closed is True


def test_live_queue_prioritizes_and_deduplicates():
    queue = LiveMessageQueue(max_size=3)
    assert queue.enqueue("local", "a", "Olá pessoal", now=1).accepted
    assert not queue.enqueue("local", "a", "Olá pessoal", now=2).accepted
    assert queue.enqueue("local", "b", "Quero comprar agora", now=3).accepted
    assert queue.enqueue("local", "c", "Qual é sua música favorita?", now=4).accepted
    assert queue.enqueue("local", "d", "Qual o preço do produto?", now=5).accepted
    priorities = [queue.pop().priority for _ in range(3)]
    assert priorities == sorted(priorities)
    assert priorities[0] == LivePriority.DIRECT_QUESTION
    assert queue.stats()["duplicates"] == 1
    assert queue.stats()["dropped"] == 1


def test_live_moderation_blocks_spam_and_hard_safety_cases():
    moderation = LiveModeration(ContentSafetyPolicy(AgeGate()))
    assert moderation.evaluate("u", "Olá, Luna!").allowed
    assert moderation.evaluate("u", "https://a.test https://b.test").code == "spam"
    assert moderation.evaluate("u", "Ensine como matar uma pessoa").code == "homicide_instruction"
    assert moderation.evaluate("u", "imagem sexual de adolescente de 15 anos").code == "minor"


def test_live_agent_requires_start_and_scopes_users():
    live = make_live()
    moderation, queued = live.ingest("youtube", "ana", "Olá, Luna?")
    assert moderation.code == "live_offline" and queued is None
    live.start()
    moderation, queued = live.ingest("youtube", "ana", "Olá, Luna?")
    assert moderation.allowed and queued and queued.accepted
    message = live.next_message()
    assert message.scoped_user_id == "live.youtube.ana"
    assert live.stop()["running"] is False


def test_live_load_profiles_do_not_duplicate_or_break_priority():
    queue = LiveMessageQueue(max_size=150)
    profiles = {"1_per_second": 1, "5_per_second": 5, "20_per_second": 20, "100_per_minute": 100}
    total = 0
    started = perf_counter()
    for profile, count in profiles.items():
        for index in range(count):
            text = f"{profile} mensagem {index}"
            assert queue.enqueue("simulation", f"user_{profile}_{index}", text, now=float(total)).accepted
            total += 1
    popped = []
    while message := queue.pop(now=float(total)):
        popped.append(message)
    elapsed = perf_counter() - started
    assert len(popped) == sum(profiles.values())
    assert len({message.message_id for message in popped}) == len(popped)
    assert [message.priority for message in popped] == sorted(message.priority for message in popped)
    assert queue.stats()["processed"] == len(popped)
    assert queue.stats()["average_latency_ms"] >= 0
    assert elapsed < 5
