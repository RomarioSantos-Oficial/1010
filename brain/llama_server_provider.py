import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path

from .llm_provider import LLMProvider, Message


class LlamaServerProvider(LLMProvider):
    """Executa o servidor oficial llama.cpp localmente e usa sua API HTTP."""

    def __init__(self, model_path: Path, n_ctx: int = 4096, n_gpu_layers: int = -1, port: int = 8081):
        if not model_path.is_file():
            raise FileNotFoundError(f"Modelo GGUF não encontrado: {model_path}")
        executable, command = self._find_executable()
        self.base_url = f"http://127.0.0.1:{port}"
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self._process = subprocess.Popen(
            [executable, *command, "-m", str(model_path), "-c", str(n_ctx), "-ngl", str(n_gpu_layers),
             "--host", "127.0.0.1", "--port", str(port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        self._wait_until_ready()

    @staticmethod
    def _find_executable() -> tuple[str, list[str]]:
        bundled = Path(__file__).resolve().parents[1] / "tools" / "llama.cpp" / "bin" / "llama-server.exe"
        if bundled.is_file():
            return str(bundled), []
        found = shutil.which("llama-server")
        if found:
            return found, []
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
        matches = list(local.glob("ggml.llamacpp_*/*llama-server.exe"))
        if matches:
            return str(matches[0]), []
        unified = list(local.glob("ggml.llamacpp_*/llama.exe"))
        if unified:
            return str(unified[0]), ["serve"]
        raise FileNotFoundError("llama.cpp não foi encontrado no PATH nem no WinGet.")

    def _wait_until_ready(self, timeout: float = 120) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._process.poll() is not None:
                raise RuntimeError("llama-server encerrou durante a carga do modelo.")
            try:
                with urllib.request.urlopen(f"{self.base_url}/health", timeout=2) as response:
                    if response.status == 200:
                        return
            except (OSError, urllib.error.URLError):
                time.sleep(0.5)
        self.close()
        raise TimeoutError("llama-server não carregou o modelo em 120 segundos.")

    @property
    def name(self) -> str:
        return "llama.cpp-server"

    def chat(self, messages: Sequence[Message]) -> str:
        payload = json.dumps({
            "messages": list(messages), "temperature": 0.75, "top_p": 0.9,
            "max_tokens": 700, "chat_template_kwargs": {"enable_thinking": False},
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions", data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(request, timeout=300) as response:
            result = json.load(response)
        return str(result["choices"][0]["message"]["content"]).strip()

    def close(self) -> None:
        if getattr(self, "_process", None) and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
