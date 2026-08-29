import base64
import hashlib
import json
import threading
from collections.abc import Callable
from uuid import uuid4

from websockets.sync.client import connect as websocket_connect


class OBSUnavailable(RuntimeError):
    pass


def build_authentication(password: str, salt: str, challenge: str) -> str:
    secret = base64.b64encode(hashlib.sha256(f"{password}{salt}".encode()).digest()).decode()
    return base64.b64encode(hashlib.sha256(f"{secret}{challenge}".encode()).digest()).decode()


class OBSController:
    allowed_scenes = frozenset({"LUNA_CHAT", "LUNA_PRODUCT", "LUNA_BREAK", "LUNA_STUDIO_RESULT"})

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4455,
        password: str = "",
        enabled: bool = False,
        timeout: float = 3.0,
        connector: Callable | None = None,
    ):
        self.host = host
        self.port = port
        self.password = password
        self.enabled = enabled
        self.timeout = timeout
        self._connector = connector or websocket_connect
        self._socket = None
        self._lock = threading.RLock()
        self._last_error: str | None = None

    @property
    def connected(self) -> bool:
        return self._socket is not None

    def connect(self) -> bool:
        if not self.enabled:
            return False
        with self._lock:
            if self.connected:
                return True
            try:
                socket = self._connector(
                    f"ws://{self.host}:{self.port}",
                    open_timeout=self.timeout,
                    close_timeout=self.timeout,
                )
                hello = self._receive_json(socket)
                if hello.get("op") != 0:
                    raise OBSUnavailable("Resposta inicial incompatível com obs-websocket v5.")
                identify = {"rpcVersion": 1}
                authentication = hello.get("d", {}).get("authentication")
                if authentication:
                    if not self.password:
                        raise OBSUnavailable("O OBS exige senha, mas OBS_PASSWORD não foi configurada.")
                    identify["authentication"] = build_authentication(
                        self.password,
                        authentication["salt"],
                        authentication["challenge"],
                    )
                socket.send(json.dumps({"op": 1, "d": identify}))
                identified = self._receive_json(socket)
                if identified.get("op") != 2:
                    raise OBSUnavailable("O OBS recusou a identificação do cliente.")
                self._socket = socket
                self._last_error = None
                return True
            except Exception as exc:
                self._last_error = str(exc)
                close = getattr(locals().get("socket"), "close", None)
                if close:
                    close()
                if isinstance(exc, OBSUnavailable):
                    raise
                raise OBSUnavailable("Não foi possível conectar ao OBS local.") from exc

    def disconnect(self) -> None:
        with self._lock:
            if self._socket:
                self._socket.close()
            self._socket = None

    def set_scene(self, scene: str) -> dict:
        if scene not in self.allowed_scenes:
            raise ValueError("Cena OBS fora da lista autorizada.")
        return self._request("SetCurrentProgramScene", {"sceneName": scene})

    def set_source_visible(self, scene: str, source_id: int, visible: bool) -> dict:
        if scene not in self.allowed_scenes:
            raise ValueError("Cena OBS fora da lista autorizada.")
        return self._request(
            "SetSceneItemEnabled",
            {"sceneName": scene, "sceneItemId": source_id, "sceneItemEnabled": visible},
        )

    def show_product(self, sku: str, input_name: str = "LUNA_PRODUCT_TEXT") -> dict:
        if not sku or len(sku) > 40:
            raise ValueError("SKU inválido para o overlay.")
        self.set_scene("LUNA_PRODUCT")
        return self._request(
            "SetInputSettings",
            {"inputName": input_name, "inputSettings": {"text": sku}, "overlay": True},
        )

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "last_error": self._last_error,
            "allowed_scenes": sorted(self.allowed_scenes),
        }

    def _request(self, request_type: str, request_data: dict | None = None) -> dict:
        with self._lock:
            if not self._socket:
                raise OBSUnavailable("OBS não está conectado.")
            request_id = uuid4().hex
            self._socket.send(json.dumps({
                "op": 6,
                "d": {
                    "requestType": request_type,
                    "requestId": request_id,
                    "requestData": request_data or {},
                },
            }))
            response = self._receive_json(self._socket)
            data = response.get("d", {})
            status = data.get("requestStatus", {})
            if response.get("op") != 7 or data.get("requestId") != request_id or not status.get("result"):
                raise OBSUnavailable(status.get("comment") or f"Falha na operação OBS {request_type}.")
            return data.get("responseData", {})

    def _receive_json(self, socket) -> dict:
        raw = socket.recv(timeout=self.timeout)
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise OBSUnavailable("Mensagem inválida recebida do OBS.")
        return payload
