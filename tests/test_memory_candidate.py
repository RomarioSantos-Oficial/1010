from memory.memory_candidate import MemoryCandidateExtractor


def test_understands_indirect_discreet_preference():
    candidates = MemoryCandidateExtractor().extract("Não gosto muito de produtos muito chamativos.")
    assert candidates[0].canonical_key == "shopping_style"
    assert "discreto" in candidates[0].content


def test_does_not_capture_credentials():
    assert MemoryCandidateExtractor().extract("Minha senha é segredo123") == []


def test_normalizes_plural_color_and_keeps_garment_type():
    candidates = MemoryCandidateExtractor().extract(
        "Eu prefiro roupas azuis e vestidos longos."
    )
    by_key = {candidate.canonical_key: candidate.content for candidate in candidates}
    assert by_key["product_color"] == "prefere produtos na cor azul"
    assert by_key["product_type"] == "prefere vestidos longos"
