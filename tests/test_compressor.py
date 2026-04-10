"""Tests for CavemanCompressor."""

from caveman import CavemanCompressor


# ------------------------------------------------------------------
# Level 1
# ------------------------------------------------------------------

def test_level1_removes_can_you_please():
    c = CavemanCompressor(level=1)
    result = c.compress("Can you please write a function")
    assert "can you please" not in result.lower()
    assert "write" in result.lower()


def test_level1_removes_could_you_please():
    c = CavemanCompressor(level=1)
    result = c.compress("Could you please explain this")
    assert "could you please" not in result.lower()


def test_level1_removes_i_was_wondering():
    c = CavemanCompressor(level=1)
    result = c.compress("I was wondering if you could help me debug this")
    assert "i was wondering" not in result.lower()
    assert "debug" in result.lower()


def test_level1_keeps_content_words():
    c = CavemanCompressor(level=1)
    result = c.compress("Can you please write a function that returns a list")
    assert "write" in result.lower()
    assert "function" in result.lower()


# ------------------------------------------------------------------
# Level 2
# ------------------------------------------------------------------

def test_level2_abbreviates_function():
    c = CavemanCompressor(level=2)
    result = c.compress("write a function")
    assert "fn" in result
    assert "function" not in result.lower()


def test_level2_abbreviates_database():
    c = CavemanCompressor(level=2)
    result = c.compress("query the database")
    assert "db" in result
    assert "database" not in result.lower()


def test_level2_returns_becomes_arrow():
    c = CavemanCompressor(level=2)
    result = c.compress("a function that returns a list")
    assert "->" in result


def test_level2_action_shortcut_write():
    c = CavemanCompressor(level=2)
    result = c.compress("write a function")
    assert "make" in result


def test_level2_preserves_filler_removal():
    c = CavemanCompressor(level=2)
    result = c.compress("Can you please write a function that returns a list?")
    assert "can you please" not in result.lower()
    assert "fn" in result
    assert "->" in result


# ------------------------------------------------------------------
# Level 3
# ------------------------------------------------------------------

def test_level3_removes_articles():
    c = CavemanCompressor(level=3)
    result = c.compress("write a function that returns a list")
    assert " a " not in f" {result} "
    assert " the " not in f" {result} "


def test_level3_removes_that():
    c = CavemanCompressor(level=3)
    result = c.compress("a function that returns something")
    assert " that " not in f" {result} "


def test_level3_removes_relative_that():
    c = CavemanCompressor(level=3)
    result = c.compress("a function that returns something")
    assert " that " not in f" {result} "


# ------------------------------------------------------------------
# Return type and chaining
# ------------------------------------------------------------------

def test_compress_returns_string():
    c = CavemanCompressor()
    assert isinstance(c.compress("hello world"), str)


def test_set_level_chainable():
    c = CavemanCompressor()
    assert c.set_level(3) is c
    assert c._level == 3


def test_add_sacred_chainable():
    c = CavemanCompressor()
    assert c.add_sacred("MyWord") is c
    assert "MyWord" in c._sacred_words


def test_add_rule_chainable():
    c = CavemanCompressor()
    assert c.add_rule("utilize", "use") is c


def test_chained_setters():
    c = CavemanCompressor()
    result = c.set_level(3).add_rule("utilize", "use")
    assert result is c
    assert c._level == 3


# ------------------------------------------------------------------
# Custom rules
# ------------------------------------------------------------------

def test_custom_rule_applied():
    c = CavemanCompressor(level=1)
    c.add_rule("utilize", "use")
    result = c.compress("utilize the function")
    assert "utilize" not in result.lower()
    assert "use" in result.lower()


def test_custom_rule_case_insensitive():
    c = CavemanCompressor(level=1)
    c.add_rule("utilize", "use")
    result = c.compress("Utilize the function")
    assert "Utilize" not in result
    assert "use" in result.lower()


# ------------------------------------------------------------------
# Sacred content preservation
# ------------------------------------------------------------------

