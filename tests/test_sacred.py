"""Tests for the sacred content guard."""

from caveman import CavemanCompressor
from caveman.sacred import build_sacred_regex, protect, restore


def roundtrip(text, extra=None):
    regex = build_sacred_regex(extra or [])
    protected, placeholders = protect(text, regex)
    return protected, restore(protected, placeholders)


# ------------------------------------------------------------------
# protect / restore round-trips
# ------------------------------------------------------------------

def test_code_block_protected():
    regex = build_sacred_regex([])
    protected, ph = protect("Do ```x = 1\nreturn x``` this", regex)
    assert "```x = 1" not in protected
    assert len(ph) == 1


def test_code_block_roundtrip():
    text = "Do ```x = 1\nreturn x``` this"
    _, restored = roundtrip(text)
    assert restored == text


def test_inline_code_protected():
    regex = build_sacred_regex([])
    text = "Use `foo_bar()` here"
    protected, ph = protect(text, regex)
    assert "`foo_bar()`" not in protected
    assert len(ph) == 1


def test_inline_code_roundtrip():
    text = "Use `foo_bar()` here"
    _, restored = roundtrip(text)
    assert restored == text


def test_url_roundtrip():
    text = "See https://example.com/path?q=1 for details"
    _, restored = roundtrip(text)
    assert restored == text


def test_snake_case_protected():
    regex = build_sacred_regex([])
    text = "Use my_variable here"
    protected, ph = protect(text, regex)
    assert "my_variable" not in protected
    assert len(ph) == 1


def test_pascal_case_roundtrip():
    text = "Use MyClassName here"
    _, restored = roundtrip(text)
    assert restored == text


def test_multiple_sacred_segments_roundtrip():
    text = "Run `git status` and check https://github.com for issues"
    _, restored = roundtrip(text)
    assert restored == text


def test_user_sacred_words():
    regex = build_sacred_regex(["MyCustomWord"])
    text = "Use MyCustomWord here"
    protected, ph = protect(text, regex)
    assert "MyCustomWord" not in protected


# ------------------------------------------------------------------
# Sacred content survives full compression
# ------------------------------------------------------------------

def test_snake_case_not_compressed():
    c = CavemanCompressor(level=3)
    assert "my_variable" in c.compress("Use my_variable here")


def test_pascal_case_not_compressed():
    c = CavemanCompressor(level=3)
    assert "MyClassName" in c.compress("Refactor MyClassName now")


def test_numbers_not_compressed():
    c = CavemanCompressor(level=3)
    assert "42" in c.compress("Use 42 tokens max")


def test_double_quoted_string_preserved():
    c = CavemanCompressor(level=3)
    assert '"hello world"' in c.compress('The value is "hello world" here')


def test_single_quoted_string_preserved():
    c = CavemanCompressor(level=3)
    assert "'hello world'" in c.compress("The value is 'hello world' here")


def test_dunder_preserved():
    c = CavemanCompressor(level=3)
    assert "__init__" in c.compress("Call the __init__ method")
