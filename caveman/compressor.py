"""CavemanCompressor — core compression engine."""

import re

from .rules import (
    LEVEL2_PHRASES,
    LEVEL2_SUBS,
    LEVEL3_PHRASE_REPLACEMENTS,
    LEVEL3_REMOVALS,
    LEVEL3_WORD_REPLACEMENTS,
)
from .sacred import build_sacred_regex, protect, restore
from .report import print_report, token_savings
from .nlp import (
    apply_level1_nlp,
    apply_level2_nlp,
    apply_level2_phrases_nlp,
    apply_level3_nlp,
)

# Pre-compiled regexes — all static rule data compiled once at import time.
_L2_PHRASE_RE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE), abbrev)
    for phrase, abbrev in sorted(LEVEL2_PHRASES, key=lambda x: len(x[0]), reverse=True)
]

_L3_PHRASE_RE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE), repl)
    for phrase, repl in sorted(LEVEL3_PHRASE_REPLACEMENTS, key=lambda x: len(x[0]), reverse=True)
]

_L3_WORD_RE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(word) + r"\b", re.IGNORECASE), repl)
    for word, repl in LEVEL3_WORD_REPLACEMENTS.items()
]

# Replacement values that must survive POS-based removal (e.g. "no" tagged as DET).
# L2 abbreviations are included because spaCy can mistag unknown words like "rm" as ADP.
# "without" is explicitly protected — it is an ADP but carries negation meaning.
_L3_SKIP_LOWER: frozenset[str] = (
    frozenset(LEVEL3_WORD_REPLACEMENTS.values())
    | frozenset(LEVEL2_SUBS.values())
    | {"without"}
)

_L3_REMOVAL_RE = re.compile(
    r"\b(?:" + "|".join(
        re.escape(w) for w in sorted(LEVEL3_REMOVALS, key=len, reverse=True)
    # Negative lookahead: don't match words attached to a contraction suffix
    # (e.g. "that" in "that's") — removing the host word orphans the suffix.
    ) + r")\b(?!')",
    re.IGNORECASE,
)


class CavemanCompressor:
    def __init__(self, level: int = 2) -> None:
        self._level = level
        self._sacred_words: list[str] = []
        self._custom_rules: list[tuple[re.Pattern, str]] = []
        self._sacred_regex = build_sacred_regex(self._sacred_words)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compress(self, text: str, verbose: bool = False):
        """Return the compressed version of *text*.

        When *verbose* is True, return a (compressed_text, stats) tuple
        where stats contains: original_tokens, compressed_tokens,
        saved_tokens, saved_pct.
        """
        protected, placeholders = protect(text, self._sacred_regex)
        result = self._apply_compression(protected)
        # Normalize whitespace BEFORE restoring sacred content so that
        # indentation inside code blocks is not collapsed.
        result = re.sub(r"[ \t]+", " ", result).strip()
        result = re.sub(r"\n{3,}", "\n\n", result)
        # Clean up orphaned leading/trailing punctuation left after filler removal
        result = re.sub(r"^[,;:\s]+", "", result)
        result = re.sub(r"\n[,;:\s]+", "\n", result)
        result = restore(result, placeholders)
        # Never erase the entire prompt — return original if nothing survives
        result = result if result else text.strip()
        if verbose:
            return result, token_savings(text, result)
        return result

    def report(self, text: str) -> None:
        """Compress *text* and pretty-print the token-savings breakdown."""
        print_report(text, self.compress(text))

    def set_level(self, level: int) -> "CavemanCompressor":
        self._level = level
        return self

    def add_sacred(self, word: str) -> "CavemanCompressor":
        if word not in self._sacred_words:
            self._sacred_words.append(word)
            self._sacred_regex = build_sacred_regex(self._sacred_words)
        return self

    def add_rule(self, from_word: str, to_word: str) -> "CavemanCompressor":
        pattern = re.compile(r"\b" + re.escape(from_word.lower()) + r"\b", re.IGNORECASE)
        self._custom_rules.append((pattern, to_word))
        return self

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_compression(self, text: str) -> str:
        parts = re.split(r'(\n+|(?<=[.!?])\s+)', text)
        return "".join(
            self._compress_segment(part) if part and part.strip() else part
            for part in parts
        )

    def _compress_segment(self, text: str) -> str:
        """Compress one sentence, falling back a level if no word characters survive.

        If every level strips all word content the segment is pure filler and is
        erased entirely. The full-prompt guard in compress() ensures the overall
        result is never blank.
        """
        for level in range(self._level, 0, -1):
            compressed = self._apply_up_to_level(text, level)
            if re.search(r'\w', compressed):
                return compressed
        return ""

    def _apply_up_to_level(self, text: str, level: int) -> str:
        for pattern, to_word in self._custom_rules:
            text = pattern.sub(to_word, text)

        if level >= 1:
            text = apply_level1_nlp(text)
        if level >= 2:
            text = self._apply_level2(text)
        if level >= 3:
            text = self._apply_level3(text)

        return text

    def _apply_level2(self, text: str) -> str:
        # NLP-based phrase simplification (Matcher with lemma/POS patterns)
        text = apply_level2_phrases_nlp(text)
        # Tech abbreviation phrases (regex — these are simple acronym expansions)
        for pattern, abbrev in _L2_PHRASE_RE:
            text = pattern.sub(abbrev, text)
        # POS-gated filler adverb removal + determiner removal + tech word subs
        return apply_level2_nlp(text, LEVEL2_SUBS)

    def _apply_level3(self, text: str) -> str:
        for pattern, replacement in _L3_PHRASE_RE:
            text = pattern.sub(replacement, text)
        for pattern, replacement in _L3_WORD_RE:
            text = pattern.sub(replacement, text)
        # POS-based removal (DET, AUX, PRON, ADP) — re-parsed after replacements above
        text = apply_level3_nlp(text, _L3_SKIP_LOWER)
        # Remaining filler adverbs not catchable by POS alone
        return _L3_REMOVAL_RE.sub("", text)