def test_code_block_preserved():
    c = CavemanCompressor(level=3)
    code = "```python\ndef function():\n    return database\n```"
    result = c.compress(f"write this: {code}")
    assert "```python" in result
    assert "def function():" in result
    assert "return database" in result


def test_inline_code_preserved():
    c = CavemanCompressor(level=3)
    result = c.compress("use the `my_function()` method")
    assert "`my_function()`" in result


def test_url_preserved():
    c = CavemanCompressor(level=3)
    result = c.compress("check https://example.com for details")
    assert "https://example.com" in result


def test_user_sacred_word_preserved():
    c = CavemanCompressor(level=3)
    c.add_sacred("DatabaseManager")
    result = c.compress("use the DatabaseManager function")
    assert "DatabaseManager" in result


# ------------------------------------------------------------------
# Whitespace
# ------------------------------------------------------------------

def test_whitespace_normalized():
    c = CavemanCompressor(level=1)
    result = c.compress("Can you please   write   this")
    assert "  " not in result


def test_leading_trailing_stripped():
    c = CavemanCompressor(level=1)
    result = c.compress("  Can you please write this  ")
    assert result == result.strip()


# ------------------------------------------------------------------
# Smoke test matching doc example
# ------------------------------------------------------------------

def test_doc_example_level2():
    c = CavemanCompressor(level=2)
    result = c.compress("Can you please write a function that returns a list?")
    assert "fn" in result
    assert "->" in result
    assert "can you please" not in result.lower()


# ------------------------------------------------------------------
# Safety: never erase the entire prompt
# ------------------------------------------------------------------

def test_all_filler_returns_original():
    c = CavemanCompressor(level=3)
    assert c.compress("Please") == "Please"
    assert c.compress("Can you please") == "Can you please"


def test_empty_input_returns_empty():
    c = CavemanCompressor(level=3)
    assert c.compress("") == ""


# ------------------------------------------------------------------
# Per-sentence fallback
# ------------------------------------------------------------------

def test_filler_sentence_erased_in_multi_sentence():
    # A sentence that is pure filler is erased; adjacent content sentences
    # are still compressed at the configured level.
    c = CavemanCompressor(level=3)
    result = c.compress("Can you please. Write a function.")
    assert "Can you please" not in result
    assert "fn" in result


def test_filler_only_sentence_erased_adjacent_content_compressed():
    c = CavemanCompressor(level=2)
    result = c.compress("Can you please. Explain the function.")
    assert "Can you please" not in result
    assert "fn" in result


# ------------------------------------------------------------------
# L3 POS removal: sacred placeholders survive
# ------------------------------------------------------------------

def test_numbers_survive_level3():
    c = CavemanCompressor(level=3)
    result = c.compress("Increase the pool size from 5 to 20.")
    assert "5" in result
    assert "20" in result


def test_numbers_after_preposition_survive():
    c = CavemanCompressor(level=3)
    result = c.compress("Set the timeout to 30 seconds.")
    assert "30" in result


# ------------------------------------------------------------------
# L3 POS removal: bare file paths survive
# ------------------------------------------------------------------

def test_bare_filenames_survive_level3():
    c = CavemanCompressor(level=3)
    result = c.compress("Copy the function from utils.py to helpers.py.")
    assert "utils.py" in result
    assert "helpers.py" in result


def test_various_file_extensions_survive():
    c = CavemanCompressor(level=3)
    for ext in ["py", "js", "ts", "go", "rs", "java"]:
        result = c.compress(f"Edit the file main.{ext}")
        assert f"main.{ext}" in result, f"main.{ext} was stripped"


# ------------------------------------------------------------------
# L3 POS removal: L2 abbreviations survive
# ------------------------------------------------------------------

def test_rm_survives_level3():
    c = CavemanCompressor(level=3)
    result = c.compress("Don't remove the backward compatibility layer.")
    assert "rm" in result


def test_negation_with_remove_preserves_meaning():
    c = CavemanCompressor(level=3)
    result = c.compress("Make sure you don't remove the old config.")
    # "rm" must be present so "no rm" keeps the negation intact
    assert "rm" in result
    assert "no" in result
