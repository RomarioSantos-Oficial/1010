import os
from abc import ABC, abstractmethod
from collections.abc import Sequence


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...


class SentenceTransformerEmbeddings(EmbeddingProvider):
    def __init__(self, model_name: str):
        # Usa os certificados confiáveis do Windows, inclusive ambientes com
        # proxy corporativo, sem desativar a validação TLS.
        try:
            import truststore
            truststore.inject_into_ssl()
        except ImportError:
            pass
        os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
        os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name, device="cpu")

    @property
    def dimension(self) -> int:
        return int(self._model.get_embedding_dimension())

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        vectors = self._model.encode(list(texts), normalize_embeddings=True)
        return vectors.tolist()
