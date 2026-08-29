from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field


class ActionRequest(BaseModel):
    action: str = Field(pattern=r"^[a-z_]+$")
    action_args: dict[str, Any] = Field(default_factory=dict)


class ActionResult(BaseModel):
    action: str
    success: bool
    data: dict[str, Any] = Field(default_factory=dict)
    spoken_text: str
    error_code: str | None = None


class ActionRouter:
    def __init__(self):
        self._actions: dict[str, Callable[..., ActionResult]] = {}

    def register(self, name: str, action: Callable[..., ActionResult]) -> None:
        if not name.replace("_", "").isalnum():
            raise ValueError("Nome de ação inválido.")
        self._actions[name] = action

    def execute(self, request: ActionRequest) -> ActionResult:
        action = self._actions.get(request.action)
        if not action:
            return ActionResult(
                action=request.action,
                success=False,
                spoken_text="Essa ação não é autorizada.",
                error_code="unauthorized_action",
            )
        try:
            return action(**request.action_args)
        except (TypeError, ValueError):
            return ActionResult(
                action=request.action,
                success=False,
                spoken_text="Os argumentos dessa ação são inválidos.",
                error_code="invalid_arguments",
            )
