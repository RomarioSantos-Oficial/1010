from dataclasses import dataclass


@dataclass
class AgeVerification:
    confirmed_adult: bool = False


class AgeGate:
    def __init__(self):
        self._verified: dict[str, AgeVerification] = {}

    def verify(self, user_id: str, confirmed_adult: bool) -> bool:
        self._verified[user_id] = AgeVerification(confirmed_adult=confirmed_adult)
        return confirmed_adult

    def is_verified(self, user_id: str) -> bool:
        return self._verified.get(user_id, AgeVerification()).confirmed_adult

    def clear(self, user_id: str) -> None:
        self._verified.pop(user_id, None)

