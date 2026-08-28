import ctypes
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from .llm_provider import LLMProvider, Message

_DLL_HANDLES: list[object] = []


class LlamaCppProvider(LLMProvider):
    def __init__(self, model_path: Path, n_ctx: int = 4096, n_gpu_layers: int = -1):
        # Wheels CUDA no Windows distribuem cudart/cuBLAS dentro do ambiente
        # Python; registre esses diretórios antes de carregar llama.dll.
        if os.name == "nt":
            nvidia_root = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
            for dll_dir in nvidia_root.glob("*/bin"):
                if dll_dir.is_dir():
                    _DLL_HANDLES.append(os.add_dll_directory(str(dll_dir)))
            # O carregador do Windows pode não resolver dependências transitivas
            # da wheel mesmo com add_dll_directory; carregue-as na ordem correta.
            for pattern in ("cuda_runtime/bin/cudart64_*.dll", "cublas/bin/cublasLt64_*.dll", "cublas/bin/cublas64_*.dll"):
                for library in nvidia_root.glob(pattern):
                    _DLL_HANDLES.append(ctypes.CDLL(str(library)))
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python não está instalado. Instale requirements-llm.txt."
            ) from exc
        if not model_path.is_file():
            raise FileNotFoundError(f"Modelo GGUF não encontrado: {model_path}")
        self._llm = Llama(
            model_path=str(model_path), n_ctx=n_ctx, n_gpu_layers=n_gpu_layers,
            verbose=False,
        )

    @property
    def name(self) -> str:
        return "llama.cpp"

    def chat(self, messages: Sequence[Message]) -> str:
        result = self._llm.create_chat_completion(
            messages=list(messages), temperature=0.75, top_p=0.9, max_tokens=400,
        )
        return str(result["choices"][0]["message"]["content"]).strip()
