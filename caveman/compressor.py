"""CavemanCompressor — core compression engine."""

import re

from .rules import (
    LEVEL1_PHRASES,
    LEVEL2_PHRASES,
    LEVEL2_SUBS,
    LEVEL3_PHRASE_REPLACEMENTS,
    LEVEL3_REMOVALS,
    LEVEL3_WORD_REPLACEMENTS,
)
from .sacred import build_sacred_regex, protect, restore
from .report import print_report

# Pre-compiled regex for level-3 word removals (static data, built once).
_REMOVAL_RE = re.compile(
    r"\b(?:" + "|".join(
        re.escape(w) for w in sorted(LEVEL3_REMOVALS, key=len, reverse=True)
    ) + r")\b",
    re.IGNORECASE,
)


class CavemanCompressor:
    def __init__(self, level: int = 2) -> None:
        self._level = level
        self._sacred_words: list[str] = []
        self._custom_rules: dict[str, str] = {}
        self._sacred_regex = build_sacred_regex(self._sacred_words)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compress(self, text: str) -> str:
        """Return the compressed version of *text*."""
        protected, placeholders = protect(text, self._sacred_regex)
        result = self._apply_compression(protected)
        result = restore(result, placeholders)
        result = re.sub(r"[ \t]+", " ", result).strip()
        result = re.sub(r"\n{3,}", "\n\n", result)
        # Never erase the entire prompt — return original if nothing survives
        return result if result else text.strip()

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
        self._custom_rules[from_word.lower()] = to_word
        return self

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_compression(self, text: str) -> str:
        # User-defined custom rules take priority
        for from_word, to_word in self._custom_rules.items():
            text = re.sub(
                r"\b" + re.escape(from_word) + r"\b",
                to_word,
                text,
                flags=re.IGNORECASE,
            )

        if self._level >= 1:
            text = self._apply_level1(text)
        if self._level >= 2:
            text = self._apply_level2(text)
        if self._level >= 3:
            text = self._apply_level3(text)

        return text

    def _apply_level1(self, text: str) -> str:
        for phrase in sorted(LEVEL1_PHRASES, key=len, reverse=True):
            text = re.sub(
                r"\b" + re.escape(phrase) + r"[\s,]*",
                "",
                text,
                flags=re.IGNORECASE,
            )
        return text

    def _apply_level2(self, text: str) -> str:
        # Multi-word phrases first (longest first)
        for phrase, abbrev in sorted(LEVEL2_PHRASES, key=lambda x: len(x[0]), reverse=True):
            text = re.sub(
                r"\b" + re.escape(phrase) + r"\b",
                abbrev,
                text,
                flags=re.IGNORECASE,
            )
        # Single-word substitutions
        for full, abbrev in LEVEL2_SUBS.items():
            text = re.sub(
                r"\b" + re.escape(full) + r"\b",
                abbrev,
                text,
                flags=re.IGNORECASE,
            )
        return text

    def _apply_level3(self, text: str) -> str:
        # Multi-word phrase replacements first (longest first)
        for phrase, replacement in sorted(LEVEL3_PHRASE_REPLACEMENTS, key=lambda x: len(x[0]), reverse=True):
            text = re.sub(
                r"\b" + re.escape(phrase) + r"\b",
                replacement,
                text,
                flags=re.IGNORECASE,
            )

        # Single-word replacements
        for word, replacement in LEVEL3_WORD_REPLACEMENTS.items():
            text = re.sub(
                r"\b" + re.escape(word) + r"\b",
                replacement,
                text,
                flags=re.IGNORECASE,
            )

        # Single-word removals (one combined pass)
        text = _REMOVAL_RE.sub("", text)

        return text
