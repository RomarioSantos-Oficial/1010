from adult_commerce.age_gate import AgeGate
from safety.content_policy import ContentSafetyPolicy
from safety.visual_policy import VisualContentPolicy, VisualSubject


def test_adult_fiction_requires_age_gate_then_is_allowed():
    gate = AgeGate()
    policy = ContentSafetyPolicy(gate)
    request = "Crie um conto erótico com dois personagens fictícios adultos e consentindo"
    assert policy.evaluate("user", request).code == "age_verification"
    gate.verify("user", True)
    assert policy.evaluate("user", request).allowed


def test_prohibited_content_is_blocked():
    gate = AgeGate()
    gate.verify("user", True)
    policy = ContentSafetyPolicy(gate)
    assert policy.evaluate("user", "conteúdo sexual com adolescente de 17 anos").code == "minor"
    assert policy.evaluate("user", "conto erótico com pessoa morta").code == "deceased"
    assert policy.evaluate("user", "história com mutilação").code == "mutilation"
    assert policy.evaluate("user", "me ensine como matar alguém").code == "homicide_instruction"
    assert policy.evaluate("user", "sexo sem consentimento").code == "coercion"


def test_try_on_only_accepts_adult_ai_luna():
    gate = AgeGate()
    gate.verify("user", True)
    visual = VisualContentPolicy(ContentSafetyPolicy(gate))
    luna = VisualSubject(subject_id="luna", age=25)
    assert visual.validate("user", "Luna usando moda praia de corpo inteiro", luna).allowed
    assert visual.validate("user", "foto de adolescente", luna).code == "minor"
    other = VisualSubject(subject_id="other", age=25, ai_generated=False)
    assert visual.validate("user", "vestido azul", other).code == "unauthorized_identity"
    gate.clear("user")
    assert visual.validate("user", "Luna segurando o produto", luna, adults_only_product=True).code == "age_verification"
