from collections.abc import Sequence

from .llm_provider import LLMProvider, Message


class DemoProvider(LLMProvider):
    """Fallback explícito para validar o aplicativo sem baixar um GGUF."""

    @property
    def name(self) -> str:
        return "demo"

    def chat(self, messages: Sequence[Message]) -> str:
        text = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        lower = text.lower()
        if any(term in lower for term in ("quem é você", "quem e voce", "você é real", "voce e real")):
            return "Sou Luna, uma personagem virtual de IA. Estou rodando localmente no seu computador."
        if any(term in lower for term in ("preço", "preco", "estoque", "tamanho")):
            return "Ainda não tenho um catálogo conectado nesta versão. Não vou inventar preço ou estoque."
        return (
            "Estou funcionando no modo de demonstração, com memória local ativa. "
            f"Entendi sua mensagem: “{text}”. Instale o modelo GGUF para liberar respostas completas."
        )

