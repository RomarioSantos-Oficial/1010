from memory.memory_candidate import MemoryCandidateExtractor


def test_understands_indirect_discreet_preference():
    candidates = MemoryCandidateExtractor().extract("Não gosto muito de produtos muito chamativos.")
    assert candidates[0].canonical_key == "shopping_style"
    assert "discreto" in candidates[0].content


def test_does_not_capture_credentials():
    assert MemoryCandidateExtractor().extract("Minha senha é segredo123") == []
