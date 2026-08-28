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
