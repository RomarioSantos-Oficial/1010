import re
import unicodedata
from dataclasses import dataclass

from adult_commerce.age_gate import AgeGate


def normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text.casefold())
    return "".join(character for character in value if not unicodedata.combining(character))


SEXUAL = re.compile(
    r"\b(?:erotic[oa]s?|sexo|sexual|pornograf\w*|nudez|nu[ao]s?|orgasm\w*|sex\s*shop|conto\s+adulto)\b"
)
MINOR = re.compile(
    r"\b(?:menor(?:es)?|crianca|infantil|adolescente|pre[- ]?adolescente|bebe|(?:[0-9]|1[0-7])\s*anos?)\b"
)
DECEASED = re.compile(r"\b(?:mort[oa]s?|cadaver(?:es)?|falecid[oa]s?|necrofili\w*)\b")
COERCION = re.compile(
    r"\b(?:estupro|sem\s+consentimento|nao\s+consensual|forcar|coagir|exploracao\s+sexual)\b"
)
MUTILATION = re.compile(r"\b(?:mutila\w*|desmembra\w*|esquarteja\w*|arrancar\s+(?:um\s+)?membro)\b")
HOMICIDE_INSTRUCTION = re.compile(
    r"\b(?:como|maneira|jeito|plano|instrucao|ensine|sugira|aconselhe)\b.{0,45}\b(?:matar|assassinar|eliminar)\b"
    r"|\b(?:devo|posso|quero|vou)\s+(?:matar|assassinar)\b|\bmate\s+(?:ele|ela|alguem|essa|esse)\b"
)


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    code: str | None = None
    message: str | None = None


class ContentSafetyPolicy:
    def __init__(self, age_gate: AgeGate | None = None):
        self.age_gate = age_gate or AgeGate()

    def evaluate(self, user_id: str, text: str, modality: str = "chat") -> PolicyDecision:
        clean = normalize(text)
        sexual = bool(SEXUAL.search(clean))
        visual = modality in {"image", "video", "try_on"}
        if MINOR.search(clean) and (sexual or visual):
            return PolicyDecision(False, "minor", "Não posso criar conteúdo sexual ou imagens envolvendo menores de 18 anos.")
        if DECEASED.search(clean) and (sexual or visual):
            return PolicyDecision(False, "deceased", "Não posso criar conteúdo sexual ou imagens envolvendo pessoas mortas.")
        if COERCION.search(clean):
            return PolicyDecision(False, "coercion", "Não posso criar conteúdo sexual sem consentimento ou com exploração.")
        if MUTILATION.search(clean):
            return PolicyDecision(False, "mutilation", "Não posso criar conteúdo de mutilação ou desmembramento.")
        if HOMICIDE_INSTRUCTION.search(clean):
            return PolicyDecision(False, "homicide_instruction", "Não posso incentivar nem ensinar como matar uma pessoa.")
        if sexual and not self.age_gate.is_verified(user_id):
            return PolicyDecision(False, "age_verification", "Conteúdo adulto exige confirmação de que você tem 18 anos ou mais.")
        return PolicyDecision(True)
