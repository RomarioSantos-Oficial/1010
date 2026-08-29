from adult_commerce.age_gate import AgeGate
from brain.action_router import ActionRequest
from brain.tool_router import CommerceIntentRouter, CommerceToolRouter, Intent
from commerce.catalog import CatalogService


def make_tools(tmp_path):
    gate = AgeGate()
    return CommerceToolRouter(CatalogService(tmp_path / "catalog.db"), gate), gate


def test_stock_comes_from_catalog(tmp_path):
    tools, _ = make_tools(tmp_path)
    result = tools.execute("ana", "Tem LING-001 tamanho G?", CommerceIntentRouter().classify("Tem LING-001 tamanho G?"))
    assert result.success
    assert result.data["stock"] == 4
    assert "4 unidade" in result.spoken_text


def test_invalid_tool_is_refused(tmp_path):
    tools, _ = make_tools(tmp_path)
    result = tools.execute_requested("ana", "faça isso", ActionRequest(action="run_system_command", action_args={"command": "x"}))
    assert not result.success
    assert result.error_code == "unauthorized_action"
    assert "não é autorizada" in result.spoken_text


def test_invalid_tool_arguments_are_identified(tmp_path):
    tools, _ = make_tools(tmp_path)
    result = tools.execute_requested(
        "ana",
        "Eu prefiro roupas azuis.",
        ActionRequest(action="recommend_products", action_args={"color": "azul"}),
    )
    assert not result.success
    assert result.error_code == "invalid_arguments"


def test_adult_catalog_requires_age_gate(tmp_path):
    tools, gate = make_tools(tmp_path)
    intent = Intent("search_products", {"category": "bem_estar_adulto"})
    blocked = tools.execute("ana", "Mostre produtos de sex shop", intent)
    assert not blocked.success
    gate.verify("ana", True)
    allowed = tools.execute("ana", "Mostre produtos de sex shop", intent)
    assert allowed.success
    assert "ADULT-" in allowed.spoken_text


def test_illegal_adult_request_is_refused_even_after_verification(tmp_path):
    tools, gate = make_tools(tmp_path)
    gate.verify("ana", True)
    result = tools.execute("ana", "produto adulto para menor", Intent("search_products", {"category": "bem_estar_adulto"}))
    assert not result.success
    assert "menores" in result.spoken_text


def test_adult_product_guide_requires_gate_and_uses_catalog(tmp_path):
    tools, gate = make_tools(tmp_path)
    text = "Como usar ADULT-001?"
    blocked = tools.execute("ana", text, CommerceIntentRouter().classify(text))
    assert not blocked.success
    gate.verify("ana", True)
    allowed = tools.execute("ana", text, CommerceIntentRouter().classify(text))
    assert allowed.success
    assert allowed.data["usage_guidance"]
    assert "Higienize" in allowed.spoken_text


def test_beachwear_and_shoe_intents(tmp_path):
    tools, _ = make_tools(tmp_path)
    beach = tools.execute("ana", "Mostre produtos de moda praia", CommerceIntentRouter().classify("Mostre produtos de moda praia"))
    assert beach.success and "PRAIA-" in beach.spoken_text
    shoe = tools.execute("ana", "Tem CALC-001 tamanho 37?", CommerceIntentRouter().classify("Tem CALC-001 tamanho 37?"))
    assert shoe.success and shoe.data["stock"] == 5
