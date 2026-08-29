import re
import unicodedata

from .schemas import MemoryCandidate

SENSITIVE = re.compile(
    r"\b(?:cpf|rg|passaporte|cart[aã]o|cvv|senha|token|chave pix|conta banc[aá]ria)\b",
    re.IGNORECASE,
)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value))


class MemoryCandidateExtractor:
    """Extrai somente preferências úteis; nunca dados pessoais livres."""

    def extract(self, text: str) -> list[MemoryCandidate]:
        clean = text.strip().rstrip(".!?")
        normalized = normalize(clean)
        if not clean or SENSITIVE.search(clean):
            return []

        response = self._response_style(normalized)
        if response:
            return [response]

        shopping = self._shopping_style(normalized)
        if shopping:
            return [shopping]

        return self._product_preferences(normalized)

    def _response_style(self, text: str) -> MemoryCandidate | None:
        if "resposta" not in text and not text.startswith("responda"):
            return None
        if any(term in text for term in ("curta", "curtas", "direta", "diretas", "resumida")):
            value = "curtas"
        elif any(term in text for term in ("detalhada", "detalhadas", "com detalhes")):
            value = "detalhadas"
        else:
            return None
        return MemoryCandidate(
            memory_type="response_style", content=f"prefere respostas {value}",
            canonical_key="response_style", confidence=0.96, importance=0.9,
        )

    def _shopping_style(self, text: str) -> MemoryCandidate | None:
        styles = {
            "discreto": ("discreto", "discreta", "discretos", "discretas", "nao chamativo", "pouco chamativo"),
            "marcante": ("marcante", "chamativo", "chamativa", "ousado", "ousada"),
            "elegante": ("elegante", "sofisticado", "sofisticada"),
        }
        preference_signal = any(term in text for term in ("prefiro", "gosto", "escolho", "quase sempre", "normalmente"))
        negative_signal = "nao gosto" in text
        for style, terms in styles.items():
            if any(term in text for term in terms) and (preference_signal or negative_signal):
                if negative_signal and style == "marcante":
                    style = "discreto"
                return MemoryCandidate(
                    memory_type="shopping_style", content=f"prefere produtos de estilo {style}",
                    canonical_key="shopping_style", confidence=0.91, importance=0.82,
                )
        return None

    def _product_preferences(self, text: str) -> list[MemoryCandidate]:
        signal = re.search(r"\b(?:gosto|prefiro|adoro|escolho)\b(?:\s+de)?\s+(.+)", text)
        if not signal:
            return []
        value = signal.group(1).strip()
        if len(value) < 3:
            return []
        colors = {
            "preto": "preto", "preta": "preto", "pretos": "preto", "pretas": "preto",
            "vermelho": "vermelho", "vermelha": "vermelho",
            "vermelhos": "vermelho", "vermelhas": "vermelho",
            "azul": "azul", "azuis": "azul",
            "branco": "branco", "branca": "branco", "brancos": "branco", "brancas": "branco",
        }
        color = next((colors[word] for word in value.split() if word in colors), None)
        results: list[MemoryCandidate] = []
        if color:
            results.append(MemoryCandidate(
                memory_type="product_preference", content=f"prefere produtos na cor {color}",
                canonical_key="product_color", confidence=0.88, importance=0.76,
            ))

        garment_preferences = {
            "vestidos longos": ("vestidos longos", "vestido longo"),
            "vestidos curtos": ("vestidos curtos", "vestido curto"),
            "moda praia": ("moda praia", "roupas de praia"),
            "roupas intimas": ("roupas intimas", "roupa intima", "lingerie"),
        }
        garment = next(
            (canonical for canonical, variants in garment_preferences.items() if any(item in value for item in variants)),
            None,
        )
        if garment:
            results.append(MemoryCandidate(
                memory_type="product_preference",
                content=f"prefere {garment}",
                canonical_key="product_type",
                confidence=0.88,
                importance=0.76,
            ))
        if results:
            return results

        stems = {word[:-1] if word.endswith("s") and len(word) > 4 else word for word in value.split()}
        canonical = "product_preference:" + "_".join(sorted(stems))[:90]
        return [MemoryCandidate(
            memory_type="product_preference", content=f"prefere {value}",
            canonical_key=canonical, confidence=0.84, importance=0.72,
        )]
