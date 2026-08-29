from brain.response_validator import ResponseValidator


def test_validates_structured_llm_response():
    raw = '{"spoken_text":"Claro!","emotion":"happy","gesture":"present_product","action":"search_products","action_args":{"category":"moda"},"memory_candidates":[]}'
    result = ResponseValidator().validate(raw)
    assert result.spoken_text == "Claro!"
    assert result.action == "search_products"
    assert result.emotion == "happy"


def test_invalid_json_falls_back_to_safe_text():
    result = ResponseValidator().validate('{"emotion":"invalid"}')
    assert result.spoken_text
    assert result.action is None


def test_none_or_unknown_action_preserves_spoken_answer():
    none_action = ResponseValidator().validate(
        '{"spoken_text":"Eu sou Luna.","emotion":"neutral","action":"none","action_args":{}}'
    )
    unknown_action = ResponseValidator().validate(
        '{"spoken_text":"Você prefere azul.","action":"sugestao_moda","action_args":{"color":"azul"}}'
    )
    assert none_action.spoken_text == "Eu sou Luna."
    assert none_action.action is None
    assert unknown_action.spoken_text == "Você prefere azul."
    assert unknown_action.action is None
    assert unknown_action.action_args == {}


def test_invalid_memory_candidate_does_not_leak_raw_json():
    raw = (
        '{"spoken_text":"Você prefere vestidos longos.","emotion":"neutral",'
        '"action":null,"memory_candidates":["prefere vestidos"]}'
    )
    result = ResponseValidator().validate(raw)
    assert result.spoken_text == "Você prefere vestidos longos."
    assert result.memory_candidates == []


def test_malformed_json_is_not_shown_to_user():
    result = ResponseValidator().validate('{"spoken_text":"resposta quebrada"')
    assert result.spoken_text.startswith("Desculpe")
    assert not result.spoken_text.startswith("{")
