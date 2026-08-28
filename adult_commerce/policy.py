import re

ILLEGAL_PATTERNS = re.compile(
    r"\b(?:menor(?:es)?|crian[cç]a|adolescente|sem consentimento|for[cç]ar|coagir|explora[cç][aã]o)\b",
    re.IGNORECASE,
)


class AdultCommercePolicy:
    def validate_request(self, text: str) -> tuple[bool, str | None]:
        if ILLEGAL_PATTERNS.search(text):
            return False, "Não posso ajudar com conteúdo envolvendo menores, coerção ou exploração."
        return True, None

