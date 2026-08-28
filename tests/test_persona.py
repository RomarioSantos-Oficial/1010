from config.settings import ROOT
from persona.identity import load_persona


def test_loads_luna_persona():
    persona = load_persona(ROOT / "config" / "persona.yaml")
    assert persona.name == "Luna"
    assert persona.identity.disclosure is True
    assert persona.sales.never_invent_stock is True

